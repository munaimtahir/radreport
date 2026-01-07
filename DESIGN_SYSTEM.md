# Consultants Place Clinic — Design System (v1)

## Purpose
A single, consistent visual system for:
- Frontend UI
- A4 receipts (duplicated on one page)
- Reports / PDFs

This document is the source of truth.

---

## Brand Identity

### Brand Name
Consultants Place Clinic

### Logo
Use the provided “CP” logo lockup.
- Never stretch
- Keep generous whitespace around the logo (at least 16px on screen; 6–10mm on print)

---

## Color Palette (Core)

> Note: exact hex values can be adjusted after sampling the final logo file, but these are the initial locked defaults.

- Primary Blue: #0B5ED7
- Accent Orange: #F39C12
- Text (Dark): #2E2E2E
- Muted Grey: #9AA0A6
- Border Grey: #E5E7EB
- Background: #FFFFFF

Usage rules:
- Blue: headings, clinic name, table headers
- Orange: totals, key actions, highlights
- Dark text: body text
- Grey: meta info, labels, separator lines, footer

Avoid gradients. Avoid heavy shadows.

---

## Typography

### Preferred Font (UI + PDF)
- Inter (preferred), Roboto (acceptable), Arial fallback

Frontend stack:
Inter, Roboto, Arial, sans-serif

Print/PDF:
Use a clean sans-serif (Inter/Roboto if embedded; otherwise Arial/Helvetica).

Font weights:
- Title: Bold
- Section headings: Medium/Semibold
- Body: Regular
- Meta/labels: Regular
- Footer: Regular, small, grey

---

## Spacing & Layout Principles

- Clean whitespace, low clutter
- Light borders instead of heavy boxes
- Use consistent padding:
  - UI cards: 16–20px
  - Print blocks: 8–12mm equivalents
- Keep alignment strict (left for text, right for numeric amounts)

---

## Receipt (A4) — Locked Requirements

### Paper
- A4 Portrait

### Duplicate Receipt
- Two identical receipts printed on the same A4 page:
  - Top half: Patient copy
  - Bottom half: Office copy

Only difference between copies:
- Copy label:
  - Top: “Patient copy”
  - Bottom: “Office copy”

Separator between copies:
- Thin dotted horizontal line
- Optional subtle scissors icon (grey)

### Receipt Header (per copy)
- Logo
- Clinic name: “Consultants Place Clinic”
- Optional tagline (can be configured later)

### Receipt Meta (per copy)
- Receipt No (format: YYMM-001)
- Date/Time
- MR No (if available)
- Patient Name, Age/Gender, Mobile (optional)
- Consultant (optional)

### Services Table (per copy)
Columns:
- Service/Test
- Qty
- Rate
- Amount

Table rules:
- Header row in Primary Blue
- Amount column right-aligned
- Total line highlighted (Accent Orange)

### Payment Summary (per copy)
Right-aligned:
- Subtotal
- Discount (if any)
- Total Payable (orange + bold)
- Paid
- Balance

### Footer (per copy) — Locked Text
Adjust Excel Labs, Near Arman Pan Shop Faisalabad Road Jaranwala
For information/Appointment: Tel: 041 4313 777 | WhatsApp: 0322 7972 958

Footer style:
- Small font
- Center aligned
- Light grey
- Minimal spacing

---

## Frontend UI (High-level)
- White background
- Card-based layout with subtle borders
- Primary button: Blue
- Confirm/Pay/Total emphasis: Orange
- Destructive/Cancel: Grey
- No flashy imagery or busy backgrounds
