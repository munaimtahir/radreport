export interface VisibilityRule {
    when: {
        key: string;
        op: "eq" | "neq" | "in";
        value: any;
    };
    hide: string[];
    show?: string[]; // optional
    note?: {
        key: string;
        text: string;
    };
}

export interface UiDefaults {
    // future expansion
}

export interface FieldEnhancement {
    label?: string;
    help?: string;
    widget?: "segmented_boolean" | "measurement" | "enum" | "textarea" | "text";
    unit?: "cm" | "mm" | "ml" | "%" | "none";
    enumLabels?: Record<string, string>; // prettified labels for enum values
    compact?: boolean; // render in compact grid style
}

export interface PairedGroup {
    id: string;
    title: string; // e.g. "Kidneys"
    rightTitle: string; // "Right"
    leftTitle: string; // "Left"
    match: {
        rightPrefix: string;
        leftPrefix: string;
    };
    fieldOrder?: string[]; // suffixes or exact keys
    renderAs: "two_column";
}

export interface SectionEnhancement {
    sectionTitle: string; // Match by title
    layout: "stack" | "grid2" | "grid3";
    compact?: boolean;
}

export interface TemplateUiSpec {
    templateCode: string;
    version: string;
    sections?: SectionEnhancement[];
    fieldEnhancements?: Record<string, FieldEnhancement>;
    visibilityRules?: VisibilityRule[];
    pairedGroups?: PairedGroup[];
    uiDefaults?: UiDefaults;
}
