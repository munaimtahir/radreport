## Global conventions (Phase-1b Normalized Block Library v1.0)

* **Key prefixing rule**
  Every structured field key is globally unique by prefixing with the block identifier (e.g., `liv_...`, `gb_...`). No unprefixed keys are used.

* **Units convention**

  * Length: **mm** unless specifically stated **cm** (used for organ length where common).
  * Volume: **mL**
  * Velocity: **cm/s**
  * Heart rate: **bpm**
  * Percentile: **%**

* **Threshold expression standard**
  Any trigger that uses “enlarged / dilated / thickened / short / significant / high / low” must reference an explicit **Threshold policy** under the relevant field(s). Triggers then become deterministic comparisons (e.g., `gb_gb_wall_thickness_mm > 3`).

* **Impression inclusion rule**
  **Only high-value abnormalities** appear in Impression (stones, obstruction, masses/suspicious lesions, significant fluid, thrombus, placenta previa/oligo-polyhydramnios, suspected torsion, etc.). Minor descriptive items (e.g., mild heterogeneity without clinical implication) can remain narrative-only unless flagged as clinically important by the template.

---

## 🔹 BLOCK: Liver

**Clinical purpose**
Used to document hepatic size, parenchymal appearance, focal lesions, and intrahepatic biliary dilatation in routine ultrasound.

**Used in exams**

* Abdomen
* RUQ ultrasound
* Whole abdomen screening
* KUB (extended upper abdomen)

**Structured fields**

* Organ visualized (liv_visualized)

  * Type: boolean
  * Required: Yes

* Image quality (liv_image_quality)

  * Type: enum
  * Required: Yes
  * Enum values: adequate, limited

* Limitation reason (liv_limitation_reason)

  * Type: short text
  * Required: No

* Liver craniocaudal length (liv_size_cm)

  * Type: numeric (cm)
  * Required: No
  * Notes: Midclavicular line measurement
  * Threshold policy: hepatomegaly if liv_size_cm > 15.0 cm (adult default)

* Liver contour (liv_contour)

  * Type: enum
  * Required: No
  * Enum values: smooth, mildly_irregular, nodular

* Parenchymal echotexture (liv_echotexture)

  * Type: enum
  * Required: Yes
  * Enum values: homogeneous, coarse

* Echogenicity (liv_echogenicity)

  * Type: enum
  * Required: Yes
  * Enum values: normal, increased, decreased

* Focal hepatic lesion present (liv_focal_lesion_present)

  * Type: boolean
  * Required: Yes

* Intrahepatic biliary dilatation (liv_ihbd_present)

  * Type: boolean
  * Required: Yes

* Portal vein diameter (liv_portal_vein_diameter_mm)

  * Type: numeric (mm)
  * Required: No
  * Threshold policy: portal vein dilated if liv_portal_vein_diameter_mm > 13 mm

**Normal narrative output**

* “The liver is normal in size with homogeneous echotexture and normal echogenicity. No focal hepatic lesion is seen.”
* “No intrahepatic biliary dilatation is noted.”

**Abnormal triggers → narrative**

* Trigger: liv_image_quality = limited
  Narrative sentence:
  “Assessment is limited due to suboptimal acoustic window.”
* Trigger: liv_size_cm > 15.0
  Narrative sentence:
  “The liver is enlarged with preserved echotexture.”
* Trigger: liv_echogenicity = increased
  Narrative sentence:
  “The liver shows increased echogenicity consistent with fatty change.”
* Trigger: liv_echotexture = coarse
  Narrative sentence:
  “Coarse hepatic echotexture is noted, suggestive of chronic parenchymal disease.”
* Trigger: liv_contour = nodular
  Narrative sentence:
  “Nodular liver contour is noted, in keeping with cirrhotic morphology.”
* Trigger: liv_focal_lesion_present = true
  Narrative sentence:
  “Focal hepatic lesion(s) are identified as described.”
* Trigger: liv_ihbd_present = true
  Narrative sentence:
  “Intrahepatic biliary dilatation is present.”
* Trigger: liv_portal_vein_diameter_mm > 13
  Narrative sentence:
  “The portal vein is dilated.”

**Impression contribution**

* Hepatomegaly
* Hepatic steatosis
* Features suggestive of chronic liver disease / cirrhosis
* Hepatic focal lesion(s)
* Intrahepatic biliary dilatation
* Dilated portal vein (suggestive of portal hypertension in context)

**Optional / edge notes (if any)**

* If liv_visualized = false: “Liver not adequately visualized.”

---

## 🔹 BLOCK: Gall bladder & CBD

**Clinical purpose**
Used to document gallbladder status, stones/sludge, cholecystitis features, and CBD caliber in biliary assessment.

**Used in exams**

* Abdomen
* RUQ ultrasound
* Whole abdomen screening
* KUB (extended upper abdomen)

**Structured fields**

* Organ visualized (gb_visualized)

  * Type: boolean
  * Required: Yes

* Image quality (gb_image_quality)

  * Type: enum
  * Required: Yes
  * Enum values: adequate, limited

* Limitation reason (gb_limitation_reason)

  * Type: short text
  * Required: No

* Gallbladder status (gb_status)

  * Type: enum
  * Required: Yes
  * Enum values: distended_normal, contracted, post_cholecystectomy

* Gallstones present (gb_stones_present)

  * Type: boolean
  * Required: Yes

* Sludge present (gb_sludge_present)

  * Type: boolean
  * Required: No

* Wall thickness (gb_wall_thickness_mm)

  * Type: numeric (mm)
  * Required: No
  * Threshold policy: wall thickening if gb_wall_thickness_mm > 3 mm

* Sonographic Murphy sign (gb_murphy_sign_positive)

  * Type: boolean
  * Required: No

* Pericholecystic fluid (gb_pericholecystic_fluid_present)

  * Type: boolean
  * Required: No

* CBD diameter (gb_cbd_diameter_mm)

  * Type: numeric (mm)
  * Required: No
  * Threshold policy: CBD dilated if gb_cbd_diameter_mm > 6 mm (simple default)

* CBD stone suspected (gb_cbd_stone_suspected)

  * Type: boolean
  * Required: No

**Normal narrative output**

* “The gallbladder is normal in outline with no calculus or sludge. Wall thickness is within normal limits.”
* “The common bile duct is not dilated.”

**Abnormal triggers → narrative**

* Trigger: gb_image_quality = limited
  Narrative sentence:
  “Assessment is limited due to suboptimal acoustic window.”
* Trigger: gb_status = contracted
  Narrative sentence:
  “The gallbladder is contracted.”
* Trigger: gb_status = post_cholecystectomy
  Narrative sentence:
  “Status post cholecystectomy.”
* Trigger: gb_stones_present = true
  Narrative sentence:
  “Cholelithiasis is present.”
* Trigger: gb_sludge_present = true
  Narrative sentence:
  “Dependent biliary sludge is noted.”
* Trigger: (gb_wall_thickness_mm > 3) OR gb_murphy_sign_positive = true OR gb_pericholecystic_fluid_present = true
  Narrative sentence:
  “Findings are suggestive of acute cholecystitis.”
* Trigger: gb_cbd_diameter_mm > 6
  Narrative sentence:
  “The common bile duct is dilated.”
* Trigger: gb_cbd_stone_suspected = true
  Narrative sentence:
  “Choledocholithiasis is suspected.”

**Impression contribution**

* Cholelithiasis
* Features suggestive of acute cholecystitis
* Dilated CBD
* Suspected choledocholithiasis

**Optional / edge notes (if any)**

* Non-fasting state can limit GB distension interpretation (use gb_limitation_reason).

---

## 🔹 BLOCK: Pancreas

**Clinical purpose**
Used to document pancreas appearance, duct caliber, and supportive findings for pancreatitis or focal lesions.

**Used in exams**

* Abdomen
* RUQ ultrasound (extended)
* Whole abdomen screening

**Structured fields**

* Organ visualized (panc_visualized)

  * Type: boolean
  * Required: Yes

* Image quality (panc_image_quality)

  * Type: enum
  * Required: Yes
  * Enum values: adequate, limited

* Limitation reason (panc_limitation_reason)

  * Type: short text
  * Required: No

* Visualized extent (panc_visualized_extent)

  * Type: enum
  * Required: Yes
  * Enum values: complete, partial

* Pancreas size (panc_size)

  * Type: enum
  * Required: No
  * Enum values: normal, bulky

* Echotexture (panc_echotexture)

  * Type: enum
  * Required: Yes
  * Enum values: normal, heterogeneous

* Main pancreatic duct diameter (panc_mpd_diameter_mm)

  * Type: numeric (mm)
  * Required: No
  * Threshold policy: MPD dilated if panc_mpd_diameter_mm > 3 mm (adult default)

* Peripancreatic fluid (panc_peripancreatic_fluid_present)

  * Type: boolean
  * Required: No

* Focal lesion present (panc_focal_lesion_present)

  * Type: boolean
  * Required: No

**Normal narrative output**

* “The pancreas is unremarkable in the visualized portions with no focal lesion.”
* “The pancreatic duct is not dilated.”

**Abnormal triggers → narrative**

* Trigger: panc_image_quality = limited
  Narrative sentence:
  “Assessment is limited due to suboptimal acoustic window.”
* Trigger: panc_visualized_extent = partial
  Narrative sentence:
  “The pancreas is partially visualized.”
* Trigger: panc_size = bulky AND panc_echotexture = heterogeneous
  Narrative sentence:
  “A bulky heterogeneous pancreas is noted, which may be seen in pancreatitis.”
* Trigger: panc_mpd_diameter_mm > 3
  Narrative sentence:
  “The pancreatic duct appears dilated.”
* Trigger: panc_peripancreatic_fluid_present = true
  Narrative sentence:
  “Peripancreatic fluid is present.”
