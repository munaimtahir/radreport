# Brand Theme Quick Reference

## Using Brand Colors

```typescript
import { theme } from '../theme';

// In inline styles
<div style={{ color: theme.colors.brandBlue }} />
<div style={{ backgroundColor: theme.colors.brandOrangeSoft }} />

// Primary button
<button style={{ 
  backgroundColor: theme.colors.primary,
  color: 'white',
  borderRadius: theme.radius.base,
  padding: '10px 20px'
}} />
```

## Brand Components

```typescript
import { BrandLogo, BrandTitle, BrandHeader } from './ui/components/brand';

// Logo only
<BrandLogo size="sm" variant="full" />
<BrandLogo size="md" variant="icon" />

// Title only
<BrandTitle size="md" />

// Combined header
<BrandHeader 
  logoSize="lg" 
  titleSize="md" 
  layout="vertical" 
  align="center"
  onClick={() => navigate('/')}
/>
```

## Color Palette

| Color | Hex | Usage |
|-------|-----|-------|
| Brand Blue | `#0B5ED7` | Primary buttons, active nav, links |
| Brand Blue Dark | `#094BB8` | Hover states |
| Brand Blue Soft | `#E8F2FF` | Backgrounds, active states |
| Brand Orange | `#FF6B35` | Secondary buttons, accents |
| Brand Orange Dark | `#E65520` | Hover states |
| Brand Orange Soft | `#FFF0EB` | Backgrounds, highlights |

## Typography

```typescript
// Font family
fontFamily: theme.typography.fontFamily

// Sizes
fontSize: theme.typography.fontSize.sm  // 12px
fontSize: theme.typography.fontSize.base // 14px
fontSize: theme.typography.fontSize.md  // 16px
fontSize: theme.typography.fontSize.lg  // 18px

// Weights
fontWeight: theme.typography.fontWeight.normal   // 400
fontWeight: theme.typography.fontWeight.medium   // 500
fontWeight: theme.typography.fontWeight.semibold // 600
```

## Spacing

```typescript
padding: theme.spacing.sm   // 8px
padding: theme.spacing.base // 16px
padding: theme.spacing.lg   // 20px
gap: theme.spacing.md       // 12px
```

## Other Design Tokens

```typescript
// Border radius
borderRadius: theme.radius.base // 6px
borderRadius: theme.radius.md   // 8px

// Shadows
boxShadow: theme.shadows.base   // Standard card shadow
boxShadow: theme.shadows.md     // Modal shadow

// Transitions
transition: theme.transitions.fast // 0.15s ease
transition: theme.transitions.base // 0.2s ease
```

## Page Title Pattern

```typescript
import { useEffect } from 'react';

function MyPage() {
  useEffect(() => {
    document.title = "Page Name • Consultants Place Clinic";
    return () => {
      document.title = "Consultants Place Clinic";
    };
  }, []);
  
  // ...
}
```

## Button Variants

```typescript
import Button from './ui/components/Button';

<Button variant="primary">Primary Action</Button>    // Brand Blue
<Button variant="secondary">Secondary</Button>       // Brand Orange
<Button variant="success">Success</Button>           // Green
<Button variant="warning">Warning</Button>           // Yellow
<Button variant="danger">Danger</Button>             // Red
```

## Common Patterns

### Active Navigation Link
```typescript
<Link
  to="/path"
  style={{
    color: isActive ? theme.colors.brandBlue : theme.colors.textSecondary,
    backgroundColor: isActive ? theme.colors.brandBlueSoft : 'transparent',
    padding: '10px 12px',
    borderRadius: theme.radius.base,
    fontWeight: isActive ? theme.typography.fontWeight.medium : theme.typography.fontWeight.normal,
  }}
>
  Link Text
</Link>
```

### Hover Effect
```typescript
onMouseEnter={(e) => {
  e.currentTarget.style.backgroundColor = theme.colors.brandBlueDark;
}}
onMouseLeave={(e) => {
  e.currentTarget.style.backgroundColor = theme.colors.brandBlue;
}}
```

### Card with Brand Border
```typescript
<div style={{
  border: `2px solid ${theme.colors.brandBlueSoft}`,
  borderRadius: theme.radius.md,
  padding: theme.spacing.lg,
  boxShadow: theme.shadows.sm,
}}>
  Card Content
</div>
```

## Logo Asset Paths

```typescript
// Public directory (preferred for production)
const logoSrc = '/brand/Consultants_Place_Clinic_Logo_Transparent.png';

// Import from assets (alternative)
import logo from '@/assets/brand/Consultants_Place_Clinic_Logo_Transparent.png';
```

## Accessibility Notes

- ✅ Use brand blue for interactive elements (buttons, links)
- ✅ Use brand orange for accents and highlights
- ❌ Don't use orange for body text (contrast issue)
- ✅ Ensure focus states are visible (brand blue at low opacity)
- ✅ Maintain at least 4.5:1 contrast ratio for text

## Responsive Considerations

```typescript
// Sidebar logo - small on mobile/sidebar
<BrandLogo size="sm" variant="full" />

// Login page - large and prominent
<BrandHeader logoSize="lg" titleSize="md" layout="vertical" />

// Header bar - compact horizontal
<BrandHeader logoSize="sm" titleSize="sm" layout="horizontal" />
```
