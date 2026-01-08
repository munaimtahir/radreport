import React from "react";

interface PageHeaderProps {
  title: string;
  actions?: React.ReactNode;
  subtitle?: string;
}

export default function PageHeader({ title, actions, subtitle }: PageHeaderProps) {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: subtitle ? "flex-start" : "center",
        marginBottom: 24,
        paddingBottom: 16,
        borderBottom: "1px solid #e0e0e0",
      }}
    >
      <div>
        <h1 style={{ margin: 0, fontSize: 28, fontWeight: 600, color: "#333" }}>
          {title}
        </h1>
        {subtitle && (
          <div style={{ marginTop: 4, fontSize: 14, color: "#666" }}>
            {subtitle}
          </div>
        )}
      </div>
      {actions && (
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          {actions}
        </div>
      )}
    </div>
  );
}
