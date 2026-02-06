import { TemplateUiSpec } from "../types";

export const USG_KUB_V1_SPEC: TemplateUiSpec = {
    templateCode: "USG_KUB_V1",
    version: "1.0",

    visibilityRules: [
        // Kidneys
        {
            when: { key: "kid_r_visualized", op: "eq", value: false },
            hide: [
                "kid_r_length_cm",
                "kid_r_cortical_echogenicity",
                "kid_r_cmd",
                "kid_r_hydronephrosis_grade",
                "kid_r_calculus_present",
                "kid_r_largest_calculus_mm",
                "kid_r_simple_cyst_present",
                "kid_r_largest_cyst_mm",
                "kid_r_mass_suspected",
                "kid_r_perinephric_collection_present"
            ]
        },
        {
            when: { key: "kid_l_visualized", op: "eq", value: false },
            hide: [
                "kid_l_length_cm",
                "kid_l_cortical_echogenicity",
                "kid_l_cmd",
                "kid_l_hydronephrosis_grade",
                "kid_l_calculus_present",
                "kid_l_largest_calculus_mm",
                "kid_l_simple_cyst_present",
                "kid_l_largest_cyst_mm",
                "kid_l_mass_suspected",
                "kid_l_perinephric_collection_present"
            ]
        },
        // Kidney Detail Rules
        {
            when: { key: "kid_r_calculus_present", op: "eq", value: false },
            hide: ["kid_r_largest_calculus_mm"]
        },
        {
            when: { key: "kid_l_calculus_present", op: "eq", value: false },
            hide: ["kid_l_largest_calculus_mm"]
        },
        {
            when: { key: "kid_r_simple_cyst_present", op: "eq", value: false },
            hide: ["kid_r_largest_cyst_mm"]
        },
        {
            when: { key: "kid_l_simple_cyst_present", op: "eq", value: false },
            hide: ["kid_l_largest_cyst_mm"]
        },

        // Ureters
        {
            when: { key: "ure_r_visualized", op: "eq", value: false },
            hide: [
                "ure_r_segment_assessed",
                "ure_r_hydroureter_present",
                "ure_r_stone_suspected",
                "ure_r_stone_location",
                "ure_r_stone_size_mm",
                "ure_r_jet_seen"
            ]
        },
        {
            when: { key: "ure_l_visualized", op: "eq", value: false },
            hide: [
                "ure_l_segment_assessed",
                "ure_l_hydroureter_present",
                "ure_l_stone_suspected",
                "ure_l_stone_location",
                "ure_l_stone_size_mm",
                "ure_l_jet_seen"
            ]
        },
        // Ureter Detail Rules
        {
            when: { key: "ure_r_stone_suspected", op: "eq", value: false },
            hide: ["ure_r_stone_location", "ure_r_stone_size_mm"]
        },
        {
            when: { key: "ure_l_stone_suspected", op: "eq", value: false },
            hide: ["ure_l_stone_location", "ure_l_stone_size_mm"]
        },

        // Bladder
        {
            when: { key: "bl_visualized", op: "eq", value: false },
            hide: [
                "bl_distended",
                "bl_wall_thickness_mm",
                "bl_trabeculation_present",
                "bl_stone_present",
                "bl_mass_suspected",
                "bl_debris_present",
                "bl_prevoid_volume_ml",
                "bl_pvr_ml"
            ]
        }
    ],

    fieldEnhancements: {
        // Kidneys
        "kid_r_visualized": { widget: "segmented_boolean", compact: true },
        "kid_l_visualized": { widget: "segmented_boolean", compact: true },
        "kid_r_cmd": { label: "Corticomedullary diff" },
        "kid_l_cmd": { label: "Corticomedullary diff" },
        "kid_r_length_cm": { unit: "cm", widget: "measurement" },
        "kid_l_length_cm": { unit: "cm", widget: "measurement" },
        "kid_r_calculus_present": { widget: "segmented_boolean", compact: true },
        "kid_l_calculus_present": { widget: "segmented_boolean", compact: true },
        "kid_r_largest_calculus_mm": { unit: "mm", widget: "measurement" },
        "kid_l_largest_calculus_mm": { unit: "mm", widget: "measurement" },
        "kid_r_simple_cyst_present": { widget: "segmented_boolean", compact: true },
        "kid_l_simple_cyst_present": { widget: "segmented_boolean", compact: true },
        "kid_r_largest_cyst_mm": { unit: "mm", widget: "measurement" },
        "kid_l_largest_cyst_mm": { unit: "mm", widget: "measurement" },
        "kid_r_mass_suspected": { widget: "segmented_boolean", compact: true },
        "kid_l_mass_suspected": { widget: "segmented_boolean", compact: true },
        "kid_r_perinephric_collection_present": { widget: "segmented_boolean", compact: true },
        "kid_l_perinephric_collection_present": { widget: "segmented_boolean", compact: true },

        // Ureters
        "ure_r_visualized": { widget: "segmented_boolean", compact: true },
        "ure_l_visualized": { widget: "segmented_boolean", compact: true },
        "ure_r_hydroureter_present": { widget: "segmented_boolean", compact: true },
        "ure_l_hydroureter_present": { widget: "segmented_boolean", compact: true },
        "ure_r_stone_suspected": { widget: "segmented_boolean", compact: true },
        "ure_l_stone_suspected": { widget: "segmented_boolean", compact: true },
        "ure_r_stone_size_mm": { unit: "mm", widget: "measurement" },
        "ure_l_stone_size_mm": { unit: "mm", widget: "measurement" },
        "ure_r_jet_seen": { widget: "segmented_boolean", compact: true },
        "ure_l_jet_seen": { widget: "segmented_boolean", compact: true },

        // Bladder
        "bl_visualized": { widget: "segmented_boolean", compact: true },
        "bl_distended": { widget: "segmented_boolean", compact: true },
        "bl_wall_thickness_mm": { unit: "mm", widget: "measurement" },
        "bl_trabeculation_present": { widget: "segmented_boolean", compact: true },
        "bl_stone_present": { widget: "segmented_boolean", compact: true },
        "bl_mass_suspected": { widget: "segmented_boolean", compact: true },
        "bl_debris_present": { widget: "segmented_boolean", compact: true },
        "bl_prevoid_volume_ml": { unit: "ml", widget: "measurement" },
        "bl_pvr_ml": { label: "Post-void residual (mL)", unit: "ml", widget: "measurement" },
    },

    pairedGroups: [
        {
            id: "kidneys",
            title: "Kidneys",
            rightTitle: "Right",
            leftTitle: "Left",
            match: {
                rightPrefix: "kid_r_",
                leftPrefix: "kid_l_"
            },
            renderAs: "two_column"
        },
        {
            id: "ureters",
            title: "Ureters",
            rightTitle: "Right",
            leftTitle: "Left",
            match: {
                rightPrefix: "ure_r_",
                leftPrefix: "ure_l_"
            },
            renderAs: "two_column"
        }
    ]
};
