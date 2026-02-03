
export type FieldType = "string" | "number" | "integer" | "boolean" | "enum" | "text";

export type FieldDef = {
    key: string;              // schema property key (snake_case)
    title: string;            // label
    type: FieldType;
    required?: boolean;
    enumValues?: string[];    // if type "enum"
    widget?: "text" | "textarea" | "select" | "checkbox";
    min?: number;
    max?: number;
    default?: any;
};

export type SectionDef = {
    id: string;               // uuid in UI
    title: string;
    fields: FieldDef[];
};

export type ConditionOp = "equals" | "not_equals" | "gt" | "gte" | "lt" | "lte" | "in" | "not_in" | "is_empty" | "is_not_empty";

export type Condition = { field: string; op: ConditionOp; value?: any };

export type NarrativeLine =
    | { kind: "text"; template: string } // supports {{field}}
    | { kind: "if"; if: Condition; then: NarrativeLine[]; else?: NarrativeLine[] };

export type NarrativeSection = { title: string; lines: NarrativeLine[] };

export type ComputedField = { key: string; expr: string };

export type ImpressionRule = { priority: number; when: Condition; text: string; continue?: boolean };

export type NarrativeState = {
    computed_fields: ComputedField[];
    sections: NarrativeSection[];
    impression_rules: ImpressionRule[];
};

export type BuilderState = {
    meta: { code: string; name: string; modality: string; version: number; is_frozen: boolean; status: string; };
    sections: SectionDef[];
    narrative: NarrativeState;
};

// --- Conversion Logic ---

export function buildJsonSchema(builderState: BuilderState): any {
    const properties: Record<string, any> = {};
    const required: string[] = [];

    builderState.sections.forEach(section => {
        section.fields.forEach(field => {
            const fieldSchema: any = {};

            // Map basic types
            if (field.type === "text") {
                fieldSchema.type = "string";
            } else if (field.type === "enum") {
                fieldSchema.type = "string";
                if (field.enumValues && field.enumValues.length > 0) {
                    fieldSchema.enum = field.enumValues;
                }
            } else {
                fieldSchema.type = field.type;
            }

            // Title
            fieldSchema.title = field.title;

            // Min/Max for numbers
            if (field.type === "number" || field.type === "integer") {
                if (field.min !== undefined) fieldSchema.minimum = field.min;
                if (field.max !== undefined) fieldSchema.maximum = field.max;
            }

            // Default
            if (field.default !== undefined && field.default !== "") {
                fieldSchema.default = field.default;
            }

            properties[field.key] = fieldSchema;

            if (field.required) {
                required.push(field.key);
            }
        });
    });

    const schema: any = {
        type: "object",
        properties,
    };

    if (required.length > 0) {
        schema.required = required;
    }

    return schema;
}

export function buildUiSchema(builderState: BuilderState): any {
    const groups = builderState.sections.map(section => {
        const fields = section.fields.map(f => f.key);
        const widgets: Record<string, string> = {};

        section.fields.forEach(f => {
            // Explicit widget override or infer from type
            if (f.widget) {
                widgets[f.key] = f.widget;
            } else if (f.type === "text") {
                widgets[f.key] = "textarea";
            } else if (f.type === "boolean") {
                widgets[f.key] = "checkbox"; // Default for boolean
            } else if (f.type === "enum") {
                widgets[f.key] = "select"; // Default for enum
            }
        });

        const groupDef: any = {
            title: section.title,
            fields
        };

        if (Object.keys(widgets).length > 0) {
            groupDef.widgets = widgets;
        }

        return groupDef;
    });

    return { groups };
}

function buildBackendCondition(cond: Condition): any {
    const c: any = { field: cond.field };

    if (cond.op === "is_empty") {
        c["is_empty"] = true;
    } else if (cond.op === "is_not_empty") {
        c["is_not_empty"] = true;
    } else {
        c[cond.op] = cond.value;
    }

    return c;
}

function buildBackendNarrativeContent(lines: NarrativeLine[]): any[] {
    return lines.map(line => {
        if (line.kind === "text") {
            return line.template;
        } else {
            const cond = buildBackendCondition(line.if);
            const node: any = {
                if: cond,
                then: buildBackendNarrativeContent(line.then),
            };
            if (line.else && line.else.length > 0) {
                node.else = buildBackendNarrativeContent(line.else);
            }
            return node;
        }
    });
}

export function buildNarrativeRules(builderState: BuilderState): any {
    // Computed fields
    const computed_fields: Record<string, string> = {};
    if (builderState.narrative.computed_fields) {
        builderState.narrative.computed_fields.forEach(cf => {
            computed_fields[cf.key] = cf.expr;
        });
    }

    // Sections
    const sections = builderState.narrative.sections.map(sec => ({
        title: sec.title,
        content: buildBackendNarrativeContent(sec.lines)
    }));

    // Impression Rules
    const impression_rules = builderState.narrative.impression_rules.map(rule => ({
        priority: Number(rule.priority), // ensure number
        when: buildBackendCondition(rule.when),
        text: rule.text,
        continue: !!rule.continue
    }));

    return {
        computed_fields,
        sections,
        impression_rules
    };
}

