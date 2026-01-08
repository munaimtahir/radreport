# Tests.md

## Smoke Tests (Must Pass Before v1)
### Reception
1. Create new patient → MR generated
2. Create visit → SV generated
3. Add services from catalog
4. Apply discount (fixed + percent)
5. Partial payment → due computed
6. Save & print receipt PDF
7. Reprint receipt and confirm version log

### Routing
8. Visit with USG → appears in USG worklist
9. Visit with OPD → appears in OPD worklist
10. Visit with both → appears in both, same SV

### USG
11. Operator saves draft
12. Submit for verification
13. Verifier returns with reason
14. Operator edits and resubmits
15. Verifier verifies
16. Publish generates PDF and locks report
17. Reprint shows correct version

### OPD
18. Operator enters vitals
19. Doctor finalizes prescription
20. Publish generates PDF and locks prescription
21. Reprint shows correct version

### Data Integrity
22. Change catalog rates → old receipts remain unchanged (snapshot works)
23. Audit log records major actions
