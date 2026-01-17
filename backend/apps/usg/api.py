from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone

from .models import (
    UsgTemplate, UsgServiceProfile, UsgStudy,
    UsgFieldValue, UsgPublishedSnapshot
)
from .serializers import (
    UsgTemplateSerializer, UsgServiceProfileSerializer,
    UsgStudySerializer, UsgFieldValueSerializer,
    UsgFieldValueBulkSerializer, UsgPublishedSnapshotSerializer
)
from .renderer import render_usg_report, render_usg_report_with_metadata
from .pdf_generator import generate_usg_pdf
from .google_drive import upload_pdf_to_drive, get_pdf_from_drive


class UsgTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List and retrieve USG report templates.
    Read-only: templates are loaded via management command.
    """
    queryset = UsgTemplate.objects.all()
    serializer_class = UsgTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['code', 'category', 'version', 'is_locked']
    search_fields = ['code', 'name', 'category']
    ordering_fields = ['code', 'version', 'created_at']


class UsgServiceProfileViewSet(viewsets.ModelViewSet):
    """
    Manage service-to-template mappings.
    """
    queryset = UsgServiceProfile.objects.select_related('template').all()
    serializer_class = UsgServiceProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['service_code', 'template']
    search_fields = ['service_code']


class UsgStudyViewSet(viewsets.ModelViewSet):
    """
    Manage USG studies with immutability enforcement.
    """
    queryset = UsgStudy.objects.select_related(
        'patient', 'visit', 'template',
        'created_by', 'verified_by', 'published_by'
    ).prefetch_related('field_values').all()
    serializer_class = UsgStudySerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status', 'patient', 'visit', 'service_code']
    search_fields = ['patient__name', 'patient__mrn', 'visit__visit_number', 'service_code']
    ordering_fields = ['created_at', 'published_at']

    def get_queryset(self):
        """Filter based on query parameters"""
        queryset = super().get_queryset()
        
        # Filter by visit if provided
        visit_id = self.request.query_params.get('visit_id')
        if visit_id:
            queryset = queryset.filter(visit_id=visit_id)
        
        return queryset

    def perform_create(self, serializer):
        """Set created_by on creation"""
        serializer.save(created_by=self.request.user)

    def update(self, request, *args, **kwargs):
        """Block updates to published studies"""
        instance = self.get_object()
        if instance.status == 'published':
            return Response(
                {'detail': 'Cannot modify a published study'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """Block partial updates to published studies"""
        instance = self.get_object()
        if instance.status == 'published':
            return Response(
                {'detail': 'Cannot modify a published study'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Block deletion of published studies"""
        instance = self.get_object()
        if instance.status == 'published':
            return Response(
                {'detail': 'Cannot delete a published study'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['put', 'patch'], url_path='values')
    def update_values(self, request, pk=None):
        """
        Bulk update field values for a study.
        
        Expects:
        {
            "values": [
                {"field_key": "liver_size", "value_json": "normal", "is_not_applicable": false},
                {"field_key": "gb_calculi", "value_json": null, "is_not_applicable": true}
            ]
        }
        """
        study = self.get_object()
        
        # Block if published
        if study.status == 'published':
            return Response(
                {'detail': 'Cannot modify field values of a published study'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        values_data = request.data.get('values', [])
        
        # Validate bulk data
        serializer = UsgFieldValueBulkSerializer(data=values_data, many=True)
        serializer.is_valid(raise_exception=True)
        
        # Update or create field values
        with transaction.atomic():
            for item in serializer.validated_data:
                UsgFieldValue.objects.update_or_create(
                    study=study,
                    field_key=item['field_key'],
                    defaults={
                        'value_json': item.get('value_json'),
                        'is_not_applicable': item.get('is_not_applicable', False),
                        'updated_by': request.user
                    }
                )
        
        return Response({'detail': 'Field values updated successfully'})

    @action(detail=True, methods=['post'], url_path='render')
    def render_preview(self, request, pk=None):
        """
        Preview rendered narrative for draft studies.
        Does NOT save anything, just returns the rendered text.
        """
        study = self.get_object()
        
        # Get template schema
        template_schema = study.template.schema_json
        
        # Get field values
        field_values = study.field_values.all()
        field_values_dict = {
            fv.field_key: {
                'value_json': fv.value_json,
                'is_not_applicable': fv.is_not_applicable
            }
            for fv in field_values
        }
        
        # Render narrative
        narrative = render_usg_report(template_schema, field_values_dict)
        
        # Also get full report with metadata
        full_report = render_usg_report_with_metadata(
            template_schema, field_values_dict, study, study.patient
        )
        
        return Response({
            'narrative': narrative,
            'full_report': full_report,
            'renderer_version': 'usg_renderer_v1'
        })

    @action(detail=True, methods=['post'], url_path='publish')
    def publish_study(self, request, pk=None):
        """
        Publish a study: creates immutable snapshot, generates PDF, uploads to Drive.
        
        Steps:
        1. Validate study is not already published
        2. Freeze field values into published_json_snapshot
        3. Generate published_text_snapshot using renderer v1
        4. Create PDF using layout v1
        5. Upload PDF to Google Drive
        6. Create UsgPublishedSnapshot
        7. Set study status to 'published'
        """
        study = self.get_object()
        
        # Check if already published
        if study.status == 'published':
            return Response(
                {'detail': 'Study is already published'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            # Get template schema
            template_schema = study.template.schema_json
            
            # Freeze field values
            field_values = study.field_values.all()
            published_json_snapshot = {
                fv.field_key: {
                    'value_json': fv.value_json,
                    'is_not_applicable': fv.is_not_applicable
                }
                for fv in field_values
            }
            
            # Generate narrative text
            published_text_snapshot = render_usg_report_with_metadata(
                template_schema, published_json_snapshot, study, study.patient
            )
            
            # Generate PDF
            pdf_content = generate_usg_pdf(
                published_text_snapshot,
                study.patient,
                study.visit,
                study,
                published_by=request.user
            )
            
            # Upload to Google Drive
            filename = f"USG_{study.service_code}_{study.patient.mrn}_{study.visit.visit_number}_{study.id}.pdf"
            drive_result = upload_pdf_to_drive(pdf_content, filename, study)
            
            pdf_drive_file_id = None
            pdf_drive_folder_id = None
            pdf_sha256 = None
            
            if drive_result:
                pdf_drive_file_id = drive_result['file_id']
                pdf_drive_folder_id = drive_result['folder_id']
                pdf_sha256 = drive_result['sha256']
            
            # Create published snapshot
            snapshot = UsgPublishedSnapshot.objects.create(
                study=study,
                template_code=study.template.code,
                template_version=study.template.version,
                renderer_version='usg_renderer_v1',
                published_json_snapshot=published_json_snapshot,
                published_text_snapshot=published_text_snapshot,
                pdf_drive_file_id=pdf_drive_file_id,
                pdf_drive_folder_id=pdf_drive_folder_id,
                pdf_sha256=pdf_sha256,
                published_by=request.user
            )
            
            # Update study status
            study.status = 'published'
            study.published_by = request.user
            study.published_at = timezone.now()
            study.save()
        
        return Response({
            'detail': 'Study published successfully',
            'snapshot_id': snapshot.id,
            'pdf_drive_file_id': pdf_drive_file_id
        })

    @action(detail=True, methods=['get'], url_path='pdf')
    def get_pdf(self, request, pk=None):
        """
        Retrieve PDF for a published study.
        
        - If Drive file exists: stream from Drive
        - If Drive file missing: regenerate from published_text_snapshot
        """
        study = self.get_object()
        
        if study.status != 'published':
            return Response(
                {'detail': 'PDF is only available for published studies'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get snapshot
        try:
            snapshot = study.published_snapshot
        except UsgPublishedSnapshot.DoesNotExist:
            return Response(
                {'detail': 'Published snapshot not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Try to get from Drive
        if snapshot.pdf_drive_file_id:
            pdf_bytes = get_pdf_from_drive(snapshot.pdf_drive_file_id)
            
            if pdf_bytes:
                response = HttpResponse(pdf_bytes, content_type='application/pdf')
                response['Content-Disposition'] = f'inline; filename="usg_report_{study.id}.pdf"'
                return response
        
        # Drive file missing, regenerate from published_text_snapshot
        pdf_content = generate_usg_pdf(
            snapshot.published_text_snapshot,
            study.patient,
            study.visit,
            study,
            published_by=snapshot.published_by
        )
        
        # Re-upload to Drive
        filename = f"USG_{study.service_code}_{study.patient.mrn}_{study.visit.visit_number}_{study.id}.pdf"
        drive_result = upload_pdf_to_drive(pdf_content, filename, study)
        
        if drive_result:
            # Update snapshot with new file ID
            snapshot.pdf_drive_file_id = drive_result['file_id']
            snapshot.pdf_drive_folder_id = drive_result['folder_id']
            snapshot.pdf_sha256 = drive_result['sha256']
            snapshot.audit_note = (
                f"{snapshot.audit_note or ''}\n"
                f"PDF regenerated from published text snapshot on {timezone.now().isoformat()}"
            ).strip()
            snapshot.save()
        
        # Return PDF
        response = HttpResponse(pdf_content.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="usg_report_{study.id}.pdf"'
        return response


class UsgPublishedSnapshotViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only access to published snapshots.
    Snapshots are created via the publish endpoint.
    """
    queryset = UsgPublishedSnapshot.objects.select_related(
        'study', 'study__patient', 'study__visit', 'published_by'
    ).all()
    serializer_class = UsgPublishedSnapshotSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['study', 'template_code', 'template_version']
    search_fields = ['study__patient__name', 'study__patient__mrn', 'template_code']
    ordering_fields = ['published_at']
