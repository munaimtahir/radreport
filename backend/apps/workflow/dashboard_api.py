import logging
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import ServiceVisit, ServiceVisitItem, Payment
from apps.patients.models import Patient
from apps.catalog.models import Modality

logger = logging.getLogger(__name__)

DEFAULT_CRITICAL_DELAY_HOURS = 4

def is_admin(user):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name__iexact="admin").exists()

def get_status_display(status_code):
    return dict(ServiceVisitItem._meta.get_field("status").choices).get(status_code, status_code)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_summary(request):
    user = request.user
    admin_flag = is_admin(user)
    scope = request.query_params.get("scope", "department" if admin_flag else "my")
    
    # Timezone handling
    now = timezone.now()
    local_now = timezone.localtime(now)
    tz_used = getattr(settings, "TIME_ZONE", "UTC")
    today_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    threshold_hours = int(request.query_params.get("threshold_hours", DEFAULT_CRITICAL_DELAY_HOURS))
    threshold_time = now - timedelta(hours=threshold_hours)

    tenant_id = None # No tenancy model found in codebase
    
    # Metric computations
    total_patients_today = ServiceVisit.objects.filter(
        registered_at__gte=today_start, registered_at__lt=today_end
    ).values('patient').distinct().count()
    
    total_services_today = ServiceVisitItem.objects.filter(
        created_at__gte=today_start, created_at__lt=today_end
    ).count()
    
    reports_pending = ServiceVisitItem.objects.filter(
        status="PENDING_VERIFICATION"
    ).count()
    
    reports_verified = ServiceVisitItem.objects.filter(
        status="PUBLISHED",
        published_at__gte=today_start,
        published_at__lt=today_end
    ).count()
    
    critical_delays = ServiceVisitItem.objects.filter(
        Q(status="IN_PROGRESS") | Q(status="PENDING_VERIFICATION"),
        Q(started_at__lt=threshold_time) | Q(submitted_at__lt=threshold_time) | Q(created_at__lt=threshold_time)
    ).count()

    metrics = [
        {
            "key": "total_patients_today",
            "label": "Total Patients Today",
            "value": total_patients_today,
            "definition": f"Count of distinct patients from visits registered today ({tz_used} timezone)."
        },
        {
            "key": "total_services_today",
            "label": "Total Services Today",
            "value": total_services_today,
            "definition": f"Count of service visit items created today ({tz_used} timezone)."
        },
        {
            "key": "reports_pending",
            "label": "Reports Pending",
            "value": reports_pending,
            "definition": "Count of all items currently in PENDING_VERIFICATION status globally."
        },
        {
            "key": "reports_verified",
            "label": "Reports Verified Today",
            "value": reports_verified,
            "definition": f"Count of items published today ({tz_used} timezone)."
        },
        {
            "key": "critical_delays",
            "label": "Critical Delays",
            "value": critical_delays,
            "definition": f"Count of items in IN_PROGRESS or PENDING_VERIFICATION longer than {threshold_hours} hours."
        }
    ]

    # Flow computations
    registered_count = ServiceVisit.objects.filter(registered_at__gte=today_start, registered_at__lt=today_end).count()
    paid_count = ServiceVisit.objects.filter(payments__received_at__gte=today_start, payments__received_at__lt=today_end).distinct().count()
    performed_count = ServiceVisitItem.objects.filter(status="IN_PROGRESS", started_at__gte=today_start, started_at__lt=today_end).count()
    reported_count = ServiceVisitItem.objects.filter(status="PENDING_VERIFICATION", submitted_at__gte=today_start, submitted_at__lt=today_end).count()
    verified_count = ServiceVisitItem.objects.filter(status="PUBLISHED", published_at__gte=today_start, published_at__lt=today_end).count()
    
    flow = {
        "registered_count": registered_count,
        "paid_count": paid_count,
        "performed_count": performed_count,
        "reported_count": reported_count,
        "verified_count": verified_count,
    }

    # Worklist query
    work_statuses = ["IN_PROGRESS", "PENDING_VERIFICATION", "RETURNED_FOR_CORRECTION", "FINALIZED"]
    worklist_qs = ServiceVisitItem.objects.filter(
        status__in=work_statuses
    ).select_related(
        "service_visit", "service_visit__patient", "service_visit__assigned_to", "service_visit__created_by", "service"
    ).order_by("created_at")
    
    if scope == "my" and not admin_flag:
        worklist_qs = worklist_qs.filter(
            Q(service_visit__assigned_to=user) | Q(service_visit__created_by=user)
        )
    
    work_items = []
    for item in worklist_qs[:100]:
        waiting_since = item.started_at or item.submitted_at or item.created_at
        waiting_minutes = int((now - waiting_since).total_seconds() / 60) if waiting_since else 0
        
        action_url = None
        if item.status in ["IN_PROGRESS", "RETURNED_FOR_CORRECTION"]:
            action_url = f"/worklist/{item.id}/report"
        elif item.department_snapshot == "USG":
            action_url = f"/worklists/usg?item_id={item.id}"
        elif item.department_snapshot == "OPD":
            action_url = f"/worklists/opd?item_id={item.id}"
        else:
            action_url = f"/worklists/verification?item_id={item.id}"
            
        work_items.append({
            "id": str(item.id),
            "visit_id": str(item.service_visit.id) if item.service_visit else "",
            "patient_name": item.service_visit.patient.name,
            "patient_mrn": item.service_visit.patient.mrn,
            "service_name": item.service_name_snapshot,
            "department": item.department_snapshot,
            "status": item.status,
            "status_display": get_status_display(item.status),
            "created_at": item.created_at.isoformat(),
            "last_updated": item.updated_at.isoformat(),
            "waiting_minutes": waiting_minutes,
            "assigned_to": item.service_visit.assigned_to.username if item.service_visit.assigned_to else None,
            "action_url": action_url,
        })
    
    grouped_by_department = None
    if scope == "department" and admin_flag:
        grouped_by_department = {}
        for item in work_items:
            dept = item["department"]
            if dept not in grouped_by_department:
                grouped_by_department[dept] = []
            grouped_by_department[dept].append(item)

    payload = {
        "timestamp_generated": now.isoformat(),
        "timezone_used": tz_used,
        "tenant_id": tenant_id,
        "user_context": {
            "username": user.username,
            "is_admin": admin_flag,
            "scope": scope
        },
        "metrics": metrics,
        "sections": {
            "pending_worklist": {
                "items": work_items,
                "grouped_by_department": grouped_by_department,
                "total_items": len(work_items),
                "scope": scope
            },
            "flow": flow,
        }
    }
    return Response(payload)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_worklist(request):
    """Deprecated: using dashboard_summary instead."""
    return Response({"detail": "Deprecated. Use /api/dashboard/summary/"}, status=status.HTTP_410_GONE)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_flow(request):
    """Deprecated: using dashboard_summary instead."""
    return Response({"detail": "Deprecated. Use /api/dashboard/summary/"}, status=status.HTTP_410_GONE)
