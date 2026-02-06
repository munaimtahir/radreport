import { TemplateUiSpec } from "../types";

export const USG_ABD_V1_SPEC: TemplateUiSpec = {
    templateCode: "USG_ABD_V1",
    version: "1.0",

    visibilityRules: [
        {
            when: { key: "liv_visualized", op: "eq", value: "No" },
            hide: [
                "liv_size_cm",
                "liv_contour",
                "liv_echotexture",
                "liv_echogenicity",
                "liv_focal_lesion_present",
                "liv_ihbd_present",
                "liv_portal_vein_diameter_mm"
            ]
        },
        {
            when: { key: "gb_visualized", op: "eq", value: "No" },
            hide: [
                "gb_status",
                "gb_stones_present",
                "gb_sludge_present",
                "gb_wall_thickness_mm",
                "gb_murphy_sign_positive",
                "gb_pericholecystic_fluid_present",
                "gb_cbd_diameter_mm",
                "gb_cbd_stone_suspected"
            ]
        },
        {
            when: { key: "panc_visualized", op: "eq", value: "Obscured by bowel gas" },
            hide: [
                "panc_echotexture",
                "panc_mpd_diameter_mm",
                "panc_focal_lesion_present"
            ]
        },
        {
            when: { key: "spl_visualized", op: "eq", value: "No" },
            hide: [
                "spl_length_cm",
                "spl_echotexture"
            ]
        },
        {
            when: { key: "kid_r_visualized", op: "eq", value: "No" },
            hide: [
                "kid_r_length_cm",
                "kid_r_cortical_echogenicity",
                "kid_r_cmd",
                "kid_r_hydronephrosis_grade",
                "kid_r_calculus_present",
                "kid_r_largest_calculus_mm",
                "kid_r_mass_suspected"
            ]
        },
        {
            when: { key: "kid_l_visualized", op: "eq", value: "No" },
            hide: [
                "kid_l_length_cm",
                "kid_l_cortical_echogenicity",
                "kid_l_cmd",
                "kid_l_hydronephrosis_grade",
                "kid_l_calculus_present",
                "kid_l_largest_calculus_mm",
                "kid_l_mass_suspected"
            ]
        },
        {
            when: { key: "ff_present", op: "eq", value: false },
            hide: [
                "ff_amount"
            ]
        },
        {
            when: { key: "aiv_visualized", op: "eq", value: "Obscured" },
            hide: ["aiv_aorta_max_diameter_mm"]
        },
        {
            when: { key: "kid_r_calculus_present", op: "eq", value: false },
            hide: ["kid_r_largest_calculus_mm"]
        },
        {
            when: { key: "kid_l_calculus_present", op: "eq", value: false },
            hide: ["kid_l_largest_calculus_mm"]
        }
    ],

    fieldEnhancements: {
        // Kidneys
        "kid_r_visualized": {
            enumLabels: {
                "Satisfactory": "Well seen",
                "No": "Not seen"
            }
        },
        "kid_l_visualized": {
            enumLabels: {
                "Satisfactory": "Well seen",
                "No": "Not seen"
            }
        },
        "kid_r_cmd": { label: "Corticomedullary diff" },
        "kid_l_cmd": { label: "Corticomedullary diff" },
        "kid_r_length_cm": { unit: "cm", widget: "measurement" },
        "kid_l_length_cm": { unit: "cm", widget: "measurement" },
        "kid_r_calculus_present": { widget: "segmented_boolean", compact: true },
        "kid_l_calculus_present": { widget: "segmented_boolean", compact: true },
        "kid_r_largest_calculus_mm": { unit: "mm", widget: "measurement" },
        "kid_l_largest_calculus_mm": { unit: "mm", widget: "measurement" },
        "kid_r_mass_suspected": { widget: "segmented_boolean", compact: true },
        "kid_l_mass_suspected": { widget: "segmented_boolean", compact: true },

        // Liver
        "liv_size_cm": { unit: "cm", widget: "measurement" },
        "liv_portal_vein_diameter_mm": { unit: "mm", widget: "measurement" },
        "liv_focal_lesion_present": { widget: "segmented_boolean", compact: true },
        "liv_ihbd_present": { widget: "segmented_boolean", compact: true },
        "liv_visualized": {
            enumLabels: {
                "Satisfactory": "Well seen",
                "Partially": "Partially seen",
                "No": "Not seen"
            }
        },

        // Gallbladder
        "gb_wall_thickness_mm": { unit: "mm", widget: "measurement" },
        "gb_cbd_diameter_mm": { unit: "mm", widget: "measurement" },
        "gb_stones_present": { widget: "segmented_boolean", compact: true },
        "gb_sludge_present": { widget: "segmented_boolean", compact: true },
        "gb_murphy_sign_positive": { widget: "segmented_boolean", compact: true },
        "gb_pericholecystic_fluid_present": { widget: "segmented_boolean", compact: true },
        "gb_cbd_stone_suspected": { widget: "segmented_boolean", compact: true },

        // Pancreas
        "panc_mpd_diameter_mm": { unit: "mm", widget: "measurement" },
        "panc_focal_lesion_present": { widget: "segmented_boolean", compact: true },
        "panc_visualized": {
            enumLabels: {
                "Satisfactory": "Well seen",
                "Partially": "Partially seen",
                "Obscured by bowel gas": "Not visualized (Gas)"
            }
        },

        // Spleen
        "spl_length_cm": { unit: "cm", widget: "measurement" },
        "spl_visualized": {
            enumLabels: {
                "Satisfactory": "Well seen",
                "No": "Not seen"
            }
        },

        // Aorta
        "aiv_aorta_max_diameter_mm": { unit: "mm", widget: "measurement" },

        // Free Fluids
        "ff_present": { widget: "segmented_boolean", compact: true },
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
        }
    ]
};
