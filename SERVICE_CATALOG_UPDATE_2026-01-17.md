# Service Catalog Update - January 17, 2026

## Summary

Successfully updated the RIMS service catalog with production ultrasound services from the official rate list. All previous demo services have been removed and replaced with 36 production ultrasound services.

## Changes Made

### 1. Service Catalog Import ✅

**Script Used:** `backend/import_services_inline.py`

**Actions Performed:**
- Deleted all existing demo services (39 services)
- Deleted all related data (service visits, studies, reports)
- Imported 36 ultrasound services from official rate list
- All services properly configured with:
  - Service codes (US001 - US036)
  - Accurate pricing in PKR
  - Turnaround times (TAT)
  - Department categorization
  - Modality (USG - Ultrasound)

### 2. Seed Data Script Updated ✅

**File:** `backend/seed_data.py`

**Changes:**
- Disabled automatic creation of demo services
- Disabled automatic creation of demo patients
- Disabled automatic creation of demo studies
- Disabled automatic creation of demo reports
- Script now only creates:
  - Superuser (admin/admin123)
  - Modalities (USG, XRAY, CT, MRI)
  - Templates (if needed)

This ensures that future deployments or restarts won't recreate demo data.

### 3. Import Scripts Created/Updated ✅

**Files:**
1. `backend/import_ultrasound_services.py` - Updated with inline CSV data
2. `backend/import_services_inline.py` - New script with embedded service data
3. `backend/apps/catalog/management/commands/import_ultrasound_services.py` - Django management command

All scripts contain the complete service data inline, so they can be run without requiring external CSV files.

## Current Service Catalog

### Statistics
- **Total Services:** 36
- **Total Modalities:** 4 (USG active, XRAY/CT/MRI available for future expansion)
- **Active USG Services:** 36

### Service Categories

#### 1. Doppler Studies (13 services)
- Doppler Obstetric (Single, Twins, Triplet)
- Doppler Peripheral Veins (Single/Both sides)
- Doppler Peripheral Arteries (Single/Both sides)
- Doppler Peripheral Arteries & Veins (Both sides)
- Doppler Renal
- Doppler Abdomen
- Doppler Thyroid
- Doppler Uterine Arteries
- Doppler Scrotum
- Doppler Neck

**Price Range:** PKR 3,000 - 9,000
**TAT Range:** 30-60 minutes

#### 2. Gray Scale Ultrasound (17 services)
- Abdomen
- Abdomen and Pelvis
- KUB
- Pelvis
- Soft Tissue
- Obstetrics (1st & 2nd Trimester)
- Swelling
- Anomaly / Congenital Scan
- Breast (Single/Bilateral)
- Chest
- Scrotum
- Cranial
- Knee Joint
- Both Hip Joints (Child)
- Twin Obstetrics (Non-Doppler)

**Price Range:** PKR 1,500 - 5,000
**TAT Range:** 20-45 minutes

#### 3. Ultrasound Guided Procedures (6 services)
- Abscess Drainage (Diagnostic/Therapeutic)
- Pleural Effusion Tap (Diagnostic/Therapeutic)
- Ascitic Fluid Tap (Diagnostic/Therapeutic)

**Price Range:** PKR 2,500 - 5,000
**TAT Range:** 30-45 minutes

## Service Listing

