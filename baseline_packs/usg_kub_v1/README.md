# Baseline Pack: USG KUB v1

Contents:
- profiles.csv: creates `USG_KUB` profile (USG KUB)
- parameters.csv: kidneys/ureters/bladder coverage including hydronephrosis, calculi, volumes, PVR, jets, impression & limitations
- services.csv: catalog entry `USG_KUB`
- linkage.csv: links service `USG_KUB` to profile `USG_KUB` as default

Import order:
1) profiles.csv
2) parameters.csv
3) services.csv
4) linkage.csv

Expected result:
- Focused KUB profile with hydronephrosis/stone/PVR tracking
- Service registered and bound to the profile for reporting