* Trigger: panc_focal_lesion_present = true
  Narrative sentence:
  “A pancreatic focal lesion is noted as described.”

**Impression contribution**

* Features may suggest pancreatitis (correlate clinically/biochemically)
* Dilated pancreatic duct
* Pancreatic lesion (further characterization advised)

**Optional / edge notes (if any)**

* None.

---

## 🔹 BLOCK: Spleen

**Clinical purpose**
Used to document splenic size, echotexture, and focal lesions.

**Used in exams**

* Abdomen
* Whole abdomen screening
* KUB (extended upper abdomen)

**Structured fields**

* Organ visualized (spl_visualized)

  * Type: boolean
  * Required: Yes

* Image quality (spl_image_quality)

  * Type: enum
  * Required: Yes
  * Enum values: adequate, limited

* Limitation reason (spl_limitation_reason)

  * Type: short text
  * Required: No

* Splenic length (spl_length_cm)

  * Type: numeric (cm)
  * Required: No
  * Threshold policy: splenomegaly if spl_length_cm > 12.0 cm (adult default)

* Echotexture (spl_echotexture)

  * Type: enum
  * Required: Yes
  * Enum values: normal, heterogeneous

* Focal lesion present (spl_focal_lesion_present)

  * Type: boolean
  * Required: Yes

**Normal narrative output**

* “The spleen is normal in size and echotexture with no focal lesion.”

**Abnormal triggers → narrative**

* Trigger: spl_image_quality = limited
  Narrative sentence:
  “Assessment is limited due to suboptimal acoustic window.”
* Trigger: spl_length_cm > 12.0
  Narrative sentence:
  “Splenomegaly is present.”
* Trigger: spl_echotexture = heterogeneous
  Narrative sentence:
  “Heterogeneous splenic echotexture is noted.”
* Trigger: spl_focal_lesion_present = true
  Narrative sentence:
  “Focal splenic lesion(s) are noted.”

**Impression contribution**

* Splenomegaly
* Splenic focal lesion(s)

**Optional / edge notes (if any)**

* None.

---

## 🔹 BLOCK: Abdominal aorta & IVC

**Clinical purpose**
Used to document abdominal aorta caliber (aneurysm screening) and IVC thrombus suspicion.

**Used in exams**

* Abdomen
* Whole abdomen screening
* KUB (extended abdomen)

**Structured fields**

* Organ visualized (aiv_visualized)

  * Type: boolean
  * Required: Yes
  * Notes: Combined visibility for this block (aorta/IVC region)

* Image quality (aiv_image_quality)

  * Type: enum
  * Required: Yes
  * Enum values: adequate, limited

* Limitation reason (aiv_limitation_reason)

  * Type: short text
  * Required: No

* Max aortic diameter (aiv_aorta_max_diameter_mm)

  * Type: numeric (mm)
  * Required: No
  * Threshold policy: AAA if aiv_aorta_max_diameter_mm ≥ 30 mm

* Atherosclerotic plaque (aiv_aorta_plaque_present)

  * Type: boolean
  * Required: No

* IVC thrombus suspected (aiv_ivc_thrombus_suspected)

  * Type: boolean
  * Required: No

**Normal narrative output**

* “The abdominal aorta is normal in caliber with no aneurysm.”
* “No IVC thrombus is suspected.”

**Abnormal triggers → narrative**

* Trigger: aiv_image_quality = limited
  Narrative sentence:
  “Assessment is limited due to suboptimal acoustic window.”
* Trigger: aiv_aorta_max_diameter_mm ≥ 30
  Narrative sentence:
  “An abdominal aortic aneurysm is noted.”
* Trigger: aiv_aorta_plaque_present = true
  Narrative sentence:
  “Atherosclerotic changes are noted in the abdominal aorta.”
* Trigger: aiv_ivc_thrombus_suspected = true
  Narrative sentence:
  “IVC thrombus is suspected.”

**Impression contribution**

* Abdominal aortic aneurysm
* Suspected IVC thrombosis

**Optional / edge notes (if any)**

* This block uses prefix **aiv_** to avoid collisions; it can be mapped internally as “Aorta & IVC.”

---

## 🔹 BLOCK: Portal vein & hepatic venous Doppler

**Clinical purpose**
Used to document portal vein caliber/flow direction and hepatic venous waveform for portal hypertension and liver disease assessment.

**Used in exams**

* Abdomen
* Liver Doppler
* Portal hypertension assessment

**Structured fields**

* Organ visualized (pvd_visualized)

  * Type: boolean
  * Required: Yes

* Image quality (pvd_image_quality)

  * Type: enum
  * Required: Yes
  * Enum values: adequate, limited

* Limitation reason (pvd_limitation_reason)

  * Type: short text
  * Required: No

* Portal vein diameter (pvd_pv_diameter_mm)

  * Type: numeric (mm)
  * Required: No
  * Threshold policy: portal vein dilated if pvd_pv_diameter_mm > 13 mm

* Portal vein flow direction (pvd_pv_flow_direction)

  * Type: enum
  * Required: No
  * Enum values: hepatopetal, hepatofugal, bidirectional, not_assessed

* Portal vein velocity (pvd_pv_velocity_cm_s)

  * Type: numeric (cm/s)
  * Required: No

* Portal vein thrombosis suspected (pvd_pv_thrombosis_suspected)

  * Type: boolean
  * Required: No

* Hepatic vein waveform (pvd_hepatic_vein_waveform)

  * Type: enum
  * Required: No
  * Enum values: triphasic, biphasic, monophasic, not_assessed

* Collaterals suspected (pvd_collaterals_suspected)

  * Type: boolean
  * Required: No

**Normal narrative output**

* “Portal vein is normal in caliber with hepatopetal flow.”
* “Hepatic venous waveform appears triphasic.”

**Abnormal triggers → narrative**

* Trigger: pvd_image_quality = limited
  Narrative sentence:
  “Doppler assessment is limited.”
* Trigger: pvd_pv_diameter_mm > 13
  Narrative sentence:
  “The portal vein is dilated.”
* Trigger: pvd_pv_flow_direction = hepatofugal
  Narrative sentence:
  “Hepatofugal portal venous flow is noted.”
* Trigger: pvd_pv_thrombosis_suspected = true
  Narrative sentence:
  “Portal vein thrombosis is suspected.”
* Trigger: pvd_hepatic_vein_waveform = monophasic
  Narrative sentence:
  “Hepatic venous waveform appears dampened/monophasic.”
* Trigger: pvd_collaterals_suspected = true
  Narrative sentence:
  “Portosystemic collaterals are suspected.”

**Impression contribution**

* Findings suggestive of portal hypertension
* Suspected portal vein thrombosis

**Optional / edge notes (if any)**

* This is a Doppler block; do not use “not assessed” values in Impression.

---

## 🔹 BLOCK: Kidney (paired, instance per side)

**Clinical purpose**
Used to document renal size, parenchymal appearance, hydronephrosis, stones, cysts, and masses for a single kidney instance.

**Used in exams**

* Abdomen
* KUB
* Pelvis (urinary tract)
* Whole abdomen screening

**Structured fields**

* Organ visualized (kid_visualized)

  * Type: boolean
  * Required: Yes

* Image quality (kid_image_quality)

  * Type: enum
  * Required: Yes
  * Enum values: adequate, limited

* Limitation reason (kid_limitation_reason)

  * Type: short text
  * Required: No

* Side (kid_side)

  * Type: enum
  * Required: Yes
  * Enum values: right, left

* Renal length (kid_length_cm)

  * Type: numeric (cm)
  * Required: No
  * Threshold policy: small kidney if kid_length_cm < 9.0 cm (adult default)

* Cortical echogenicity (kid_cortical_echogenicity)

  * Type: enum
  * Required: Yes
  * Enum values: normal, increased

* Corticomedullary differentiation (kid_cmd)

  * Type: enum
  * Required: Yes
  * Enum values: preserved, reduced

* Hydronephrosis (kid_hydronephrosis_grade)

  * Type: enum
  * Required: Yes
  * Enum values: none, mild, moderate, severe

* Renal calculus present (kid_calculus_present)

  * Type: boolean
  * Required: Yes

* Largest calculus size (kid_largest_calculus_mm)

  * Type: numeric (mm)
  * Required: No

* Simple cyst present (kid_simple_cyst_present)

  * Type: boolean
  * Required: Yes

* Largest cyst size (kid_largest_cyst_mm)

  * Type: numeric (mm)
  * Required: No

* Solid mass suspected (kid_mass_suspected)

  * Type: boolean
  * Required: No

* Perinephric collection (kid_perinephric_collection_present)

  * Type: boolean
  * Required: No

**Normal narrative output**

* “The {kid_side} kidney is normal in size with preserved corticomedullary differentiation. No hydronephrosis or calculus is seen.”

**Abnormal triggers → narrative**

* Trigger: kid_image_quality = limited
  Narrative sentence:
  “Assessment is limited due to suboptimal acoustic window.”
* Trigger: kid_length_cm < 9.0
  Narrative sentence:
  “The {kid_side} kidney is small in size.”
* Trigger: kid_hydronephrosis_grade != none
  Narrative sentence:
  “{Kid_side} hydronephrosis ({kid_hydronephrosis_grade}) is present.”
* Trigger: kid_calculus_present = true
  Narrative sentence:
  “A {kid_side} renal calculus is present.”
* Trigger: kid_cortical_echogenicity = increased AND kid_cmd = reduced
  Narrative sentence:
  “Increased cortical echogenicity with reduced corticomedullary differentiation is noted, suggestive of medical renal disease.”
* Trigger: kid_simple_cyst_present = true
  Narrative sentence:
  “Simple renal cyst(s) are noted.”
* Trigger: kid_mass_suspected = true
  Narrative sentence:
  “A renal mass lesion is suspected.”
