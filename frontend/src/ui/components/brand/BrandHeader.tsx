import React from 'react';
import BrandLogo, { BrandLogoProps } from './BrandLogo';
import BrandTitle, { BrandTitleProps } from './BrandTitle';

export interface BrandHeaderProps {
  logoSize?: BrandLogoProps['size'];
  titleSize?: BrandTitleProps['size'];
  layout?: 'vertical' | 'horizontal';
  align?: 'left' | 'center' | 'right';
  showTitle?: boolean;
  onClick?: () => void;
  style?: React.CSSProperties;
}

/**
 * BrandHeader Component
 * 
 * Combined logo + title for consistent branding
 * Used in login screens, app header, and print views
 */
export default function BrandHeader({
  logoSize = 'md',
  titleSize = 'md',
  layout = 'vertical',
  align = 'center',
  showTitle = true,
  onClick,
  style,
}: BrandHeaderProps) {
  const containerStyle: React.CSSProperties = {
    display: 'flex',
    flexDirection: layout === 'vertical' ? 'column' : 'row',
    alignItems: align === 'center' ? 'center' : align === 'left' ? 'flex-start' : 'flex-end',
    gap: layout === 'vertical' ? 16 : 12,
    cursor: onClick ? 'pointer' : 'default',
    ...style,
  };

  return (
    <div style={containerStyle} onClick={onClick}>
      <BrandLogo size={logoSize} variant="full" />
      {showTitle && <BrandTitle size={titleSize} />}
    </div>
  );
}
