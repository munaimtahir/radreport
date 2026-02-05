# Phase-2 Base Templates v1.1 (Composition Map + Normal/Abnormal Narratives)

This document upgrades **Phase-2 Base Templates v1.0** to **v1.1** by applying deterministic rules-engine policies, explicit side/right and left wording, and standardized constraints—**without changing the underlying block/key structure** (prefixes and `_r_/_l_` instance tags remain unchanged). **Field lists remain unchanged.**

---

## Global conventions (v1.1)

### 1) Key and instance rules (unchanged)

* All field keys remain **prefixed** (e.g., `kid_`, `pleff_`, `scr_`).
* Repeated paired blocks continue to use **instance-tagged keys**:

  * Right instance keys: `*_r_*` (e.g., `kid_r_length_cm`)
  * Left instance keys: `*_l_*` (e.g., `kid_l_length_cm`)
* **No new templates** are introduced; only templates **A–P** are refactored.

### 2) Narrative rule model

* **One sentence per triggered rule.**
* **Multiple rules may trigger**, producing multiple sentences.
* Output is **deterministically ordered**:

  1. Technique/limitations (always first if triggered)
  2. Organ sections in the **template section order**
  3. Within each organ: **priority descending**, then stable lexical order by `rule_id`

### 3) Side-specific + right and left wording policy (paired instances)

For any finding based on right/left instances (kidney, ureter/UVJ, pleural effusion, scrotum, ovary, carotid):

* If **only right** abnormal → sentence explicitly says **“Right …”**
* If **only left** abnormal → sentence explicitly says **“Left …”**
* If **both sides** abnormal → either:

  * one combined sentence starting **“right and left …”** with **(R: …, L: …)** details **only when the template explicitly defines a combined rule**, OR
  * two separate sentences (Right…, Left…) when the template uses separate side rules

**No sentence may use “side-specific”.**

### 4) Conflict prevention

Rules must not create contradictions within the same structure. Each rule can declare:

* **priority** (integer; higher runs first within an organ)
* **suppress_if** (a condition that prevents the rule from firing)
* **suppresses** (a list of rule_ids this rule suppresses if it fires)

(See **RULES_ENGINE_POLICY.md** section below.)

### 5) Impression inclusion rule (unchanged intent; now side-aware)

* Only **high-value abnormalities** go to Impression.
* For paired findings, Impression text must be **Right / Left / right and left** and must not use “side-specific”.

---

## Default adult thresholds (v1.1)

These constants are referenced by templates; thresholds are **unchanged** from v1.0 intent.

* **AAA definition:** `AAA_MM = 30` → abnormal if `aiv_aorta_max_diameter_mm ≥ 30`
* **CBD dilatation:** `CBD_DIL_MM = 6` → abnormal if `gb_cbd_diameter_mm > 6`
* **Portal vein dilatation:** `PV_DIL_MM = 13` → abnormal if `liv_portal_vein_diameter_mm > 13` (used only if a template references it)
* **Appendix abnormal diameter:** `APP_DIL_MM = 6` → abnormal if `app_appendix_diameter_mm > 6`
* **Significant PVR:** `PVR_ML = 100` → significant if `bl_pvr_ml ≥ 100`
* **Prostate enlarged:** `PROS_ML = 30` → enlarged if `pros_volume_ml > 30`
* **Short cervix:** `CERVIX_MM = 25` → short if `pl_cervical_length_mm < 25`

---

# RULES_ENGINE_POLICY.md (v1.1)

## 1) Rule evaluation order

For each report generation:

1. **Technique/limitations rules** (global + per-block quality fields)
2. **Organ sections** strictly in the template’s section order
3. **Within each organ section**:

   * **Priority descending** (higher first)
   * If equal priority: stable lexical order by `rule_id`

## 2) Rule schema (spec-level; no code)

Each abnormal rule is specified as:

* **rule_id:** unique within the template
* **trigger:** deterministic condition using fields
* **sentence:** exactly one sentence
* **priority:** integer (recommended range 10–100)
* **suppress_if:** condition that prevents firing
* **suppresses:** list of `rule_id`s to suppress if this rule fires

## 3) Suppression/conflict handling

* If a rule fires, it removes any rules listed in its **suppresses** list from the output set.
* A rule with **suppress_if** true is treated as **not triggered**.
* **Non-visualization** rules are treated as *gatekeepers* and typically suppress diagnosis rules for that structure.

## 4) Side/right and left sentence generation policy

Paired-instance findings (kidneys, ureters/UVJ, pleural effusion, scrotum, ovaries, carotids) may be represented in **either** of two template patterns. The engine must support both, and must **not** invent combined wording unless the template explicitly defines it.

**Pattern A — Combined branching rule (single rule, single sentence):**

* The rule evaluates both sides and outputs **exactly one** of:
  * **Right-only** sentence starting “Right …”
  * **Left-only** sentence starting “Left …”
  * **Both-sides** combined sentence starting “right and left …”, optionally with **(R: …, L: …)** details

**Pattern B — Separate side rules (two rules, two sentences):**

* Two independent rules exist (e.g., `..._R` and `..._L`).
* If only one side is abnormal, only that side’s sentence appears.
* If both sides are abnormal, **both** sentences appear (Right…, Left…) in deterministic order.

**Hard constraint:** no output sentence may contain the phrase “side-specific”.

## 5) Placeholder resolution policy

Placeholders like `{ep_ga_weeks_days}` or `{pleff_r_amount}` are resolved as:

* If the referenced field is present and non-empty → substitute its display value.
* If missing/empty:

  * For clinical measurements: omit the parenthetical detail rather than output “null”.
  * Example: `“Right pleural effusion is present.”` (instead of including empty `{pleff_r_amount}`)

### Placeholder-safe rendering rules (non-negotiable)

* If a placeholder resolves to missing/empty, the engine must **remove the entire dependent fragment** and must not leave:
  * `null`, `None`, `NaN`, or empty strings rendered as text
  * empty parentheses `()`
  * dangling punctuation (e.g., `due to .`, `mm).`, extra double-spaces)

### Optional segment syntax (spec-level)

* Any text wrapped in `[[ ... ]]` is an **optional segment**.
* An optional segment is rendered **only if all placeholders inside it resolve to non-empty values**.
* If any placeholder inside is missing/empty, the entire segment (including surrounding spaces/punctuation inside the brackets) is removed.

### FIRST_NON_EMPTY() macro (spec-level)

* The macro `{FIRST_NON_EMPTY(k1, k2, ... , kn)}` resolves to the **first non-empty** value among the listed keys.
* If all are empty, the macro resolves to empty and must trigger fragment omission (same as above).

---

# Templates A–P (v1.1)

> **Note:** “Fields included (by key)” lists are **unchanged** from v1.0 and are repeated verbatim here for implementation safety.

---

## A) USG Abdomen (complete)

### Template header

* **template_code:** USG_ABD_COMPLETE_V1
* **display_name:** USG Abdomen (Complete)
* **modality:** USG
* **Default sections order (Headings)**

  * Technique / Limitations
  * Liver
  * Gall bladder & CBD
  * Pancreas
  * Spleen
  * Abdominal aorta & IVC
  * Right kidney
  * Left kidney
  * Right ureter/UVJ
  * Left ureter/UVJ
  * Urinary bladder
  * Free fluid
  * Pleural effusion (lung bases)
  * Impression

### Block instances used

* Liver ×1
* Gall bladder & CBD ×1
* Pancreas ×1
* Spleen ×1
* Abdominal aorta & IVC ×1
* Kidney ×2 (Right, Left)
* Ureter/UVJ ×2 (Right, Left)
* Urinary bladder ×1
* Free fluid ×1
* Pleural effusion ×2 (Right, Left)

### Fields included (by key) — unchanged

**Liver**

* liv_visualized, liv_image_quality, liv_limitation_reason
* liv_size_cm, liv_contour, liv_echotexture, liv_echogenicity
* liv_focal_lesion_present, liv_ihbd_present
* liv_portal_vein_diameter_mm

**Gall bladder & CBD**

* gb_visualized, gb_image_quality, gb_limitation_reason
* gb_status, gb_stones_present, gb_sludge_present
* gb_wall_thickness_mm, gb_murphy_sign_positive, gb_pericholecystic_fluid_present
* gb_cbd_diameter_mm, gb_cbd_stone_suspected

**Pancreas**

* panc_visualized, panc_image_quality, panc_limitation_reason
* panc_visualized_extent
* panc_size, panc_echotexture
* panc_mpd_diameter_mm
* panc_peripancreatic_fluid_present
* panc_focal_lesion_present

**Spleen**

* spl_visualized, spl_image_quality, spl_limitation_reason
* spl_length_cm, spl_echotexture, spl_focal_lesion_present

**Abdominal aorta & IVC**

* aiv_visualized, aiv_image_quality, aiv_limitation_reason
* aiv_aorta_max_diameter_mm, aiv_aorta_plaque_present
* aiv_ivc_thrombus_suspected

**Right kidney (Kidney instance)**

* kid_r_visualized, kid_r_image_quality, kid_r_limitation_reason
* kid_r_side
* kid_r_length_cm
* kid_r_cortical_echogenicity, kid_r_cmd
* kid_r_hydronephrosis_grade
* kid_r_calculus_present, kid_r_largest_calculus_mm
* kid_r_simple_cyst_present, kid_r_largest_cyst_mm
* kid_r_mass_suspected, kid_r_perinephric_collection_present

