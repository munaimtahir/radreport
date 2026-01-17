import React, { useState } from "react";
import { theme } from "../../theme";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "success" | "warning" | "danger" | "accent";
  children: React.ReactNode;
}

export default function Button({
  variant = "primary",
  children,
  style,
  ...props
}: ButtonProps) {
  const [isHovered, setIsHovered] = useState(false);

  const baseStyle: React.CSSProperties = {
    padding: "10px 20px",
    fontSize: 14,
    fontWeight: theme.typography.fontWeight.medium,
    borderRadius: theme.radius.base,
    cursor: props.disabled ? "not-allowed" : "pointer",
    transition: theme.transitions.base,
    fontFamily: theme.typography.fontFamily,
    ...style,
  };

  const variantStyles: Record<string, React.CSSProperties> = {
    primary: {
      backgroundColor: props.disabled 
        ? theme.colors.border 
        : isHovered 
          ? theme.colors.brandBlueDark 
          : theme.colors.brandBlue,
      color: "white",
      border: "none",
    },
    secondary: {
      backgroundColor: props.disabled 
        ? theme.colors.borderLight 
        : isHovered 
          ? theme.colors.brandBlueSoft 
          : "transparent",
      color: props.disabled 
        ? theme.colors.textTertiary 
        : isHovered 
          ? theme.colors.brandBlueDark 
          : theme.colors.brandBlue,
      border: `1px solid ${props.disabled ? theme.colors.border : theme.colors.brandBlue}`,
    },
    accent: {
      backgroundColor: props.disabled 
        ? theme.colors.borderLight 
        : isHovered 
          ? theme.colors.brandOrangeSoft 
          : "transparent",
      color: props.disabled 
        ? theme.colors.textTertiary 
        : isHovered 
          ? theme.colors.brandOrangeDark 
          : theme.colors.brandOrange,
      border: `1px solid ${props.disabled ? theme.colors.border : theme.colors.brandOrange}`,
    },
    success: {
      backgroundColor: props.disabled ? theme.colors.border : theme.colors.success,
      color: "white",
      border: "none",
    },
    warning: {
      backgroundColor: props.disabled ? theme.colors.border : theme.colors.warning,
      color: theme.colors.textPrimary,
      border: "none",
    },
    danger: {
      backgroundColor: props.disabled ? theme.colors.border : theme.colors.danger,
      color: "white",
      border: "none",
    },
  };

  return (
    <button
      {...props}
      onMouseEnter={(e) => {
        setIsHovered(true);
        props.onMouseEnter?.(e);
      }}
      onMouseLeave={(e) => {
        setIsHovered(false);
        props.onMouseLeave?.(e);
      }}
      style={{ ...baseStyle, ...variantStyles[variant] }}
    >
      {children}
    </button>
  );
}