* Trigger: kid_perinephric_collection_present = true
  Narrative sentence:
  “Perinephric collection is noted.”

**Impression contribution**

* {Side} hydronephrosis (grade)
* {Side} renal calculus
* Sonographic features suggest medical renal disease
* Renal mass suspected
* Perinephric collection
* Small {Side} kidney (if clinically relevant)

**Optional / edge notes (if any)**

* Templates will include two kidney instances; this block stays side-safe and collision-free.

---

## 🔹 BLOCK: Ureter / UVJ (paired, instance per side)

**Clinical purpose**
Used to document hydroureter, distal ureter/UVJ stone suspicion, and obstruction support for one side.

**Used in exams**

* KUB
* Abdomen (renal colic)
* Pelvis (distal ureter/UVJ)

**Structured fields**

* Organ visualized (ure_visualized)

  * Type: boolean
  * Required: Yes

* Image quality (ure_image_quality)

  * Type: enum
  * Required: Yes
  * Enum values: adequate, limited

* Limitation reason (ure_limitation_reason)

  * Type: short text
  * Required: No

* Side (ure_side)

  * Type: enum
  * Required: Yes
  * Enum values: right, left

* Segment assessed (ure_segment_assessed)

  * Type: enum
  * Required: Yes
  * Enum values: proximal, mid, distal_uvj, limited

* Hydroureter present (ure_hydroureter_present)

  * Type: boolean
  * Required: Yes

* Ureteric stone suspected (ure_stone_suspected)

  * Type: boolean
  * Required: No

* Stone location (ure_stone_location)

  * Type: enum
  * Required: No
  * Enum values: proximal, mid, distal_uvj

* Stone size (ure_stone_size_mm)

  * Type: numeric (mm)
  * Required: No

* Ureteric jet seen (ure_jet_seen)

  * Type: boolean
  * Required: No

**Normal narrative output**

* “No hydroureter is seen and no ureteric calculus is identified in the assessed segments.”

**Abnormal triggers → narrative**

* Trigger: ure_image_quality = limited
  Narrative sentence:
  “Assessment is limited due to suboptimal acoustic window.”
* Trigger: ure_hydroureter_present = true
  Narrative sentence:
  “{Ure_side} hydroureter is present.”
* Trigger: ure_stone_suspected = true
  Narrative sentence:
  “A {ure_side} ureteric calculus is suspected at the {ure_stone_location} ureter.”
* Trigger: ure_jet_seen = false (when assessed)
  Narrative sentence:
  “Ureteric jet is not seen on the {ure_side}.”

**Impression contribution**

* {Side} hydroureter
* Suspected {Side} ureteric calculus (location)
* Obstructive uropathy pattern (when paired with hydronephrosis)

**Optional / edge notes (if any)**

* None.

---

## 🔹 BLOCK: Urinary bladder

**Clinical purpose**
Used to document bladder distension, wall features, intraluminal pathology, debris, and post-void residual.

**Used in exams**

* KUB
* Pelvis
* Abdomen

**Structured fields**

* Organ visualized (bl_visualized)

  * Type: boolean
  * Required: Yes

* Image quality (bl_image_quality)

  * Type: enum
  * Required: Yes
  * Enum values: adequate, limited

* Limitation reason (bl_limitation_reason)

  * Type: short text
  * Required: No

* Adequately distended (bl_distended)

  * Type: boolean
  * Required: Yes

* Wall thickness (bl_wall_thickness_mm)

  * Type: numeric (mm)
  * Required: No
  * Threshold policy: wall thickening if bl_wall_thickness_mm > 3 mm when adequately distended

* Trabeculation/irregularity (bl_trabeculation_present)

  * Type: boolean
  * Required: No

* Intraluminal stone (bl_stone_present)

  * Type: boolean
  * Required: No

* Mass/polypoid lesion suspected (bl_mass_suspected)

  * Type: boolean
  * Required: No

* Debris/clot (bl_debris_present)

  * Type: boolean
  * Required: No

* Pre-void volume (bl_prevoid_volume_ml)

  * Type: numeric (mL)
  * Required: No

* Post-void residual (bl_pvr_ml)

  * Type: numeric (mL)
  * Required: No
  * Threshold policy: significant PVR if bl_pvr_ml ≥ 100 mL

**Normal narrative output**

* “The urinary bladder is well distended with normal wall thickness. No intraluminal calculus or mass is seen.”

**Abnormal triggers → narrative**

* Trigger: bl_image_quality = limited
  Narrative sentence:
  “Assessment is limited due to suboptimal acoustic window.”
* Trigger: bl_distended = false
  Narrative sentence:
  “The urinary bladder is underdistended; wall assessment is limited.”
* Trigger: bl_wall_thickness_mm > 3 AND bl_distended = true
  Narrative sentence:
  “Bladder wall thickening is noted.”
* Trigger: bl_trabeculation_present = true
  Narrative sentence:
  “Bladder wall trabeculation is noted.”
* Trigger: bl_stone_present = true
  Narrative sentence:
  “A vesical calculus is noted.”
* Trigger: bl_mass_suspected = true
  Narrative sentence:
  “A polypoid bladder lesion is suspected.”
* Trigger: bl_debris_present = true
  Narrative sentence:
  “Mobile internal echoes/debris are noted within the bladder.”
* Trigger: bl_pvr_ml ≥ 100
  Narrative sentence:
  “Significant post-void residual urine is noted.”

**Impression contribution**

* Urinary bladder stone
* Suspected urinary bladder lesion
* Significant post-void residual urine
* Bladder wall thickening/trabeculation (if clinically relevant)

**Optional / edge notes (if any)**

* None.

---

## 🔹 BLOCK: Prostate & seminal vesicles (paired structure, single instance)

**Clinical purpose**
Used to document prostate volume/enlargement and seminal vesicle appearance in male pelvis.

**Used in exams**

* Pelvis (male)
* KUB (LUTS/retention evaluation)

**Structured fields**

* Organ visualized (pros_visualized)

  * Type: boolean
  * Required: Yes

* Image quality (pros_image_quality)

  * Type: enum
  * Required: Yes
  * Enum values: adequate, limited

* Limitation reason (pros_limitation_reason)

  * Type: short text
  * Required: No

* Prostate volume (pros_volume_ml)

  * Type: numeric (mL)
  * Required: No
  * Threshold policy: prostatomegaly if pros_volume_ml > 30 mL

* Echotexture (pros_echotexture)

  * Type: enum
  * Required: No
  * Enum values: normal, heterogeneous

* Median lobe protrusion (pros_median_lobe_protrusion)

  * Type: boolean
  * Required: No

* Calcifications (pros_calcifications_present)

  * Type: boolean
  * Required: No

* Seminal vesicles (pros_seminal_vesicles)

  * Type: enum
  * Required: No
  * Enum values: normal, prominent

**Normal narrative output**

* “The prostate is normal in size and echotexture.”
* “Seminal vesicles are unremarkable.”

**Abnormal triggers → narrative**

* Trigger: pros_image_quality = limited
  Narrative sentence:
  “Assessment is limited due to suboptimal acoustic window.”
* Trigger: pros_volume_ml > 30
  Narrative sentence:
  “The prostate is enlarged.”
* Trigger: pros_median_lobe_protrusion = true
  Narrative sentence:
  “Median lobe protrusion into the bladder base is noted.”
* Trigger: pros_echotexture = heterogeneous
  Narrative sentence:
  “The prostate appears heterogeneous.”
* Trigger: pros_calcifications_present = true
  Narrative sentence:
  “Prostatic calcifications are noted.”

**Impression contribution**

* Benign prostatic enlargement (BPH pattern)
* Median lobe protrusion (optional if clinically relevant)

**Optional / edge notes (if any)**

* None.

---

## 🔹 BLOCK: Uterus & endometrium

**Clinical purpose**
Used to document uterine size/position, myometrial echotexture, fibroids, and endometrial thickness/appearance.

**Used in exams**

* Pelvis
* OB (background uterine assessment)
* Gyn ultrasound

**Structured fields**

* Organ visualized (ut_visualized)

  * Type: boolean
  * Required: Yes

* Image quality (ut_image_quality)

  * Type: enum
  * Required: Yes
  * Enum values: adequate, limited

* Limitation reason (ut_limitation_reason)

  * Type: short text
  * Required: No

* Uterine length (ut_length_cm)

  * Type: numeric (cm)
  * Required: No

* Uterine AP diameter (ut_ap_cm)

  * Type: numeric (cm)
  * Required: No

* Uterine width (ut_width_cm)

  * Type: numeric (cm)
  * Required: No

* Uterine position (ut_position)

  * Type: enum
  * Required: No
  * Enum values: anteverted, retroverted, neutral

* Myometrium echotexture (ut_myometrium_echotexture)

  * Type: enum
  * Required: Yes
  * Enum values: normal, heterogeneous

* Fibroid present (ut_fibroid_present)

  * Type: boolean
  * Required: Yes

* Endometrial thickness (ut_endometrial_thickness_mm)

  * Type: numeric (mm)
  * Required: No
  * Threshold policy: “thickened endometrium” if ut_endometrial_thickness_mm > 12 mm (premenopausal default) or > 5 mm (postmenopausal default). Use a single default in templates.

* Endometrium appearance (ut_endometrium_appearance)

  * Type: enum
  * Required: No
  * Enum values: normal, thickened, fluid, polypoid

* IUD present (ut_iud_present)

  * Type: boolean
  * Required: No

**Normal narrative output**

* “The uterus is normal in size and echotexture. The endometrium is within normal limits.”

**Abnormal triggers → narrative**

* Trigger: ut_image_quality = limited
  Narrative sentence:
  “Assessment is limited due to suboptimal acoustic window.”
* Trigger: ut_fibroid_present = true
  Narrative sentence:
  “Uterine fibroid(s) are noted.”
