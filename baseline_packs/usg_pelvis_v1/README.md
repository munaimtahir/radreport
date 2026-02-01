# Baseline Pack: USG Pelvis v1

Contents:
- profiles.csv: creates `USG_PELVIS` profile (USG Pelvis)
- parameters.csv: uterus, myometrium, endometrium, cervix, ovaries, adnexa, free fluid, optional prostate, impression & limitations
- services.csv: catalog entry `USG_PELVIS`
- linkage.csv: links service `USG_PELVIS` to profile `USG_PELVIS` as default

Import order:
1) profiles.csv
2) parameters.csv
3) services.csv
4) linkage.csv

Expected result:
- Pelvic ultrasound template ready for narrative generation with required sections
- Service available and linked to profile
