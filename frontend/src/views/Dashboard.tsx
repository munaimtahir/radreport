import React, { useEffect, useState } from "react";
import { useAuth } from "../ui/auth";
import { apiGet } from "../ui/api";
import { Link } from "react-router-dom";
import PageHeader from "../ui/components/PageHeader";

export default function Dashboard() {
  const { token } = useAuth();
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    Promise.all([
      apiGet("/patients/", token).catch(() => ({ count: 0 })),
      apiGet("/workflow/visits/?status=PUBLISHED", token).catch(() => ({ count: 0 })),
      apiGet("/templates/", token).catch(() => ({ count: 0 })),
    ]).then(([patients, published, templates]) => {
      setStats({
        patients: Array.isArray(patients) ? patients.length : patients.count || 0,
        published: Array.isArray(published) ? published.length : published.count || 0,
        templates: Array.isArray(templates) ? templates.length : templates.count || 0,
      });
      setLoading(false);
    });
  }, [token]);

  if (loading) {
    return (
      <div>
        <PageHeader title="Dashboard" />
        <div style={{ textAlign: "center", padding: 40, color: "#666" }}>Loading...</div>
      </div>
    );
  }

  return (
    <div>
      <PageHeader title="Dashboard" />
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 20 }}>
        <div style={{ border: "1px solid #e0e0e0", borderRadius: 8, padding: 20, background: "white", boxShadow: "0 1px 3px rgba(0,0,0,0.1)" }}>
          <h3 style={{ margin: "0 0 10px 0", color: "#666", fontSize: 14, fontWeight: 500 }}>Patients</h3>
          <div style={{ fontSize: 32, fontWeight: "bold", color: "#0B5ED7", marginBottom: 8 }}>{stats?.patients || 0}</div>
          <Link to="/patients" style={{ fontSize: 13, color: "#0B5ED7", textDecoration: "none", fontWeight: 500 }}>
            View all →
          </Link>
        </div>
        <div style={{ border: "1px solid #e0e0e0", borderRadius: 8, padding: 20, background: "white", boxShadow: "0 1px 3px rgba(0,0,0,0.1)" }}>
          <h3 style={{ margin: "0 0 10px 0", color: "#666", fontSize: 14, fontWeight: 500 }}>Final Reports</h3>
          <div style={{ fontSize: 32, fontWeight: "bold", color: "#28a745", marginBottom: 8 }}>{stats?.published || 0}</div>
          <Link to="/reports" style={{ fontSize: 13, color: "#0B5ED7", textDecoration: "none", fontWeight: 500 }}>
            View all →
          </Link>
        </div>
        <div style={{ border: "1px solid #e0e0e0", borderRadius: 8, padding: 20, background: "white", boxShadow: "0 1px 3px rgba(0,0,0,0.1)" }}>
          <h3 style={{ margin: "0 0 10px 0", color: "#666", fontSize: 14, fontWeight: 500 }}>Templates</h3>
          <div style={{ fontSize: 32, fontWeight: "bold", color: "#ffc107", marginBottom: 8 }}>{stats?.templates || 0}</div>
          <Link to="/templates" style={{ fontSize: 13, color: "#0B5ED7", textDecoration: "none", fontWeight: 500 }}>
            View all →
          </Link>
        </div>
      </div>
    </div>
  );
}