* Trigger: ut_myometrium_echotexture = heterogeneous
  Narrative sentence:
  “Heterogeneous myometrium is noted, which may be seen with adenomyosis in the appropriate clinical setting.”
* Trigger: ut_endometrium_appearance = thickened
  Narrative sentence:
  “The endometrium appears thickened.”
* Trigger: ut_endometrium_appearance = fluid
  Narrative sentence:
  “Fluid is noted within the endometrial cavity.”
* Trigger: ut_endometrium_appearance = polypoid
  Narrative sentence:
  “A focal polypoid endometrial lesion is suspected.”
* Trigger: ut_iud_present = true
  Narrative sentence:
  “An intrauterine contraceptive device is seen in situ.”

**Impression contribution**

* Uterine fibroid(s)
* Thickened endometrium (template should set context)
* Suspected endometrial polyp (if polypoid)

**Optional / edge notes (if any)**

* Endometrial thickness threshold must be chosen per template context (premenopausal vs postmenopausal). Keep the block neutral.

---

## 🔹 BLOCK: Ovary (paired, instance per side)

**Clinical purpose**
Used to document ovarian visualization, cysts, and adnexal mass suspicion for one ovary instance.

**Used in exams**

* Pelvis
* OB (adnexal assessment)
* Gyn ultrasound

**Structured fields**

* Organ visualized (ov_visualized)

  * Type: boolean
  * Required: Yes

* Image quality (ov_image_quality)

  * Type: enum
  * Required: Yes
  * Enum values: adequate, limited

* Limitation reason (ov_limitation_reason)

  * Type: short text
  * Required: No

* Side (ov_side)

  * Type: enum
  * Required: Yes
  * Enum values: right, left

* Ovary volume (ov_volume_ml)

  * Type: numeric (mL)
  * Required: No
  * Threshold policy: enlarged ovary if ov_volume_ml > 10 mL (adult default)

* Simple cyst present (ov_simple_cyst_present)

  * Type: boolean
  * Required: Yes

* Largest simple cyst size (ov_largest_simple_cyst_mm)

  * Type: numeric (mm)
  * Required: No

* Complex cyst suspected (ov_complex_cyst_suspected)

  * Type: boolean
  * Required: No

* Solid mass suspected (ov_solid_mass_suspected)

  * Type: boolean
  * Required: No

* PCOM pattern present (ov_pcom_pattern_present)

  * Type: boolean
  * Required: No

**Normal narrative output**

* “The {ov_side} ovary is normal in size with no adnexal mass. No significant ovarian cyst is seen.”

**Abnormal triggers → narrative**

* Trigger: ov_image_quality = limited
  Narrative sentence:
  “Assessment is limited due to suboptimal acoustic window.”
* Trigger: ov_volume_ml > 10
  Narrative sentence:
  “The {ov_side} ovary is enlarged.”
* Trigger: ov_simple_cyst_present = true
  Narrative sentence:
  “A simple ovarian cyst is noted.”
* Trigger: ov_complex_cyst_suspected = true
  Narrative sentence:
  “A complex ovarian cyst is noted.”
* Trigger: ov_solid_mass_suspected = true
  Narrative sentence:
  “An adnexal mass is suspected.”
* Trigger: ov_pcom_pattern_present = true
  Narrative sentence:
  “Polycystic ovarian morphology is noted.”

**Impression contribution**

* {Side} ovarian cyst (simple/complex if clinically significant)
* {Side} adnexal mass suspected
* Polycystic ovarian morphology (correlate clinically)

**Optional / edge notes (if any)**

* None.

---

## 🔹 BLOCK: Adnexal mass characterization

**Clinical purpose**
Used to standardize descriptors for an adnexal mass, independent of origin (ovarian/tubal/paraovarian).

**Used in exams**

* Pelvis
* OB (adnexal mass evaluation)
* Gyn ultrasound

**Structured fields**

* Organ visualized (adnx_visualized)

  * Type: boolean
  * Required: Yes

* Image quality (adnx_image_quality)

  * Type: enum
  * Required: Yes
  * Enum values: adequate, limited

* Limitation reason (adnx_limitation_reason)

  * Type: short text
  * Required: No

* Mass present (adnx_mass_present)

  * Type: boolean
  * Required: Yes

* Side (adnx_side)

  * Type: enum
  * Required: No
  * Enum values: right, left

* Max size (adnx_mass_max_mm)

  * Type: numeric (mm)
  * Required: No

* Composition (adnx_composition)

  * Type: enum
  * Required: No
  * Enum values: cystic, solid, mixed

* Septations present (adnx_septations_present)

  * Type: boolean
  * Required: No

* Solid component present (adnx_solid_component_present)

  * Type: boolean
  * Required: No

* Papillary projection present (adnx_papillary_projection_present)

  * Type: boolean
  * Required: No

* Internal echoes (adnx_internal_echoes_present)

  * Type: boolean
  * Required: No

* Vascularity (adnx_vascularity)

  * Type: enum
  * Required: No
  * Enum values: none, peripheral, internal, marked

**Normal narrative output**

* “No adnexal mass is seen.”

**Abnormal triggers → narrative**

* Trigger: adnx_image_quality = limited
  Narrative sentence:
  “Assessment is limited due to suboptimal acoustic window.”
* Trigger: adnx_mass_present = true
  Narrative sentence:
  “An adnexal mass is noted as described.”
* Trigger: adnx_mass_present = true AND adnx_composition = cystic AND adnx_septations_present = false AND adnx_solid_component_present = false AND adnx_papillary_projection_present = false
  Narrative sentence:
  “The adnexal lesion appears benign cystic in nature.”
* Trigger: adnx_papillary_projection_present = true OR adnx_solid_component_present = true OR adnx_vascularity = internal OR adnx_vascularity = marked
  Narrative sentence:
  “The adnexal lesion shows suspicious features.”

**Impression contribution**

* Adnexal mass
* Suspicious adnexal lesion (if suspicious features)

**Optional / edge notes (if any)**

* None.

---

## 🔹 BLOCK: Free fluid / ascites / collection

**Clinical purpose**
Used to document free fluid, quantify it, and flag complex or loculated collections.

**Used in exams**

* Abdomen
* Pelvis
* OB
* KUB (if pelvic views included)

**Structured fields**

* Organ visualized (ff_visualized)

  * Type: boolean
  * Required: Yes

* Image quality (ff_image_quality)

  * Type: enum
  * Required: Yes
  * Enum values: adequate, limited

* Limitation reason (ff_limitation_reason)

  * Type: short text
  * Required: No

* Free fluid present (ff_present)

  * Type: boolean
  * Required: Yes

* Amount (ff_amount)

  * Type: enum
  * Required: No
  * Enum values: trace, mild, moderate, large

* Distribution (ff_distribution)

  * Type: enum
  * Required: No
  * Enum values: pelvic, perihepatic, perisplenic, generalized

* Complex fluid features (ff_complex_present)

  * Type: boolean
  * Required: No

* Loculated collection suspected (ff_loculated_collection_suspected)

  * Type: boolean
  * Required: No

**Normal narrative output**

* “No free fluid is seen.”

**Abnormal triggers → narrative**

* Trigger: ff_image_quality = limited
  Narrative sentence:
  “Assessment is limited due to suboptimal acoustic window.”
* Trigger: ff_present = true
  Narrative sentence:
  “Free fluid is present ({ff_amount}).”
* Trigger: ff_complex_present = true
  Narrative sentence:
  “Complex free fluid with internal echoes/septations is noted.”
* Trigger: ff_loculated_collection_suspected = true
  Narrative sentence:
  “A loculated collection is suspected.”

**Impression contribution**

* Moderate/large free fluid
* Complex free fluid
* Suspected loculated collection

**Optional / edge notes (if any)**

* Trace pelvic fluid can be physiologic; template can keep it out of Impression.

---

## 🔹 BLOCK: Appendix / bowel focused

**Clinical purpose**
Used for targeted RLQ/bowel evaluation to support appendicitis or inflammatory bowel findings.

**Used in exams**

* Abdomen (appendix)
* Pelvis (RLQ pain)
* Pediatric abdomen (appendix)

**Structured fields**

* Organ visualized (app_visualized)

  * Type: boolean
  * Required: Yes

* Image quality (app_image_quality)

  * Type: enum
  * Required: Yes
  * Enum values: adequate, limited

* Limitation reason (app_limitation_reason)

  * Type: short text
  * Required: No

* Appendix visualized (app_appendix_visualized)

  * Type: boolean
  * Required: Yes

* Appendix diameter (app_appendix_diameter_mm)

  * Type: numeric (mm)
  * Required: No
  * Threshold policy: abnormal appendix if app_appendix_diameter_mm > 6 mm

* Compressible (app_compressible)

  * Type: boolean
  * Required: No

* Appendicolith present (app_appendicolith_present)

  * Type: boolean
  * Required: No

* Hyperemia present (app_hyperemia_present)

  * Type: boolean
  * Required: No

* Periappendiceal fluid (app_periappendiceal_fluid_present)

  * Type: boolean
  * Required: No

* Bowel wall thickening present (app_bowel_wall_thickening_present)

  * Type: boolean
  * Required: No

**Normal narrative output**

* “The appendix is visualized and appears normal with no periappendiceal fluid.”

**Abnormal triggers → narrative**

* Trigger: app_image_quality = limited
  Narrative sentence:
  “Assessment is limited due to suboptimal acoustic window.”
* Trigger: app_appendix_visualized = false
  Narrative sentence:
  “The appendix is not visualized.”
* Trigger: (app_appendix_diameter_mm > 6) OR (app_compressible = false) OR (app_hyperemia_present = true)
  Narrative sentence:
  “Findings are suggestive of acute appendicitis.”
* Trigger: app_appendicolith_present = true
  Narrative sentence:
  “An appendicolith is noted.”
