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
        }
    ],

    fieldEnhancements: {
        // Kidneys
        "kid_r_cmd": { label: "Corticomedullary diff" },
        "kid_l_cmd": { label: "Corticomedullary diff" },
        "kid_r_length_cm": { unit: "cm", widget: "measurement" },
        "kid_l_length_cm": { unit: "cm", widget: "measurement" },
        "kid_r_largest_calculus_mm": { unit: "mm", widget: "measurement" },
        "kid_l_largest_calculus_mm": { unit: "mm", widget: "measurement" },

        // Liver
        "liv_size_cm": { unit: "cm", widget: "measurement" },
        "liv_portal_vein_diameter_mm": { unit: "mm", widget: "measurement" },
        "liv_visualized": {
            // keeping enum, just labels if needed. Structure is fine in schema.
        },

        // Gallbladder
        "gb_wall_thickness_mm": { unit: "mm", widget: "measurement" },
        "gb_cbd_diameter_mm": { unit: "mm", widget: "measurement" },

        // Pancreas
        "panc_mpd_diameter_mm": { unit: "mm", widget: "measurement" },
        "panc_visualized": {
            enumLabels: {
                "Satisfactory": "Well seen",
                "Partially": "Partially unseen",
                "Obscured by bowel gas": "Not visualized (Gas)"
            }
        },

        // Spleen
        "spl_length_cm": { unit: "cm", widget: "measurement" },

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
