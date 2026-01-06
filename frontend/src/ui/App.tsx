import React from "react";
import { Routes, Route, Navigate, Link } from "react-router-dom";
import { useAuth, AuthProvider } from "./auth";
import Login from "../views/Login";
import Dashboard from "../views/Dashboard";
import Patients from "../views/Patients";
import Studies from "../views/Studies";
import Templates from "../views/Templates";
import ReportEditor from "../views/ReportEditor";

function Shell() {
  const { token, logout } = useAuth();
  if (!token) return <Navigate to="/login" replace />;

  return (
    <div style={{ display: "flex", minHeight: "100vh", fontFamily: "system-ui" }}>
      <aside style={{ width: 240, padding: 16, borderRight: "1px solid #ddd" }}>
        <h2 style={{ marginTop: 0 }}>RIMS</h2>
        <nav style={{ display: "grid", gap: 8 }}>
          <Link to="/">Dashboard</Link>
          <Link to="/patients">Patients</Link>
          <Link to="/studies">Studies</Link>
          <Link to="/templates">Templates</Link>
        </nav>
        <button style={{ marginTop: 16 }} onClick={logout}>Logout</button>
      </aside>
      <main style={{ flex: 1, padding: 20 }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/patients" element={<Patients />} />
          <Route path="/studies" element={<Studies />} />
          <Route path="/templates" element={<Templates />} />
          <Route path="/reports/:reportId/edit" element={<ReportEditor />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/*" element={<Shell />} />
      </Routes>
    </AuthProvider>
  );
}