* Trigger: app_bowel_wall_thickening_present = true
  Narrative sentence:
  “Bowel wall thickening is noted in the assessed segment.”

**Impression contribution**

* Features suggest acute appendicitis
* Appendicolith
* Bowel wall thickening (enteritis/colitis pattern, correlate clinically)

**Optional / edge notes (if any)**

* Non-visualized appendix is not a negative study; keep narrative neutral.

---

## 🔹 BLOCK: Hernia (abdominal wall / groin)

**Clinical purpose**
Used to evaluate abdominal wall and groin hernias, including type, content, and reducibility.

**Used in exams**

* Abdominal wall ultrasound
* Groin ultrasound
* Post-operative scar site

**Structured fields**

* Organ visualized (hern_visualized)

  * Type: boolean
  * Required: Yes

* Image quality (hern_image_quality)

  * Type: enum
  * Required: Yes
  * Enum values: adequate, limited

* Limitation reason (hern_limitation_reason)

  * Type: short text
  * Required: No

* Site/region (hern_site)

  * Type: short text
  * Required: Yes

* Hernia present (hern_present)

  * Type: boolean
  * Required: Yes

* Hernia type (hern_type)

  * Type: enum
  * Required: No
  * Enum values: inguinal, femoral, umbilical, paraumbilical, incisional, other

* Neck size (hern_neck_mm)

  * Type: numeric (mm)
  * Required: No

* Content (hern_content)

  * Type: enum
  * Required: No
  * Enum values: fat, bowel, fluid, mixed

* Reducible (hern_reducible)

  * Type: boolean
  * Required: No

* Strangulation suspected (hern_strangulation_suspected)

  * Type: boolean
  * Required: No

**Normal narrative output**

* “No hernia is identified at the stated site.”

**Abnormal triggers → narrative**

* Trigger: hern_image_quality = limited
  Narrative sentence:
  “Assessment is limited due to suboptimal acoustic window.”
* Trigger: hern_present = true
  Narrative sentence:
  “A {hern_type} hernia is noted containing {hern_content}.”
* Trigger: hern_reducible = true
  Narrative sentence:
  “The hernia appears reducible.”
* Trigger: hern_strangulation_suspected = true
  Narrative sentence:
  “Features suspicious for incarceration/strangulation are noted.”

**Impression contribution**

* {Type} hernia (with content)
* Suspected incarceration/strangulation (urgent correlation)

**Optional / edge notes (if any)**

* Reducibility requires dynamic maneuvers; if not assessed, leave blank.

---

## 🔹 BLOCK: Pleural effusion (lung bases)

**Clinical purpose**
Used to document pleural effusion, complexity, and adjacent consolidation suspicion.

**Used in exams**

* Abdomen (incidental lung bases)
* Pleural ultrasound
* Whole abdomen screening

**Structured fields**

* Organ visualized (pleff_visualized)

  * Type: boolean
  * Required: Yes

* Image quality (pleff_image_quality)

  * Type: enum
  * Required: Yes
  * Enum values: adequate, limited

* Limitation reason (pleff_limitation_reason)

  * Type: short text
  * Required: No

* Side (pleff_side)

  * Type: enum
  * Required: Yes
  * Enum values: right, left

* Effusion present (pleff_present)

  * Type: boolean
  * Required: Yes

* Amount (pleff_amount)

  * Type: enum
  * Required: No
  * Enum values: small, moderate, large

* Complex features (pleff_complex_present)

  * Type: boolean
  * Required: No

* Adjacent consolidation suspected (pleff_adjacent_consolidation_suspected)

  * Type: boolean
  * Required: No

**Normal narrative output**

* “No pleural effusion is seen on the {pleff_side}.”

**Abnormal triggers → narrative**

* Trigger: pleff_image_quality = limited
  Narrative sentence:
  “Assessment is limited due to suboptimal acoustic window.”
* Trigger: pleff_present = true
  Narrative sentence:
  “Pleural effusion is noted ({pleff_amount}).”
* Trigger: pleff_complex_present = true
  Narrative sentence:
  “Complex pleural effusion with internal echoes/septations is noted.”
* Trigger: pleff_adjacent_consolidation_suspected = true
  Narrative sentence:
  “Adjacent consolidation is suspected.”

**Impression contribution**

* Pleural effusion
* Complex pleural effusion (if present)

**Optional / edge notes (if any)**

* For bilateral effusion, use two instances (right and left).

---

## 🔹 BLOCK: Thyroid

**Clinical purpose**
Used to document thyroid parenchyma and nodules with structured descriptors suitable for routine thyroid ultrasound.

**Used in exams**

* Thyroid ultrasound
* Neck ultrasound
* Neck lump evaluation

**Structured fields**

* Organ visualized (thy_visualized)

  * Type: boolean
  * Required: Yes

* Image quality (thy_image_quality)

  * Type: enum
  * Required: Yes
  * Enum values: adequate, limited

* Limitation reason (thy_limitation_reason)

  * Type: short text
  * Required: No

* Right lobe length (thy_rt_lobe_length_cm)

  * Type: numeric (cm)
  * Required: No

* Left lobe length (thy_lt_lobe_length_cm)

  * Type: numeric (cm)
  * Required: No

* Isthmus thickness (thy_isthmus_mm)

  * Type: numeric (mm)
  * Required: No
  * Threshold policy: thickened isthmus if thy_isthmus_mm > 5 mm (simple default)

* Parenchymal echotexture (thy_echotexture)

  * Type: enum
  * Required: Yes
  * Enum values: normal, heterogeneous

* Vascularity (thy_vascularity)

  * Type: enum
  * Required: No
  * Enum values: normal, increased, decreased

* Nodule present (thy_nodule_present)

  * Type: boolean
  * Required: Yes

* Dominant nodule max size (thy_dominant_nodule_mm)

  * Type: numeric (mm)
  * Required: No

* Dominant nodule composition (thy_dominant_composition)

  * Type: enum
  * Required: No
  * Enum values: cystic, solid, mixed

* Dominant nodule echogenicity (thy_dominant_echogenicity)

  * Type: enum
  * Required: No
  * Enum values: anechoic, hyperechoic, isoechoic, hypoechoic, very_hypoechoic

* Dominant nodule margins (thy_dominant_margins)

  * Type: enum
  * Required: No
  * Enum values: smooth, ill_defined, lobulated, irregular

* Microcalcifications suspected (thy_microcalcifications_suspected)

  * Type: boolean
  * Required: No

* Taller-than-wide (thy_taller_than_wide)

  * Type: boolean
  * Required: No

**Normal narrative output**

* “The thyroid gland is normal in size with homogeneous echotexture. No focal thyroid nodule is seen.”

**Abnormal triggers → narrative**

* Trigger: thy_image_quality = limited
  Narrative sentence:
  “Assessment is limited due to suboptimal acoustic window.”
* Trigger: thy_echotexture = heterogeneous
  Narrative sentence:
  “Heterogeneous thyroid echotexture is noted, which may be seen with thyroiditis in the appropriate clinical setting.”
* Trigger: thy_nodule_present = true
  Narrative sentence:
  “Thyroid nodule(s) are noted as described.”
* Trigger: thy_microcalcifications_suspected = true OR thy_dominant_margins = irregular OR thy_taller_than_wide = true
  Narrative sentence:
  “Suspicious sonographic features are present in the dominant thyroid nodule.”

**Impression contribution**

* Features may suggest thyroiditis
* Thyroid nodule(s)
* Dominant thyroid nodule with suspicious features (risk stratification/FNA as per protocol)

**Optional / edge notes (if any)**

* None.

---

## 🔹 BLOCK: Salivary glands (parotid/submandibular)

**Clinical purpose**
Used to document salivary gland echotexture, duct dilatation, stones, inflammation pattern, and focal lesions.

**Used in exams**

* Neck ultrasound
* Salivary gland ultrasound
* Neck lump evaluation

**Structured fields**

* Organ visualized (sal_visualized)

  * Type: boolean
  * Required: Yes

* Image quality (sal_image_quality)

  * Type: enum
  * Required: Yes
  * Enum values: adequate, limited

* Limitation reason (sal_limitation_reason)

  * Type: short text
  * Required: No

* Gland (sal_gland)

  * Type: enum
  * Required: Yes
  * Enum values: parotid, submandibular

* Side (sal_side)

  * Type: enum
  * Required: Yes
  * Enum values: right, left

* Size (sal_size)

  * Type: enum
  * Required: No
  * Enum values: normal, enlarged

* Echotexture (sal_echotexture)

  * Type: enum
  * Required: Yes
  * Enum values: normal, heterogeneous

* Hypervascularity (sal_hypervascularity_present)

  * Type: boolean
  * Required: No

* Duct dilatation (sal_duct_dilatation_present)

  * Type: boolean
  * Required: No

* Sialolith present (sal_sialolith_present)

  * Type: boolean
  * Required: No

* Focal lesion present (sal_focal_lesion_present)

  * Type: boolean
  * Required: No

**Normal narrative output**

* “The {sal_side} {sal_gland} gland appears unremarkable with no focal lesion or duct dilatation.”

**Abnormal triggers → narrative**

* Trigger: sal_image_quality = limited
  Narrative sentence:
  “Assessment is limited due to suboptimal acoustic window.”
* Trigger: sal_size = enlarged AND sal_echotexture = heterogeneous
  Narrative sentence:
  “Findings are suggestive of sialadenitis.”
* Trigger: sal_duct_dilatation_present = true
  Narrative sentence:
  “Salivary duct dilatation is noted.”
* Trigger: sal_sialolith_present = true
  Narrative sentence:
  “Sialolithiasis is noted.”
* Trigger: sal_focal_lesion_present = true
  Narrative sentence:
  “A focal salivary gland lesion is noted.”

**Impression contribution**

