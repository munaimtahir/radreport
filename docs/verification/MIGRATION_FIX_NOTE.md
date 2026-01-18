# Migration Fix Verification Note

## Issue
Runing `python manage.py migrate` failed on `usg.0002_rename_...` with `psycopg2.errors.UndefinedTable: relation "usg_usgfie_study__b1d291_idx" does not exist`.

## Root Cause
Django's `RenameIndex` operation assumes the old index name exists. However, index names are often auto-generated based on a hash of the model/field names. If the database was initialized with a different Django version or environment that generated a different index name (or if the index was already renamed/created with the new name), the `RenameIndex` operation fails because it cannot find the source index.

## Fix Approach
We replaced the explicit `migrations.RenameIndex` operations with idempotent `migrations.RunSQL` blocks.
The SQL logic checks `pg_class` to see if the **OLD** index exists.
- If the old index exists, it renames it to the new name.
- If the old index does NOT exist, it assumes the index is already in the correct state (or missing, in which case a rename wouldn't help anyway) and does nothing.

This makes the migration safe for:
1. **Fresh DBs**: Where the previous migration might have created the index with the *new* name directly (depending on Django version).
2. **Existing DBs**: Where the index might effectively already be renamed or named differently.
3. **Correct DBs**: Where the old index exists and needs renaming.

## Verification
Ran `migrate` and verified it completed without error.
Checked indexes via `psql` and confirmed `usg_usgfiel_study_i_acf6f5_idx` (the target name) exists.
