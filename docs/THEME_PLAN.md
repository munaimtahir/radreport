# Theme Plan (Minimal Design System)

## Design goals
- Clean, calm medical UI with soft backgrounds and a teal accent.
- Consistent spacing, card layout, and form controls.
- Minimal changes that can be applied across existing inline-styled views.

## Colors
- **Background:** `#F6F8FA` (soft gray)
- **Surface/Card:** `#FFFFFF`
- **Border:** `#E2E8F0`
- **Primary / Teal Accent:** `#0F766E`
- **Primary Hover:** `#115E59`
- **Text (primary):** `#0F172A`
- **Text (muted):** `#64748B`
- **Success:** `#16A34A`
- **Warning:** `#D97706`
- **Error:** `#DC2626`

## Typography
- Base font: `Inter`, fallback `system-ui`.
- Heading sizes:
  - H1: 24–28px, weight 600
  - H2: 18–20px, weight 600
  - Body: 14–16px, weight 400

## Spacing + layout
- Base spacing unit: 8px.
- Page padding: 24px.
- Cards: 16–20px padding, 8px radius, 1px border.
- Table rows: 12px vertical padding.

## Components
- **Buttons**
  - Primary: teal background, white text, 8px radius.
  - Secondary: white background, teal border, teal text.
  - Disabled: `#CBD5E1` background, `#94A3B8` text.

- **Inputs**
  - 1px solid `#E2E8F0` border, 8px radius.
  - Focus ring: teal outline (`box-shadow: 0 0 0 2px rgba(15,118,110,0.2)`).

- **Cards**
  - White background, subtle shadow (`0 1px 2px rgba(0,0,0,0.06)`), 1px border.

## Logo placement
- Top-left in sidebar with the wordmark “RIMS”.
- Use a 32px height mark + text to keep layout simple.

## Where to implement
- **Preferred approach (no Tailwind detected):**
  - Create a CSS variables file (e.g., `frontend/src/ui/theme.css`) and import it in `frontend/src/main.tsx`.
  - Replace inline styles in `frontend/src/views/*` with shared class names.
  - Add a small component library in `frontend/src/ui/` (e.g., `Button`, `Card`, `Input`) to reduce duplication.

- **Optional alternative:**
  - Introduce Tailwind only if the team wants utility classes; otherwise keep CSS variables + small components.

> This plan focuses on minimal refactors: define a theme once, then replace inline styles page by page.
