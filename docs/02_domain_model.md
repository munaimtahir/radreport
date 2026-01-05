# Domain Model

## Core Entities
- Patient (UUID)
- Modality (USG / XRAY / CT)
- Service
- Study (Accession-based exam)
- Template
- TemplateVersion
- Report
- AuditLog

## Invariants
- A Study belongs to one Patient and one Service
- A Report belongs to one Study
- Reports reference immutable TemplateVersions
