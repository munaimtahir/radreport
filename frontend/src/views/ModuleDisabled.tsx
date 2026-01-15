import React from "react";
import { Link } from "react-router-dom";

interface ModuleDisabledProps {
  title?: string;
  message?: string;
}

export default function ModuleDisabled({ title = "Module disabled", message = "This module is disabled in this build." }: ModuleDisabledProps) {
  return (
    <div style={{ padding: 32, fontFamily: "system-ui" }}>
      <div
        style={{
          maxWidth: 520,
          margin: "0 auto",
          padding: 24,
          borderRadius: 8,
          border: "1px solid #e9e1b5",
          backgroundColor: "#fffaf0",
          color: "#7a5b00",
        }}
      >
        <h2 style={{ marginTop: 0 }}>{title}</h2>
        <p style={{ marginBottom: 16 }}>{message}</p>
        <Link to="/" style={{ color: "#0B5ED7", textDecoration: "none" }}>
          Return to dashboard
        </Link>
      </div>
    </div>
  );
}