**Left kidney (Kidney instance)**

* kid_l_visualized, kid_l_image_quality, kid_l_limitation_reason
* kid_l_side
* kid_l_length_cm
* kid_l_cortical_echogenicity, kid_l_cmd
* kid_l_hydronephrosis_grade
* kid_l_calculus_present, kid_l_largest_calculus_mm
* kid_l_simple_cyst_present, kid_l_largest_cyst_mm
* kid_l_mass_suspected, kid_l_perinephric_collection_present

**Right ureter/UVJ (Ureter instance)**

* ure_r_visualized, ure_r_image_quality, ure_r_limitation_reason
* ure_r_side
* ure_r_segment_assessed
* ure_r_hydroureter_present
* ure_r_stone_suspected, ure_r_stone_location, ure_r_stone_size_mm
* ure_r_jet_seen

**Left ureter/UVJ (Ureter instance)**

* ure_l_visualized, ure_l_image_quality, ure_l_limitation_reason
* ure_l_side
* ure_l_segment_assessed
* ure_l_hydroureter_present
* ure_l_stone_suspected, ure_l_stone_location, ure_l_stone_size_mm
* ure_l_jet_seen

**Urinary bladder**

* bl_visualized, bl_image_quality, bl_limitation_reason
* bl_distended
* bl_wall_thickness_mm, bl_trabeculation_present
* bl_stone_present, bl_mass_suspected, bl_debris_present
* bl_prevoid_volume_ml, bl_pvr_ml

**Free fluid**

* ff_visualized, ff_image_quality, ff_limitation_reason
* ff_present, ff_amount, ff_distribution
* ff_complex_present, ff_loculated_collection_suspected

**Pleural effusion — Right**

* pleff_r_visualized, pleff_r_image_quality, pleff_r_limitation_reason
* pleff_r_side
* pleff_r_present, pleff_r_amount
* pleff_r_complex_present, pleff_r_adjacent_consolidation_suspected

**Pleural effusion — Left**

* pleff_l_visualized, pleff_l_image_quality, pleff_l_limitation_reason
* pleff_l_side
* pleff_l_present, pleff_l_amount
* pleff_l_complex_present, pleff_l_adjacent_consolidation_suspected

### Normal narrative (unchanged)

1. “Assessment is satisfactory with no significant limitation.”
2. “The liver is normal in size with homogeneous echotexture and normal echogenicity, and no focal lesion is seen.”
3. “The gallbladder is unremarkable with no calculus or sludge, and the common bile duct is not dilated.”
4. “The pancreas is unremarkable in the visualized portions with no ductal dilatation.”
5. “The spleen is normal in size and echotexture with no focal lesion.”
6. “The abdominal aorta is normal in caliber with no aneurysm, and no IVC thrombus is suspected.”
7. “Both kidneys are normal in size with preserved corticomedullary differentiation, and no hydronephrosis or renal calculus is seen.”
8. “No hydroureter is seen and no ureteric calculus is identified in the assessed segments.”
9. “The urinary bladder is well distended with normal wall thickness, and no intraluminal mass or calculus is seen.”
10. “No free fluid or pleural effusion is seen.”

### Abnormal narrative rules (updated; side-aware + precedence)

**Technique / Limitations**

* rule_id: ABD_TECH_OK
  Trigger: aiv_image_quality!=limited AND bl_image_quality!=limited AND ff_image_quality!=limited AND gb_image_quality!=limited AND kid_l_image_quality!=limited AND kid_r_image_quality!=limited AND liv_image_quality!=limited AND panc_image_quality!=limited AND pleff_l_image_quality!=limited AND pleff_r_image_quality!=limited AND spl_image_quality!=limited AND ure_l_image_quality!=limited AND ure_r_image_quality!=limited AND aiv_visualized!=false AND bl_visualized!=false AND ff_visualized!=false AND gb_visualized!=false AND kid_l_visualized!=false AND kid_r_visualized!=false AND liv_visualized!=false AND panc_visualized!=false AND pleff_l_visualized!=false AND pleff_r_visualized!=false AND spl_visualized!=false AND ure_l_visualized!=false AND ure_r_visualized!=false
  Sentence: “Assessment is satisfactory.”
  Priority: 110
* rule_id: ABD_TECH_LIMITED_WITH_REASON
  Trigger: (aiv_image_quality=limited OR bl_image_quality=limited OR ff_image_quality=limited OR gb_image_quality=limited OR kid_l_image_quality=limited OR kid_r_image_quality=limited OR liv_image_quality=limited OR panc_image_quality=limited OR pleff_l_image_quality=limited OR pleff_r_image_quality=limited OR spl_image_quality=limited OR ure_l_image_quality=limited OR ure_r_image_quality=limited OR aiv_visualized=false OR bl_visualized=false OR ff_visualized=false OR gb_visualized=false OR kid_l_visualized=false OR kid_r_visualized=false OR liv_visualized=false OR panc_visualized=false OR pleff_l_visualized=false OR pleff_r_visualized=false OR spl_visualized=false OR ure_l_visualized=false OR ure_r_visualized=false) AND (aiv_limitation_reason is not empty OR bl_limitation_reason is not empty OR ff_limitation_reason is not empty OR gb_limitation_reason is not empty OR kid_l_limitation_reason is not empty OR kid_r_limitation_reason is not empty OR liv_limitation_reason is not empty OR panc_limitation_reason is not empty OR pleff_l_limitation_reason is not empty OR pleff_r_limitation_reason is not empty OR spl_limitation_reason is not empty OR ure_l_limitation_reason is not empty OR ure_r_limitation_reason is not empty)
  Sentence: “Assessment is limited due to {FIRST_NON_EMPTY(aiv_limitation_reason, bl_limitation_reason, ff_limitation_reason, gb_limitation_reason, kid_l_limitation_reason, kid_r_limitation_reason, liv_limitation_reason, panc_limitation_reason, pleff_l_limitation_reason, pleff_r_limitation_reason, spl_limitation_reason, ure_l_limitation_reason, ure_r_limitation_reason)}.”
  Priority: 120
* rule_id: ABD_TECH_LIMITED
  Trigger: (aiv_image_quality=limited OR bl_image_quality=limited OR ff_image_quality=limited OR gb_image_quality=limited OR kid_l_image_quality=limited OR kid_r_image_quality=limited OR liv_image_quality=limited OR panc_image_quality=limited OR pleff_l_image_quality=limited OR pleff_r_image_quality=limited OR spl_image_quality=limited OR ure_l_image_quality=limited OR ure_r_image_quality=limited OR aiv_visualized=false OR bl_visualized=false OR ff_visualized=false OR gb_visualized=false OR kid_l_visualized=false OR kid_r_visualized=false OR liv_visualized=false OR panc_visualized=false OR pleff_l_visualized=false OR pleff_r_visualized=false OR spl_visualized=false OR ure_l_visualized=false OR ure_r_visualized=false) AND NOT (aiv_limitation_reason is not empty OR bl_limitation_reason is not empty OR ff_limitation_reason is not empty OR gb_limitation_reason is not empty OR kid_l_limitation_reason is not empty OR kid_r_limitation_reason is not empty OR liv_limitation_reason is not empty OR panc_limitation_reason is not empty OR pleff_l_limitation_reason is not empty OR pleff_r_limitation_reason is not empty OR spl_limitation_reason is not empty OR ure_l_limitation_reason is not empty OR ure_r_limitation_reason is not empty)
  Sentence: “Assessment is limited due to suboptimal acoustic window.”
  Priority: 121

**Liver**

* rule_id: LIV_HEPATOMEGALY
  Trigger: liv_size_cm > 15.0
  Sentence: “The liver is enlarged with preserved echotexture.”
  Priority: 90
* rule_id: LIV_FATTY
  Trigger: liv_echogenicity = increased
  Sentence: “The liver shows increased echogenicity consistent with fatty change.”
  Priority: 80
* rule_id: LIV_FOCAL_LESION
  Trigger: liv_focal_lesion_present = true
  Sentence: “A focal hepatic lesion is present.”
  Priority: 85
* rule_id: LIV_IHBD
  Trigger: liv_ihbd_present = true
  Sentence: “Intrahepatic biliary dilatation is present.”
  Priority: 88
* rule_id: LIV_PORTAL_VEIN_DIL
  Trigger: liv_portal_vein_diameter_mm > PV_DIL_MM
  Sentence: “The portal vein is dilated.”
  Priority: 60

**Gall bladder & CBD**

* rule_id: GB_CHOLELITHIASIS
  Trigger: gb_stones_present = true
  Sentence: “Cholelithiasis is present.”
  Priority: 85
* rule_id: GB_WALL_THICKENING
  Trigger: gb_wall_thickness_mm > 3
  Sentence: “Gallbladder wall thickening is noted (measures {gb_wall_thickness_mm} mm).”
  Priority: 82
* rule_id: GB_MURPHY_POSITIVE
  Trigger: gb_murphy_sign_positive = true
  Sentence: “Sonographic Murphy sign is positive.”
  Priority: 83
* rule_id: GB_PERICHOLECYSTIC_FLUID
  Trigger: gb_pericholecystic_fluid_present = true
  Sentence: “Pericholecystic fluid is present.”
  Priority: 84
