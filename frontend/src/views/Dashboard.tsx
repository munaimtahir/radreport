import React, { useEffect, useState } from "react";
import { useAuth } from "../ui/auth";
import { apiGet } from "../ui/api";
import { Link } from "react-router-dom";

export default function Dashboard() {
  const { token } = useAuth();
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    Promise.all([
      apiGet("/patients/", token).catch(() => ({ count: 0 })),
      apiGet("/studies/?status=registered", token).catch(() => ({ count: 0 })),
      apiGet("/studies/?status=draft", token).catch(() => ({ count: 0 })),
      apiGet("/studies/?status=final", token).catch(() => ({ count: 0 })),
      apiGet("/templates/", token).catch(() => ({ count: 0 })),
    ]).then(([patients, registered, draft, final, templates]) => {
      setStats({
        patients: Array.isArray(patients) ? patients.length : patients.count || 0,
        registered: Array.isArray(registered) ? registered.length : registered.count || 0,
        draft: Array.isArray(draft) ? draft.length : draft.count || 0,
        final: Array.isArray(final) ? final.length : final.count || 0,
        templates: Array.isArray(templates) ? templates.length : templates.count || 0,
      });
      setLoading(false);
    });
  }, [token]);

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <h1>Dashboard</h1>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 20, marginTop: 20 }}>
        <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 20, background: "white" }}>
          <h3 style={{ margin: "0 0 10px 0", color: "#666" }}>Patients</h3>
          <div style={{ fontSize: 32, fontWeight: "bold", color: "#007bff" }}>{stats?.patients || 0}</div>
          <Link to="/patients" style={{ fontSize: 14, color: "#007bff", textDecoration: "none" }}>
            View all →
          </Link>
        </div>
        <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 20, background: "white" }}>
          <h3 style={{ margin: "0 0 10px 0", color: "#666" }}>Registered Studies</h3>
          <div style={{ fontSize: 32, fontWeight: "bold", color: "#6c757d" }}>{stats?.registered || 0}</div>
          <Link to="/studies" style={{ fontSize: 14, color: "#007bff", textDecoration: "none" }}>
            View all →
          </Link>
        </div>
        <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 20, background: "white" }}>
          <h3 style={{ margin: "0 0 10px 0", color: "#666" }}>Draft Reports</h3>
          <div style={{ fontSize: 32, fontWeight: "bold", color: "#17a2b8" }}>{stats?.draft || 0}</div>
          <Link to="/studies" style={{ fontSize: 14, color: "#007bff", textDecoration: "none" }}>
            View all →
          </Link>
        </div>
        <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 20, background: "white" }}>
          <h3 style={{ margin: "0 0 10px 0", color: "#666" }}>Final Reports</h3>
          <div style={{ fontSize: 32, fontWeight: "bold", color: "#28a745" }}>{stats?.final || 0}</div>
          <Link to="/studies" style={{ fontSize: 14, color: "#007bff", textDecoration: "none" }}>
            View all →
          </Link>
        </div>
        <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 20, background: "white" }}>
          <h3 style={{ margin: "0 0 10px 0", color: "#666" }}>Templates</h3>
          <div style={{ fontSize: 32, fontWeight: "bold", color: "#ffc107" }}>{stats?.templates || 0}</div>
          <Link to="/templates" style={{ fontSize: 14, color: "#007bff", textDecoration: "none" }}>
            View all →
          </Link>
        </div>
      </div>
    </div>
  );
}
