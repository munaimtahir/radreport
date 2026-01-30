import React, { useEffect, useState } from "react";
import { Routes, Route, Navigate, Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth, AuthProvider } from "./auth";
import { apiGet } from "./api";
import Login from "../views/Login";
import Dashboard from "../views/Dashboard";
import Patients from "../views/Patients";
import ReceiptSettings from "../views/ReceiptSettings";
import ConsultantSettlementsPage from "../views/ConsultantSettlementsPage";
import ConsultantsPage from "../views/ConsultantsPage";
import RegistrationPage from "../views/RegistrationPage";
import PatientsWorkflow from "../views/PatientsWorkflow";
import AccessDenied from "../views/AccessDenied";
import ReportingPage from "../views/ReportingPage";
import ReportingWorklistPage from "../views/ReportingWorklistPage";
import TemplatesList from "../views/settings/TemplatesList";
import TemplateEditor from "../views/settings/TemplateEditor";
import ServicesList from "../views/settings/ServicesList";
import ServiceEditor from "../views/settings/ServiceEditor";


import ModuleDisabled from "../views/ModuleDisabled";
import Footer from "./components/Footer";
import { BrandLogo, BrandTitle } from "./components/brand";
import { theme } from "../theme";

function Shell() {
  const { token, logout, user, isLoading } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const groups = user?.groups || [];
  const isSuperuser = user?.is_superuser || false;
  const canRegister = isSuperuser || groups.includes("registration");
  const canPerform = isSuperuser || groups.includes("performance");
  const canVerify = isSuperuser || groups.includes("verification");
  const canAdmin = isSuperuser;
  const canWorkflow = isSuperuser || canRegister || canPerform || canVerify;

  // Helper function to check if a route is active (handles sub-routes)
  const isActiveRoute = (path: string) => {
    if (path === "/") {
      return location.pathname === "/";
    }
    return location.pathname === path || location.pathname.startsWith(path + "/");
  };

  if (!token) return <Navigate to="/login" replace />;
  if (isLoading) {
    return (
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "100vh",
        fontFamily: theme.typography.fontFamily
      }}>
        Loading user...
      </div>
    );
  }

  return (
    <div style={{
      display: "flex",
      minHeight: "100vh",
      fontFamily: theme.typography.fontFamily,
      flexDirection: "column"
    }}>
      <div style={{ display: "flex", flex: 1, minHeight: 0 }}>
        <aside
          style={{
            width: 240,
            padding: 20,
            borderRight: `1px solid ${theme.colors.border}`,
            backgroundColor: theme.colors.backgroundGray,
            display: "flex",
            flexDirection: "column",
          }}
        >
          <div
            style={{
              marginBottom: 24,
              cursor: "pointer"
            }}
            onClick={() => navigate("/")}
          >
            <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", gap: 12 }}>
              <BrandLogo size="lg" variant="full" />
              <BrandTitle size="md" />
            </div>
          </div>
          <nav style={{ display: "flex", flexDirection: "column", gap: 4, flex: 1 }}>
            <Link
              to="/"
              style={{
                padding: "10px 12px",
                textDecoration: "none",
                color: isActiveRoute("/") ? theme.colors.brandBlue : theme.colors.textSecondary,
                backgroundColor: isActiveRoute("/") ? theme.colors.brandBlueSoft : "transparent",
                borderRadius: theme.radius.base,
                fontSize: 14,
                fontWeight: isActiveRoute("/") ? theme.typography.fontWeight.medium : theme.typography.fontWeight.normal,
                transition: theme.transitions.fast,
              }}
            >
              Dashboard
            </Link>
            <div style={{ marginTop: 12, paddingTop: 12, borderTop: `1px solid ${theme.colors.border}` }}>
              <div style={{
                fontSize: 11,
                color: theme.colors.textTertiary,
                fontWeight: theme.typography.fontWeight.semibold,
                textTransform: "uppercase",
                letterSpacing: "0.5px",
                marginBottom: 8
              }}>
                WORKFLOW
              </div>
            </div>
            {canRegister && (
              <Link
                to="/registration"
                style={{
                  padding: "10px 12px",
                  textDecoration: "none",
                  color: isActiveRoute("/registration") ? theme.colors.brandBlue : theme.colors.textSecondary,
                  backgroundColor: isActiveRoute("/registration") ? theme.colors.brandBlueSoft : "transparent",
                  borderRadius: theme.radius.base,
                  fontSize: 14,
                  fontWeight: isActiveRoute("/registration") ? theme.typography.fontWeight.medium : theme.typography.fontWeight.normal,
                  transition: theme.transitions.fast,
                }}
              >
                Registration
              </Link>
            )}
            {canWorkflow && (
              <Link
                to="/patients/workflow"
                style={{
                  padding: "10px 12px",
                  textDecoration: "none",
                  color: isActiveRoute("/patients/workflow") ? theme.colors.brandBlue : theme.colors.textSecondary,
                  backgroundColor: isActiveRoute("/patients/workflow") ? theme.colors.brandBlueSoft : "transparent",
                  borderRadius: theme.radius.base,
                  fontSize: 14,
                  fontWeight: isActiveRoute("/patients/workflow") ? theme.typography.fontWeight.medium : theme.typography.fontWeight.normal,
                  transition: theme.transitions.fast,
                }}
              >
                Patient workflow
              </Link>
            )}
            {(canPerform || canVerify) && (
              <Link
                to="/reporting/worklist"
                style={{
                  padding: "10px 12px",
                  textDecoration: "none",
                  color: isActiveRoute("/reporting/worklist") ? theme.colors.brandBlue : theme.colors.textSecondary,
                  backgroundColor: isActiveRoute("/reporting/worklist") ? theme.colors.brandBlueSoft : "transparent",
                  borderRadius: theme.radius.base,
                  fontSize: 14,
                  fontWeight: isActiveRoute("/reporting/worklist") ? theme.typography.fontWeight.medium : theme.typography.fontWeight.normal,
                  transition: theme.transitions.fast,
                }}
              >
                Reporting worklist
              </Link>
            )}


            {canAdmin && (
              <div style={{
                marginTop: 12,
                paddingTop: 12,
                borderTop: `1px solid ${theme.colors.border}`,
                display: "flex",
                flexDirection: "column",
                gap: 4
              }}>
                <div style={{
                  fontSize: 11,
                  color: theme.colors.textTertiary,
                  fontWeight: theme.typography.fontWeight.semibold,
                  textTransform: "uppercase",
                  letterSpacing: "0.5px",
                  marginBottom: 8
                }}>
                  SETTINGS
                </div>
                <Link
                  to="/settings/consultants"
                  style={{
                    padding: "10px 12px",
                    textDecoration: "none",
                    color: isActiveRoute("/settings/consultants") ? theme.colors.brandBlue : theme.colors.textSecondary,
                    backgroundColor: isActiveRoute("/settings/consultants") ? theme.colors.brandBlueSoft : "transparent",
                    borderRadius: theme.radius.base,
                    fontSize: 14,
                    fontWeight: isActiveRoute("/settings/consultants") ? theme.typography.fontWeight.medium : theme.typography.fontWeight.normal,
                    transition: theme.transitions.fast,
                  }}
                >
                  Consultants
                </Link>

                <Link
                  to="/settings/consultant-settlements"
                  style={{
                    padding: "10px 12px",
                    textDecoration: "none",
                    color: isActiveRoute("/settings/consultant-settlements") ? theme.colors.brandBlue : theme.colors.textSecondary,
                    backgroundColor: isActiveRoute("/settings/consultant-settlements") ? theme.colors.brandBlueSoft : "transparent",
                    borderRadius: theme.radius.base,
                    fontSize: 14,
                    fontWeight: isActiveRoute("/settings/consultant-settlements") ? theme.typography.fontWeight.medium : theme.typography.fontWeight.normal,
                    transition: theme.transitions.fast,
                  }}
                >
                  Consultant Settlements
                </Link>
                <Link
                  to="/receipt-settings"
                  style={{
                    padding: "10px 12px",
                    textDecoration: "none",
                    color: isActiveRoute("/receipt-settings") ? theme.colors.brandBlue : theme.colors.textSecondary,
                    backgroundColor: isActiveRoute("/receipt-settings") ? theme.colors.brandBlueSoft : "transparent",
                    borderRadius: theme.radius.base,
                    fontSize: 14,
                    fontWeight: isActiveRoute("/receipt-settings") ? theme.typography.fontWeight.medium : theme.typography.fontWeight.normal,
                    transition: theme.transitions.fast,
                  }}
                >
                  Receipt Settings
                </Link>
                <Link
                  to="/settings/services"
                  style={{
                    padding: "10px 12px",
                    textDecoration: "none",
                    color: isActiveRoute("/settings/services") ? theme.colors.brandBlue : theme.colors.textSecondary,
                    backgroundColor: isActiveRoute("/settings/services") ? theme.colors.brandBlueSoft : "transparent",
                    borderRadius: theme.radius.base,
                    fontSize: 14,
                    fontWeight: isActiveRoute("/settings/services") ? theme.typography.fontWeight.medium : theme.typography.fontWeight.normal,
                    transition: theme.transitions.fast,
                  }}
                >
                  Services
                </Link>
                <Link
                  to="/settings/templates"
                  style={{
                    padding: "10px 12px",
                    textDecoration: "none",
                    color: isActiveRoute("/settings/templates") ? theme.colors.brandBlue : theme.colors.textSecondary,
                    backgroundColor: isActiveRoute("/settings/templates") ? theme.colors.brandBlueSoft : "transparent",
                    borderRadius: theme.radius.base,
                    fontSize: 14,
                    fontWeight: isActiveRoute("/settings/templates") ? theme.typography.fontWeight.medium : theme.typography.fontWeight.normal,
                    transition: theme.transitions.fast,
                  }}
                >
                  Templates
                </Link>
              </div>
            )}
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
              backgroundColor: theme.colors.danger,
              color: "white",
              border: "none",
              borderRadius: theme.radius.base,
              cursor: "pointer",
              fontSize: 14,
              fontWeight: theme.typography.fontWeight.medium,
              transition: theme.transitions.fast,
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
            backgroundColor: theme.colors.background,
          }}
        >
          <div style={{ flex: 1, minHeight: 0, paddingBottom: 20 }}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              {/* Workflow Routes */}
              <Route
                path="/registration"
                element={canRegister ? <RegistrationPage /> : <AccessDenied />}
              />
              <Route
                path="/patients/workflow"
                element={canWorkflow ? <PatientsWorkflow /> : <AccessDenied />}
              />
              <Route
                path="/worklists/opd/*"
                element={<ModuleDisabled title="OPD module disabled" message="OPD module is disabled in this build." />}
              />
              <Route
                path="/opd/*"
                element={<ModuleDisabled title="OPD module disabled" message="OPD module is disabled in this build." />}
              />

              <Route
                path="/settings/consultant-settlements"
                element={canAdmin ? <ConsultantSettlementsPage /> : <AccessDenied />}
              />
              <Route
                path="/settings/consultants"
                element={canAdmin ? <ConsultantsPage /> : <AccessDenied />}
              />

              <Route path="/settings/templates" element={canAdmin ? <TemplatesList /> : <AccessDenied />} />
              <Route path="/settings/templates/:id" element={canAdmin ? <TemplateEditor /> : <AccessDenied />} />
              <Route path="/settings/services" element={canAdmin ? <ServicesList /> : <AccessDenied />} />
              <Route path="/settings/services/:id" element={canAdmin ? <ServiceEditor /> : <AccessDenied />} />

              {/* Legacy Routes */}
              <Route path="/patients" element={<Patients />} />
              <Route path="/receipt-settings" element={canAdmin ? <ReceiptSettings /> : <AccessDenied />} />

              {/* Legacy endpoints disabled in Phase 2 */}
              <Route path="/studies" element={<Navigate to="/" replace />} />
              <Route path="/reports/:reportId/edit" element={<Navigate to="/reports" replace />} />
              <Route path="/reporting/worklist" element={<ReportingWorklistPage />} />
              <Route path="/reporting/worklist/:service_visit_item_id/report" element={<ReportingPage />} />
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
