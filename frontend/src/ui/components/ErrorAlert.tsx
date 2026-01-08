import React from "react";

interface ErrorAlertProps {
  message: string;
  onDismiss?: () => void;
}

export default function ErrorAlert({ message, onDismiss }: ErrorAlertProps) {
  return (
    <div
      style={{
        padding: "12px 16px",
        backgroundColor: "#fee",
        border: "1px solid #fcc",
        borderRadius: 6,
        color: "#c33",
        marginBottom: 16,
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
      }}
    >
      <span>{message}</span>
      {onDismiss && (
        <button
          onClick={onDismiss}
          style={{
            background: "none",
            border: "none",
            color: "#c33",
            cursor: "pointer",
            fontSize: 18,
            padding: "0 8px",
          }}
        >
          ×
        </button>
      )}
    </div>
  );
}