* rule_id: GB_ACUTE_CHOLECYSTITIS_SUGGESTIVE
  Trigger: ((gb_wall_thickness_mm > 3) AND (gb_murphy_sign_positive = true)) OR ((gb_wall_thickness_mm > 3) AND (gb_pericholecystic_fluid_present = true)) OR ((gb_murphy_sign_positive = true) AND (gb_pericholecystic_fluid_present = true))
  Sentence: “Findings are suggestive of acute cholecystitis in the appropriate clinical setting.”
  Priority: 90
* rule_id: GB_CBD_DIL
  Trigger: gb_cbd_diameter_mm > CBD_DIL_MM
  Sentence: “The common bile duct is dilated.”
  Priority: 88
* rule_id: GB_CBD_STONE_SUSPECTED
  Trigger: gb_cbd_stone_suspected = true
  Sentence: “Choledocholithiasis is suspected.”
  Priority: 89

**Pancreas**

* rule_id: PANC_PANCREATITIS_PATTERN
  Trigger: (panc_size = bulky) AND (panc_echotexture = heterogeneous)
  Sentence: “Bulky heterogeneous pancreas; correlate clinically and with laboratory parameters for pancreatitis.”
  Priority: 85
* rule_id: PANC_FOCAL_LESION
  Trigger: panc_focal_lesion_present = true
  Sentence: “A focal pancreatic lesion is present.”
  Priority: 86
* rule_id: PANC_PERIPANCREATIC_FLUID
  Trigger: panc_peripancreatic_fluid_present = true
  Sentence: “Peripancreatic fluid is present.”
  Priority: 70

**Spleen**

* rule_id: SPL_SPLENOMEGALY
  Trigger: spl_length_cm > 12.0
  Sentence: “Splenomegaly is present.”
  Priority: 80
* rule_id: SPL_FOCAL_LESION
  Trigger: spl_focal_lesion_present = true
  Sentence: “A focal splenic lesion is present.”
  Priority: 82

**Aorta & IVC**

* rule_id: AIV_AAA
  Trigger: aiv_aorta_max_diameter_mm ≥ AAA_MM
  Sentence: “An abdominal aortic aneurysm is noted.”
  Priority: 90
* rule_id: AIV_IVC_THROMBUS_SUSPECTED
  Trigger: aiv_ivc_thrombus_suspected = true
  Sentence: “IVC thrombosis is suspected.”
  Priority: 88

**Kidneys (side-aware single-sentence rule)**

* rule_id: KID_HYDRONEPHROSIS
  Trigger: (kid_r_hydronephrosis_grade != none) OR (kid_l_hydronephrosis_grade != none)
  Sentence:

  * If right only: “Right hydronephrosis is present (Grade {kid_r_hydronephrosis_grade}).”
  * If left only: “Left hydronephrosis is present (Grade {kid_l_hydronephrosis_grade}).”
  * If both: “right and left hydronephrosis is present (R: Grade {kid_r_hydronephrosis_grade}, L: Grade {kid_l_hydronephrosis_grade}).”
    Priority: 90
* rule_id: KID_RENAL_CALCULUS_R
  Trigger: (kid_r_calculus_present = true)
  Sentence: “Right renal calculus is present[[ (largest {kid_r_largest_calculus_mm} mm)]].”
  Priority: 88
* rule_id: KID_RENAL_CALCULUS_L
  Trigger: (kid_l_calculus_present = true)
  Sentence: “Left renal calculus is present[[ (largest {kid_l_largest_calculus_mm} mm)]].”
  Priority: 88
* rule_id: KID_MEDICAL_RENAL_DISEASE_PATTERN_R
  Trigger: (kid_r_cortical_echogenicity = increased AND kid_r_cmd = reduced)
  Sentence: “Sonographic features suggest medical renal disease on the right.”
  Priority: 80
* rule_id: KID_MEDICAL_RENAL_DISEASE_PATTERN_L
  Trigger: (kid_l_cortical_echogenicity = increased AND kid_l_cmd = reduced)
  Sentence: “Sonographic features suggest medical renal disease on the left.”
  Priority: 80
* rule_id: KID_MASS_SUSPECTED_R
  Trigger: (kid_r_mass_suspected = true)
  Sentence: “A right renal mass is suspected.”
  Priority: 92
* rule_id: KID_MASS_SUSPECTED_L
  Trigger: (kid_l_mass_suspected = true)
  Sentence: “A left renal mass is suspected.”
  Priority: 92

**Ureters / UVJ (side-aware)**

* rule_id: URE_STONE_SUSPECTED_R
  Trigger: (ure_r_stone_suspected = true)
  Sentence: “A right ureteric calculus is suspected.”
  Priority: 88
* rule_id: URE_STONE_SUSPECTED_L
  Trigger: (ure_l_stone_suspected = true)
  Sentence: “A left ureteric calculus is suspected.”
  Priority: 88
* rule_id: URE_HYDROURETER_R
  Trigger: (ure_r_hydroureter_present = true)
  Sentence: “Right hydroureter is present.”
  Priority: 80
* rule_id: URE_HYDROURETER_L
  Trigger: (ure_l_hydroureter_present = true)
  Sentence: “Left hydroureter is present.”
  Priority: 80

**Urinary bladder**

* rule_id: BL_MASS_SUSPECTED
  Trigger: bl_mass_suspected = true
  Sentence: “A polypoid bladder lesion is suspected.”
  Priority: 90
* rule_id: BL_PVR_SIGNIFICANT
  Trigger: bl_pvr_ml ≥ PVR_ML
  Sentence: “Significant post-void residual urine is noted.”
  Priority: 85
* rule_id: BL_STONE
  Trigger: bl_stone_present = true
  Sentence: “A vesical calculus is noted.”
  Priority: 84

**Free fluid**

* rule_id: FF_MOD_LARGE
  Trigger: ff_present = true AND (ff_amount = moderate OR ff_amount = large)
  Sentence: “Moderate to large free fluid is present.”
  Priority: 88
* rule_id: FF_COMPLEX
  Trigger: ff_present = true AND (ff_complex_present = true OR ff_loculated_collection_suspected = true)
  Sentence: “Complex or loculated free fluid is present.”
  Priority: 89

**Pleural effusion (side-aware single-sentence rule)**

* rule_id: PLEFF_PRESENT_R
  Trigger: (pleff_r_present = true)
  Sentence: “Right pleural effusion is present[[ ({pleff_r_amount})]].”
  Priority: 85
* rule_id: PLEFF_PRESENT_L
  Trigger: (pleff_l_present = true)
  Sentence: “Left pleural effusion is present[[ ({pleff_l_amount})]].”
  Priority: 85

### Impression rules (updated to be side/right and left specific)

* **Goes to Impression**

  * Liver: hepatomegaly; hepatic steatosis; focal hepatic lesion; IHBD; portal vein dilatation (if triggered)
  * GB/CBD: cholelithiasis; acute cholecystitis pattern; CBD dilatation; suspected choledocholithiasis
  * Pancreas: pancreatitis pattern; focal lesion
  * Spleen: splenomegaly; focal lesion
  * Aorta/IVC: AAA; suspected IVC thrombosis
  * Kidneys: Right/Left/right and left hydronephrosis (include grade); Right/Left/right and left renal calculus (include size); renal mass suspected (side); medical renal disease (side/right and left)
  * Ureters: Right/Left/right and left ureteric calculus; hydroureter (side/right and left)
  * Bladder: suspected lesion; significant PVR; vesical calculus
  * Free fluid: moderate/large; complex/loculated
  * Pleural effusion: side/right and left (include amount when available)
* **Stays narrative-only**

  * Minor plaque/descriptor findings unless clinically emphasized

### Template constraints (standardized)

* Uses **Default adult thresholds**: AAA_MM=30, CBD_DIL_MM=6, PV_DIL_MM=13 (if used), PVR_ML=100.

---

## B) USG KUB

### Template header

* **template_code:** USG_KUB_V1
* **display_name:** USG KUB
* **modality:** USG
* **Default sections order (Headings)**

  * Technique / Limitations
  * Right kidney
  * Left kidney
  * Right ureter/UVJ
  * Left ureter/UVJ
  * Urinary bladder
  * Impression

### Block instances used

* Kidney ×2 (Right, Left)
* Ureter/UVJ ×2 (Right, Left)
* Urinary bladder ×1

### Fields included (by key) — unchanged

*(Same as v1.0; omitted here for brevity in this section if you prefer, but per your requirement they should remain unchanged. Keeping them unchanged as in v1.0.)*
**Right kidney:** kid_r_visualized, kid_r_image_quality, kid_r_limitation_reason, kid_r_side, kid_r_length_cm, kid_r_cortical_echogenicity, kid_r_cmd, kid_r_hydronephrosis_grade, kid_r_calculus_present, kid_r_largest_calculus_mm, kid_r_simple_cyst_present, kid_r_largest_cyst_mm, kid_r_mass_suspected, kid_r_perinephric_collection_present
**Left kidney:** kid_l_visualized, kid_l_image_quality, kid_l_limitation_reason, kid_l_side, kid_l_length_cm, kid_l_cortical_echogenicity, kid_l_cmd, kid_l_hydronephrosis_grade, kid_l_calculus_present, kid_l_largest_calculus_mm, kid_l_simple_cyst_present, kid_l_largest_cyst_mm, kid_l_mass_suspected, kid_l_perinephric_collection_present
**Right ureter/UVJ:** ure_r_visualized, ure_r_image_quality, ure_r_limitation_reason, ure_r_side, ure_r_segment_assessed, ure_r_hydroureter_present, ure_r_stone_suspected, ure_r_stone_location, ure_r_stone_size_mm, ure_r_jet_seen
**Left ureter/UVJ:** ure_l_visualized, ure_l_image_quality, ure_l_limitation_reason, ure_l_side, ure_l_segment_assessed, ure_l_hydroureter_present, ure_l_stone_suspected, ure_l_stone_location, ure_l_stone_size_mm, ure_l_jet_seen
**Urinary bladder:** bl_visualized, bl_image_quality, bl_limitation_reason, bl_distended, bl_wall_thickness_mm, bl_trabeculation_present, bl_stone_present, bl_mass_suspected, bl_debris_present, bl_prevoid_volume_ml, bl_pvr_ml