* Sialadenitis
* Sialolithiasis
* Salivary gland lesion

**Optional / edge notes (if any)**

* None.

---

## 🔹 BLOCK: Cervical lymph nodes

**Clinical purpose**
Used to document cervical lymphadenopathy with structured suspicious features.

**Used in exams**

* Neck ultrasound
* Thyroid ultrasound (adjunct)
* Salivary gland ultrasound (adjunct)

**Structured fields**

* Organ visualized (cln_visualized)

  * Type: boolean
  * Required: Yes

* Image quality (cln_image_quality)

  * Type: enum
  * Required: Yes
  * Enum values: adequate, limited

* Limitation reason (cln_limitation_reason)

  * Type: short text
  * Required: No

* Lymphadenopathy present (cln_enlarged_present)

  * Type: boolean
  * Required: Yes

* Level (cln_level)

  * Type: enum
  * Required: No
  * Enum values: I, II, III, IV, V, VI, other

* Largest short-axis (cln_short_axis_mm)

  * Type: numeric (mm)
  * Required: No
  * Threshold policy: “enlarged” if cln_short_axis_mm > 10 mm (simple default; jugulodigastric may be larger)

* Shape (cln_shape)

  * Type: enum
  * Required: No
  * Enum values: oval, round

* Hilum preserved (cln_hilum_preserved)

  * Type: boolean
  * Required: No

* Necrosis/cystic change (cln_necrosis_present)

  * Type: boolean
  * Required: No

* Calcification (cln_calcification_present)

  * Type: boolean
  * Required: No

* Abnormal vascularity (cln_abnormal_vascularity_present)

  * Type: boolean
  * Required: No

**Normal narrative output**

* “No significant cervical lymphadenopathy is seen.”

**Abnormal triggers → narrative**

* Trigger: cln_image_quality = limited
  Narrative sentence:
  “Assessment is limited due to suboptimal acoustic window.”
* Trigger: cln_enlarged_present = true OR cln_short_axis_mm > 10
  Narrative sentence:
  “Enlarged cervical lymph node(s) are noted.”
* Trigger: cln_shape = round OR cln_hilum_preserved = false OR cln_necrosis_present = true OR cln_calcification_present = true OR cln_abnormal_vascularity_present = true
  Narrative sentence:
  “Suspicious nodal features are present.”

**Impression contribution**

* Likely reactive cervical lymph nodes (if benign features)
* Suspicious cervical lymphadenopathy (if suspicious features)

**Optional / edge notes (if any)**

* None.

---

## 🔹 BLOCK: Breast parenchyma (background)

**Clinical purpose**
Used to document background breast appearance and diffuse findings independent of focal lesions.

**Used in exams**

* Breast ultrasound
* Targeted breast ultrasound (adjunct)

**Structured fields**

* Organ visualized (brp_visualized)

  * Type: boolean
  * Required: Yes

* Image quality (brp_image_quality)

  * Type: enum
  * Required: Yes
  * Enum values: adequate, limited

* Limitation reason (brp_limitation_reason)

  * Type: short text
  * Required: No

* Side (brp_side)

  * Type: enum
  * Required: Yes
  * Enum values: right, left

* Parenchymal pattern (brp_pattern)

  * Type: enum
  * Required: No
  * Enum values: fatty, fibroglandular, dense

* Duct ectasia (brp_duct_ectasia_present)

  * Type: boolean
  * Required: No

* Skin thickening (brp_skin_thickening_present)

  * Type: boolean
  * Required: No

* Edema (brp_edema_present)

  * Type: boolean
  * Required: No

**Normal narrative output**

* “Breast parenchyma appears unremarkable on the examined side with no suspicious diffuse abnormality.”

**Abnormal triggers → narrative**

* Trigger: brp_image_quality = limited
  Narrative sentence:
  “Assessment is limited due to suboptimal acoustic window.”
* Trigger: brp_duct_ectasia_present = true
  Narrative sentence:
  “Duct ectasia is noted.”
* Trigger: brp_skin_thickening_present = true OR brp_edema_present = true
  Narrative sentence:
  “Skin thickening/edema is noted.”

**Impression contribution**

* Duct ectasia (optional)
* Diffuse breast edema/skin thickening (correlate clinically)

**Optional / edge notes (if any)**

* For bilateral background, use two instances.

---

## 🔹 BLOCK: Breast focal lesion (BI-RADS descriptors)

**Clinical purpose**
Used to characterize a breast focal lesion with structured descriptors and BI-RADS category.

**Used in exams**

* Breast ultrasound
* Targeted breast lump ultrasound

**Structured fields**

* Organ visualized (brl_visualized)

  * Type: boolean
  * Required: Yes

* Image quality (brl_image_quality)

  * Type: enum
  * Required: Yes
  * Enum values: adequate, limited

* Limitation reason (brl_limitation_reason)

  * Type: short text
  * Required: No

* Lesion present (brl_lesion_present)

  * Type: boolean
  * Required: Yes

* Lesion max size (brl_lesion_max_mm)

  * Type: numeric (mm)
  * Required: No

* Location clock-face (brl_location_clock_face)

  * Type: enum
  * Required: No
  * Enum values: 1,2,3,4,5,6,7,8,9,10,11,12

* Distance from nipple (brl_distance_from_nipple_mm)

  * Type: numeric (mm)
  * Required: No

* Shape (brl_shape)

  * Type: enum
  * Required: No
  * Enum values: oval, round, irregular

* Orientation (brl_orientation)

  * Type: enum
  * Required: No
  * Enum values: parallel, non_parallel

* Margins (brl_margins)

  * Type: enum
  * Required: No
  * Enum values: circumscribed, indistinct, angular, microlobulated, spiculated

* Echo pattern (brl_echo_pattern)

  * Type: enum
  * Required: No
  * Enum values: anechoic, hyperechoic, complex, hypoechoic, heterogeneous

* Posterior features (brl_posterior_features)

  * Type: enum
  * Required: No
  * Enum values: none, enhancement, shadowing, mixed

* Vascularity (brl_vascularity)

  * Type: enum
  * Required: No
  * Enum values: none, peripheral, internal, marked

* BI-RADS category (brl_birads)

  * Type: enum
  * Required: No
  * Enum values: 1,2,3,4,5
  * Notes: Required when brl_lesion_present = true

**Normal narrative output**

* “No focal breast lesion is identified.”

**Abnormal triggers → narrative**

* Trigger: brl_image_quality = limited
  Narrative sentence:
  “Assessment is limited due to suboptimal acoustic window.”
* Trigger: brl_lesion_present = true
  Narrative sentence:
  “A focal breast lesion is noted as described.”
* Trigger: brl_birads = 2
  Narrative sentence:
  “The lesion appears benign (BI-RADS 2).”
* Trigger: brl_birads = 3
  Narrative sentence:
  “The lesion is probably benign (BI-RADS 3); short-interval follow-up is suggested.”
* Trigger: brl_birads = 4 OR brl_birads = 5
  Narrative sentence:
  “A suspicious lesion is noted (BI-RADS {brl_birads}); tissue diagnosis is advised.”

**Impression contribution**

* BI-RADS 3 lesion — follow-up recommended
* BI-RADS 4/5 lesion — biopsy recommended

**Optional / edge notes (if any)**

* None.

---

## 🔹 BLOCK: Scrotum (single side per instance)

**Clinical purpose**
Used to document testis echotexture/vascularity, epididymal inflammatory changes, hydrocele, and varicocele for one side.

**Used in exams**

* Scrotum ultrasound
* Testicular pain ultrasound
* Varicocele assessment

**Structured fields**

* Organ visualized (scr_visualized)

  * Type: boolean
  * Required: Yes

* Image quality (scr_image_quality)

  * Type: enum
  * Required: Yes
  * Enum values: adequate, limited

* Limitation reason (scr_limitation_reason)

  * Type: short text
  * Required: No

* Side (scr_side)

  * Type: enum
  * Required: Yes
  * Enum values: right, left

* Testis echotexture (scr_testis_echotexture)

  * Type: enum
  * Required: Yes
  * Enum values: normal, heterogeneous

* Intratesticular lesion present (scr_intratesticular_lesion_present)

  * Type: boolean
  * Required: Yes

* Intratesticular flow (scr_testicular_flow)

  * Type: enum
  * Required: Yes
  * Enum values: normal, reduced, absent, increased

* Epididymis enlarged (scr_epididymis_enlarged)

  * Type: boolean
  * Required: No

* Epididymis hypervascular (scr_epididymis_hypervascular)

  * Type: boolean
  * Required: No

* Hydrocele (scr_hydrocele)

  * Type: enum
  * Required: No
  * Enum values: none, mild, moderate, large

* Varicocele (scr_varicocele)

  * Type: enum
  * Required: No
  * Enum values: none, mild, moderate, severe

**Normal narrative output**

* “The {scr_side} testis is normal in echotexture with preserved vascularity. No focal intratesticular lesion is seen.”
* “No hydrocele or varicocele is noted.”

**Abnormal triggers → narrative**

* Trigger: scr_testicular_flow = reduced OR scr_testicular_flow = absent
  Narrative sentence:
  “Reduced/absent intratesticular flow is noted, suspicious for torsion.”
* Trigger: scr_epididymis_enlarged = true AND scr_epididymis_hypervascular = true
  Narrative sentence:
  “Findings are suggestive of epididymitis.”
* Trigger: scr_testicular_flow = increased AND scr_testis_echotexture = heterogeneous
  Narrative sentence:
  “Findings are suggestive of orchitis/epididymo-orchitis.”
* Trigger: scr_intratesticular_lesion_present = true
  Narrative sentence:
  “An intratesticular lesion is noted.”
* Trigger: scr_hydrocele != none
  Narrative sentence:
  “A {scr_hydrocele} hydrocele is noted.”
