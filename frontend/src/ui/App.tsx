import React from "react";
import { Routes, Route, Navigate, Link } from "react-router-dom";
import { useAuth, AuthProvider } from "./auth";
import Login from "../views/Login";
import Dashboard from "../views/Dashboard";
import Patients from "../views/Patients";
import Studies from "../views/Studies";
import Templates from "../views/Templates";
import ReportEditor from "../views/ReportEditor";
import FrontDeskIntake from "../views/FrontDeskIntake";
import ReceiptSettings from "../views/ReceiptSettings";
import RegistrationPage from "../views/RegistrationPage";
import USGWorklistPage from "../views/USGWorklistPage";
import OPDVitalsWorklistPage from "../views/OPDVitalsWorklistPage";
import ConsultantWorklistPage from "../views/ConsultantWorklistPage";
import VerificationWorklistPage from "../views/VerificationWorklistPage";
import FinalReportsPage from "../views/FinalReportsPage";

function Shell() {
  const { token, logout } = useAuth();
  if (!token) return <Navigate to="/login" replace />;

  return (
    <div style={{ display: "flex", minHeight: "100vh", fontFamily: "system-ui" }}>
      <aside style={{ width: 240, padding: 16, borderRight: "1px solid #ddd" }}>
        <h2 style={{ marginTop: 0 }}>RIMS</h2>
        <nav style={{ display: "grid", gap: 8 }}>
          <Link to="/">Dashboard</Link>
          <div style={{ marginTop: 8, paddingTop: 8, borderTop: "1px solid #ddd" }}>
            <strong style={{ fontSize: 12, color: "#666" }}>WORKFLOW</strong>
          </div>
          <Link to="/registration">Registration</Link>
          <Link to="/worklists/usg">USG Worklist</Link>
          <Link to="/worklists/opd-vitals">OPD Vitals</Link>
          <Link to="/worklists/consultant">Consultant</Link>
          <Link to="/worklists/verification">Verification</Link>
          <Link to="/reports">Final Reports</Link>
          <div style={{ marginTop: 8, paddingTop: 8, borderTop: "1px solid #ddd" }}>
            <strong style={{ fontSize: 12, color: "#666" }}>LEGACY</strong>
          </div>
          <Link to="/intake">Front Desk Intake</Link>
          <Link to="/patients">Patients</Link>
          <Link to="/studies">Studies</Link>
          <Link to="/templates">Templates</Link>
          <Link to="/receipt-settings">Receipt Settings</Link>
        </nav>
        <button style={{ marginTop: 16 }} onClick={logout}>Logout</button>
      </aside>
      <main style={{ flex: 1, padding: 20 }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          {/* Workflow Routes */}
          <Route path="/registration" element={<RegistrationPage />} />
          <Route path="/worklists/usg" element={<USGWorklistPage />} />
          <Route path="/worklists/opd-vitals" element={<OPDVitalsWorklistPage />} />
          <Route path="/worklists/consultant" element={<ConsultantWorklistPage />} />
          <Route path="/worklists/verification" element={<VerificationWorklistPage />} />
          <Route path="/reports" element={<FinalReportsPage />} />
          {/* Legacy Routes */}
          <Route path="/intake" element={<FrontDeskIntake />} />
          <Route path="/patients" element={<Patients />} />
          <Route path="/studies" element={<Studies />} />
          <Route path="/templates" element={<Templates />} />
          <Route path="/receipt-settings" element={<ReceiptSettings />} />
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
