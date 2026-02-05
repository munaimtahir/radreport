import csv
import sys
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_date
from apps.reporting.models import ReportPublishSnapshot

class Command(BaseCommand):
    help = 'Export published reports within a date range to CSV'

    def add_arguments(self, parser):
        parser.add_argument('--from', type=str, help='Start date YYYY-MM-DD')
        parser.add_argument('--to', type=str, help='End date YYYY-MM-DD')

    def handle(self, *args, **options):
        from_str = options.get('from')
        to_str = options.get('to')
        
        queryset = ReportPublishSnapshot.objects.select_related('report', 'report__service_visit_item', 'report__service_visit_item__service').all()
        
        if from_str:
            d = parse_date(from_str)
            if d:
                queryset = queryset.filter(published_at__date__gte=d)
        
        if to_str:
            d = parse_date(to_str)
            if d:
                queryset = queryset.filter(published_at__date__lte=d)

        writer = csv.writer(sys.stdout)
        writer.writerow(['report_id', 'workitem_id', 'service', 'published_at', 'version', 'sha256'])
        
        for snap in queryset:
            writer.writerow([
                snap.report.id,
                snap.report.service_visit_item.id,
                snap.report.service_visit_item.service.name,
                snap.published_at.isoformat(),
                snap.version,
                snap.sha256
            ])
