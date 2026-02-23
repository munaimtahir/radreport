import os
import django
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rims_backend.settings")
django.setup()

from apps.workflow.models import ServiceVisit, ServiceVisitItem

now = timezone.now()
local_now = timezone.localtime(now)
# Get the configured timezone string
from django.conf import settings
tz_used = settings.TIME_ZONE

today_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
today_end = today_start + timedelta(days=1)

print(tz_used)
print(today_start)