* Trigger: scr_varicocele != none
  Narrative sentence:
  “A {scr_varicocele} varicocele is noted.”

**Impression contribution**

* Suspicious for testicular torsion (urgent correlation)
* Epididymitis / epididymo-orchitis
* Intratesticular lesion
* Hydrocele / varicocele

**Optional / edge notes (if any)**

* For bilateral reporting, use two instances (right and left).

---

## 🔹 BLOCK: Soft tissue lump / abscess / foreign body

**Clinical purpose**
Used for any superficial lump to classify cystic/solid/mixed lesion, abscess features, and foreign body suspicion.

**Used in exams**

* Soft tissue ultrasound (any region)
* Neck/axilla/limb lumps
* Post-operative site

**Structured fields**

* Organ visualized (st_visualized)

  * Type: boolean
  * Required: Yes

* Image quality (st_image_quality)

  * Type: enum
  * Required: Yes
  * Enum values: adequate, limited

* Limitation reason (st_limitation_reason)

  * Type: short text
  * Required: No

* Site/region (st_site)

  * Type: short text
  * Required: Yes

* Lesion present (st_lesion_present)

  * Type: boolean
  * Required: Yes

* Max size (st_lesion_max_mm)

  * Type: numeric (mm)
  * Required: No

* Depth plane (st_depth_plane)

  * Type: enum
  * Required: No
  * Enum values: dermal, subcutaneous, intramuscular, deep

* Composition (st_composition)

  * Type: enum
  * Required: No
  * Enum values: cystic, solid, mixed

* Margins (st_margins)

  * Type: enum
  * Required: No
  * Enum values: well_defined, ill_defined

* Vascularity (st_vascularity)

  * Type: enum
  * Required: No
  * Enum values: none, peripheral, internal, marked

* Collection features present (st_collection_features_present)

  * Type: boolean
  * Required: No

* Sinus/tract suspected (st_sinus_tract_suspected)

  * Type: boolean
  * Required: No

* Foreign body suspected (st_foreign_body_suspected)

  * Type: boolean
  * Required: No

**Normal narrative output**

* “No focal soft tissue lesion is identified at the stated site.”

**Abnormal triggers → narrative**

* Trigger: st_image_quality = limited
  Narrative sentence:
  “Assessment is limited due to suboptimal acoustic window.”
* Trigger: st_lesion_present = true
  Narrative sentence:
  “A focal soft tissue lesion is noted as described.”
* Trigger: st_composition = cystic AND st_collection_features_present = true
  Narrative sentence:
  “A complex fluid collection is noted, suggestive of abscess in the appropriate clinical setting.”
* Trigger: st_foreign_body_suspected = true
  Narrative sentence:
  “An echogenic foreign body is suspected.”
* Trigger: st_margins = ill_defined AND (st_vascularity = internal OR st_vascularity = marked)
  Narrative sentence:
  “A suspicious soft tissue lesion is noted; further evaluation is advised.”

**Impression contribution**

* Soft tissue abscess (if abscess pattern)
* Suspected foreign body
* Suspicious soft tissue mass

**Optional / edge notes (if any)**

* None.

---

## 🔹 BLOCK: Early pregnancy (first trimester viability & dating)

**Clinical purpose**
Used to document IUP presence, viability markers, dating (CRL), and common early pregnancy complications.

**Used in exams**

* OB (first trimester)
* Pelvis (pregnancy query)
* TVS early pregnancy

**Structured fields**

* Organ visualized (ep_visualized)

  * Type: boolean
  * Required: Yes

* Image quality (ep_image_quality)

  * Type: enum
  * Required: Yes
  * Enum values: adequate, limited

* Limitation reason (ep_limitation_reason)

  * Type: short text
  * Required: No

* Intrauterine gestational sac seen (ep_ius_seen)

  * Type: boolean
  * Required: Yes

* Mean sac diameter (ep_msd_mm)

  * Type: numeric (mm)
  * Required: No

* Yolk sac seen (ep_yolk_sac_seen)

  * Type: boolean
  * Required: No

* Fetal pole seen (ep_fetal_pole_seen)

  * Type: boolean
  * Required: No

* Crown-rump length (ep_crl_mm)

  * Type: numeric (mm)
  * Required: No

* Cardiac activity present (ep_cardiac_activity_present)

  * Type: boolean
  * Required: No

* Fetal heart rate (ep_fhr_bpm)

  * Type: numeric (bpm)
  * Required: No

* Subchorionic hemorrhage present (ep_sch_present)

  * Type: boolean
  * Required: No

* Gestational age by CRL (ep_ga_weeks_days)

  * Type: short text
  * Required: No

* Estimated due date (ep_edd_date)

  * Type: short text
  * Required: No

**Normal narrative output**

* “A single intrauterine gestational sac is seen with fetal pole and cardiac activity.”
* “Gestational age corresponds to approximately {ep_ga_weeks_days}.”

**Abnormal triggers → narrative**

* Trigger: ep_image_quality = limited
  Narrative sentence:
  “Assessment is limited due to suboptimal acoustic window.”
* Trigger: ep_ius_seen = false
  Narrative sentence:
  “No definite intrauterine gestational sac is seen.”
* Trigger: ep_fetal_pole_seen = true AND ep_cardiac_activity_present = false
  Narrative sentence:
  “A fetal pole is seen without demonstrable cardiac activity.”
* Trigger: ep_sch_present = true
  Narrative sentence:
  “A subchorionic hemorrhage is noted.”

**Impression contribution**

* Viable intrauterine pregnancy (if IUP + cardiac activity)
* Pregnancy of unknown location (if no IUP; correlate β-hCG and follow-up)
* Non-viable pregnancy suspected (if fetal pole without cardiac activity; follow-up/criteria)
* Subchorionic hemorrhage

**Optional / edge notes (if any)**

* None.

---

## 🔹 BLOCK: Fetal biometry & growth (2nd/3rd trimester)

**Clinical purpose**
Used to document fetal presentation and standard biometry for dating/growth and estimated fetal weight.

**Used in exams**

* OB (2nd/3rd trimester)
* Growth scan
* Follow-up scans

**Structured fields**

* Organ visualized (fb_visualized)

  * Type: boolean
  * Required: Yes

* Image quality (fb_image_quality)

  * Type: enum
  * Required: Yes
  * Enum values: adequate, limited

* Limitation reason (fb_limitation_reason)

  * Type: short text
  * Required: No

* Presentation (fb_presentation)

  * Type: enum
  * Required: No
  * Enum values: cephalic, breech, transverse, oblique

* BPD (fb_bpd_mm)

  * Type: numeric (mm)
  * Required: No

* HC (fb_hc_mm)

  * Type: numeric (mm)
  * Required: No

* AC (fb_ac_mm)

  * Type: numeric (mm)
  * Required: No

* FL (fb_fl_mm)

  * Type: numeric (mm)
  * Required: No

* Estimated fetal weight (fb_efw_g)

  * Type: numeric (g)
  * Required: No

* GA by biometry (fb_ga_weeks_days)

  * Type: short text
  * Required: No

* Growth percentile (fb_growth_percentile)

  * Type: numeric (%)
  * Required: No
  * Threshold policy: FGR suspected if fb_growth_percentile < 10%; LGA if fb_growth_percentile > 90%

**Normal narrative output**

* “Fetal biometry corresponds to approximately {fb_ga_weeks_days}. Estimated fetal weight appears appropriate for gestational age.”

**Abnormal triggers → narrative**

* Trigger: fb_image_quality = limited
  Narrative sentence:
  “Assessment is limited due to suboptimal acoustic window.”
* Trigger: fb_growth_percentile < 10
  Narrative sentence:
  “Fetal growth appears below the expected range for gestational age.”
* Trigger: fb_growth_percentile > 90
  Narrative sentence:
  “Fetal growth appears above the expected range for gestational age.”

**Impression contribution**

* Suspected fetal growth restriction
* Large for gestational age

**Optional / edge notes (if any)**

* None.

---

## 🔹 BLOCK: Placenta / amniotic fluid / cervix

**Clinical purpose**
Used to document placental location/previa risk, liquor status, and cervical length where assessed.

**Used in exams**

* OB (2nd/3rd trimester)
* Growth scan
* Anatomy scan

**Structured fields**

* Organ visualized (pl_visualized)

  * Type: boolean
  * Required: Yes

* Image quality (pl_image_quality)

  * Type: enum
  * Required: Yes
  * Enum values: adequate, limited

* Limitation reason (pl_limitation_reason)

  * Type: short text
  * Required: No

* Placenta location (pl_location)

  * Type: enum
  * Required: Yes
  * Enum values: anterior, posterior, fundal, low_lying

* Placenta previa (pl_previa_present)

  * Type: boolean
  * Required: No

* Placental grade (pl_grade)

  * Type: enum
  * Required: No
  * Enum values: 0, I, II, III

* Retroplacental hematoma (pl_retroplacental_hematoma_present)

  * Type: boolean
  * Required: No

* Fluid assessment method (pl_fluid_method)

  * Type: enum
  * Required: No
  * Enum values: afi, sdp, subjective

* AFI (pl_afi_cm)

  * Type: numeric (cm)
  * Required: No
  * Threshold policy: oligohydramnios if pl_afi_cm < 5; polyhydramnios if pl_afi_cm > 24

* SDP (pl_sdp_cm)

  * Type: numeric (cm)
  * Required: No
  * Threshold policy: oligohydramnios if pl_sdp_cm < 2; polyhydramnios if pl_sdp_cm > 8

* Oligohydramnios (pl_oligohydramnios_present)

  * Type: boolean
  * Required: No

* Polyhydramnios (pl_polyhydramnios_present)

  * Type: boolean
  * Required: No

* Cervical length (pl_cervical_length_mm)

  * Type: numeric (mm)
  * Required: No
  * Threshold policy: short cervix if pl_cervical_length_mm < 25 mm (mid-trimester default)

