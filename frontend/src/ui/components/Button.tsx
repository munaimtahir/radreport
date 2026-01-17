import React from "react";
import { theme } from "../../theme";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "success" | "warning" | "danger";
  children: React.ReactNode;
}

export default function Button({
  variant = "primary",
  children,
  style,
  ...props
}: ButtonProps) {
  const baseStyle: React.CSSProperties = {
    padding: "10px 20px",
    fontSize: 14,
    fontWeight: theme.typography.fontWeight.medium,
    border: "none",
    borderRadius: theme.radius.base,
    cursor: props.disabled ? "not-allowed" : "pointer",
    transition: theme.transitions.base,
    fontFamily: theme.typography.fontFamily,
    ...style,
  };

  const variantStyles: Record<string, React.CSSProperties> = {
    primary: {
      backgroundColor: props.disabled ? theme.colors.border : theme.colors.brandBlue,
      color: "white",
    },
    secondary: {
      backgroundColor: props.disabled ? theme.colors.border : theme.colors.brandOrange,
      color: "white",
    },
    success: {
      backgroundColor: props.disabled ? theme.colors.border : theme.colors.success,
      color: "white",
    },
    warning: {
      backgroundColor: props.disabled ? theme.colors.border : theme.colors.warning,
      color: theme.colors.textPrimary,
    },
    danger: {
      backgroundColor: props.disabled ? theme.colors.border : theme.colors.danger,
      color: "white",
    },
  };

  return (
    <button
      {...props}
      style={{ ...baseStyle, ...variantStyles[variant] }}
    >
      {children}
    </button>
  );
}
