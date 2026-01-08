# RIMS – Medical Center Workflow App (USG + OPD) – AI Development Pack (Source of Truth)

**Date:** 2026-01-08  
**Purpose:** This pack is the *authoritative blueprint* for rebuilding and aligning the existing repository to a clean, working v1.

## What’s in here
- Locked workflows (Reception → Worklists → USG/OPD → Verification → Print/PDF)
- Roles & permissions
- Data model + APIs
- UI screen map (wireframe-level)
- Print/PDF specs (A4 duplicate receipt + final reports)
- Tests, QA checklist, CI/CD notes
- Task list for repo alignment

## Ground Rules (v1)
- One **Patient** has one permanent **MR number**
- One **Visit** has one **SV (Service Visit ID)**
- A **Visit** can include multiple services (USG + OPD together)
- Billing supports: discount, paid, due
- Reception prints **A4 duplicate receipt** (patient copy + office copy)
- USG has draft → verification → publish
- OPD has vitals → doctor → publish

## How we will use this pack
1. Treat these docs as the constitution.
2. Audit the current repo against these docs.
3. Remove junk, reconnect flows, and re-test end-to-end.
4. Only then add new features.
