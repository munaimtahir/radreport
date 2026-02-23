import os
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from apps.workflow.models import ServiceVisit, ServiceVisitItem

class Command(BaseCommand):
    help = 'Verify dashboard truth and output to ARTIFACTS/dashboard_truth_check.txt'

    def handle(self, *args, **kwargs):
        # Timezone handling
        now = timezone.now()
        local_now = timezone.localtime(now)
        tz_used = getattr(settings, "TIME_ZONE", "UTC")
        today_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        output_lines = [
            f"=== DASHBOARD TRUTH MAP ===",
            f"Generated At: {local_now.isoformat()}",
            f"Timezone: {tz_used}",
            f"Boundary: {today_start} to {today_end}",
            ""
        ]

        # Metric 1
        cnt = ServiceVisit.objects.filter(registered_at__gte=today_start, registered_at__lt=today_end).values("patient").distinct().count()
        output_lines.append(f"Metric: Total Patients Today = {cnt}")
        output_lines.append(f"  Query: ServiceVisit registered_at >= {today_start} AND < {today_end} (distinct patients)")
        
        # Metric 2
        cnt = ServiceVisitItem.objects.filter(created_at__gte=today_start, created_at__lt=today_end).count()
        output_lines.append(f"Metric: Total Services Today = {cnt}")
        output_lines.append(f"  Query: ServiceVisitItem created_at >= {today_start} AND < {today_end}")

        # Metric 3
        cnt = ServiceVisitItem.objects.filter(status="PENDING_VERIFICATION").count()
        output_lines.append(f"Metric: Reports Pending = {cnt}")
        output_lines.append(f"  Query: ServiceVisitItem status == PENDING_VERIFICATION")

        # Metric 4
        cnt = ServiceVisitItem.objects.filter(status="PUBLISHED", published_at__gte=today_start, published_at__lt=today_end).count()
        output_lines.append(f"Metric: Reports Verified Today = {cnt}")
        output_lines.append(f"  Query: ServiceVisitItem status == PUBLISHED AND published_at >= {today_start} AND < {today_end}")
        
        # Breakdown by status today
        output_lines.append("")
        output_lines.append("=== ITEM STATUS BREAKDOWN TODAY (created today) ===")
        statuses = ServiceVisitItem.objects.filter(created_at__gte=today_start, created_at__lt=today_end).values('status')
        counts = {}
        for s in statuses:
            counts[s['status']] = counts.get(s['status'], 0) + 1
        
        if not counts:
            output_lines.append("  (No items created today)")
        for st, c in counts.items():
            output_lines.append(f"  {st}: {c}")

        output_lines.append("")
        output_lines.append("=== ITEM STATUS BREAKDOWN OVERALL (All time) ===")
        all_time = ServiceVisitItem.objects.all().values('status')
        all_counts = {}
        for s in all_time:
            all_counts[s['status']] = all_counts.get(s['status'], 0) + 1
            
        for st, c in all_counts.items():
            output_lines.append(f"  {st}: {c}")

        output_str = "\n".join(output_lines)
        
        # Create ARTIFACTS directory
        os.makedirs("ARTIFACTS", exist_ok=True)
        with open("ARTIFACTS/dashboard_truth_check.txt", "w") as f:
            f.write(output_str)

        self.stdout.write(self.style.SUCCESS("Successfully generated ARTIFACTS/dashboard_truth_check.txt"))