### Normal narrative (unchanged)

1. “Assessment is satisfactory with no significant limitation.”
2. “Both kidneys are normal in size with preserved corticomedullary differentiation.”
3. “No hydronephrosis is seen on either side.”
4. “No renal calculus is identified on either side.”
5. “No hydroureter is seen and no ureteric calculus is identified in the assessed segments.”
6. “The urinary bladder is well distended with normal wall thickness and no intraluminal mass or calculus.”
7. “Post-void residual urine is not significant.”

### Abnormal narrative rules (updated; side-aware; ordered)

* rule_id: KUB_TECH_OK
  Trigger: bl_image_quality!=limited AND kid_l_image_quality!=limited AND kid_r_image_quality!=limited AND ure_l_image_quality!=limited AND ure_r_image_quality!=limited AND bl_visualized!=false AND kid_l_visualized!=false AND kid_r_visualized!=false AND ure_l_visualized!=false AND ure_r_visualized!=false
  Sentence: “Assessment is satisfactory.”
  Priority: 110
* rule_id: KUB_TECH_LIMITED_WITH_REASON
  Trigger: (bl_image_quality=limited OR kid_l_image_quality=limited OR kid_r_image_quality=limited OR ure_l_image_quality=limited OR ure_r_image_quality=limited OR bl_visualized=false OR kid_l_visualized=false OR kid_r_visualized=false OR ure_l_visualized=false OR ure_r_visualized=false) AND (bl_limitation_reason is not empty OR kid_l_limitation_reason is not empty OR kid_r_limitation_reason is not empty OR ure_l_limitation_reason is not empty OR ure_r_limitation_reason is not empty)
  Sentence: “Assessment is limited due to {FIRST_NON_EMPTY(bl_limitation_reason, kid_l_limitation_reason, kid_r_limitation_reason, ure_l_limitation_reason, ure_r_limitation_reason)}.”
  Priority: 120
* rule_id: KUB_TECH_LIMITED
  Trigger: (bl_image_quality=limited OR kid_l_image_quality=limited OR kid_r_image_quality=limited OR ure_l_image_quality=limited OR ure_r_image_quality=limited OR bl_visualized=false OR kid_l_visualized=false OR kid_r_visualized=false OR ure_l_visualized=false OR ure_r_visualized=false) AND NOT (bl_limitation_reason is not empty OR kid_l_limitation_reason is not empty OR kid_r_limitation_reason is not empty OR ure_l_limitation_reason is not empty OR ure_r_limitation_reason is not empty)
  Sentence: “Assessment is limited due to suboptimal acoustic window.”
  Priority: 121

* rule_id: KUB_KID_HYDRONEPHROSIS
  Trigger: kid_r_hydronephrosis_grade!=none OR kid_l_hydronephrosis_grade!=none
  Sentence: Right/Left/right and left hydronephrosis sentence (same wording policy as Template A).
  Priority: 90

* rule_id: KUB_KID_RENAL_CALCULUS
  Trigger: kid_r_calculus_present=true OR kid_l_calculus_present=true
  Sentence: Right/Left/right and left renal calculus sentence (same wording policy as Template A).
  Priority: 88

* rule_id: KUB_URE_STONE
  Trigger: ure_r_stone_suspected=true OR ure_l_stone_suspected=true
  Sentence: “A right/left/right and left ureteric calculus is suspected.”
  Priority: 87

* rule_id: KUB_BL_STONE
  Trigger: bl_stone_present=true
  Sentence: “A vesical calculus is noted.”
  Priority: 86

* rule_id: KUB_BL_MASS
  Trigger: bl_mass_suspected=true
  Sentence: “A polypoid bladder lesion is suspected.”
  Priority: 90

* rule_id: KUB_PVR
  Trigger: bl_pvr_ml ≥ PVR_ML
  Sentence: “Significant post-void residual urine is noted.”
  Priority: 85

### Impression rules (side-aware)

* **Goes to Impression:** hydronephrosis (R/L/right and left with grade), renal calculi (R/L/right and left with size), ureteric calculus suspected (R/L/right and left), suspected bladder lesion, significant PVR, renal mass suspected (side)
* **Stays narrative-only:** mild debris/trabeculation unless clinically emphasized

### Template constraints (standardized)

* References **PVR_ML = 100** and other relevant adult defaults as applicable.

---

## C) USG Pelvis Female

### Template header

* **template_code:** USG_PELVIS_FEMALE_V1
* **display_name:** USG Pelvis Female
* **modality:** USG
* **Default sections order (Headings)**

  * Technique / Limitations
  * Urinary bladder
  * Uterus & endometrium
  * Right ovary
  * Left ovary
  * Adnexa (mass characterization)
  * Free fluid
  * Impression

### Block instances used

* Urinary bladder ×1
* Uterus & endometrium ×1
* Ovary ×2 (Right, Left)
* Adnexal mass ×1
* Free fluid ×1

### Fields included (by key) — unchanged

*(Same as v1.0.)*

### Normal narrative (unchanged)

1. “Assessment is satisfactory with no significant limitation.”
2. “The urinary bladder is adequately distended with normal wall thickness and no intraluminal mass or calculus.”
3. “The uterus is normal in size and echotexture.”
4. “The endometrium is within expected limits for the clinical context.”
5. “Both ovaries are normal in size with no adnexal mass.”
6. “No significant ovarian cyst is seen.”
7. “No free fluid is seen.”

### Abnormal narrative rules (updated; side-aware; precedence)

* rule_id: PF_TECH_OK
  Trigger: adnx_image_quality!=limited AND bl_image_quality!=limited AND ff_image_quality!=limited AND ov_l_image_quality!=limited AND ov_r_image_quality!=limited AND ut_image_quality!=limited
  Sentence: “Assessment is satisfactory.”
  Priority: 110
* rule_id: PF_TECH_LIMITED
  Trigger: adnx_image_quality=limited OR bl_image_quality=limited OR ff_image_quality=limited OR ov_l_image_quality=limited OR ov_r_image_quality=limited OR ut_image_quality=limited
  Sentence: “Assessment is limited due to suboptimal acoustic window.”
  Priority: 120

**Uterus/endometrium**

* rule_id: PF_UT_FIBROID
  Trigger: ut_fibroid_present=true
  Sentence: “Uterine fibroid(s) are noted.”
  Priority: 85
* rule_id: PF_UT_ENDO_THICK_APPEARANCE
  Trigger: ut_endometrium_appearance=thickened
  Sentence: “The endometrium appears thickened.”
  Priority: 80
* rule_id: PF_UT_ENDO_POLYPOID
  Trigger: ut_endometrium_appearance=polypoid
  Sentence: “A focal polypoid endometrial lesion is suspected.”
  Priority: 88

**Ovaries (side-aware combined rules)**

* rule_id: PF_OV_COMPLEX_CYST_R
  Trigger: ov_r_complex_cyst_suspected=true
  Sentence: “A complex right ovarian cyst is noted.”
  Priority: 86
* rule_id: PF_OV_COMPLEX_CYST_L
  Trigger: ov_l_complex_cyst_suspected=true
  Sentence: “A complex left ovarian cyst is noted.”
  Priority: 86
* rule_id: PF_OV_SOLID_MASS_SUSPECTED_R
  Trigger: ov_r_solid_mass_suspected=true
  Sentence: “A right adnexal mass is suspected.”
  Priority: 90
* rule_id: PF_OV_SOLID_MASS_SUSPECTED_L
  Trigger: ov_l_solid_mass_suspected=true
  Sentence: “A left adnexal mass is suspected.”
  Priority: 90

**Adnexal mass characterization**

* rule_id: PF_ADNX_SUSPICIOUS_FEATURES
  Trigger: adnx_mass_present=true AND (adnx_papillary_projection_present=true OR adnx_solid_component_present=true OR adnx_vascularity=internal OR adnx_vascularity=marked)
  Sentence: “The adnexal lesion shows suspicious sonographic features.”
  Priority: 92
* rule_id: PF_ADNX_MASS_PRESENT
  Trigger: adnx_mass_present=true
  Sentence: “An adnexal mass is present.”
  Priority: 80
  suppress_if: (adnx_papillary_projection_present=true OR adnx_solid_component_present=true OR adnx_vascularity=internal OR adnx_vascularity=marked)
  (So “mass present” does not duplicate when suspicious-features sentence is already output.)

**Free fluid**

* rule_id: PF_FF_MOD_LARGE
  Trigger: ff_present=true AND (ff_amount=moderate OR ff_amount=large)
  Sentence: “Moderate to large free fluid is present.”
  Priority: 85

### Impression rules (side-aware where applicable)

