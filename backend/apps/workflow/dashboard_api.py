"""
Dashboard API endpoints for role-based dashboard v1.

Provides:
- GET /api/dashboard/summary/ - KPI counts for Layer 1
- GET /api/dashboard/worklist/ - Work items for Layer 2 (role-based)
- GET /api/dashboard/flow/ - Today's flow counts for Layer 3
"""
import logging
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q, Count, F, Case, When, IntegerField
from django.db import connection
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import ServiceVisit, ServiceVisitItem, Payment
from apps.patients.models import Patient
from apps.catalog.models import Modality
from .transitions import get_user_roles

logger = logging.getLogger(__name__)

# Default threshold for critical delays (4 hours)
DEFAULT_CRITICAL_DELAY_HOURS = 4


def is_admin(user):
    """Check if user is admin (superuser or in ADMIN group)"""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name__iexact="admin").exists()


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_summary(request):
    """
    GET /api/dashboard/summary/?date=today
    
    Returns KPI counts for Layer 1 (Global Status Strip):
    - total_patients_today
    - total_services_today
    - reports_pending
    - reports_verified
    - critical_delays
    
    All counts are for "today" (server timezone).
    """
    # Get today's date range (server timezone)
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    # Get threshold for critical delays (from query param or default)
    threshold_hours = int(request.query_params.get("threshold_hours", DEFAULT_CRITICAL_DELAY_HOURS))
    threshold_time = now - timedelta(hours=threshold_hours)
    
    # Total patients today (visits registered today)
    total_patients_today = ServiceVisit.objects.filter(
        registered_at__gte=today_start,
        registered_at__lt=today_end
    ).values('patient').distinct().count()
    
    # Total services today (items created today)
    total_services_today = ServiceVisitItem.objects.filter(
        created_at__gte=today_start,
        created_at__lt=today_end
    ).count()
    
    # Reports pending (items in PENDING_VERIFICATION status)
    reports_pending = ServiceVisitItem.objects.filter(
        status="PENDING_VERIFICATION"
    ).count()
    
    # Reports verified (items PUBLISHED today)
    reports_verified = ServiceVisitItem.objects.filter(
        status="PUBLISHED",
        published_at__gte=today_start,
        published_at__lt=today_end
    ).count()
    
    # Critical delays: items in reporting pipeline pending > threshold_hours
    # This includes items in IN_PROGRESS or PENDING_VERIFICATION that have been waiting too long
    critical_delays = ServiceVisitItem.objects.filter(
        Q(status="IN_PROGRESS") | Q(status="PENDING_VERIFICATION")
    ).filter(
        Q(started_at__lt=threshold_time) | Q(submitted_at__lt=threshold_time) | Q(created_at__lt=threshold_time)
    ).count()
    
    return Response({
        "date": today_start.date().isoformat(),
        "server_time": now.isoformat(),
        "total_patients_today": total_patients_today,
        "total_services_today": total_services_today,
        "reports_pending": reports_pending,
        "reports_verified": reports_verified,
        "critical_delays": critical_delays,
        "threshold_hours": threshold_hours,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_worklist(request):
    """
    GET /api/dashboard/worklist/?scope=my|department&department=USG|OPD|...
    
    Returns work items for Layer 2 (Work In Progress).
    
    Role-based behavior:
    - Admin: scope=department (default), shows all departments grouped
    - Non-admin: scope=my (only), shows items assigned to or created by user
    
    Each item includes:
    - id (item id)
    - visit_id
    - patient_name, patient_mrn
    - service_name, department
    - status
    - created_at, last_updated
    - waiting_minutes
    - assigned_to (optional)
    - action_url
    """
    user = request.user
    scope = request.query_params.get("scope", "my" if not is_admin(user) else "department")
    department_filter = request.query_params.get("department", None)
    
    # Base queryset: items that are in work (not PUBLISHED, CANCELLED, or REGISTERED)
    work_statuses = ["IN_PROGRESS", "PENDING_VERIFICATION", "RETURNED_FOR_CORRECTION", "FINALIZED"]
    queryset = ServiceVisitItem.objects.filter(
        status__in=work_statuses
    ).select_related(
        "service_visit", "service_visit__patient", "service_visit__assigned_to", "service_visit__created_by", "service"
    ).order_by(
        "created_at"  # Longest waiting first
    )
    
    # Role-based filtering
    if scope == "my" and not is_admin(user):
        # Non-admin: only items assigned to me or created by me (via visit)
        # Note: assigned_to is at ServiceVisit level, not Item level
        queryset = queryset.filter(
            Q(service_visit__assigned_to=user) |
            Q(service_visit__created_by=user)
        )
    elif scope == "department" and is_admin(user):
        # Admin: filter by department if specified
        if department_filter:
            queryset = queryset.filter(department_snapshot=department_filter)
        # Otherwise show all departments (will be grouped in response)
    else:
        # Invalid scope for user role
        return Response(
            {"detail": f"Invalid scope '{scope}' for user role"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Calculate waiting time and build response
    now = timezone.now()
    items = []
    for item in queryset[:100]:  # Limit to 100 items
        # Calculate waiting minutes
        waiting_since = item.started_at or item.submitted_at or item.created_at
        if waiting_since:
            waiting_minutes = int((now - waiting_since).total_seconds() / 60)
        else:
            waiting_minutes = 0
        
        # Build action URL based on department and status
        action_url = None
        if item.department_snapshot == "USG":
            action_url = f"/worklists/usg?item_id={item.id}"
        elif item.department_snapshot == "OPD":
            action_url = f"/worklists/opd?item_id={item.id}"
        else:
            action_url = f"/worklists/verification?item_id={item.id}"
        
        items.append({
            "id": str(item.id),
            "visit_id": item.service_visit.visit_id,
            "patient_name": item.service_visit.patient.name,
            "patient_mrn": item.service_visit.patient.mrn,
            "service_name": item.service_name_snapshot,
            "department": item.department_snapshot,
            "status": item.status,
            "status_display": dict(ServiceVisitItem._meta.get_field("status").choices).get(item.status, item.status),
            "created_at": item.created_at.isoformat(),
            "last_updated": item.updated_at.isoformat(),
            "waiting_minutes": waiting_minutes,
            "assigned_to": item.service_visit.assigned_to.username if item.service_visit.assigned_to else None,
            "action_url": action_url,
        })
    
    # If admin and no department filter, group by department
    if scope == "department" and is_admin(user) and not department_filter:
        grouped = {}
        for item in items:
            dept = item["department"]
            if dept not in grouped:
                grouped[dept] = []
            grouped[dept].append(item)
        
        return Response({
            "scope": "department",
            "grouped_by_department": grouped,
            "total_items": len(items),
        })
    
    return Response({
        "scope": scope,
        "items": items,
        "total_items": len(items),
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_flow(request):
    """
    GET /api/dashboard/flow/?date=today
    
    Returns counts for Layer 3 (Today's Flow):
    - registered_count
    - paid_count (visits with payments today)
    - performed_count (items moved to IN_PROGRESS today)
    - reported_count (items moved to PENDING_VERIFICATION today)
    - verified_count (items PUBLISHED today)
    """
    # Get today's date range (server timezone)
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    # Registered: visits registered today
    registered_count = ServiceVisit.objects.filter(
        registered_at__gte=today_start,
        registered_at__lt=today_end
    ).count()
    
    # Paid: visits with payments today
    paid_count = ServiceVisit.objects.filter(
        payments__received_at__gte=today_start,
        payments__received_at__lt=today_end
    ).distinct().count()
    
    # Performed: items moved to IN_PROGRESS today
    performed_count = ServiceVisitItem.objects.filter(
        status="IN_PROGRESS",
        started_at__gte=today_start,
        started_at__lt=today_end
    ).count()
    
    # Reported: items moved to PENDING_VERIFICATION today
    reported_count = ServiceVisitItem.objects.filter(
        status="PENDING_VERIFICATION",
        submitted_at__gte=today_start,
        submitted_at__lt=today_end
    ).count()
    
    # Verified: items PUBLISHED today
    verified_count = ServiceVisitItem.objects.filter(
        status="PUBLISHED",
        published_at__gte=today_start,
        published_at__lt=today_end
    ).count()
    
    return Response({
        "date": today_start.date().isoformat(),
        "server_time": now.isoformat(),
        "registered_count": registered_count,
        "paid_count": paid_count,
        "performed_count": performed_count,
        "reported_count": reported_count,
        "verified_count": verified_count,
    })
