# ID Format Comparison

## Quick Reference

### Patient Registration Number

| Aspect | Old Format | New Format |
|--------|-----------|------------|
| **Example** | `PRN000009` | `CCJ-26-0001` |
| **Pattern** | `PRN` + 6-digit number | `CCJ-YY-NNNN` |
| **Length** | 9 characters | 12 characters |
| **Reset Period** | Never (continuous) | Yearly |
| **Readability** | Low | High |
| **Date Context** | No | Yes (year) |

**Format Breakdown:**
```
CCJ-26-0001
│   │  │
│   │  └─── Sequential number (4 digits, resets yearly)
│   └────── Year (2 digits)
└────────── Clinic Code (Consultant Clinic Jaranwala)
```

### Visit ID

| Aspect | Old Format | New Format |
|--------|-----------|------------|
| **Example** | `SV20260120-0003` | `2601-001` |
| **Pattern** | `SV` + YYYYMMDD + 4-digit | `YYMM-NNN` |
| **Length** | 16 characters | 8 characters |
| **Reset Period** | Daily | Monthly |
| **Readability** | Medium | High |
| **Date Context** | Full date | Year + Month |

**Format Breakdown:**
```
2601-001
│││  │
│││  └─── Sequential number (3 digits, resets monthly)
││└────── Month (2 digits)
│└─────── Year (2 digits)
```

## Examples Throughout Time

### Patient Registration Numbers

```
2026:
  CCJ-26-0001  (First patient of 2026)
  CCJ-26-0031  (31st patient of 2026)
  CCJ-26-0100  (100th patient of 2026)
  CCJ-26-9999  (Last possible patient of 2026)

2027:
  CCJ-27-0001  (First patient of 2027 - counter resets)
  CCJ-27-0002  (Second patient of 2027)
```

### Visit IDs

```
January 2026:
  2601-001  (First visit of January)
  2601-023  (23rd visit of January)
  2601-999  (Last possible visit of January)

February 2026:
  2602-001  (First visit of February - counter resets)
  2602-002  (Second visit of February)

December 2026:
  2612-001  (First visit of December)

January 2027:
  2701-001  (First visit of January 2027)
```

## Benefits of New Format

### Patient Registration Number (CCJ-26-0001)
✅ **Clinic Identification**: "CCJ" clearly identifies Consultant Clinic Jaranwala
✅ **Year Context**: Easy to identify when patient was registered
✅ **Manageable Numbers**: Resets yearly, keeping numbers small
✅ **Human-Readable**: Easier to read and communicate over phone
✅ **Professional**: Looks more organized and systematic

### Visit ID (2601-001)
✅ **Compact**: 50% shorter than old format (8 vs 16 characters)
✅ **Time Context**: Year and month immediately visible
✅ **Monthly Reset**: Keeps sequential numbers small and manageable
✅ **Easy to Sort**: Natural sorting works correctly
✅ **Quick Reference**: Easy to identify visit month at a glance

## Migration Notes

- ✅ **No database migration required**
- ✅ **Backward compatible** - old records remain valid
- ✅ **Automatic** - new format applies to all new records
- ✅ **No frontend changes needed**
- ✅ **Existing data unaffected**

## Usage in Application

### Where Patient Reg No Appears:
- Patient registration form
- Patient search results
- Patient profile header
- Receipts and invoices
- Medical reports (USG, OPD)
- Admin interface

### Where Visit ID Appears:
- Service registration confirmation
- Visit/service list
- Receipts (as visit reference)
- Reports (as visit reference)
- Billing records
- Admin interface

All these locations will automatically display the new format for new records.