* **Goes to Impression:** fibroids (if clinically relevant), thickened/polypoid endometrium, adnexal mass (with side if available via adnx_side), suspicious adnexal lesion, moderate/large or complex free fluid, right/left/right and left ovarian complex cysts or suspected masses
* **Stays narrative-only:** PCOM pattern unless requested; small simple cysts unless policy later defines size escalation

### Template constraints (standardized)

* Endometrium: **Template uses appearance enum only** (no auto-thresholding).
* Uses **Default adult thresholds** where relevant (none mandatory here beyond global formatting).

---

## D) USG Pelvis Male

*(Updates: side wording not applicable; PVR and prostate thresholds referenced as constants; ordering clarified.)*

### Template header

* **template_code:** USG_PELVIS_MALE_V1
* **display_name:** USG Pelvis Male
* **modality:** USG

### Block instances used

* Urinary bladder ×1
* Prostate & seminal vesicles ×1
* Free fluid ×1

### Fields included (by key) — unchanged

*(Same as v1.0.)*

### Normal narrative (unchanged)

1. “Assessment is satisfactory with no significant limitation.”
2. “The urinary bladder is adequately distended with normal wall thickness and no intraluminal mass or calculus.”
3. “Post-void residual urine is not significant.”
4. “The prostate is normal in size and echotexture.”
5. “Seminal vesicles are unremarkable.”
6. “No free fluid is seen.”

### Abnormal narrative rules (updated; ordered)

* rule_id: PM_TECH_OK
  Trigger: bl_image_quality!=limited AND ff_image_quality!=limited AND pros_image_quality!=limited
  Sentence: “Assessment is satisfactory.”
  Priority: 110
* rule_id: PM_TECH_LIMITED
  Trigger: bl_image_quality=limited OR ff_image_quality=limited OR pros_image_quality=limited
  Sentence: “Assessment is limited due to suboptimal acoustic window.”
  Priority: 120
* rule_id: PM_PROSTATE_ENLARGED
  Trigger: pros_volume_ml > PROS_ML
  Sentence: “The prostate is enlarged.”
  Priority: 90
* rule_id: PM_MEDIAN_LOBE
  Trigger: pros_median_lobe_protrusion=true
  Sentence: “Median lobe protrusion into the bladder base is noted.”
  Priority: 85
* rule_id: PM_PVR
  Trigger: bl_pvr_ml ≥ PVR_ML
  Sentence: “Significant post-void residual urine is noted.”
  Priority: 88
* rule_id: PM_BL_MASS
  Trigger: bl_mass_suspected=true
  Sentence: “A polypoid bladder lesion is suspected.”
  Priority: 92
* rule_id: PM_FF_MOD_LARGE
  Trigger: ff_present=true AND (ff_amount=moderate OR ff_amount=large)
  Sentence: “Moderate to large free fluid is present.”
  Priority: 80

### Impression rules (updated)

* **Goes to Impression:** BPH pattern (enlarged prostate ± median lobe), significant PVR, suspected bladder lesion, moderate/large or complex free fluid
* **Stays narrative-only:** mild trabeculation/debris unless clinically emphasized

### Template constraints (standardized)

* Uses PROS_ML=30 and PVR_ML=100.

---

## E) USG RUQ (targeted)

*(Updates: right-only kidney/pleural already explicit; CBD threshold referenced.)*

### Template header

* **template_code:** USG_RUQ_TARGETED_V1
* **display_name:** USG RUQ (Targeted)
* **modality:** USG

### Block instances used

* Liver ×1
* Gall bladder & CBD ×1
* Pancreas ×1
* Kidney ×1 (Right)
* Pleural effusion ×1 (Right)

### Fields included (by key) — unchanged

*(Same as v1.0.)*

### Normal narrative (unchanged)

1. “Targeted right upper quadrant ultrasound is performed with satisfactory assessment.”
2. “The liver is normal in size with homogeneous echotexture and normal echogenicity, and no focal lesion is seen.”
3. “The gallbladder is unremarkable with no calculus or sludge.”
4. “The common bile duct is not dilated.”
5. “The pancreas is unremarkable in the visualized portions with no ductal dilatation.”
6. “The right kidney shows no hydronephrosis or renal calculus.”
7. “No right pleural effusion is seen.”

### Abnormal narrative rules (updated; ordered; no duplication)

* rule_id: RUQ_TECH_OK
  Trigger: gb_image_quality!=limited AND kid_r_image_quality!=limited AND liv_image_quality!=limited AND panc_image_quality!=limited AND pleff_r_image_quality!=limited
  Sentence: “Assessment is satisfactory.”
  Priority: 110
* rule_id: RUQ_TECH_LIMITED
  Trigger: gb_image_quality=limited OR kid_r_image_quality=limited OR liv_image_quality=limited OR panc_image_quality=limited OR pleff_r_image_quality=limited
  Sentence: “Assessment is limited due to suboptimal acoustic window.”
  Priority: 120
* rule_id: RUQ_GB_ACUTE_CHOLECYSTITIS_PATTERN
  Trigger: gb_wall_thickness_mm>3 OR gb_murphy_sign_positive=true OR gb_pericholecystic_fluid_present=true
  Sentence: “Findings are suggestive of acute cholecystitis.”
  Priority: 92
* rule_id: RUQ_GB_CHOLELITHIASIS
  Trigger: gb_stones_present=true
  Sentence: “Cholelithiasis is present.”
  Priority: 90
* rule_id: RUQ_CBD_DIL
  Trigger: gb_cbd_diameter_mm > CBD_DIL_MM
  Sentence: “The common bile duct is dilated.”
  Priority: 91
* rule_id: RUQ_CBD_STONE_SUSPECTED
  Trigger: gb_cbd_stone_suspected=true
  Sentence: “Choledocholithiasis is suspected.”
  Priority: 93
* rule_id: RUQ_LIV_IHBD
  Trigger: liv_ihbd_present=true
  Sentence: “Intrahepatic biliary dilatation is present.”
  Priority: 89
* rule_id: RUQ_PANC_PANCREATITIS_PATTERN
  Trigger: panc_size=bulky AND panc_echotexture=heterogeneous
  Sentence: “A bulky heterogeneous pancreas is noted, which may be seen in pancreatitis.”
  Priority: 85
* rule_id: RUQ_RIGHT_HYDRONEPHROSIS
  Trigger: kid_r_hydronephrosis_grade != none
  Sentence: “Right hydronephrosis is present (Grade {kid_r_hydronephrosis_grade}).”
  Priority: 88
* rule_id: RUQ_RIGHT_PLEFF
  Trigger: pleff_r_present=true
  Sentence: “Right pleural effusion is present[[ ({pleff_r_amount})]].”
  Priority: 80

### Impression rules (updated)

* **Goes to Impression:** cholelithiasis, acute cholecystitis pattern, CBD dilatation, suspected choledocholithiasis, IHBD, pancreatitis pattern, right hydronephrosis (with grade), right pleural effusion (with amount if available)
* **Stays narrative-only:** minor descriptors without a defined syndrome

### Template constraints (standardized)

* Uses CBD_DIL_MM=6, AAA/PVR not applicable here.

---

## F) USG Thyroid

### Template header

* **template_code:** USG_THYROID_V1
* **display_name:** USG Thyroid
* **modality:** USG

### Block instances used

* Thyroid ×1
* Cervical lymph nodes ×1

### Fields included (by key) — unchanged

*(Same as v1.0.)*

### Normal narrative (unchanged)

1. “Thyroid ultrasound is performed with satisfactory assessment.”
2. “Both thyroid lobes are normal in size with homogeneous echotexture.”
3. “The isthmus is within normal thickness.”
4. “No focal thyroid nodule is seen.”
5. “No suspicious cervical lymphadenopathy is seen.”
6. “No significant limitation is noted.”

### Abnormal narrative rules (updated; explicit suppression policy for “nodule present”)

**Policy chosen (v1.1):**
If suspicious nodule-feature rule fires, it **suppresses** the generic “nodule(s) present” sentence to avoid low-value duplication.

* rule_id: THY_TECH_OK
  Trigger: cln_image_quality!=limited AND thy_image_quality!=limited
  Sentence: “Assessment is satisfactory.”
  Priority: 110
* rule_id: THY_TECH_LIMITED
  Trigger: cln_image_quality=limited OR thy_image_quality=limited
  Sentence: “Assessment is limited due to suboptimal acoustic window.”
  Priority: 120

* rule_id: THY_THYROIDITIS_PATTERN
  Trigger: thy_echotexture=heterogeneous
  Sentence: “Heterogeneous thyroid echotexture is noted, which may be seen with thyroiditis in the appropriate clinical setting.”
  Priority: 85

* rule_id: THY_SUSPICIOUS_NODULE_FEATURES
  Trigger: thy_microcalcifications_suspected=true OR thy_dominant_margins=irregular OR thy_taller_than_wide=true
  Sentence: “Suspicious sonographic features are present in the dominant thyroid nodule.”
  Priority: 95
  suppresses: THY_NODULE_PRESENT

* rule_id: THY_NODULE_PRESENT
  Trigger: thy_nodule_present=true
  Sentence: “Thyroid nodule(s) are present.”
  Priority: 80

* rule_id: THY_LN_ENLARGED
  Trigger: cln_enlarged_present=true OR cln_short_axis_mm > 10
  Sentence: “Enlarged cervical lymph node(s) are noted.”
  Priority: 85

