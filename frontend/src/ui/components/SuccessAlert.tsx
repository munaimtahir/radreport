import React from "react";

interface SuccessAlertProps {
  message: string;
  onDismiss?: () => void;
}

export default function SuccessAlert({ message, onDismiss }: SuccessAlertProps) {
  return (
    <div
      style={{
        padding: "12px 16px",
        backgroundColor: "#efe",
        border: "1px solid #cfc",
        borderRadius: 6,
        color: "#3c3",
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
            color: "#3c3",
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
