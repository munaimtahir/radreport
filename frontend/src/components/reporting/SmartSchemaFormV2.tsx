import React, { useMemo } from "react";
import SchemaFormV2, { SchemaFormV2Props } from "./SchemaFormV2";
import { TemplateUiSpec, FieldEnhancement, VisibilityRule } from "../../reporting_ui/types";
import { theme } from "../../theme";
import SegmentedBoolean from "./widgets/SegmentedBoolean";
import MeasurementInput from "./widgets/MeasurementInput";
import PairedTwoColumnGroup from "./layout/PairedTwoColumnGroup";
import Button from "../../ui/components/Button";

interface SmartSchemaFormV2Props extends SchemaFormV2Props {
    uiSpec?: TemplateUiSpec | null;
}

// Helper to evaluate visibility
function isVisible(rules: VisibilityRule[] | undefined, values: Record<string, any>, fieldKey: string): boolean {
    if (!rules) return true;

    // Default visible. If ANY rule hides it, return false.
    // A rule hides 'fieldKey' if the rule condition is met AND 'fieldKey' is in rule.hide.

    for (const rule of rules) {
        if (!rule.hide.includes(fieldKey)) continue;

        const val = values[rule.when.key];
        const target = rule.when.value;
        let triggered = false;

        switch (rule.when.op) {
            case "eq":
                triggered = val === target;
                break;
            case "neq":
                triggered = val !== target;
                break;
            case "in":
                triggered = Array.isArray(target) && target.includes(val);
                break;
        }

        if (triggered) return false;
    }
    return true;
}

function getEnhancedSections(uiSchema: Record<string, any> | null) {
    if (!uiSchema) return [];

    // Support both 'sections' and 'groups' as per SchemaFormV2 logic
    const raw = Array.isArray(uiSchema.groups) ? uiSchema.groups : Array.isArray(uiSchema.sections) ? uiSchema.sections : [];

    return raw
        .filter((section: any) => section && Array.isArray(section.fields))
        .map((section: any) => ({
            title: section.title || "Section",
            fields: section.fields as string[],
            widgets: section.widgets || {},
        }));
}

