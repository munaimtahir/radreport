import { TemplateUiSpec } from "./types";
import { USG_ABD_V1_SPEC } from "./specs/USG_ABD_V1";

const specs: Record<string, TemplateUiSpec> = {
    "USG_ABD_V1": USG_ABD_V1_SPEC
};

export function getUiSpec(templateCode: string): TemplateUiSpec | null {
    return specs[templateCode] || null;
}