| Code  | Service Name                                        | Price (PKR) | TAT (min) | Category  |
|-------|-----------------------------------------------------|-------------|-----------|-----------|
| US001 | Doppler Obstetric Single                            | 3,000       | 30        | Radiology |
| US002 | Doppler Obstetric Twins                             | 6,000       | 45        | Radiology |
| US003 | Doppler Obstetric Triplet                           | 9,000       | 60        | Radiology |
| US004 | Doppler Peripheral Veins Single Side                | 3,500       | 30        | Radiology |
| US005 | Doppler Peripheral Veins Both Sides                 | 7,500       | 45        | Radiology |
| US006 | Doppler Renal                                       | 3,500       | 30        | Radiology |
| US007 | Doppler Abdomen                                     | 5,000       | 30        | Radiology |
| US008 | Ultrasound Abdomen                                  | 1,500       | 20        | Radiology |
| US009 | Ultrasound Abdomen and Pelvis                       | 3,000       | 30        | Radiology |
| US010 | Ultrasound KUB                                      | 1,500       | 20        | Radiology |
| US011 | Ultrasound Pelvis                                   | 1,500       | 20        | Radiology |
| US012 | Ultrasound Soft Tissue                              | 2,500       | 20        | Radiology |
| US013 | Ultrasound Obstetrics (1st & 2nd Trimester)         | 2,000       | 25        | Radiology |
| US014 | Ultrasound for Swelling                             | 2,500       | 20        | Radiology |
| US015 | Doppler Thyroid                                     | 3,500       | 30        | Radiology |
| US016 | Ultrasound Anomaly / Congenital Scan                | 4,000       | 45        | Radiology |
| US017 | Ultrasound Breast (Single)                          | 2,500       | 20        | Radiology |
| US018 | Ultrasound Chest                                    | 2,500       | 20        | Radiology |
| US019 | Doppler Uterine Arteries                            | 3,500       | 30        | Radiology |
| US020 | Ultrasound Scrotum                                  | 1,500       | 20        | Radiology |
| US021 | Doppler Peripheral Arteries Single Side             | 3,500       | 30        | Radiology |
| US022 | Ultrasound Cranial                                  | 2,500       | 20        | Radiology |
| US023 | Doppler Peripheral Arteries and Veins Both Sides    | 7,000       | 45        | Radiology |
| US024 | Doppler Peripheral Arteries Both Sides              | 7,000       | 45        | Radiology |
| US025 | Ultrasound Guided Abscess Drainage (Diagnostic)     | 3,000       | 30        | Radiology |
| US026 | Ultrasound Guided Pleural Effusion Tap (Diagnostic) | 2,500       | 30        | Radiology |
| US027 | Ultrasound Guided Ascitic Fluid Tap (Diagnostic)    | 3,000       | 30        | Radiology |
| US028 | Ultrasound Guided Abscess Drainage (Therapeutic)    | 5,000       | 45        | Radiology |
| US029 | Ultrasound Guided Ascitic Fluid Tap (Therapeutic)   | 5,000       | 45        | Radiology |
| US030 | Ultrasound Guided Pleural Effusion Tap (Therapeutic)| 5,000       | 45        | Radiology |
| US031 | Ultrasound Knee Joint                               | 2,500       | 20        | Radiology |
| US032 | Ultrasound Both Hip Joints (Child)                  | 3,000       | 25        | Radiology |
| US033 | Doppler Scrotum                                     | 3,500       | 30        | Radiology |
| US034 | Doppler Neck                                        | 3,500       | 30        | Radiology |
| US035 | Ultrasound Breast (Bilateral)                       | 5,000       | 30        | Radiology |
| US036 | Ultrasound Twin Obstetrics (Non-Doppler)            | 3,000       | 30        | Radiology |

## Source Data

**Original Files:**
- `Ultrasound rate list.pdf` - Official rate list from Consultants Place Clinic
- `rims_services_ultrasound_import.csv` - CSV export of rate list

**Pricing Reference:**
All prices are taken from the official Consultants Place Clinic rate list for Adjust Excel Labs, Jaranwala.

## How to Re-run Import

If you need to re-import services in the future:

### Option 1: Using Docker (Recommended)
```bash
# Copy script to container
docker cp backend/import_services_inline.py rims_backend_prod:/app/

# Run the import
docker exec rims_backend_prod python /app/import_services_inline.py
```

### Option 2: Using Django Management Command
```bash
# Inside the container
docker exec rims_backend_prod python manage.py import_ultrasound_services

# Or with custom CSV
docker exec rims_backend_prod python manage.py import_ultrasound_services --csv-path /path/to/file.csv
```

### Option 3: Direct Python Script
```bash
# Inside the backend directory
cd backend
python import_ultrasound_services.py
```

## Verification

To verify the services are correctly imported:

```bash
# Check service count
docker exec rims_backend_prod python manage.py shell -c "from apps.catalog.models import Service; print(f'Total services: {Service.objects.count()}')"

# List all services
docker exec rims_backend_prod python manage.py shell -c "from apps.catalog.models import Service; [print(f'{s.code} - {s.name} - PKR {s.price}') for s in Service.objects.all().order_by('code')]"
```

## Next Steps

1. **Add Templates** - Create ultrasound report templates for each service type
2. **Configure Workflow** - Set up appropriate workflow rules for ultrasound services
3. **Test Registration** - Register test patients and service visits
4. **Add More Services** - Expand to other modalities (XRAY, CT, MRI) as needed

## Notes

- All demo data has been completely removed
- The system is ready for production use
- Future deployments will not recreate demo data
- The USG modality is fully configured and operational
- Other modalities (XRAY, CT, MRI) exist but have no services yet

## Files Modified

1. `backend/seed_data.py` - Disabled demo data creation
2. `backend/import_ultrasound_services.py` - Updated with inline data
3. `backend/import_services_inline.py` - Created new import script
4. `backend/apps/catalog/management/commands/import_ultrasound_services.py` - Created management command

## Database State

- **Services:** 36 (all production ultrasound services)
- **Patients:** 0 (no demo patients)
- **Studies:** 0 (no demo studies)
- **Reports:** 0 (no demo reports)
- **Service Visits:** 0 (no demo visits)

System is clean and ready for production data entry.

---

**Date:** January 17, 2026
**Performed By:** AI Assistant
**Status:** ✅ Completed Successfully
