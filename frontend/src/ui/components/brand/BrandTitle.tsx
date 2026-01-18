import React from 'react';
import { theme } from '../../../theme';

export interface BrandTitleProps {
  size?: 'sm' | 'md' | 'lg';
  style?: React.CSSProperties;
}

/**
 * BrandTitle Component
 * 
 * Displays "Consultants Place Clinic" with brand styling
 * - "Consultants" in brand blue
 * - "Place" and "Clinic" in brand orange
 * - Dots between words matching brand colors
 */
export default function BrandTitle({ size = 'md', style }: BrandTitleProps) {
  const sizeMap = {
    sm: { fontSize: 14, dotSize: 3, gap: 6 },
    md: { fontSize: 18, dotSize: 4, gap: 8 },
    lg: { fontSize: 24, dotSize: 5, gap: 10 },
  };

  const { fontSize, dotSize, gap } = sizeMap[size];

  const containerStyle: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: gap,
    fontFamily: theme.typography.fontFamily,
    fontWeight: theme.typography.fontWeight.semibold,
    lineHeight: 1.2,
    flexWrap: 'wrap',
    ...style,
  };

  const dotStyle: React.CSSProperties = {
    width: dotSize,
    height: dotSize,
    borderRadius: '50%',
    flexShrink: 0,
  };

  return (
    <div style={containerStyle}>
      <span style={{ color: theme.colors.brandBlue, fontSize }}>
        Consultants
      </span>
      <span style={{ ...dotStyle, backgroundColor: theme.colors.brandBlue }} />
      <span style={{ color: theme.colors.brandOrange, fontSize }}>
        Place
      </span>
      <span style={{ ...dotStyle, backgroundColor: theme.colors.brandOrange }} />
      <span style={{ color: theme.colors.brandOrange, fontSize }}>
        Clinic
      </span>
    </div>
  );
}
