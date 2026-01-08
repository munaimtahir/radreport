# Services — Current State

## Service master data (where it lives)
There are **two service master sources** in the codebase:

1. **Legacy catalog services**
   - Model: `apps.catalog.models.Service` with a `Modality` FK and pricing fields (`price`, `charges`, `tat_*`).
   - Used by legacy `Visit` → `OrderItem` → `Study` flow.
   - Import path:
     - API bulk import endpoint: `POST /api/services/import-csv/` expects columns (`code`, `name`, `category`, `modality`, `charges`, `tat_value`, `tat_unit`, `active`).
     - CSV files in repo (examples): `backend/sample_services.csv`, `backend/service_master_export_20260107_143330.csv`. **Needs verification** which one is current.
     - Scripts: `backend/import_ultrasound_services.py` and `backend/export_service_master.py` (for CSV import/export).

2. **Workflow service catalog**
   - Model: `apps.workflow.models.ServiceCatalog` with `code`, `name`, and `default_price`.
   - Seeded by a management command: `apps.workflow.management.commands.seed_services` (USG + OPD).
   - Used by the desk-based workflow (`ServiceVisit`).

## How services are selected/added to a visit/order
### Workflow flow (desk-based)
- UI: `/registration` uses `GET /api/workflow/service-catalog/` to list services, then `POST /api/workflow/visits/create_visit/` to create a `ServiceVisit` with invoice + payment.
- Backend creation happens in `ServiceVisitCreateSerializer.create` (creates `ServiceVisit`, `Invoice`, `Payment`).

### Legacy flow (Visit/OrderItem/Study)
- UI: `/intake` uses `GET /api/services/` (catalog services) and `POST /api/visits/unified-intake/` with `items[]` entries (`service_id`, `indication`).
- Backend creation happens in `UnifiedIntakeSerializer.create`, which:
  - Creates `Visit` + `OrderItem` rows.
  - Creates `Study` records for radiology services (category Radiology or modality in USG/CT/XRAY).

## Where service generation is implemented
- **Legacy flow:**
  - `apps.studies.serializers.UnifiedIntakeSerializer.create` handles service lookup, charges, billing totals, and `Study` creation.
- **Workflow flow:**
  - `apps.workflow.serializers.ServiceVisitCreateSerializer.create` handles `ServiceVisit`, `Invoice`, `Payment` creation.

## Likely failure points
- **Split catalogs:** users may add services from `catalog.Service` (legacy) while the workflow worklists rely on `workflow.ServiceCatalog`. Data will not line up across the two flows.
- **Charges vs price mismatch:** `Service.save()` syncs `charges` and `price`, but import scripts and CSVs may set only one, leading to inconsistencies. **Needs verification** which field is used in UI calculations.
- **Unified intake creates studies for modality codes (`USG`, `CT`, `XRAY`)** even if category is not Radiology. If modality codes change or are missing, studies may not be created. **Needs verification**.
- **Workflow pricing vs legacy pricing:** workflow services only have `default_price`, while the UI calculates totals manually. There is no backend validation that `total_amount` matches the service price. **Needs verification**.
- **CSV import columns:** `import-csv` expects specific column names; mismatched CSV headers will fail the import. This is a common operational failure point.