// --- Reverse Conversion Logic ---

function parseBackendCondition(c: any): Condition {
    // c is like { field: "name", "equals": val }
    const keys = Object.keys(c).filter(k => k !== "field");
    let op: ConditionOp = "equals"; // default
    let value: any = undefined;

    const knownOps: ConditionOp[] = ["equals", "not_equals", "gt", "gte", "lt", "lte", "in", "not_in", "is_empty", "is_not_empty"];

    for (const k of keys) {
        if (knownOps.includes(k as ConditionOp)) {
            op = k as ConditionOp;
            value = c[k];
            break;
        }
    }

    if (op === "is_empty" && value === true) value = undefined;

    return { field: c.field, op, value };
}

function parseBackendNarrativeContent(content: any[]): NarrativeLine[] {
    if (!Array.isArray(content)) return [];
    return content.map(item => {
        if (typeof item === "string") {
            return { kind: "text", template: item };
        } else {
            const cond = item.if ? parseBackendCondition(item.if) : { field: "error", op: "equals" as ConditionOp };
            const thenLines = Array.isArray(item.then) ? parseBackendNarrativeContent(item.then) : (item.then ? parseBackendNarrativeContent([item.then]) : []);
            const elseLines = item.else ? (Array.isArray(item.else) ? parseBackendNarrativeContent(item.else) : parseBackendNarrativeContent([item.else])) : undefined;

            return {
                kind: "if",
                if: cond,
                then: thenLines,
                else: elseLines
            };
        }
    });
}

function generateUUID(): string {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        var r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

export function parseBuilderState(
    meta: any,
    jsonSchema: any,
    uiSchema: any,
    narrativeRules: any
): BuilderState {
    // 1. Sections & Fields
    const sections: SectionDef[] = [];
    const propertyMap = jsonSchema?.properties || {};

    if (uiSchema && uiSchema.groups) {
        uiSchema.groups.forEach((group: any) => {
            const section: SectionDef = {
                id: generateUUID(),
                title: group.title || "Untitled Section",
                fields: []
            };

            const groupFields = group.fields || [];
            const widgets = group.widgets || {};

            groupFields.forEach((key: string) => {
                const prop = propertyMap[key];
                if (!prop) return;

                const field: FieldDef = {
                    key,
                    title: prop.title || key,
                    type: "string" // default
                };

                if (prop.type === "integer") field.type = "integer";
                else if (prop.type === "number") field.type = "number";
                else if (prop.type === "boolean") field.type = "boolean";
                else if (prop.enum) field.type = "enum";
                else if (prop.type === "string") field.type = "string";

                if (prop.enum) field.enumValues = prop.enum;

                if (widgets[key]) {
                    field.widget = widgets[key] as any;
                    if (field.widget === "textarea") field.type = "text";
                }

                if (prop.minimum !== undefined) field.min = prop.minimum;
                if (prop.maximum !== undefined) field.max = prop.maximum;

                if (jsonSchema.required && jsonSchema.required.includes(key)) {
                    field.required = true;
                }

                if (prop.default !== undefined) {
                    field.default = prop.default;
                }

                section.fields.push(field);
            });

            sections.push(section);
        });
    } else {
        // If no UI schema, create one default section
        const section: SectionDef = { id: generateUUID(), title: "General", fields: [] };
        Object.keys(propertyMap).forEach(key => {
            const prop = propertyMap[key];
            section.fields.push({
                key, title: prop.title || key, type: "string"
            });
        });
        if (section.fields.length > 0) sections.push(section);
    }

    // 2. Narrative
    const narrative: NarrativeState = {
        computed_fields: [],
        sections: [],
        impression_rules: []
    };

    if (narrativeRules) {
        if (narrativeRules.computed_fields) {
            Object.entries(narrativeRules.computed_fields).forEach(([key, expr]) => {
                narrative.computed_fields.push({ key, expr: expr as string });
            });
        }

        if (narrativeRules.sections) {
            narrativeRules.sections.forEach((sec: any) => {
                narrative.sections.push({
                    title: sec.title,
                    lines: parseBackendNarrativeContent(sec.content || [])
                });
            });
        }

        if (narrativeRules.impression_rules) {
            narrativeRules.impression_rules.forEach((rule: any) => {
                narrative.impression_rules.push({
                    priority: rule.priority,
                    when: parseBackendCondition(rule.when),
                    text: rule.text,
                    continue: rule.continue
                });
            });
        }
    }

    return {
        meta,
        sections,
        narrative
    };
}
