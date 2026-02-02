import React, { useMemo } from "react";
import { theme } from "../../theme";
import Button from "../../ui/components/Button";

interface SchemaFormV2Props {
  jsonSchema: Record<string, any>;
  uiSchema?: Record<string, any> | null;
  values: Record<string, any>;
  onChange: (updatedValues: Record<string, any>) => void;
  onSave?: () => void;
  saving?: boolean;
  isReadOnly?: boolean;
}

interface SectionDefinition {
  title: string;
  fields: string[];
  widgets?: Record<string, string>;
}

function getSections(uiSchema?: Record<string, any> | null): SectionDefinition[] {
  if (!uiSchema) return [];
  const raw =
    Array.isArray(uiSchema.groups) ? uiSchema.groups : Array.isArray(uiSchema.sections) ? uiSchema.sections : [];
  return raw
    .filter((section: any) => section && Array.isArray(section.fields))
    .map((section: any) => ({
      title: section.title || "Section",
      fields: section.fields,
      widgets: section.widgets || {},
    }));
}

function getWidget(uiSchema: Record<string, any> | null | undefined, field: string) {
  if (!uiSchema) return null;
  const fieldUi = uiSchema[field];
  if (!fieldUi) return null;
  return fieldUi["ui:widget"] || fieldUi.widget || null;
}

export default function SchemaFormV2({
  jsonSchema,
  uiSchema,
  values,
  onChange,
  onSave,
  saving,
  isReadOnly,
}: SchemaFormV2Props) {
  const properties = jsonSchema?.properties || {};
  const requiredSet = useMemo(() => new Set(jsonSchema?.required || []), [jsonSchema]);
  const sectionDefs = useMemo(() => getSections(uiSchema), [uiSchema]);

  const fieldEntries = Object.entries(properties) as Array<[string, Record<string, any>]>;
  const assignedFields = new Set(sectionDefs.flatMap((section) => section.fields));
  const ungroupedFields = fieldEntries
    .filter(([field]) => !assignedFields.has(field))
    .map(([field]) => field);

  const handleFieldChange = (field: string, value: any) => {
    onChange({
      ...values,
      [field]: value,
    });
  };

  const renderField = (field: string, schema: Record<string, any>, widgetOverride?: string | null) => {
    const label = schema.title || field;
    const isRequired = requiredSet.has(field);
    const widget = widgetOverride ?? getWidget(uiSchema, field);
    const fieldValue = values[field] ?? "";
    const enumValues = schema.enum as string[] | undefined;

    const labelStyle: React.CSSProperties = {
      display: "block",
      marginBottom: 6,
      fontWeight: 600,
      fontSize: 14,
      color: theme.colors.textPrimary,
    };

    const inputStyle: React.CSSProperties = {
      width: "100%",
      padding: "10px 12px",
      borderRadius: 8,
      border: `1px solid ${theme.colors.border}`,
      fontSize: 14,
      fontFamily: "inherit",
      backgroundColor: isReadOnly ? theme.colors.backgroundGray : "white",
    };

    const description = schema.description;

    if (schema.type === "boolean") {
      return (
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <input
            type="checkbox"
            checked={Boolean(fieldValue)}
            onChange={(event) => handleFieldChange(field, event.target.checked)}
            disabled={isReadOnly}
          />
          <span style={{ fontSize: 14 }}>{label}</span>
          {isRequired && <span style={{ color: theme.colors.danger }}>*</span>}
        </div>
      );
    }

    return (
      <div>
        <label style={labelStyle}>
          {label}
          {isRequired && <span style={{ color: theme.colors.danger, marginLeft: 4 }}>*</span>}
        </label>
        {enumValues && (
          <select
            value={fieldValue}
            onChange={(event) => handleFieldChange(field, event.target.value)}
            disabled={isReadOnly}
            style={inputStyle}
          >
            <option value="">Select...</option>
            {enumValues.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        )}
        {!enumValues && (schema.type === "number" || schema.type === "integer") && (
          <input
            type="number"
            value={fieldValue}
            onChange={(event) => {
              const nextValue = event.target.value === "" ? "" : Number(event.target.value);
              handleFieldChange(field, nextValue);
            }}
            disabled={isReadOnly}
            style={inputStyle}
          />
        )}
        {!enumValues && schema.type === "string" && widget === "textarea" && (
          <textarea
            value={fieldValue}
            onChange={(event) => handleFieldChange(field, event.target.value)}
            disabled={isReadOnly}
            style={{ ...inputStyle, minHeight: 120, resize: "vertical" }}
          />
        )}
        {!enumValues && schema.type === "string" && widget !== "textarea" && (
          <input
            type="text"
            value={fieldValue}
            onChange={(event) => handleFieldChange(field, event.target.value)}
            disabled={isReadOnly}
            style={inputStyle}
          />
        )}
        {description && (
          <div style={{ marginTop: 6, fontSize: 12, color: theme.colors.textSecondary }}>
            {description}
          </div>
        )}
      </div>
    );
  };

  const renderSection = (section: SectionDefinition) => (
    <div
      key={section.title}
      style={{
        backgroundColor: "white",
        borderRadius: theme.radius.lg,
        border: `1px solid ${theme.colors.border}`,
        overflow: "hidden",
      }}
    >
      <div
        style={{
          padding: "16px 24px",
          backgroundColor: theme.colors.backgroundGray,
          borderBottom: `1px solid ${theme.colors.border}`,
          fontWeight: 600,
          fontSize: 16,
        }}
      >
        {section.title}
      </div>
      <div style={{ padding: "24px", display: "flex", flexDirection: "column", gap: 20 }}>
        {section.fields.map((field) => (
          <div key={field}>
            {renderField(field, properties[field] || {}, section.widgets?.[field])}
          </div>
        ))}
      </div>
    </div>
  );

  if (!fieldEntries.length) {
    return <div>No schema fields available.</div>;
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      {sectionDefs.map((section) => renderSection(section))}
      {ungroupedFields.length > 0 && renderSection({ title: "Fields", fields: ungroupedFields })}
      {onSave && (
        <div style={{ display: "flex", justifyContent: "flex-end" }}>
          <Button variant="primary" onClick={onSave} disabled={saving}>
            {saving ? "Saving..." : "Save"}
          </Button>
        </div>
      )}
    </div>
  );
}