* Funneling present (pl_funneling_present)

  * Type: boolean
  * Required: No

**Normal narrative output**

* “The placenta is {pl_location} with no evidence of previa.”
* “Amniotic fluid appears adequate.”

**Abnormal triggers → narrative**

* Trigger: pl_image_quality = limited
  Narrative sentence:
  “Assessment is limited due to suboptimal acoustic window.”
* Trigger: pl_location = low_lying OR pl_previa_present = true
  Narrative sentence:
  “The placenta is low-lying / previa is noted.”
* Trigger: pl_retroplacental_hematoma_present = true
  Narrative sentence:
  “A retroplacental hematoma is noted.”
* Trigger: pl_oligohydramnios_present = true OR pl_afi_cm < 5 OR pl_sdp_cm < 2
  Narrative sentence:
  “Oligohydramnios is noted.”
* Trigger: pl_polyhydramnios_present = true OR pl_afi_cm > 24 OR pl_sdp_cm > 8
  Narrative sentence:
  “Polyhydramnios is noted.”
* Trigger: pl_cervical_length_mm < 25 OR pl_funneling_present = true
  Narrative sentence:
  “A short cervix and/or funneling is noted.”

**Impression contribution**

* Low-lying placenta / placenta previa
* Oligohydramnios / polyhydramnios
* Short cervix
* Retroplacental hematoma

**Optional / edge notes (if any)**

* If both AFI and SDP are absent, rely on subjective + boolean flags only.

---

## 🔹 BLOCK: Fetal anatomy screening (basic checklist)

**Clinical purpose**
Used to document a structured “seen/limited/not seen” checklist of key fetal structures in routine screening.

**Used in exams**

* OB anatomy scan
* Growth scan (limited anatomy check)

**Structured fields**

* Organ visualized (fa_visualized)

  * Type: boolean
  * Required: Yes

* Image quality (fa_image_quality)

  * Type: enum
  * Required: Yes
  * Enum values: adequate, limited

* Limitation reason (fa_limitation_reason)

  * Type: short text
  * Required: No

* Skull/brain (fa_skull_brain)

  * Type: enum
  * Required: Yes
  * Enum values: seen, limited, not_seen

* Spine (fa_spine)

  * Type: enum
  * Required: Yes
  * Enum values: seen, limited, not_seen

* Four-chamber heart view (fa_four_chamber_heart)

  * Type: enum
  * Required: Yes
  * Enum values: seen, limited, not_seen

* Stomach (fa_stomach)

  * Type: enum
  * Required: Yes
  * Enum values: seen, limited, not_seen

* Kidneys (fa_kidneys)

  * Type: enum
  * Required: Yes
  * Enum values: both_seen, one_seen, not_seen, limited

* Urinary bladder (fa_bladder)

  * Type: enum
  * Required: Yes
  * Enum values: seen, limited, not_seen

* Anterior abdominal wall intact (fa_abdominal_wall_intact)

  * Type: enum
  * Required: No
  * Enum values: yes, no, limited

* Cord vessels (fa_cord_vessels)

  * Type: enum
  * Required: No
  * Enum values: three_vessel, two_vessel_suspected, not_assessed

**Normal narrative output**

* “Basic fetal anatomy as listed appears unremarkable on this screening assessment.”

**Abnormal triggers → narrative**

* Trigger: fa_image_quality = limited
  Narrative sentence:
  “Anatomy assessment is limited.”
* Trigger: any of fa_skull_brain/fa_spine/fa_four_chamber_heart/fa_stomach/fa_kidneys/fa_bladder = not_seen (and not limited)
  Narrative sentence:
  “A required structure is not visualized; follow-up/targeted assessment may be required.”
* Trigger: fa_abdominal_wall_intact = no
  Narrative sentence:
  “An anterior abdominal wall defect is suspected.”
* Trigger: fa_cord_vessels = two_vessel_suspected
  Narrative sentence:
  “Two-vessel cord is suspected.”

**Impression contribution**

* Suspected fetal anomaly (when defect suspected)
* Limited anatomy assessment

**Optional / edge notes (if any)**

* Keep this as screening; detailed anomaly blocks can be added later.

---

## 🔹 BLOCK: Carotid Doppler (paired, instance per side)

**Clinical purpose**
Used to document carotid plaque and stenosis category using structured stenosis grading.

**Used in exams**

* Carotid Doppler
* Stroke/TIA workup

**Structured fields**

* Organ visualized (car_visualized)

  * Type: boolean
  * Required: Yes

* Image quality (car_image_quality)

  * Type: enum
  * Required: Yes
  * Enum values: adequate, limited

* Limitation reason (car_limitation_reason)

  * Type: short text
  * Required: No

* Side (car_side)

  * Type: enum
  * Required: Yes
  * Enum values: right, left

* Plaque present (car_plaque_present)

  * Type: boolean
  * Required: Yes

* Plaque type (car_plaque_type)

  * Type: enum
  * Required: No
  * Enum values: soft, calcified, mixed

* ICA PSV (car_ica_psv_cm_s)

  * Type: numeric (cm/s)
  * Required: No
  * Threshold policy: ≥ 125 suggests ≥50% stenosis; ≥ 230 suggests ≥70% stenosis (simple defaults)

* ICA EDV (car_ica_edv_cm_s)

  * Type: numeric (cm/s)
  * Required: No

* CCA PSV (car_cca_psv_cm_s)

  * Type: numeric (cm/s)
  * Required: No

* ICA/CCA ratio (car_ica_cca_ratio)

  * Type: numeric
  * Required: No
  * Threshold policy: ratio ≥ 2 suggests ≥50%; ratio ≥ 4 suggests ≥70% (simple defaults)

* Stenosis category (car_stenosis_category)

  * Type: enum
  * Required: Yes
  * Enum values: normal, lt_50, stenosis_50_69, ge_70, near_occlusion

* Vertebral flow direction (car_vertebral_flow)

  * Type: enum
  * Required: No
  * Enum values: antegrade, retrograde, not_assessed

**Normal narrative output**

* “No hemodynamically significant carotid stenosis is seen on the {car_side}.”

**Abnormal triggers → narrative**

* Trigger: car_image_quality = limited
  Narrative sentence:
  “Doppler assessment is limited.”
* Trigger: car_plaque_present = true
  Narrative sentence:
  “Atherosclerotic plaque is noted.”
* Trigger: car_stenosis_category = stenosis_50_69 OR car_stenosis_category = ge_70 OR car_stenosis_category = near_occlusion
  Narrative sentence:
  “Hemodynamically significant stenosis is present ({car_stenosis_category}).”
* Trigger: car_vertebral_flow = retrograde
  Narrative sentence:
  “Retrograde vertebral flow is noted.”

**Impression contribution**

* {Side} ICA stenosis: {car_stenosis_category}
* Subclavian steal pattern suspected (if retrograde vertebral flow)

**Optional / edge notes (if any)**

* None.

---

## 🔹 BLOCK: Lower limb venous Doppler (DVT) (paired, instance per side)

**Clinical purpose**
Used to document DVT assessment using compressibility and a structured thrombus summary.

**Used in exams**

* Lower limb venous Doppler
* DVT evaluation

**Structured fields**

* Organ visualized (dvt_visualized)

  * Type: boolean
  * Required: Yes

* Image quality (dvt_image_quality)

  * Type: enum
  * Required: Yes
  * Enum values: adequate, limited

* Limitation reason (dvt_limitation_reason)

  * Type: short text
  * Required: No

* Side (dvt_side)

  * Type: enum
  * Required: Yes
  * Enum values: right, left

* CFV compressible (dvt_cfv_compressible)

  * Type: boolean
  * Required: Yes

* FV compressible (dvt_fv_compressible)

  * Type: boolean
  * Required: Yes

* Popliteal compressible (dvt_popliteal_compressible)

  * Type: boolean
  * Required: Yes

* Calf veins assessed (dvt_calf_veins_assessed)

  * Type: enum
  * Required: No
  * Enum values: yes, limited, not_assessed

* Thrombus present (dvt_thrombus_present)

  * Type: boolean
  * Required: Yes

* Thrombus location (dvt_thrombus_location)

  * Type: enum
  * Required: No
  * Enum values: proximal, distal, both

* Thrombus chronicity (dvt_thrombus_chronicity)

  * Type: enum
  * Required: No
  * Enum values: acute, chronic, indeterminate

**Normal narrative output**

* “Deep veins of the {dvt_side} lower limb are compressible with no evidence of DVT.”

**Abnormal triggers → narrative**

* Trigger: dvt_image_quality = limited
  Narrative sentence:
  “Doppler assessment is limited.”
* Trigger: (dvt_cfv_compressible = false) OR (dvt_fv_compressible = false) OR (dvt_popliteal_compressible = false) OR (dvt_thrombus_present = true)
  Narrative sentence:
  “Findings are consistent with DVT involving the {dvt_thrombus_location} deep veins.”
* Trigger: dvt_thrombus_chronicity = chronic
  Narrative sentence:
  “Features suggest chronic thrombosis.”
* Trigger: dvt_calf_veins_assessed = limited OR dvt_calf_veins_assessed = not_assessed
  Narrative sentence:
  “Calf vein assessment is limited.”

**Impression contribution**

* DVT in {Side} lower limb ({location})
* Chronic venous thrombosis changes
* Limited calf vein assessment (if limited)

**Optional / edge notes (if any)**

* None.

---

## Optional blocks to add later (only if needed)

* **Upper limb venous Doppler (UEDVT)** (for lines/arm swelling workflows)
* **Renal artery Doppler** (HTN/renal stenosis protocols)
* **Testicular/ovarian torsion Doppler detail** (arterial/venous waveform fields)
* **Musculoskeletal (shoulder rotator cuff / knee effusion)** (if you plan MSK services)
