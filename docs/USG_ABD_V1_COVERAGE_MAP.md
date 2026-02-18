# USG_ABD_V1 Template Coverage Map

## Affected Templates

| Template ID    | Name          | File Path                                                                 |
|----------------|---------------|---------------------------------------------------------------------------|
| USG_ABD_V1     | USG Abdomen   | `backend/apps/reporting/seed_data/templates_v2/library/phase2_v1.1/USG_ABD_V1.json` |
| USG_KUB_V1     | USG KUB       | `backend/apps/reporting/seed_data/templates_v2/library/phase2_v1.1/USG_KUB_V1.json` |
| USG_PELVIS_V1  | USG Pelvis    | `backend/apps/reporting/seed_data/templates_v2/library/phase2_v1.1/USG_PELVIS_V1.json` |

**Primary template upgraded:** USG_ABD_V1 (most commonly used whole-abdomen template).

---

## Current Coverage (Pre-Upgrade)

| Organ          | Existing Fields | Existing Narrative Rules | Missing Abnormal Packs |
|----------------|-----------------|--------------------------|------------------------|
| Liver          | liv_visualized, liv_image_quality, liv_limitation_reason, liv_size_cm, liv_contour, liv_echotexture, liv_echogenicity, liv_focal_lesion_present, liv_ihbd_present, liv_portal_vein_diameter_mm | Size, contour, echogenicity, focal lesion, IHBD, PV | liv_size enum, liv_surface, liv_fatty_grade, liv_largest_lesion_mm, liv_lesion_character, liv_lesion_echo |
| Gallbladder    | gb_visualized, gb_status, gb_stones_present, gb_sludge_present, gb_wall_thickness_mm, gb_murphy_sign_positive, gb_pericholecystic_fluid_present, gb_cbd_diameter_mm, gb_cbd_stone_suspected | Status, wall, stones, sludge, CBD, stone suspected | gb_largest_stone_mm, gb_polyp_present, gb_polyp_mm, gb_post_cholecystectomy (bool), cbd_dilated |
| CBD            | gb_cbd_diameter_mm, gb_cbd_stone_suspected | CBD diameter, stone suspected | cbd_diameter_mm alias, cbd_dilated |
| Pancreas       | panc_visualized, panc_echotexture, panc_mpd_diameter_mm, panc_focal_lesion_present | Echotexture, focal lesion | panc_size, panc_duct_dilated, panc_peripancreatic_fluid, panc_calcification_present |
| Spleen         | spl_visualized, spl_length_cm, spl_echotexture | Echotexture, length | spl_size, spl_lesion_present, spl_largest_lesion_mm, spl_lesion_character |
| Kidneys R/L    | kid_r/l_visualized, length_cm, cortical_echogenicity, cmd, hydronephrosis_grade, calculus_present, largest_calculus_mm, mass_suspected | Length, echogenicity, CMD, calculus, hydro, mass | kid_*_cortical_thickness_mm, kid_*_cyst_present, kid_*_cyst_type, kid_*_mass_mm, kid_*_hydro_grade (enum), kid_*_ureter_stone_present, kid_*_ureter_stone_mm |
| Bladder        | (none)         | (none)                    | bla_adequately_filled, bla_wall_thickness_mm, bla_wall_thickened, bla_trabeculation, bla_calculus_present, bla_calculus_mm, bla_mass_present, bla_post_void_residual_ml |
| Ascites/FF     | ff_present, ff_amount | (none)                    | asc_present, asc_amount, aff_collection_present, aff_collection_site, aff_collection_mm |