* rule_id: THY_LN_SUSPICIOUS_FEATURES
  Trigger: cln_shape=round OR cln_hilum_preserved=false OR cln_necrosis_present=true OR cln_calcification_present=true OR cln_abnormal_vascularity_present=true
  Sentence: “Suspicious nodal features are present.”
  Priority: 92

### Impression rules (updated)

* **Goes to Impression:** thyroiditis pattern (if used), thyroid nodule(s) (or suspicious nodule features), suspicious cervical lymphadenopathy
* **Stays narrative-only:** minor vascularity change without syndrome

### Template constraints (standardized)

* No threshold changes; suspicious logic remains feature-based.

---

## G) USG Breast (unilateral)

*(No side-instances; keep deterministic ordering and BI-RADS rule wording.)*

### Template header

* **template_code:** USG_BREAST_UNILATERAL_V1
* **display_name:** USG Breast (Unilateral)
* **modality:** USG

### Block instances used

* Breast parenchyma ×1
* Breast focal lesion ×1

### Fields included (by key) — unchanged

*(Same as v1.0.)*

### Normal narrative (unchanged)

1. “Unilateral breast ultrasound is performed with satisfactory assessment.”
2. “Breast parenchyma on the examined side is unremarkable.”
3. “No suspicious diffuse abnormality is seen.”
4. “No focal breast lesion is identified.”
5. “No significant limitation is noted.”
6. “Correlation with clinical findings is advised.”

### Abnormal narrative rules (updated; ordered)

* rule_id: BR_TECH_OK
  Trigger: brl_image_quality!=limited AND brp_image_quality!=limited
  Sentence: “Assessment is satisfactory.”
  Priority: 110
* rule_id: BR_TECH_LIMITED
  Trigger: brl_image_quality=limited OR brp_image_quality=limited
  Sentence: “Assessment is limited due to suboptimal acoustic window.”
  Priority: 120
* rule_id: BR_DUCT_ECTASIA
  Trigger: brp_duct_ectasia_present=true
  Sentence: “Duct ectasia is noted.”
  Priority: 70
* rule_id: BR_LESION_PRESENT
  Trigger: brl_lesion_present=true
  Sentence: “A focal breast lesion is present.”
  Priority: 90
* rule_id: BR_BIRADS_3
  Trigger: brl_birads=3
  Sentence: “The lesion is probably benign (BI-RADS 3) and short-interval follow-up is suggested.”
  Priority: 85
  suppress_if: brl_lesion_present=false
* rule_id: BR_BIRADS_4_5
  Trigger: brl_birads=4 OR brl_birads=5
  Sentence: “A suspicious lesion is noted (BI-RADS {brl_birads}) and tissue diagnosis is advised.”
  Priority: 95
  suppress_if: brl_lesion_present=false

### Impression rules (unchanged intent)

* **Goes to Impression:** BI-RADS 3/4/5 conclusion
* **Stays narrative-only:** background descriptors unless needed

### Template constraints

* BI-RADS is selected explicitly (no auto-scoring).

---

## H) USG Scrotum (right and left as two instances)

### Template header

* **template_code:** USG_SCROTUM_RL_V1
* **display_name:** USG Scrotum (right and left)
* **modality:** USG

### Block instances used

* Scrotum ×2 (Right, Left)

### Fields included (by key) — unchanged

*(Same as v1.0.)*

### Normal narrative (unchanged)

1. “right and left scrotal ultrasound is performed with satisfactory assessment.”
2. “The right testis is normal in echotexture with preserved vascularity and no focal lesion.”
3. “The left testis is normal in echotexture with preserved vascularity and no focal lesion.”
4. “No hydrocele is noted on either side.”
5. “No varicocele is noted on either side.”
6. “No significant limitation is noted.”

### Abnormal narrative rules (updated; side/right and left coherent; ordered)

* rule_id: SCR_TECH_OK
  Trigger: scr_l_image_quality!=limited AND scr_r_image_quality!=limited
  Sentence: “Assessment is satisfactory.”
  Priority: 110
* rule_id: SCR_TECH_LIMITED
  Trigger: scr_l_image_quality=limited OR scr_r_image_quality=limited
  Sentence: “Assessment is limited due to suboptimal acoustic window.”
  Priority: 120

* rule_id: SCR_TORSION_FLOW_R
  Trigger: (scr_r_testicular_flow = reduced OR scr_r_testicular_flow = absent)
  Sentence: “Reduced or absent intratesticular flow is noted in the right testis, suspicious for torsion.”
  Priority: 98
* rule_id: SCR_TORSION_FLOW_L
  Trigger: (scr_l_testicular_flow = reduced OR scr_l_testicular_flow = absent)
  Sentence: “Reduced or absent intratesticular flow is noted in the left testis, suspicious for torsion.”
  Priority: 98

* rule_id: SCR_EPIDIDYMITIS_PATTERN_R
  Trigger: (scr_r_epididymis_enlarged=true AND scr_r_epididymis_hypervascular=true)
  Sentence: “Findings are suggestive of right epididymitis.”
  Priority: 90
* rule_id: SCR_EPIDIDYMITIS_PATTERN_L
  Trigger: (scr_l_epididymis_enlarged=true AND scr_l_epididymis_hypervascular=true)
  Sentence: “Findings are suggestive of left epididymitis.”
  Priority: 90

* rule_id: SCR_INTRATESTICULAR_LESION_R
  Trigger: scr_r_intratesticular_lesion_present=true
  Sentence: “An intratesticular lesion is present in the right testis.”
  Priority: 92
* rule_id: SCR_INTRATESTICULAR_LESION_L
  Trigger: scr_l_intratesticular_lesion_present=true
  Sentence: “An intratesticular lesion is present in the left testis.”
  Priority: 92

* rule_id: SCR_HYDROCELE_R
  Trigger: scr_r_hydrocele != none
  Sentence: “A right hydrocele is noted.”
  Priority: 80
* rule_id: SCR_HYDROCELE_L
  Trigger: scr_l_hydrocele != none
  Sentence: “A left hydrocele is noted.”
  Priority: 80

* rule_id: SCR_VARICOCELE_R
  Trigger: scr_r_varicocele != none
  Sentence: “A right varicocele is noted.”
  Priority: 78
* rule_id: SCR_VARICOCELE_L
  Trigger: scr_l_varicocele != none
  Sentence: “A left varicocele is noted.”
  Priority: 78

### Impression rules (side-aware)

* **Goes to Impression:** torsion suspicion (side/right and left), epididymitis pattern (side/right and left), intratesticular lesion (side/right and left), hydrocele (if moderate/large; side), varicocele (moderate/severe; side)
* **Stays narrative-only:** mild hydrocele/varicocele unless emphasized

### Template constraints

* None.

---

## I) USG Soft tissue lump

*(No paired sides; ordering clarified.)*

### Template header

* **template_code:** USG_SOFT_TISSUE_LUMP_V1
* **display_name:** USG Soft Tissue Lump
* **modality:** USG

### Block instances used

* Soft tissue lump ×1

### Fields included (by key) — unchanged

*(Same as v1.0.)*

### Normal narrative (unchanged)

1. “Targeted soft tissue ultrasound is performed with satisfactory assessment.”
2. “The stated site is evaluated.”
3. “No focal soft tissue lesion is identified.”
4. “No drainable collection is seen.”
5. “No foreign body is suspected.”
6. “No significant limitation is noted.”

### Abnormal narrative rules (ordered)

* rule_id: ST_TECH_OK
  Trigger: st_image_quality!=limited
  Sentence: “Assessment is satisfactory.”
  Priority: 110
* rule_id: ST_TECH_LIMITED
  Trigger: st_image_quality=limited
  Sentence: “Assessment is limited due to suboptimal acoustic window.”
  Priority: 120
* rule_id: ST_COLLECTION
  Trigger: st_collection_features_present=true
  Sentence: “A complex fluid collection is present, suggestive of abscess in the appropriate clinical setting.”
  Priority: 95
* rule_id: ST_FOREIGN_BODY
  Trigger: st_foreign_body_suspected=true
  Sentence: “A foreign body is suspected.”
  Priority: 90
* rule_id: ST_SINUS
  Trigger: st_sinus_tract_suspected=true
  Sentence: “A sinus tract is suspected.”
  Priority: 85
* rule_id: ST_MASS_PRESENT
  Trigger: st_lesion_present=true
  Sentence: “A focal soft tissue lesion is present at the stated site.”
  Priority: 80

### Impression rules (unchanged intent)

* **Goes to Impression:** abscess/collection, suspected foreign body, suspicious mass pattern
* **Stays narrative-only:** benign-appearing minor lesions unless later policy defines escalation

### Template constraints

* Site via `st_site` only.

---

## J) USG Appendix/RLQ

### Template header

* **template_code:** USG_APPENDIX_RLQ_V1
* **display_name:** USG Appendix / RLQ
* **modality:** USG

### Block instances used

* Appendix/bowel ×1
* Free fluid ×1

### Fields included (by key) — unchanged

*(Same as v1.0.)*

### Normal narrative (unchanged)

1. “Targeted right lower quadrant ultrasound is performed with satisfactory assessment.”
2. “The appendix is visualized and appears normal.”
3. “No periappendiceal fluid is seen.”
4. “No appendicolith is identified.”
5. “No significant bowel wall thickening is seen in the assessed segment.”
6. “No free fluid is seen.”

