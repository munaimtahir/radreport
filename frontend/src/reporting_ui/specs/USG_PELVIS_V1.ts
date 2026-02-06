import { TemplateUiSpec } from "../types";

export const USG_PELVIS_V1_SPEC: TemplateUiSpec = {
    templateCode: "USG_PELVIS_V1",
    version: "1.0",

    visibilityRules: [
        // Bladder
        {
            when: { key: "bl_distended", op: "eq", value: false },
            hide: ["bl_wall_thickness_mm"]
        },
        // Uterus
        {
            when: { key: "ut_fibroid_present", op: "eq", value: false },
            hide: ["ut_fibroid_largest_mm"]
        },
        // Adnexa
        {
            when: { key: "adnx_mass_present", op: "eq", value: false },
            hide: [
                "adnx_side",
                "adnx_papillary_projection_present",
                "adnx_solid_component_present",
                "adnx_vascularity"
            ]
        },
        // Free Fluid
        {
            when: { key: "ff_present", op: "eq", value: false },
            hide: ["ff_amount"]
        }
    ],

    fieldEnhancements: {
        // Bladder
        "bl_distended": { widget: "segmented_boolean", compact: true },
        "bl_wall_thickness_mm": { unit: "mm", widget: "measurement" },
        "bl_trabeculation_present": { widget: "segmented_boolean", compact: true },
        "bl_stone_present": { widget: "segmented_boolean", compact: true },
        "bl_mass_suspected": { widget: "segmented_boolean", compact: true },
        "bl_debris_present": { widget: "segmented_boolean", compact: true },
        "bl_pvr_ml": { label: "Post-void residual (mL)", unit: "ml", widget: "measurement" },

        // Uterus
        "ut_size_cm": { help: "Format: Length x Width x AP (e.g. 8.0 x 4.2 x 3.5)" },
        "ut_fibroid_present": { widget: "segmented_boolean", compact: true },
        "ut_fibroid_largest_mm": { unit: "mm", widget: "measurement" },

        // Ovaries
        "ov_r_simple_cyst_present": { widget: "segmented_boolean", compact: true },
        "ov_r_complex_cyst_suspected": { widget: "segmented_boolean", compact: true },
        "ov_r_solid_mass_suspected": { widget: "segmented_boolean", compact: true },
        "ov_l_simple_cyst_present": { widget: "segmented_boolean", compact: true },
        "ov_l_complex_cyst_suspected": { widget: "segmented_boolean", compact: true },
        "ov_l_solid_mass_suspected": { widget: "segmented_boolean", compact: true },

        // Adnexa
        "adnx_mass_present": { widget: "segmented_boolean", compact: true },
        "adnx_papillary_projection_present": { widget: "segmented_boolean", compact: true },
        "adnx_solid_component_present": { widget: "segmented_boolean", compact: true },

        // Free Fluid
        "ff_present": { widget: "segmented_boolean", compact: true },
    },

    pairedGroups: [
        {
            id: "ovaries",
            title: "Ovaries",
            rightTitle: "Right",
            leftTitle: "Left",
            match: {
                rightPrefix: "ov_r_",
                leftPrefix: "ov_l_"
            },
            renderAs: "two_column"
        }
    ]
};
