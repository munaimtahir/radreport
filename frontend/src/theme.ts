/**
 * Consultants Place Clinic - Brand Theme
 * 
 * Design tokens extracted from the official clinic logo
 */

export const theme = {
  // Brand Colors - Primary
  colors: {
    // Brand Blue (from logo 'C') - PRIMARY INTERACTIVE COLOR
    // Use for: Main buttons, service chips, active states, selected items
    brandBlue: '#0B5ED7',
    brandBlueDark: '#094BB8',
    brandBlueLight: '#3D80E0',
    brandBlueSoft: '#E8F2FF',
    
    // Brand Orange (from logo 'P') - ACCENT ONLY
    // Use for: Warnings, secondary emphasis, small badges/dots/icons
    // AVOID: Full-width UI elements, primary buttons, service pills
    brandOrange: '#FF6B35',
    brandOrangeDark: '#E65520',
    brandOrangeLight: '#FF8A5C',
    brandOrangeSoft: '#FFF0EB',
    
    // Semantic Colors
    primary: '#0B5ED7',
    secondary: '#FF6B35',
    success: '#28a745',
    warning: '#ffc107',
    danger: '#dc3545',
    
    // Neutrals
    textPrimary: '#333333',
    textSecondary: '#666666',
    textTertiary: '#999999',
    border: '#e0e0e0',
    borderLight: '#f0f0f0',
    background: '#ffffff',
    backgroundGray: '#fafafa',
    backgroundLight: '#f5f5f5',
  },
  
  // Typography
  typography: {
    fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    fontSize: {
      xs: 11,
      sm: 12,
      base: 14,
      md: 16,
      lg: 18,
      xl: 24,
      xxl: 28,
      xxxl: 32,
    },
    fontWeight: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
  },
  
  // Spacing
  spacing: {
    xs: 4,
    sm: 8,
    md: 12,
    base: 16,
    lg: 20,
    xl: 24,
    xxl: 32,
    xxxl: 40,
  },
  
  // Border Radius
  radius: {
    sm: 4,
    base: 6,
    md: 8,
    lg: 12,
    full: 9999,
  },
  
  // Shadows
  shadows: {
    sm: '0 1px 3px rgba(0,0,0,0.08)',
    base: '0 2px 8px rgba(0,0,0,0.1)',
    md: '0 4px 12px rgba(0,0,0,0.12)',
    lg: '0 8px 24px rgba(0,0,0,0.15)',
  },
  
  // Transitions
  transitions: {
    fast: '0.15s ease',
    base: '0.2s ease',
    slow: '0.3s ease',
  },
} as const;

export type Theme = typeof theme;

// Helper function to create CSS variables from theme
export const createCssVariables = () => {
  return {
    '--color-brand-blue': theme.colors.brandBlue,
    '--color-brand-blue-dark': theme.colors.brandBlueDark,
    '--color-brand-blue-light': theme.colors.brandBlueLight,
    '--color-brand-blue-soft': theme.colors.brandBlueSoft,
    '--color-brand-orange': theme.colors.brandOrange,
    '--color-brand-orange-dark': theme.colors.brandOrangeDark,
    '--color-brand-orange-light': theme.colors.brandOrangeLight,
    '--color-brand-orange-soft': theme.colors.brandOrangeSoft,
    '--color-primary': theme.colors.primary,
    '--color-secondary': theme.colors.secondary,
    '--font-family': theme.typography.fontFamily,
  } as React.CSSProperties;
};
