# QA-Checklist.md

- [ ] MR unique and stable for patient
- [ ] SV unique per visit
- [ ] Service catalog imports/edits do not break old bills
- [ ] Receipt prints on A4 with correct duplicate layout
- [ ] USG flow enforces verification before publish
- [ ] OPD flow enforces finalize before publish
- [ ] Worklists filter correctly by status/date
- [ ] Reprint center works and logs version/actor/time
- [ ] Permissions prevent operators from verifying
- [ ] Audit log exists for all key events
- [ ] VPS deployment uses Caddy and backend bound to 127.0.0.1
- [ ] Health endpoints available (optional): `/health`
