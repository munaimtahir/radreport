/**
 * Utility for normalizing template schema from backend to frontend format.
 * 
 * Backend emits fields with { key: "..." } while frontend expects { field_key: "..." }.
 * This helper ensures consistent normalization across all report editors.
 */

export type AnyRecord = Record<string, any>;

/**
 * Normalizes options to ensure consistent {label, value} format.
 * Converts string arrays to objects, leaves existing objects unchanged.
 */
export function normalizeOptions(options?: any[]): { label: string; value: any }[] {
  if (!Array.isArray(options)) return [];
  return options
    .map((opt) => {
      if (!opt) return null;
      if (typeof opt === "string") return { label: opt, value: opt };
      if (typeof opt === "object" && opt.label != null && opt.value != null) return opt;
      if (typeof opt === "object" && opt.value != null) return { label: String(opt.value), value: opt.value };
      return null;
    })
    .filter(Boolean) as { label: string; value: any }[];
}

/**
 * Gets the canonical field key from a field object.
 * Prefers field_key, falls back to key, returns empty string if neither exists.
 */
export function getFieldKey(field: AnyRecord): string {
  return field.field_key ?? field.key ?? "";
}

/**
 * Normalizes a single field object.
 * - Ensures field_key exists (fallback: field.key)
 * - Ensures type exists (fallback: field.field_type)
 * - Normalizes options array to {label, value} format
 * - Handles conditional logic (rules.show_if)
 */
function normalizeField(field: AnyRecord): AnyRecord {
  const normalized: AnyRecord = {
    ...field,
    field_key: field.field_key ?? field.key,
    type: field.type ?? field.field_type,
  };

  // Normalize options if present
  if (field.options) {
    normalized.options = normalizeOptions(field.options);
  }

  // Normalize conditional logic (rules.show_if)
  if (field.rules?.show_if) {
    normalized.rules = {
      ...field.rules,
      show_if: {
        ...field.rules.show_if,
        // Ensure field exists, fallback to field_key if field is missing
        field: field.rules.show_if.field ?? field.rules.show_if.field_key,
      },
    };
  }

  return normalized;
}

/**
 * Normalizes template schema from backend format to frontend format.
 * 
 * Deep-normalizes:
 * - sections[] array
 * - each section.fields[] array
 * 
 * For each field:
 * - Ensures field_key exists (fallback: key)
 * - Ensures type exists (fallback: field_type)
 * - Normalizes options to {label, value} format
 * - Handles conditional logic (rules.show_if)
 * 
 * Does not mutate input objects (creates new objects at each level).
 * 
 * @param schema - The template schema to normalize (can be null/undefined)
 * @returns Normalized schema or null if input is null/undefined
 */
export function normalizeTemplateSchema(schema: AnyRecord | null | undefined): AnyRecord | null {
  if (!schema) return null;

  return {
    ...schema,
    sections: (schema.sections || []).map((section: AnyRecord) => ({
      ...section,
      fields: (section.fields || []).map((field: AnyRecord) => normalizeField(field)),
    })),
  };
}
