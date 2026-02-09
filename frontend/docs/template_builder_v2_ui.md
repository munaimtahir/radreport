# Template Builder V2 - UI Architecture (Redesign)

## Overview
The Template Builder V2 has been redesigned to support a "non-technical user" workflow. It provides a guided, wizard-based experience (Basic Mode) that abstracts away JSON schemas, technical keys, and complex narrative logic.

## Truth Map
- **Templates**: Loaded from `/api/reporting/templates-v2/{id}/`.
- **Schema**:
    - `json_schema`: Defines the data structure (properties, types, enums).
    - `ui_schema`: Defines groupings and widget overrides.
    - `narrative_rules`: Rules-engine logic for generating the report text.
- **New Builder UI**:
    - **Basic Mode**: Default. Wizard-based (Sections -> Findings -> Narrative). Hides technical keys.
    - **Advanced Mode**: Toggle for power users. Shows raw keys and JSON schema.
- **Narrative Logic**: Shows "Auto Narrative" (generated) vs "Final Narrative" (mock/draft) for instant feedback during template design.

## Components
- `TemplateV2Builder.tsx`: Main container with Mode toggle and Step management.
- `TemplateWizard.tsx`: Core wizard layout and navigation.
- `SectionsStep.tsx`: Manage template sections as cards.
- `FindingsStep.tsx`: Define fields and logic for each section with a preview-first approach.
- `NarrativeStep.tsx`: Test automated narrative generation rules.

## Data Layer
- `labelResolver.ts`: Deteminstic mapping from technical keys (`liver_size_cm`) to human labels ("Liver size (cm)").
- `v2Builder.ts`: Utils for converting between Builder state and JSON/UI schemas.

## QA Checklist (Manual)
- [ ] Loads existing V2 template without errors.
- [ ] Wizard steps navigate correctly.
- [ ] Adding a section in Basic mode works and sets default "Normal" status.
- [ ] Paired organs (R/L) show side-by-side.
- [ ] Narrative preview updates when findings change.
- [ ] Save persists all schema/rules correctly.
- [ ] Advanced mode toggle shows/hides technical fields.