export default function SmartSchemaFormV2(props: SmartSchemaFormV2Props) {
    const { uiSpec, ...baseProps } = props;

    if (!uiSpec) {
        return <SchemaFormV2 {...baseProps} />;
    }

    const { jsonSchema, uiSchema, values, onChange, isReadOnly, onSave, saving } = baseProps;
    const properties = jsonSchema?.properties || {};
    const requiredSet = new Set(jsonSchema?.required || []);

    // Get base sections
    const rawSections = useMemo(() => getEnhancedSections(uiSchema || null), [uiSchema]);

    const handleFieldChange = (field: string, value: any) => {
        onChange({
            ...values,
            [field]: value,
        });
    };

    const renderEnhancedField = (field: string, enhancement?: FieldEnhancement) => {
        const schema = properties[field] || {};
        const label = enhancement?.label || schema.title || field;
        const isRequired = requiredSet.has(field);
        const fieldValue = values[field] ?? "";

        // Determine widget type
        // Priority: enhancement.widget -> uiSchema widget -> default based on type
        const uiWidget = uiSchema?.sections?.find((s: any) => s.fields.includes(field))?.widgets?.[field];
        const widgetType = enhancement?.widget || uiWidget;

        const description = enhancement?.help || schema.description;

        // Common styles
        const labelStyle: React.CSSProperties = {
            display: "block",
            marginBottom: 6,
            fontWeight: 600,
            fontSize: 14,
            color: theme.colors.textPrimary,
        };

        const wrapperStyle: React.CSSProperties = {
            marginBottom: 0 // handled by grid/flex gap
        };

        // Render widgets
        let inputEl: React.ReactNode = null;

        // 1. Segmented Boolean
        if (widgetType === "segmented_boolean" || (schema.type === "boolean" && widgetType === undefined)) {
            // Note: SchemaFormV2 uses checkbox for boolean by default. 
            // If enhancement.widget says "segmented_boolean", use it.
            // Or if type is boolean and we want to default to segmented? Prompt says "Replace boolean widgets with segmented buttons (Yes/No) where specified"
            // So only if specified in enhancement or generalized rule.

            // Wait, "Map to boolean safely only if it's truly boolean"
            if (schema.type === "boolean" && widgetType === "segmented_boolean") {
                inputEl = (
                    <div>
                        <label style={labelStyle}>
                            {label}
                            {isRequired && <span style={{ color: theme.colors.danger, marginLeft: 4 }}>*</span>}
                        </label>
                        <SegmentedBoolean
                            value={fieldValue === "" ? null : fieldValue}
                            onChange={(val) => handleFieldChange(field, val)}
                            disabled={isReadOnly}
                        />
                    </div>
                );
            } else if (schema.type === "boolean") {
                // Default Checkbox (Copied from SchemaFormV2 style)
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
        }

        // 2. Enum
        if (!inputEl && schema.enum) {
            const enumValues = schema.enum as string[];
            // Check if we have label map
            const labelMap = enhancement?.enumLabels || {};

            // Use Select
            inputEl = (
                <div>
                    <label style={labelStyle}>
                        {label}
                        {isRequired && <span style={{ color: theme.colors.danger, marginLeft: 4 }}>*</span>}
                    </label>
                    <select
                        value={fieldValue}
                        onChange={(e) => handleFieldChange(field, e.target.value)}
                        disabled={isReadOnly}
                        style={{
                            width: "100%",
                            padding: "10px 12px",
                            borderRadius: 8,
                            border: `1px solid ${theme.colors.border}`,
                            fontSize: 14,
                            fontFamily: "inherit",
                            backgroundColor: isReadOnly ? theme.colors.backgroundGray : "white",
                        }}
                    >
                        <option value="">Select...</option>
                        {enumValues.map(opt => (
                            <option key={opt} value={opt}>
                                {labelMap[opt] || opt}
                            </option>
                        ))}
                    </select>
                </div>
            );
        }

        // 3. Measurement
        if (!inputEl && widgetType === "measurement") {
            inputEl = (
                <div>
                    <label style={labelStyle}>
                        {label}
                        {isRequired && <span style={{ color: theme.colors.danger, marginLeft: 4 }}>*</span>}
                    </label>
                    <MeasurementInput
                        value={fieldValue}
                        onChange={(val) => handleFieldChange(field, val)}
                        unit={enhancement?.unit || ""}
                        disabled={isReadOnly}
                    />
                </div>
            );
        }

        // 4. Default Number/String
        if (!inputEl) {
            // Fallback
            const inputStyle: React.CSSProperties = {
                width: "100%",
                padding: "10px 12px",
                borderRadius: 8,
                border: `1px solid ${theme.colors.border}`,
                fontSize: 14,
                fontFamily: "inherit",
                backgroundColor: isReadOnly ? theme.colors.backgroundGray : "white",
            };

            if (schema.type === "number" || schema.type === "integer") {
                inputEl = (
                    <div>
                        <label style={labelStyle}>
                            {label}
                            {isRequired && <span style={{ color: theme.colors.danger, marginLeft: 4 }}>*</span>}
                        </label>
                        <input
                            type="number"
                            value={fieldValue}
                            onChange={(e) => {
                                const val = e.target.value === "" ? "" : Number(e.target.value);
                                handleFieldChange(field, val);
                            }}
                            disabled={isReadOnly}
                            style={inputStyle}
                        />
                    </div>
                );
            } else if (schema.type === "string") {
                const isTextarea = widgetType === "textarea";
                inputEl = (
                    <div>
                        <label style={labelStyle}>
                            {label}
                            {isRequired && <span style={{ color: theme.colors.danger, marginLeft: 4 }}>*</span>}
                        </label>
                        {isTextarea ? (
                            <textarea
                                value={fieldValue}
                                onChange={(e) => handleFieldChange(field, e.target.value)}
                                disabled={isReadOnly}
                                style={{ ...inputStyle, minHeight: 120, resize: "vertical" }}
                            />
                        ) : (
                            <input
                                type="text"
                                value={fieldValue}
                                onChange={(e) => handleFieldChange(field, e.target.value)}
                                disabled={isReadOnly}
                                style={inputStyle}
                            />
                        )}
                    </div>
                );
            }
        }

        return (
            <div style={wrapperStyle}>
                {inputEl}
                {description && (
                    <div style={{ marginTop: 4, fontSize: 12, color: theme.colors.textSecondary }}>
                        {description}
                    </div>
                )}
            </div>
        );
    };

    const renderSection = (section: any) => {
        // Filter hidden fields
        const visibleFields = section.fields.filter((f: string) => isVisible(uiSpec.visibilityRules, values, f));
        if (visibleFields.length === 0) return null;

        // Check for paired groups
        // If a section is "Right Kidney", we might have defined it as a paired group in spec? 
        // Actually, schema usually separates them or puts them in one "Kidneys" section.
        // In USG_ABD_V1.json, we have "Right Kidney" and "Left Kidney" as SEPARATE sections.
        // But the prompt says: "Render paired groups... inside the correct section positions so the overall organ order remains."
        // And "Paired groups: Kidneys: match rightPrefix, leftPrefix".
        // If the original schema has separate sections, how do we merge them?
        // Ah, the user might mean we should merge fields if they were in the same section, OR we detect if a section corresponds to a paired group.
        // BUT `USG_ABD_V1.json` has `right kidney` section and `left kidney` section.
        // If we want to display them side-by-side, we need to merge these sections or hijack one of them.

        // Strategy:
        // When rendering "Right Kidney" - check if it's the "leader" of a paired group.
        // Use `uiSpec.pairedGroups`.
        // If `pairedGroup` matches fields in this section (check prefixes), initiate paired render.
        // Note: we likely need to "pull" the fields from the OTHER section (Left Kidney) into this one, and suppress the Left Kidney section later.

        // Let's analyze `PairedGroup` spec: "match: { rightPrefix: 'kid_r_', leftPrefix: 'kid_l_' }".
        // Does this section contain any fields matching these?
        const sectionHasField = (prefix: string) => visibleFields.some((f: string) => f.startsWith(prefix));

        let pairedGroupToRender: any = null;
        let isSuppressed = false;

        // Check if this section is suppressed because it was rendered by a previous section?
        // We need a state or logic. Since we map sections, we can build a set of "rendered fields" to skip duplicates?
        // Or simpler: Pre-process sections.

        // HOWEVER, "Right Kidney" fields are strictly in "Right Kidney" section.
        // If I want to render "Kidneys" (Both) side-by-side, I should ideally create a new Combined Section or inject it into the first one.
        // If I inject into Right Kidney, I need to fetch Left Kidney fields.

        // Let's implement this logic inside the loop or pre-processing.
        // To avoid complex state, let's just render standard sections if no pairing logic matches perfectly.

        // REVISIT PROMPT: "Render paired groups inside the correct section positions".
        // If I have two sections "Right Kidney" and "Left Kidney", making them 2-col implies merging them visually.
        // Or maybe just the fields WITHIN a section?
        // NO, `USG_ABD_V1` has separate sections.
        // If I render "Right Kidney" section, I can verify if I should render "Left Kidney" fields here too.

        // Let's iterate `uiSpec.pairedGroups`.
        // If `pairedGroup` 'kidneys' matches keys in THIS section.
        // e.g. section has `kid_r_...`. It matches `rightPrefix`.
        // So this is the RIGHT side container.
        // We will try to find the LEFT side fields from the ENTIRE schema (not just this section) 
        // and render them here side-by-side. 
        // AND we must ensure the "Left Kidney" section doesn't render later.

        // This requires knowing which section "owns" the Left Kidney fields so we can hide it.
        // Or simpler: We maintain a `processedFields` set. 
        // If a field is already rendered, skip it.
        // But `renderSection` iterates sections. If I skip "Left Kidney" section completely because all its fields are done? Yes.

        // So:
        // 1. Maintain `renderedFields` Set across the section map.
        // 2. In each section, filter out `renderedFields`.
        // 3. If remaining fields match a PairedGroup (Right side), Render the paired group (fetching Left fields even if they are in another section).
        // 4. Add both Right and Left fields to `renderedFields`.

        // Wait, `SchemaFormV2` (and my Smart version) maps rendering.
        // `map` doesn't easily share state (accumulator).
        // I should use `reduce` or a loop.

    };

    // Pre-calculation for Paired Groups
    const processedSections = [];
    const fieldsToSkip = new Set<string>();

    for (const section of rawSections) {
        // Filter visibility first
        const visibleFields = section.fields.filter((f: string) => isVisible(uiSpec.visibilityRules, values, f));

        // If all fields hidden or skipped
        const actualFields = visibleFields.filter((f: string) => !fieldsToSkip.has(f));
        if (actualFields.length === 0) continue;

        // Check if this section triggers a Paired Group
        let activePairedGroup = null;
        if (uiSpec.pairedGroups) {
            for (const pg of uiSpec.pairedGroups) {
                // Check if this section contains the "Right" prefix fields
                // We assume Right is first/leader.
                if (actualFields.some(f => f.startsWith(pg.match.rightPrefix))) {
                    activePairedGroup = pg;
                    break;
                }
            }
        }

        if (activePairedGroup) {
            // Found a group leader (e.g. Right Kidney)
            // Find all matching Right fields (from this section mainly)
            const rightFields = actualFields.filter(f => f.startsWith(activePairedGroup.match.rightPrefix));

            // Find Left fields from WHOLE schema (properties keys)
            // We search `properties` for keys starting with leftPrefix
            const allKeys = Object.keys(properties);
            const leftFields = allKeys.filter(k => k.startsWith(activePairedGroup.match.leftPrefix));

            // Also apply visibility to left fields
            const visibleLeft = leftFields.filter(f => isVisible(uiSpec.visibilityRules, values, f));

            // Mark all as skipped for future sections
            rightFields.forEach(f => fieldsToSkip.add(f));
            visibleLeft.forEach(f => fieldsToSkip.add(f));

            // Create a special render object
            processedSections.push({
                type: "paired",
                group: activePairedGroup,
                rightFields,
                leftFields: visibleLeft,
                originalTitle: section.title
            });

            // Any remaining fields in this section?
            const remaining = actualFields.filter(f => !f.startsWith(activePairedGroup.match.rightPrefix));
            if (remaining.length > 0) {
                processedSections.push({
                    type: "standard",
                    title: section.title + " (Other)",
                    fields: remaining,
                    widgets: section.widgets
                });
                remaining.forEach(f => fieldsToSkip.add(f));
            }

        } else {
            // Standard section
            processedSections.push({
                type: "standard",
                title: section.title,
                fields: actualFields,
                widgets: section.widgets
            });
            actualFields.forEach(f => fieldsToSkip.add(f));
        }
    }

    return (
        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
            {processedSections.map((section: any, idx) => {
                if (section.type === "paired") {
                    return (
                        <div key={idx} style={{
                            backgroundColor: "white",
                            borderRadius: theme.radius.lg,
                            border: `1px solid ${theme.colors.border}`,
                            overflow: "hidden",
                        }}>
                            <div style={{
                                padding: "16px 24px",
                                backgroundColor: theme.colors.backgroundGray,
                                borderBottom: `1px solid ${theme.colors.border}`,
                                fontWeight: 600,
                                fontSize: 16,
                            }}>
                                {section.group.title}
                            </div>
                            <div style={{ padding: 24 }}>
                                <PairedTwoColumnGroup
                                    title="" // Already in section header
                                    rightTitle={section.group.rightTitle}
                                    leftTitle={section.group.leftTitle}
                                    rightContent={
                                        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                                            {section.rightFields.map((f: string) => (
                                                <div key={f}>{renderEnhancedField(f, uiSpec.fieldEnhancements?.[f])}</div>
                                            ))}
                                        </div>
                                    }
                                    leftContent={
                                        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                                            {section.leftFields.map((f: string) => (
                                                <div key={f}>{renderEnhancedField(f, uiSpec.fieldEnhancements?.[f])}</div>
                                            ))}
                                        </div>
                                    }
                                />
                            </div>
                        </div>
                    );
                } else {
                    // Get compact setting for this section?
                    // Check `uiSpec.sections` overrides
                    // Matches by title? 
                    const sEnhancement = uiSpec.sections?.find(s => s.sectionTitle === section.title);
                    const isCompact = sEnhancement?.compact;
                    const isGrid2 = sEnhancement?.layout === "grid2";

                    // Also check field-level compact
                    const anyCompactField = section.fields.some((f: string) => uiSpec.fieldEnhancements?.[f]?.compact);

                    return (
                        <div key={idx} style={{
                            backgroundColor: "white",
                            borderRadius: theme.radius.lg,
                            border: `1px solid ${theme.colors.border}`,
                            overflow: "hidden",
                        }}>
                            <div style={{
                                padding: "16px 24px",
                                backgroundColor: theme.colors.backgroundGray,
                                borderBottom: `1px solid ${theme.colors.border}`,
                                fontWeight: 600,
                                fontSize: 16,
                            }}>
                                {section.title}
                            </div>
                            <div style={{
                                padding: 24,
                                display: (isCompact || isGrid2) ? "grid" : "flex",
                                flexDirection: (isCompact || isGrid2) ? undefined : "column",
                                gridTemplateColumns: (isGrid2 || anyCompactField) ? "1fr 1fr" : "1fr",
                                gap: 20
                            }}>
                                {section.fields.map((field: string) => {
                                    const fEnhance = uiSpec.fieldEnhancements?.[field];
                                    const fieldIsCompact = fEnhance?.compact;

                                    // wrapper style for grid items? 
                                    return (
                                        <div key={field} style={{
                                            gridColumn: (isGrid2) ? "auto" : (fieldIsCompact ? "auto" : "1 / -1")
                                            // logic: if general grid2, auto. 
                                            // if mixed: compact fields take 1 col, normal take full width?
                                            // Prompt says: "Use compact grid layout for dense sections" and "Reduce vertical bloat: allow 2-column grids for small booleans/enums"
                                        }}>
                                            {renderEnhancedField(field, fEnhance)}
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    );
                }
            })}

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
