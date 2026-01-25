# Reporting Stage 1: Dynamic Report Entry UI

## Overview
This stage focuses on implementing the dynamic report entry interface for the new reporting spine. It allows users to enter report values based on a dynamic schema and save drafts or submit finalized reports.

## Key Components

### 1. Reporting Worklist
- **Route**: `/reporting/worklist`
- **Features**: 
    - Lists all `ServiceVisitItem` tasks from the item-centric workflow API.
    - Shows "Enter Report" for items in `REGISTERED`, `IN_PROGRESS`, or `RETURNED_FOR_CORRECTION`.
    - Shows "View Report" for completed/submitted items.
    - Filtering by status (All, Pending, Completed).

### 2. Report Entry Page
- **Route**: `/worklist/:id/report`
- **Features**:
    - Fetches schema and existing values in parallel.
    - **Grouping**: Parameters are grouped by `section`.
    - **Dynamic Form**: Renders inputs based on `parameter_type`:
        - `short_text`, `long_text`, `number`, `boolean`, `dropdown`, `checklist`, `heading`, `separator`.
    - **Defaulting Logic**: Missing values are initialized with `normal_value` or type-aware defaults.
    - **Draft Saving**: POSTs current values to `/save/`.
    - **Submission**: POSTs to `/submit/`, which locks the report for editing.
    - **Read-only Mode**: Automatically disables inputs if status is `submitted` or `verified`.

## Payload Formats

### Save Draft (POST /save/)
```json
{
  "values": [
    { "parameter_id": "<uuid>", "value": "text" },
    { "parameter_id": "<uuid>", "value": ["option1", "option2"] },
    { "parameter_id": "<uuid>", "value": 12.5 }
  ]
}
```

### Response Schema (GET /values/)
```json
{
  "status": "draft|submitted|verified",
  "values": [
    { "parameter_id": "<uuid>", "value": "..." }
  ]
}
```

## Implementation Rules
1. **Values keyed by ID**: All state and submission payloads use `parameter_id` exclusively.
2. **Checklists**: Always stored and submitted as arrays of strings.
3. **Dropdowns**: Default to "na" value if available among options.
4. **Locking**: Reports become read-only immediately upon submission success.
