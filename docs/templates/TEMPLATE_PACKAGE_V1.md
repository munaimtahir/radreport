# TemplatePackage v1 Specification

**Version**: 1.0.0  
**Status**: Draft  

## Overview
TemplatePackage v1 is the canonical interchange format for RIMS templates. It is a JSON-based format designed to be authorable by AI agents (e.g., ChatGPT) and humans alike.

## Structure
The package is a JSON object with the following top-level keys:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `code` | string | **Yes** | Unique identifier (e.g., `USG_ABDOMEN`). Updates must match this code. |
| `name` | string | **Yes** | Human-readable name (e.g., "Ultrasound Abdomen"). |
| `category` | string | No | Grouping tag (e.g., "Ultrasound", "CT"). |
| `version_note` | string | No | Description of changes in this version. |
| `language` | string | No | ISO 639-1 code (default: "en"). |
| `sections` | array | **Yes** | Ordered list of sections. |
| `service_mappings` | array | No | List of service codes to auto-link this template to. |

## Section Object
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | **Yes** | Section header. |
| `key` | string | No | Internal slug (auto-generated if missing). |
| `fields` | array | **Yes** | Ordered list of fields. |

## Field Object
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | **Yes** | One of: `short_text`, `long_text`, `number`, `boolean`, `dropdown`, `checklist`, `heading`. |
| `label` | string | **Yes** | Field label. |
| `key` | string | **Yes** | Unique key within the template for data storage. |
| `required` | boolean | No | Default `false`. |
| `options` | array | * | Required for `dropdown` and `checklist`. |
| `rules` | object | No | Validation rules (min, max, etc.). |

## Example Payload

```json
{
  "code": "USG_KUB",
  "name": "Ultrasound KUB",
  "category": "USG",
  "version_note": "Initial Release",
  "sections": [
    {
      "title": "Kidneys",
      "fields": [
        {
            "key": "right_kidney_size",
            "type": "short_text",
            "label": "Right Kidney Size"
        },
        {
            "key": "calculi_seen",
            "type": "boolean",
            "label": "Calculi Seen?"
        }
      ]
    }
  ]
}
```
