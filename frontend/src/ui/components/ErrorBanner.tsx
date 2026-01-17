import React from "react";

interface ErrorBannerProps {
  message: string;
  onDismiss?: () => void;
  actionLabel?: string;
  onAction?: () => void;
}

export default function ErrorBanner({ message, onDismiss, actionLabel, onAction }: ErrorBannerProps) {
  return (
    <div
      style={{
        padding: "12px 16px",
        backgroundColor: "#fff3f3",
        border: "1px solid #f2b8b8",
        borderRadius: 8,
        color: "#9f1d1d",
        marginBottom: 16,
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        gap: 12,
      }}
    >
      <span style={{ fontSize: 13 }}>{message}</span>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        {actionLabel && onAction && (
          <button
            onClick={onAction}
            style={{
              background: "#9f1d1d",
              color: "#fff",
              border: "none",
              borderRadius: 6,
              padding: "6px 10px",
              cursor: "pointer",
              fontSize: 12,
            }}
          >
            {actionLabel}
          </button>
        )}
        {onDismiss && (
          <button
            onClick={onDismiss}
            style={{
              background: "none",
              border: "none",
              color: "#9f1d1d",
              cursor: "pointer",
              fontSize: 18,
              padding: "0 6px",
            }}
          >
            ×
          </button>
        )}
      </div>
    </div>
  );
}