### Abnormal narrative rules (updated with suppression)

* rule_id: APP_TECH_OK
  Trigger: app_image_quality!=limited AND ff_image_quality!=limited AND app_appendix_visualized!=false
  Sentence: “Assessment is satisfactory.”
  Priority: 110
* rule_id: APP_TECH_LIMITED
  Trigger: app_image_quality=limited OR ff_image_quality=limited OR app_appendix_visualized=false
  Sentence: “Assessment is limited due to suboptimal acoustic window.”
  Priority: 120

* rule_id: APP_NOT_VISUALIZED
  Trigger: app_appendix_visualized=false
  Sentence: “Appendix not visualized.”
  Priority: 95
  suppresses: APP_APPENDICITIS_PATTERN

* rule_id: APP_APPENDICITIS_PATTERN
  Trigger: (app_appendix_diameter_mm > APP_DIL_MM) OR (app_compressible=false) OR (app_hyperemia_present=true)
  Sentence: “Findings are suggestive of acute appendicitis.”
  Priority: 90
  suppress_if: app_appendix_visualized=false

* rule_id: APP_APPENDICOLITH
  Trigger: app_appendicolith_present=true
  Sentence: “An appendicolith is noted.”
  Priority: 85
  suppress_if: app_appendix_visualized=false

* rule_id: APP_FREE_FLUID
  Trigger: ff_present=true AND (ff_amount=moderate OR ff_amount=large)
  Sentence: “Moderate to large free fluid is present.”
  Priority: 80

### Impression rules (updated)

* **Goes to Impression:** appendicitis pattern, appendicolith (if appendix visualized), significant/complex free fluid
* **Stays narrative-only:** non-visualized appendix (unless future policy escalates)

### Template constraints (standardized)

* Appendix abnormal diameter uses **APP_DIL_MM = 6 mm**.

---

## K) USG Groin/Abdominal wall hernia

*(No paired sides; rule ordering clarified; no structural change.)*

### Template header

* **template_code:** USG_HERNIA_GROIN_AW_V1
* **display_name:** USG Groin / Abdominal Wall Hernia
* **modality:** USG

### Block instances used

* Hernia ×1

### Fields included (by key) — unchanged

*(Same as v1.0.)*

### Normal narrative (unchanged)

1. “Targeted ultrasound of the stated site is performed with satisfactory assessment.”
2. “No hernia is identified at the stated site.”
3. “No bowel-containing defect is seen.”
4. “No concerning collection is noted.”
5. “No significant limitation is noted.”
6. “Correlation with clinical examination is advised.”

### Abnormal narrative rules (ordered; deterministic)

* rule_id: HERN_TECH_OK
  Trigger: hern_image_quality!=limited
  Sentence: “Assessment is satisfactory.”
  Priority: 110
* rule_id: HERN_TECH_LIMITED
  Trigger: hern_image_quality=limited
  Sentence: “Assessment is limited due to suboptimal acoustic window.”
  Priority: 120
* rule_id: HERN_STRANGULATION
  Trigger: hern_strangulation_suspected=true
  Sentence: “Features suspicious for incarceration or strangulation are present.”
  Priority: 95
* rule_id: HERN_PRESENT
  Trigger: hern_present=true
  Sentence: “A {hern_type} hernia is present containing {hern_content}.”
  Priority: 90
* rule_id: HERN_REDUCIBLE
  Trigger: hern_reducible=true
  Sentence: “The hernia appears reducible.”
  Priority: 80
  suppress_if: hern_present=false

### Impression rules (unchanged intent)

* **Goes to Impression:** hernia (type/content), suspected incarceration/strangulation
* **Stays narrative-only:** reducibility unless emphasized

### Template constraints

* Site uses `hern_site` only.

---

## L) OB Early pregnancy viability & dating

*(No paired side instances beyond adnexal-side field; rule ordering and placeholder resolution clarified.)*

### Template header

* **template_code:** OB_EARLY_VIABILITY_DATING_V1
* **display_name:** OB Early Pregnancy (Viability & Dating)
* **modality:** USG

### Block instances used

* Early pregnancy ×1
* Adnexal mass ×1
* Free fluid ×1

### Fields included (by key) — unchanged

*(Same as v1.0.)*

### Normal narrative (unchanged)

1. “Early pregnancy ultrasound is performed with satisfactory assessment.”
2. “A single intrauterine gestational sac is seen.”
3. “A yolk sac and fetal pole are seen with cardiac activity.”
4. “Crown-rump length corresponds to approximately {ep_ga_weeks_days}.”
5. “No adnexal mass is seen.”
6. “No free fluid is seen.”

### Abnormal narrative rules (ordered)

* rule_id: EP_TECH_OK
  Trigger: adnx_image_quality!=limited AND ep_image_quality!=limited AND ff_image_quality!=limited
  Sentence: “Assessment is satisfactory.”
  Priority: 110
* rule_id: EP_TECH_LIMITED
  Trigger: adnx_image_quality=limited OR ep_image_quality=limited OR ff_image_quality=limited
  Sentence: “Assessment is limited due to suboptimal acoustic window.”
  Priority: 120
* rule_id: EP_NO_IUP
  Trigger: ep_ius_seen=false
  Sentence: “No definite intrauterine gestational sac is seen.”
  Priority: 95
* rule_id: EP_NO_CARDIAC_ACTIVITY
  Trigger: ep_fetal_pole_seen=true AND ep_cardiac_activity_present=false
  Sentence: “A fetal pole is seen without demonstrable cardiac activity.”
  Priority: 92
* rule_id: EP_SCH
  Trigger: ep_sch_present=true
  Sentence: “A subchorionic hemorrhage is present.”
  Priority: 85
* rule_id: EP_ADNX_MASS
  Trigger: adnx_mass_present=true
  Sentence: “An adnexal mass is present.”
  Priority: 80
* rule_id: EP_FF_MOD_LARGE
  Trigger: ff_present=true AND (ff_amount=moderate OR ff_amount=large)
  Sentence: “Moderate to large free fluid is present.”
  Priority: 78

### Impression rules (updated wording consistency)

* **Goes to Impression:** viable IUP (if IUP + cardiac activity), suspected non-viable pattern (fetal pole without cardiac activity), pregnancy of unknown location (if no IUP), subchorionic hemorrhage, adnexal mass, significant free fluid
* **Stays narrative-only:** trace free fluid

### Template constraints

* None beyond global placeholder resolution policy.

---

## M) OB Growth scan

### Template header

* **template_code:** OB_GROWTH_SCAN_V1
* **display_name:** OB Growth Scan
* **modality:** USG

### Block instances used

* Fetal biometry ×1
* Placenta/AF/cervix ×1

### Fields included (by key) — unchanged

*(Same as v1.0.)*

### Normal narrative (unchanged)

1. “Obstetric ultrasound is performed with satisfactory assessment.”
2. “Fetal presentation is {fb_presentation}.”
3. “Fetal biometry corresponds to approximately {fb_ga_weeks_days}.”
4. “Estimated fetal weight appears appropriate for gestational age.”
5. “The placenta is {pl_location} with no evidence of previa.”
6. “Amniotic fluid appears adequate.”
7. “Cervical length is within normal limits where assessed.”

### Abnormal narrative rules (updated; threshold references standardized)

* rule_id: OBGS_TECH_OK
  Trigger: fb_image_quality!=limited AND pl_image_quality!=limited
  Sentence: “Assessment is satisfactory.”
  Priority: 110
* rule_id: OBGS_TECH_LIMITED
  Trigger: fb_image_quality=limited OR pl_image_quality=limited
  Sentence: “Assessment is limited due to suboptimal acoustic window.”
  Priority: 120
* rule_id: OBGS_FGR_SUSPECTED
  Trigger: fb_growth_percentile < 10
  Sentence: “Fetal growth appears below the expected range for gestational age.”
  Priority: 90
* rule_id: OBGS_LGA_SUSPECTED
  Trigger: fb_growth_percentile > 90
  Sentence: “Fetal growth appears above the expected range for gestational age.”
  Priority: 88
* rule_id: OBGS_LOW_LYING_PREVIA
  Trigger: pl_location=low_lying OR pl_previa_present=true
  Sentence: “The placenta is low-lying or previa is present.”
  Priority: 92
* rule_id: OBGS_OLIGO
  Trigger: (pl_afi_cm < 5) OR (pl_sdp_cm < 2) OR (pl_oligohydramnios_present=true)
  Sentence: “Oligohydramnios is present.”
  Priority: 91
* rule_id: OBGS_POLY
  Trigger: (pl_afi_cm > 24) OR (pl_sdp_cm > 8) OR (pl_polyhydramnios_present=true)
  Sentence: “Polyhydramnios is present.”
  Priority: 90
* rule_id: OBGS_SHORT_CERVIX
  Trigger: (pl_cervical_length_mm < CERVIX_MM) OR (pl_funneling_present=true)
  Sentence: “A short cervix and/or funneling is present.”
  Priority: 89

### Impression rules (updated)

* **Goes to Impression:** suspected FGR/LGA, low-lying placenta/previa, oligohydramnios/polyhydramnios, short cervix, retroplacental hematoma
* **Stays narrative-only:** placental grade unless clinically emphasized

### Template constraints (standardized)

* References **CERVIX_MM=25** for short cervix.
* Other AF thresholds are template-specific as written above (unchanged).

