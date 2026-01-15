import React, { useEffect, useState } from "react";
import { Routes, Route, Navigate, Link, useLocation } from "react-router-dom";
import { useAuth, AuthProvider } from "./auth";
import { apiGet } from "./api";
import Login from "../views/Login";
import Dashboard from "../views/Dashboard";
import Patients from "../views/Patients";
import Templates from "../views/Templates";
import ReceiptSettings from "../views/ReceiptSettings";
import RegistrationPage from "../views/RegistrationPage";
import USGWorklistPage from "../views/USGWorklistPage";
import VerificationWorklistPage from "../views/VerificationWorklistPage";
import FinalReportsPage from "../views/FinalReportsPage";
import Footer from "./components/Footer";

function Shell() {
  const { token, logout } = useAuth();
  const location = useLocation();
  const [logoUrl, setLogoUrl] = useState<string | null>(null);

  // Helper function to check if a route is active (handles sub-routes)
  const isActiveRoute = (path: string) => {
    if (path === "/") {
      return location.pathname === "/";
    }
    return location.pathname === path || location.pathname.startsWith(path + "/");
  };

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
              <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", gap: 12 }}>
                <img
                  src={logoUrl}
                  alt="Consultant Place Clinics Logo"
                  style={{
                    width: 60,
                    height: 60,
                    objectFit: "contain",
                    display: "block",
                  }}
                  onError={(e) => {
                    // Hide image if it fails to load
                    (e.target as HTMLImageElement).style.display = "none";
                  }}
                />
                <h2 style={{ margin: 0, fontSize: 16, fontWeight: 600, color: "#333", lineHeight: 1.3 }}>
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
                color: isActiveRoute("/") ? "#0B5ED7" : "#555",
                backgroundColor: isActiveRoute("/") ? "#f0f7ff" : "transparent",
                borderRadius: 6,
                fontSize: 14,
                fontWeight: isActiveRoute("/") ? 500 : 400,
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
                color: isActiveRoute("/registration") ? "#0B5ED7" : "#555",
                backgroundColor: isActiveRoute("/registration") ? "#f0f7ff" : "transparent",
                borderRadius: 6,
                fontSize: 14,
                fontWeight: isActiveRoute("/registration") ? 500 : 400,
              }}
            >
              Registration
            </Link>
            <Link
              to="/worklists/usg"
              style={{
                padding: "10px 12px",
                textDecoration: "none",
                color: isActiveRoute("/worklists/usg") ? "#0B5ED7" : "#555",
                backgroundColor: isActiveRoute("/worklists/usg") ? "#f0f7ff" : "transparent",
                borderRadius: 6,
                fontSize: 14,
                fontWeight: isActiveRoute("/worklists/usg") ? 500 : 400,
              }}
            >
              Report Entry
            </Link>
            <Link
              to="/worklists/verification"
              style={{
                padding: "10px 12px",
                textDecoration: "none",
                color: isActiveRoute("/worklists/verification") ? "#0B5ED7" : "#555",
                backgroundColor: isActiveRoute("/worklists/verification") ? "#f0f7ff" : "transparent",
                borderRadius: 6,
                fontSize: 14,
                fontWeight: isActiveRoute("/worklists/verification") ? 500 : 400,
              }}
            >
              Verification
            </Link>
            <Link
              to="/reports"
              style={{
                padding: "10px 12px",
                textDecoration: "none",
                color: isActiveRoute("/reports") ? "#0B5ED7" : "#555",
                backgroundColor: isActiveRoute("/reports") ? "#f0f7ff" : "transparent",
                borderRadius: 6,
                fontSize: 14,
                fontWeight: isActiveRoute("/reports") ? 500 : 400,
              }}
            >
              Final Reports
            </Link>
            {/* PHASE C: Legacy routes hidden from navigation - accessible via direct URL for admin only */}
            {/* Uncomment below to show legacy routes (admin-only in production) */}
            {/*
            <div style={{ marginTop: 12, paddingTop: 12, borderTop: "1px solid #e0e0e0" }}>
              <div style={{ fontSize: 11, color: "#999", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 8 }}>
                LEGACY (ADMIN ONLY)
              </div>
            </div>
            <Link
              to="/intake"
              style={{
                padding: "10px 12px",
                textDecoration: "none",
                color: isActiveRoute("/intake") ? "#0B5ED7" : "#555",
                backgroundColor: isActiveRoute("/intake") ? "#f0f7ff" : "transparent",
                borderRadius: 6,
                fontSize: 14,
                fontWeight: isActiveRoute("/intake") ? 500 : 400,
                opacity: 0.5,
              }}
            >
              Front Desk Intake (LEGACY)
            </Link>
            <Link
              to="/patients"
              style={{
                padding: "10px 12px",
                textDecoration: "none",
                color: isActiveRoute("/patients") ? "#0B5ED7" : "#555",
                backgroundColor: isActiveRoute("/patients") ? "#f0f7ff" : "transparent",
                borderRadius: 6,
                fontSize: 14,
                fontWeight: isActiveRoute("/patients") ? 500 : 400,
                opacity: 0.5,
              }}
            >
              Patients (LEGACY)
            </Link>
            <Link
              to="/studies"
              style={{
                padding: "10px 12px",
                textDecoration: "none",
                color: isActiveRoute("/studies") ? "#0B5ED7" : "#555",
                backgroundColor: isActiveRoute("/studies") ? "#f0f7ff" : "transparent",
                borderRadius: 6,
                fontSize: 14,
                fontWeight: isActiveRoute("/studies") ? 500 : 400,
                opacity: 0.5,
              }}
            >
              Studies (LEGACY)
            </Link>
            <Link
              to="/templates"
              style={{
                padding: "10px 12px",
                textDecoration: "none",
                color: isActiveRoute("/templates") ? "#0B5ED7" : "#555",
                backgroundColor: isActiveRoute("/templates") ? "#f0f7ff" : "transparent",
                borderRadius: 6,
                fontSize: 14,
                fontWeight: isActiveRoute("/templates") ? 500 : 400,
              }}
            >
              Templates
            </Link>
            <Link
              to="/receipt-settings"
              style={{
                padding: "10px 12px",
                textDecoration: "none",
                color: isActiveRoute("/receipt-settings") ? "#0B5ED7" : "#555",
                backgroundColor: isActiveRoute("/receipt-settings") ? "#f0f7ff" : "transparent",
                borderRadius: 6,
                fontSize: 14,
                fontWeight: isActiveRoute("/receipt-settings") ? 500 : 400,
              }}
            >
              Receipt Settings
            </Link>
            */}
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
              <Route path="/worklists/verification" element={<VerificationWorklistPage />} />
              <Route path="/reports" element={<FinalReportsPage />} />
              {/* Legacy Routes */}
              <Route path="/patients" element={<Patients />} />
              <Route path="/templates" element={<Templates />} />
              <Route path="/receipt-settings" element={<ReceiptSettings />} />
              {/* Legacy endpoints disabled in Phase 2 */}
              <Route path="/studies" element={<Navigate to="/" replace />} />
              <Route path="/reports/:reportId/edit" element={<Navigate to="/reports" replace />} />
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
