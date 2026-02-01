# Baseline Pack: USG Abdomen v1

Contents:
- profiles.csv: creates `USG_ABD` profile (USG Abdomen)
- parameters.csv: liver, GB/CBD, pancreas, spleen, kidneys, bladder, pelvic organ, aorta/IVC, ascites, impression & limitations
- services.csv: catalog entry `USG_ABD`
- linkage.csv: links service `USG_ABD` to profile `USG_ABD` and marks it default

Import order (required):
1) profiles.csv
2) parameters.csv
3) services.csv
4) linkage.csv

Expected result:
- Narrative enabled abdomen profile with structured parameters and sentence templates
- Service available in catalog and selectable with default profile linkage