---

## N) OB Anatomy screening (basic checklist)

### Template header

* **template_code:** OB_ANATOMY_SCREEN_BASIC_V1
* **display_name:** OB Anatomy Screening (Basic)
* **modality:** USG

### Block instances used

* Fetal biometry ×1
* Placenta/AF/cervix ×1
* Fetal anatomy screening ×1

### Fields included (by key) — unchanged

*(Same as v1.0.)*

### Normal narrative (unchanged)

1. “Basic obstetric anatomy screening is performed with satisfactory assessment.”
2. “Fetal presentation is {fb_presentation}.”
3. “Fetal biometry corresponds to approximately {fb_ga_weeks_days}.”
4. “The placenta is {pl_location} with no evidence of previa.”
5. “Amniotic fluid appears adequate.”
6. “Basic anatomy checklist structures are visualized as listed with no abnormality detected on this screening assessment.”

### Abnormal narrative rules (updated; ordered; no contradictions)

* rule_id: OBAS_TECH_OK
  Trigger: fa_image_quality!=limited AND fb_image_quality!=limited AND pl_image_quality!=limited
  Sentence: “Assessment is satisfactory.”
  Priority: 110
* rule_id: OBAS_TECH_LIMITED
  Trigger: fa_image_quality=limited OR fb_image_quality=limited OR pl_image_quality=limited
  Sentence: “Assessment is limited due to suboptimal acoustic window.”
  Priority: 120
* rule_id: OBAS_ABD_WALL_DEFECT
  Trigger: fa_abdominal_wall_intact=no
  Sentence: “An anterior abdominal wall defect is suspected.”
  Priority: 95
* rule_id: OBAS_2VC_SUSPECTED
  Trigger: fa_cord_vessels=two_vessel_suspected
  Sentence: “Two-vessel cord is suspected.”
  Priority: 90
* rule_id: OBAS_REQUIRED_NOT_VISUALIZED
  Trigger: fa_skull_brain=not_seen OR fa_spine=not_seen OR fa_four_chamber_heart=not_seen OR fa_stomach=not_seen OR fa_bladder=not_seen
  Sentence: “A required structure is not visualized on this screening assessment.”
  Priority: 85
* rule_id: OBAS_LOW_LYING_PREVIA
  Trigger: pl_location=low_lying OR pl_previa_present=true
  Sentence: “The placenta is low-lying or previa is present.”
  Priority: 92

### Impression rules (unchanged intent)

* **Goes to Impression:** suspected anomaly, limited anatomy assessment, placenta previa/low-lying, oligohydramnios/polyhydramnios (if present in fields via pl_ flags)
* **Stays narrative-only:** isolated “not seen” without suspected abnormality unless future policy escalates

### Template constraints

* Screening scope is explicit; no added scoring.

---

## O) Carotid Doppler (right+left)

### Template header

* **template_code:** DOP_CAROTID_RL_V1
* **display_name:** Carotid Doppler (right and left)
* **modality:** USG

### Block instances used

* Carotid Doppler ×2 (Right, Left)

### Fields included (by key) — unchanged

*(Same as v1.0.)*

### Normal narrative (unchanged)

1. “right and left carotid Doppler ultrasound is performed with satisfactory assessment.”
2. “No hemodynamically significant stenosis is seen in the right carotid system.”
3. “No hemodynamically significant stenosis is seen in the left carotid system.”
4. “Vertebral artery flow is antegrade where assessed.”
5. “No significant limitation is noted.”
6. “Clinical correlation is advised.”

### Abnormal narrative rules (updated; side/right and left; ordered; no “side-specific”)

* rule_id: CAR_TECH_OK
  Trigger: car_l_image_quality!=limited AND car_r_image_quality!=limited
  Sentence: “Assessment is satisfactory.”
  Priority: 110
* rule_id: CAR_TECH_LIMITED
  Trigger: car_l_image_quality=limited OR car_r_image_quality=limited
  Sentence: “Assessment is limited due to suboptimal acoustic window.”
  Priority: 120

* rule_id: CAR_PLAQUE_PRESENT_R
  Trigger: car_r_plaque_present=true
  Sentence: “Atherosclerotic plaque is present on the right.”
  Priority: 70
* rule_id: CAR_PLAQUE_PRESENT_L
  Trigger: car_l_plaque_present=true
  Sentence: “Atherosclerotic plaque is present on the left.”
  Priority: 70

* rule_id: CAR_HEMODYN_SIG_STENOSIS_R
  Trigger: (car_r_stenosis_category in {stenosis_50_69, ge_70, near_occlusion})
  Sentence: “Hemodynamically significant right ICA stenosis is present ({car_r_stenosis_category}).”
  Priority: 95
* rule_id: CAR_HEMODYN_SIG_STENOSIS_L
  Trigger: (car_l_stenosis_category in {stenosis_50_69, ge_70, near_occlusion})
  Sentence: “Hemodynamically significant left ICA stenosis is present ({car_l_stenosis_category}).”
  Priority: 95

* rule_id: CAR_VERTEBRAL_RETROGRADE_R
  Trigger: car_r_vertebral_flow=retrograde
  Sentence: “Retrograde right vertebral artery flow is present.”
  Priority: 90
* rule_id: CAR_VERTEBRAL_RETROGRADE_L
  Trigger: car_l_vertebral_flow=retrograde
  Sentence: “Retrograde left vertebral artery flow is present.”
  Priority: 90

### Impression rules (side-aware)

* **Goes to Impression:** ICA stenosis category ≥50% (Right/Left/right and left with categories), near-occlusion (side), retrograde vertebral flow (side/right and left)
* **Stays narrative-only:** non-stenotic plaque unless policy later highlights it

### Template constraints

* Stenosis is reported via explicit category fields (no new thresholding added).

---

## P) Lower limb venous Doppler (single side)

### Template header

* **template_code:** DOP_DVT_SINGLE_SIDE_V1
* **display_name:** Lower Limb Venous Doppler (Single Side)
* **modality:** USG

### Block instances used

* Lower limb venous Doppler (DVT) ×1

### Fields included (by key) — unchanged

*(Same as v1.0.)*

### Normal narrative (unchanged)

1. “Lower limb venous Doppler ultrasound is performed with satisfactory assessment.”
2. “Deep veins of the {dvt_side} lower limb are compressible.”
3. “No intraluminal thrombus is seen in the assessed segments.”
4. “No evidence of DVT is identified.”
5. “Calf vein assessment is recorded as {dvt_calf_veins_assessed}.”
6. “No significant limitation is noted.”

### Abnormal narrative rules (updated; explicit ordering per fix C-4)

* rule_id: DVT_TECH_OK
  Trigger: dvt_image_quality!=limited
  Sentence: “Assessment is satisfactory.”
  Priority: 110
* rule_id: DVT_TECH_LIMITED
  Trigger: dvt_image_quality=limited
  Sentence: “Assessment is limited due to suboptimal acoustic window.”
  Priority: 120

* rule_id: DVT_PRESENT
  Trigger: dvt_thrombus_present=true OR dvt_cfv_compressible=false OR dvt_fv_compressible=false OR dvt_popliteal_compressible=false
  Sentence: “Findings are consistent with DVT involving the {dvt_thrombus_location} deep veins.”
  Priority: 95

* rule_id: DVT_CHRONICITY
  Trigger: dvt_thrombus_chronicity=chronic
  Sentence: “Features suggest chronic thrombosis.”
  Priority: 90
  suppress_if: DVT_PRESENT not triggered

* rule_id: DVT_CALF_LIMITED
  Trigger: dvt_calf_veins_assessed=limited OR dvt_calf_veins_assessed=not_assessed
  Sentence: “Calf vein assessment is limited.”
  Priority: 85

### Impression rules (ordered, consistent)

* **Goes to Impression:** DVT present (with side implicit via template, location), chronic thrombosis (if DVT present), limited calf assessment (if limited)
* **Stays narrative-only:** minor technical comments beyond the standardized limitation sentence

### Template constraints

* Single-side template; no right and left logic added in v1.1.

---




---
## Change Log (v1.0 → v1.1)

### Global fixes
- Enforced deterministic output: one sentence per triggered rule; multiple rules may trigger.
- Removed side-ambiguous wording: all paired-structure findings now emit explicit right/left statements.
- Standardized Technique/Limitations across all templates using TECH_OK and TECH_LIMITED (and TECH_LIMITED_WITH_REASON when limitation reason keys exist).
- Technique limitation triggers on relevant *_image_quality=limited and on required *_visualized=false keys where present.
- Updated impression guidance to be side-aware and measurement-aware.

### Template-specific fixes (high impact)
- Gallbladder: tightened acute cholecystitis suggestion logic to require two supportive signs; single supportive signs produce softer statements.
- Pancreas: pancreatitis wording softened to correlation with clinical context and laboratory parameters.
- Paired organs (kidneys/ureters/pleural effusions/ovaries/scrotum/carotids/DVT): standardized side-aware output using either (a) combined branching rules where defined, or (b) separate right/left rule blocks where defined.

### Key additions
- No new field keys were introduced. Existing prefixes and instance-tag patterns were preserved.

### Identifier note
- The scrotum and carotid template identifiers were updated to remove side-ambiguous wording in the identifier itself and replaced with “RL” variants. If your database currently stores the old identifiers, treat the RL form as documentation-only, unless you explicitly migrate identifiers in code and data.
