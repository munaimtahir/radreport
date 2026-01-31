import React from "react";
import { theme } from "../../theme";

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

export default function Modal({ isOpen, onClose, title, children }: ModalProps) {
  if (!isOpen) return null;

  return (
    <div style={{
      position: "fixed",
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: "rgba(0,0,0,0.5)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      zIndex: 1000,
    }}>
      <div style={{
        backgroundColor: "white",
        borderRadius: theme.radius.lg,
        padding: 24,
        width: "100%",
        maxWidth: 600,
        boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
        display: "flex",
        flexDirection: "column",
        gap: 16,
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h2 style={{ fontSize: 20, margin: 0, fontWeight: theme.typography.fontWeight.semibold }}>{title}</h2>
          <button onClick={onClose} style={{
            border: "none",
            background: "transparent",
            cursor: "pointer",
            fontSize: 24,
            lineHeight: 1,
            color: theme.colors.textSecondary,
          }}>&times;</button>
        </div>
        <div>
          {children}
        </div>
      </div>
    </div>
  );
}
