import React, { useEffect, useState } from "react";
import { Routes, Route, Navigate, Link, useLocation } from "react-router-dom";
import { useAuth, AuthProvider } from "./auth";
import { apiGet } from "./api";
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
import Footer from "./components/Footer";

function Shell() {
  const { token, logout } = useAuth();
  const location = useLocation();
  const [logoUrl, setLogoUrl] = useState<string | null>(null);

  useEffect(() => {
    if (token) {
      // Try to fetch logo from receipt settings
      apiGet("/receipt-settings/", token)
        .then((data: any) => {
          if (data?.logo_image_url) {
            setLogoUrl(data.logo_image_url);
          }
        })
        .catch(() => {
          // Logo not available, continue without it
        });
    }
  }, [token]);

  if (!token) return <Navigate to="/login" replace />;

  return (
    <div style={{ display: "flex", minHeight: "100vh", fontFamily: "system-ui", flexDirection: "column" }}>
      <div style={{ display: "flex", flex: 1, minHeight: 0 }}>
        <aside
          style={{
            width: 240,
            padding: 20,
            borderRight: "1px solid #e0e0e0",
            backgroundColor: "#fafafa",
            display: "flex",
            flexDirection: "column",
          }}
        >
          <div style={{ marginBottom: 24 }}>
            {logoUrl ? (
              <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
                <img
                  src={logoUrl}
                  alt="Logo"
                  style={{ width: 48, height: 48, objectFit: "contain" }}
                />
                <h2 style={{ margin: 0, fontSize: 18, fontWeight: 600, color: "#333" }}>
                  Consultant Place Clinics
                </h2>
              </div>
            ) : (
              <h2 style={{ margin: 0, fontSize: 18, fontWeight: 600, color: "#333" }}>
                Consultant Place Clinics
              </h2>
            )}
          </div>
          <nav style={{ display: "flex", flexDirection: "column", gap: 4, flex: 1 }}>
            <Link
              to="/"
              style={{
                padding: "10px 12px",
                textDecoration: "none",
                color: location.pathname === "/" ? "#0B5ED7" : "#555",
                backgroundColor: location.pathname === "/" ? "#f0f7ff" : "transparent",
                borderRadius: 6,
                fontSize: 14,
                fontWeight: location.pathname === "/" ? 500 : 400,
              }}
            >
              Dashboard
            </Link>
            <div style={{ marginTop: 12, paddingTop: 12, borderTop: "1px solid #e0e0e0" }}>
              <div style={{ fontSize: 11, color: "#999", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 8 }}>
                WORKFLOW
              </div>
            </div>
            <Link
              to="/registration"
              style={{
                padding: "10px 12px",
                textDecoration: "none",
                color: location.pathname === "/registration" ? "#0B5ED7" : "#555",
                backgroundColor: location.pathname === "/registration" ? "#f0f7ff" : "transparent",
                borderRadius: 6,
                fontSize: 14,
                fontWeight: location.pathname === "/registration" ? 500 : 400,
              }}
            >
              Registration
            </Link>
            <Link
              to="/worklists/usg"
              style={{
                padding: "10px 12px",
                textDecoration: "none",
                color: location.pathname === "/worklists/usg" ? "#0B5ED7" : "#555",
                backgroundColor: location.pathname === "/worklists/usg" ? "#f0f7ff" : "transparent",
                borderRadius: 6,
                fontSize: 14,
                fontWeight: location.pathname === "/worklists/usg" ? 500 : 400,
              }}
            >
              USG Worklist
            </Link>
            <Link
              to="/worklists/opd-vitals"
              style={{
                padding: "10px 12px",
                textDecoration: "none",
                color: location.pathname === "/worklists/opd-vitals" ? "#0B5ED7" : "#555",
                backgroundColor: location.pathname === "/worklists/opd-vitals" ? "#f0f7ff" : "transparent",
                borderRadius: 6,
                fontSize: 14,
                fontWeight: location.pathname === "/worklists/opd-vitals" ? 500 : 400,
              }}
            >
              OPD Vitals
            </Link>
            <Link
              to="/worklists/consultant"
              style={{
                padding: "10px 12px",
                textDecoration: "none",
                color: location.pathname === "/worklists/consultant" ? "#0B5ED7" : "#555",
                backgroundColor: location.pathname === "/worklists/consultant" ? "#f0f7ff" : "transparent",
                borderRadius: 6,
                fontSize: 14,
                fontWeight: location.pathname === "/worklists/consultant" ? 500 : 400,
              }}
            >
              Consultant
            </Link>
            <Link
              to="/worklists/verification"
              style={{
                padding: "10px 12px",
                textDecoration: "none",
                color: location.pathname === "/worklists/verification" ? "#0B5ED7" : "#555",
                backgroundColor: location.pathname === "/worklists/verification" ? "#f0f7ff" : "transparent",
                borderRadius: 6,
                fontSize: 14,
                fontWeight: location.pathname === "/worklists/verification" ? 500 : 400,
              }}
            >
              Verification
            </Link>
            <Link
              to="/reports"
              style={{
                padding: "10px 12px",
                textDecoration: "none",
                color: location.pathname === "/reports" ? "#0B5ED7" : "#555",
                backgroundColor: location.pathname === "/reports" ? "#f0f7ff" : "transparent",
                borderRadius: 6,
                fontSize: 14,
                fontWeight: location.pathname === "/reports" ? 500 : 400,
              }}
            >
              Final Reports
            </Link>
            <div style={{ marginTop: 12, paddingTop: 12, borderTop: "1px solid #e0e0e0" }}>
              <div style={{ fontSize: 11, color: "#999", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 8 }}>
                LEGACY
              </div>
            </div>
            <Link
              to="/intake"
              style={{
                padding: "10px 12px",
                textDecoration: "none",
                color: location.pathname === "/intake" ? "#0B5ED7" : "#555",
                backgroundColor: location.pathname === "/intake" ? "#f0f7ff" : "transparent",
                borderRadius: 6,
                fontSize: 14,
                fontWeight: location.pathname === "/intake" ? 500 : 400,
              }}
            >
              Front Desk Intake
            </Link>
            <Link
              to="/patients"
              style={{
                padding: "10px 12px",
                textDecoration: "none",
                color: location.pathname === "/patients" ? "#0B5ED7" : "#555",
                backgroundColor: location.pathname === "/patients" ? "#f0f7ff" : "transparent",
                borderRadius: 6,
                fontSize: 14,
                fontWeight: location.pathname === "/patients" ? 500 : 400,
              }}
            >
              Patients
            </Link>
            <Link
              to="/studies"
              style={{
                padding: "10px 12px",
                textDecoration: "none",
                color: location.pathname === "/studies" ? "#0B5ED7" : "#555",
                backgroundColor: location.pathname === "/studies" ? "#f0f7ff" : "transparent",
                borderRadius: 6,
                fontSize: 14,
                fontWeight: location.pathname === "/studies" ? 500 : 400,
              }}
            >
              Studies
            </Link>
            <Link
              to="/templates"
              style={{
                padding: "10px 12px",
                textDecoration: "none",
                color: location.pathname === "/templates" ? "#0B5ED7" : "#555",
                backgroundColor: location.pathname === "/templates" ? "#f0f7ff" : "transparent",
                borderRadius: 6,
                fontSize: 14,
                fontWeight: location.pathname === "/templates" ? 500 : 400,
              }}
            >
              Templates
            </Link>
            <Link
              to="/receipt-settings"
              style={{
                padding: "10px 12px",
                textDecoration: "none",
                color: location.pathname === "/receipt-settings" ? "#0B5ED7" : "#555",
                backgroundColor: location.pathname === "/receipt-settings" ? "#f0f7ff" : "transparent",
                borderRadius: 6,
                fontSize: 14,
                fontWeight: location.pathname === "/receipt-settings" ? 500 : 400,
              }}
            >
              Receipt Settings
            </Link>
          </nav>
          <button
            onClick={logout}
            style={{
              marginTop: "auto",
              padding: "10px 16px",
              backgroundColor: "#dc3545",
              color: "white",
              border: "none",
              borderRadius: 6,
              cursor: "pointer",
              fontSize: 14,
              fontWeight: 500,
            }}
          >
            Logout
          </button>
        </aside>
        <main
          style={{
            flex: 1,
            padding: 24,
            display: "flex",
            flexDirection: "column",
            minHeight: 0,
            backgroundColor: "#fff",
          }}
        >
          <div style={{ flex: 1, minHeight: 0, paddingBottom: 20 }}>
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
          </div>
          <Footer />
        </main>
      </div>
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
