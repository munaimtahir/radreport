import React from 'react';
import { theme } from '../../../theme';

export interface BrandLogoProps {
  variant?: 'icon' | 'full';
  size?: 'sm' | 'md' | 'lg';
  onClick?: () => void;
  style?: React.CSSProperties;
}

/**
 * BrandLogo Component
 * 
 * Displays the Consultants Place Clinic logo
 * - 'full' variant shows logo with text
 * - 'icon' variant shows logo mark only (cropped)
 * 
 * Note: Logo files should be placed in /src/assets/brand/
 * - Consultants_Place_Clinic_Logo_Transparent.png (preferred)
 * - Consultants_Place_Clinic_Logo.png (fallback)
 */
export default function BrandLogo({ 
  variant = 'full', 
  size = 'md',
  onClick,
  style 
}: BrandLogoProps) {
  const sizeMap = {
    sm: { width: 40, height: 40 },
    md: { width: 80, height: 80 },
    lg: { width: 120, height: 120 },
  };

  const dimensions = sizeMap[size];

  // Try to import logo - will fallback gracefully if not available
  let logoSrc = '';
  try {
    // In production, this will resolve to the actual image path
    // For now, we'll use a placeholder that can be replaced
    logoSrc = '/brand/Consultants_Place_Clinic_Logo_Transparent.png';
  } catch {
    // Logo not yet added - component will show placeholder
  }

  const containerStyle: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
    cursor: onClick ? 'pointer' : 'default',
    ...style,
  };

  const imgStyle: React.CSSProperties = {
    width: dimensions.width,
    height: dimensions.height,
    objectFit: 'contain',
    display: 'block',
  };

  // If icon variant, we crop to show just the CP mark
  if (variant === 'icon') {
    imgStyle.objectFit = 'cover';
    imgStyle.objectPosition = 'center top';
  }

  return (
    <div style={containerStyle} onClick={onClick}>
      <img
        src={logoSrc}
        alt="Consultants Place Clinic"
        style={imgStyle}
        onError={(e) => {
          // If logo fails to load, show a styled placeholder
          const target = e.target as HTMLImageElement;
          target.style.display = 'none';
          const parent = target.parentElement;
          if (parent && !parent.querySelector('.logo-fallback')) {
            const fallback = document.createElement('div');
            fallback.className = 'logo-fallback';
            fallback.style.cssText = `
              width: ${dimensions.width}px;
              height: ${dimensions.height}px;
              display: flex;
              align-items: center;
              justify-content: center;
              background: linear-gradient(135deg, ${theme.colors.brandBlue} 0%, ${theme.colors.brandOrange} 100%);
              border-radius: ${theme.radius.base}px;
              color: white;
              font-weight: ${theme.typography.fontWeight.bold};
              font-size: ${size === 'sm' ? 14 : size === 'md' ? 20 : 28}px;
            `;
            fallback.textContent = 'CP';
            parent.appendChild(fallback);
          }
        }}
      />
    </div>
  );
}
