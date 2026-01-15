import React from "react";
import { Link } from "react-router-dom";

export default function AccessDenied() {
  return (
    <div style={{ padding: 32, fontFamily: "system-ui" }}>
      <div
        style={{
          maxWidth: 520,
          margin: "0 auto",
          padding: 24,
          borderRadius: 8,
          border: "1px solid #f1c0c0",
          backgroundColor: "#fff5f5",
          color: "#8a1c1c",
        }}
      >
        <h2 style={{ marginTop: 0 }}>Access denied</h2>
        <p style={{ marginBottom: 16 }}>
          You do not have permission to access this page. Please contact an administrator if you believe this is an error.
        </p>
        <Link to="/" style={{ color: "#0B5ED7", textDecoration: "none" }}>
          Return to dashboard
        </Link>
      </div>
    </div>
  );
}
