import { TemplateUiSpec } from "./types";

/**
 * Developer-only utility to verify UI specs don't drift from schemas.
 * Warns if spec references keys that don't exist in the JSON schema.
 */
export function specLint(templateCode: string, jsonSchema: any, uiSpec: TemplateUiSpec | null) {
    if (!uiSpec) return;

    // Extract all properties from JSON schema
    const schemaKeys = new Set(Object.keys(jsonSchema.properties || {}));
    const warnings: string[] = [];

    // 1) fieldEnhancements references key not in schema
    if (uiSpec.fieldEnhancements) {
        Object.keys(uiSpec.fieldEnhancements).forEach(key => {
            if (!schemaKeys.has(key)) {
                warnings.push(`fieldEnhancements references unknown key "${key}"`);
            }
        });
    }

    // 2) visibilityRules hide/show/when keys not in schema
    if (uiSpec.visibilityRules) {
        uiSpec.visibilityRules.forEach((rule, idx) => {
            // Check 'when' key
            if (!schemaKeys.has(rule.when.key)) {
                warnings.push(`visibilityRule[${idx}] .when.key "${rule.when.key}" not in schema`);
            }
            // Check 'hide' keys
            rule.hide.forEach(hKey => {
                if (!schemaKeys.has(hKey)) {
                    warnings.push(`visibilityRule[${idx}] .hide key "${hKey}" not in schema`);
                }
            });
            // Check 'show' keys
            rule.show?.forEach(sKey => {
                if (!schemaKeys.has(sKey)) {
                    warnings.push(`visibilityRule[${idx}] .show key "${sKey}" not in schema`);
                }
            });
        });
    }

    // 3) pairedGroups prefixes match zero keys
    if (uiSpec.pairedGroups) {
        uiSpec.pairedGroups.forEach((group, idx) => {
            const rMatch = Array.from(schemaKeys).some(k => k.startsWith(group.match.rightPrefix));
            const lMatch = Array.from(schemaKeys).some(k => k.startsWith(group.match.leftPrefix));

            if (!rMatch) {
                warnings.push(`pairedGroup[${idx}] rightPrefix "${group.match.rightPrefix}" matches NO keys in schema`);
            }
            if (!lMatch) {
                warnings.push(`pairedGroup[${idx}] leftPrefix "${group.match.leftPrefix}" matches NO keys in schema`);
            }
        });
    }

    if (warnings.length > 0) {
        console.group(`%c[SpecLint] ${templateCode} - ${warnings.length} Warnings`, "color: #ffa500; font-weight: bold;");
        warnings.forEach(w => console.warn(w));
        console.groupEnd();
    }
}
