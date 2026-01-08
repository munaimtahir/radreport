import React from "react";

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
    fontWeight: 500,
    border: "none",
    borderRadius: 6,
    cursor: props.disabled ? "not-allowed" : "pointer",
    transition: "background-color 0.2s",
    ...style,
  };

  const variantStyles: Record<string, React.CSSProperties> = {
    primary: {
      backgroundColor: props.disabled ? "#ccc" : "#0B5ED7",
      color: "white",
    },
    secondary: {
      backgroundColor: props.disabled ? "#ccc" : "#6c757d",
      color: "white",
    },
    success: {
      backgroundColor: props.disabled ? "#ccc" : "#28a745",
      color: "white",
    },
    warning: {
      backgroundColor: props.disabled ? "#ccc" : "#ffc107",
      color: "#000",
    },
    danger: {
      backgroundColor: props.disabled ? "#ccc" : "#dc3545",
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
