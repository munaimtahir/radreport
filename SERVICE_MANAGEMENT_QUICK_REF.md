# Quick Reference: Service Management

## Current Status
✅ **36 Ultrasound Services Active**
✅ **All Demo Data Removed**
✅ **System Ready for Production**

## Service Statistics
- Total Services: 36
- Doppler Studies: 13
- Gray Scale Ultrasound: 17
- Ultrasound Guided Procedures: 6
- Price Range: PKR 1,500 - 9,000
- TAT Range: 20-60 minutes

## Quick Commands

### View All Services
```bash
docker exec rims_backend_prod python manage.py shell -c "
from apps.catalog.models import Service
for s in Service.objects.all().order_by('code'):
    print(f'{s.code} | {s.name:50s} | PKR {s.price:>7}')"
```

### Count Services
```bash
docker exec rims_backend_prod python manage.py shell -c "
from apps.catalog.models import Service
print(f'Total services: {Service.objects.count()}')"
```

### Re-import Services
```bash
docker exec rims_backend_prod python /app/import_services_inline.py
```

### Add New Service via Django Shell
```bash
docker exec -it rims_backend_prod python manage.py shell
```
```python
from apps.catalog.models import Modality, Service

modality = Modality.objects.get(code='USG')
service = Service.objects.create(
    code='US037',
    modality=modality,
    name='New Service Name',
    category='Radiology',
    price=2500,
    charges=2500,
    tat_value=1,
    tat_unit='hours',
    is_active=True
)
print(f"Created: {service.code} - {service.name}")
```

## Important Files

### Service Import Scripts
1. `backend/import_ultrasound_services.py` - Main import script with inline data
2. `backend/import_services_inline.py` - Alternative import script
3. `backend/apps/catalog/management/commands/import_ultrasound_services.py` - Django command

### Seed Script
- `backend/seed_data.py` - Modified to skip demo data creation

### Documentation
- `SERVICE_CATALOG_UPDATE_2026-01-17.md` - Complete update documentation

## Service Code Format
- **US001-US036** - Ultrasound services (current)
- **Reserved for future:**
  - XR### - X-Ray services
  - CT### - CT Scan services
  - MR### - MRI services

## Pricing Quick Reference
| Category | Price Range |
|----------|-------------|
| Doppler Studies | PKR 3,000 - 9,000 |
| Gray Scale US | PKR 1,500 - 5,000 |
| US Guided Procedures | PKR 2,500 - 5,000 |

## Common TAT Values
- Simple studies: 20 minutes
- Standard studies: 30 minutes
- Complex studies: 45-60 minutes

## Access Services via API
Services are available at `/api/services/` (requires authentication)

**Example:**
```bash
# Get token
TOKEN=$(curl -X POST http://localhost:8015/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r .access)

# Get services
curl http://localhost:8015/api/services/ \
  -H "Authorization: Bearer $TOKEN"
```

## Modalities
Currently configured:
- **USG** (Ultrasound) - 36 services ✅
- **XRAY** (X-Ray) - 0 services (ready to add)
- **CT** (CT Scan) - 0 services (ready to add)
- **MRI** (MRI) - 0 services (ready to add)

## Notes
- All services are linked to USG modality
- Prices are in Pakistani Rupees (PKR)
- TAT (Turnaround Time) is in minutes
- All services are marked as active
- Services belong to "Radiology" category

## Support
For issues or questions, refer to:
- Full documentation: `SERVICE_CATALOG_UPDATE_2026-01-17.md`
- Database models: `backend/apps/catalog/models.py`
- API endpoints: `backend/apps/catalog/api.py`

---
Last Updated: January 17, 2026
