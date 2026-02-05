"""
Template Governance Views

Provides admin-only actions for template versioning, cloning, freezing, archiving,
and audit logging.
"""
import csv
import io
from django.db import transaction
from django.utils import timezone
from django.http import HttpResponse
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from .models import (
    ReportProfile, ReportParameter, ReportParameterOption,
    ServiceReportProfile, TemplateAuditLog
)
from .serializers import (
    ReportProfileSerializer, TemplateAuditLogSerializer, ProfileListSerializer
)


def log_audit(user, action_type, entity_type, entity_id, metadata=None):
    """
    Helper function to create an audit log entry.
    """
    TemplateAuditLog.objects.create(
        actor=user,
        action=action_type,
        entity_type=entity_type,
        entity_id=str(entity_id),
        metadata=metadata or {}
    )


class TemplateGovernanceViewSet(viewsets.ViewSet):
    """
    Admin-only governance actions for report profiles (templates).
    
    Endpoints:
    - POST /clone/ - Clone a template to create a new draft version
    - POST /activate/ - Activate a draft version (deactivate others with same code)
    - POST /freeze/ - Freeze a template to prevent edits
    - POST /unfreeze/ - Unfreeze a template to allow edits
    - POST /archive/ - Archive a template (soft delete)
    """
    permission_classes = [IsAuthenticated, permissions.IsAdminUser]

    def _get_profile(self, pk):
        try:
            return ReportProfile.objects.get(pk=pk)
        except ReportProfile.DoesNotExist:
            return None

    @action(detail=True, methods=["post"], url_path="clone")
    def clone(self, request, pk=None):
        """
        Clone a template to create a new draft version.
        
        Creates a new profile with:
        - version = old.version + 1
        - status = draft
        - copies all parameters and options
        - revision_of = old.id
        """
        original = self._get_profile(pk)
        if not original:
            return Response({"detail": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Determine new version number
        max_version = ReportProfile.objects.filter(code=original.code).order_by("-version").first()
        new_version = (max_version.version if max_version else original.version) + 1
        
        with transaction.atomic():
            # Create new profile
            new_profile = ReportProfile.objects.create(
                code=original.code,
                name=original.name,
                modality=original.modality,
                enable_narrative=original.enable_narrative,
                narrative_mode=original.narrative_mode,
                is_active=original.is_active,
                version=new_version,
                revision_of=original,
                status="draft",
                is_frozen=False,
            )
            
            # Copy parameters
            for param in original.parameters.all():
                old_param_id = param.id
                param.pk = None  # Create new
                param.id = None
                param.profile = new_profile
                param.save()
                
                # Copy options for this parameter
                for option in ReportParameterOption.objects.filter(parameter_id=old_param_id):
                    option.pk = None
                    option.id = None
                    option.parameter = param
                    option.save()
            
            # Log audit
            log_audit(
                request.user,
                "clone",
                "report_profile",
                new_profile.id,
                {
                    "source_id": str(original.id),
                    "source_version": original.version,
                    "new_version": new_version,
                    "code": original.code,
                }
            )
        
        serializer = ReportProfileSerializer(new_profile)
        return Response({
            "detail": f"Cloned {original.code} v{original.version} to v{new_version}",
            "profile": serializer.data,
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="activate")
    def activate(self, request, pk=None):
        """
        Activate a draft version.
        
        - Deactivates any other active version with the same code
        - Sets this version as active
        - Records activated_by/at
        - Requires confirmation phrase "ACTIVATE" in request body
        """
        profile = self._get_profile(pk)
        if not profile:
            return Response({"detail": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if profile.status == "active":
            return Response({"detail": "Profile is already active"}, status=status.HTTP_400_BAD_REQUEST)
        
        if profile.status == "archived":
            return Response({"detail": "Cannot activate an archived profile"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Require confirmation
        confirmation = request.data.get("confirmation", "")
        if confirmation != "ACTIVATE":
            return Response({
                "detail": "Confirmation required. Send { \"confirmation\": \"ACTIVATE\" } to proceed.",
                "requires_confirmation": True,
            }, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            # Deactivate other active versions with same code
            other_active = ReportProfile.objects.filter(
                code=profile.code, 
                status="active"
            ).exclude(pk=profile.pk)
            
            for other in other_active:
                other.status = "archived"
                other.archived_at = timezone.now()
                other.archived_by = request.user
                other.save()
                
                log_audit(
                    request.user,
                    "archive",
                    "report_profile",
                    other.id,
                    {"reason": "Replaced by new active version", "new_active_id": str(profile.id)}
                )
            
            # Activate this version
            profile.status = "active"
            profile.activated_at = timezone.now()
            profile.activated_by = request.user
            profile.save()
            
            log_audit(
                request.user,
                "activate",
                "report_profile",
                profile.id,
                {
                    "version": profile.version,
                    "code": profile.code,
                    "deactivated_count": other_active.count(),
                }
            )
        
        serializer = ReportProfileSerializer(profile)
        return Response({
            "detail": f"Activated {profile.code} v{profile.version}",
            "profile": serializer.data,
        })

    @action(detail=True, methods=["post"], url_path="freeze")
    def freeze(self, request, pk=None):
        """
        Freeze a template to prevent edits.
        """
        profile = self._get_profile(pk)
        if not profile:
            return Response({"detail": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if profile.is_frozen:
            return Response({"detail": "Profile is already frozen"}, status=status.HTTP_400_BAD_REQUEST)
        
        profile.is_frozen = True
        profile.save()
        
        log_audit(
            request.user,
            "freeze",
            "report_profile",
            profile.id,
            {"version": profile.version, "code": profile.code}
        )
        
        serializer = ReportProfileSerializer(profile)
        return Response({
            "detail": f"Froze {profile.code} v{profile.version}",
            "profile": serializer.data,
        })

    @action(detail=True, methods=["post"], url_path="unfreeze")
    def unfreeze(self, request, pk=None):
        """
        Unfreeze a template to allow edits.
        """
        profile = self._get_profile(pk)
        if not profile:
            return Response({"detail": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if not profile.is_frozen:
            return Response({"detail": "Profile is not frozen"}, status=status.HTTP_400_BAD_REQUEST)
        
        profile.is_frozen = False
        profile.save()
        
        log_audit(
            request.user,
            "unfreeze",
            "report_profile",
            profile.id,
            {"version": profile.version, "code": profile.code}
        )
        
        serializer = ReportProfileSerializer(profile)
        return Response({
            "detail": f"Unfroze {profile.code} v{profile.version}",
            "profile": serializer.data,
        })

    @action(detail=True, methods=["post"], url_path="archive")
    def archive(self, request, pk=None):
        """
        Archive a template (soft delete).
        
        Only allowed if not active.
        Requires confirmation phrase "ARCHIVE" in request body.
        """
        profile = self._get_profile(pk)
        if not profile:
            return Response({"detail": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if profile.status == "active":
            return Response({
                "detail": "Cannot archive an active profile. Activate another version first or deactivate this one.",
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if profile.status == "archived":
            return Response({"detail": "Profile is already archived"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Require confirmation
        confirmation = request.data.get("confirmation", "")
        if confirmation != "ARCHIVE":
            return Response({
                "detail": "Confirmation required. Send { \"confirmation\": \"ARCHIVE\" } to proceed.",
                "requires_confirmation": True,
            }, status=status.HTTP_400_BAD_REQUEST)
        
        profile.status = "archived"
        profile.archived_at = timezone.now()
        profile.archived_by = request.user
        profile.save()
        
        log_audit(
            request.user,
            "archive",
            "report_profile",
            profile.id,
            {"version": profile.version, "code": profile.code, "reason": "Manual archive"}
        )
        
        serializer = ReportProfileSerializer(profile)
        return Response({
            "detail": f"Archived {profile.code} v{profile.version}",
            "profile": serializer.data,
        })

    @action(detail=True, methods=["get"], url_path="versions")
    def versions(self, request, pk=None):
        """
        Get all versions of a template by its code.
        """
        profile = self._get_profile(pk)
        if not profile:
            return Response({"detail": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
        
        versions = ReportProfile.objects.filter(code=profile.code).order_by("-version")
        serializer = ProfileListSerializer(versions, many=True)
        return Response({
            "code": profile.code,
            "versions": serializer.data,
        })


class TemplateAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset for template audit logs.
    
    GET /api/admin/audit-logs/ - List all audit logs
    GET /api/admin/audit-logs/?entity=report_profile&id=... - Filter by entity
    """
    queryset = TemplateAuditLog.objects.all()
    serializer_class = TemplateAuditLogSerializer
    permission_classes = [IsAuthenticated, permissions.IsAdminUser]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by entity type
        entity_type = self.request.query_params.get("entity")
        if entity_type:
            queryset = queryset.filter(entity_type=entity_type)
        
        # Filter by entity ID
        entity_id = self.request.query_params.get("id")
        if entity_id:
            queryset = queryset.filter(entity_id=entity_id)
        
        # Filter by action
        action_filter = self.request.query_params.get("action")
        if action_filter:
            queryset = queryset.filter(action=action_filter)
        
        # Filter by actor
        actor = self.request.query_params.get("actor")
        if actor:
            queryset = queryset.filter(actor__username__icontains=actor)
        
        return queryset

    @action(detail=False, methods=["get"], url_path="export-csv")
    def export_csv(self, request):
        """Export audit logs to CSV."""
        queryset = self.get_queryset()
        
        output = io.StringIO()
        fieldnames = ["timestamp", "actor", "action", "entity_type", "entity_id", "metadata"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for log in queryset[:1000]:  # Limit to 1000 records
            writer.writerow({
                "timestamp": log.timestamp.isoformat(),
                "actor": log.actor.username if log.actor else "",
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "metadata": str(log.metadata),
            })
        
        response = HttpResponse(output.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="audit_logs_export.csv"'
        return response
