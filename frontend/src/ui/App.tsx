import React, { useEffect, useState } from "react";
import { Routes, Route, Navigate, useLocation, useNavigate } from "react-router-dom";
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
import TemplatesV2 from "../views/admin/TemplatesV2";
import ServicesList from "../views/admin/ServicesList";
import ServiceEditor from "../views/admin/ServiceEditor";
import TemplateV2Builder from "../views/admin/TemplateV2Builder";
import BlockLibrary from "../views/admin/BlockLibrary";
import ReportPrintingWorklist from "../views/ReportPrintingWorklist";
import UserSettings from "../views/admin/UserSettings";
import BackupOpsPage from "../views/admin/BackupOpsPage";
import RadiologyReportPrintPage from "../views/RadiologyReportPrintPage";


import ModuleDisabled from "../views/ModuleDisabled";
import Footer from "./components/Footer";
import { BrandLogo, BrandTitle } from "./components/brand";
import NavLink from "./components/NavLink";
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
  const canBackupAdmin = isSuperuser || groups.includes("manager") || groups.includes("admin");
  const canWorkflow = isSuperuser || canRegister || canPerform || canVerify;

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
            <NavLink to="/">
              Dashboard
            </NavLink>
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
              <NavLink to="/registration">
                Registration
              </NavLink>
            )}
            {canWorkflow && (
              <NavLink to="/patients/workflow">
                Patient workflow
              </NavLink>
            )}
            {(canPerform || canVerify) && (
              <NavLink to="/reporting/worklist">
                Reporting worklist
              </NavLink>
            )}
            {canWorkflow && (
              <NavLink to="/reports">
                Print reports
              </NavLink>
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
                  CATALOG & TEMPLATES
                </div>
                <NavLink to="/settings/templates-v2">
                  Templates V2
                </NavLink>
                <NavLink to="/settings/block-library">
                  Block Library
                </NavLink>
                <NavLink to="/settings/services">
                  Services
                </NavLink>
              </div>
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
                <NavLink to="/settings/consultants">
                  Consultants
                </NavLink>

                <NavLink to="/settings/consultant-settlements">
                  Consultant Settlements
                </NavLink>
                <NavLink to="/settings/users">
                  User Settings
                </NavLink>
                <NavLink to="/receipt-settings">
                  Receipt Settings
                </NavLink>
                {canBackupAdmin && (
                  <NavLink to="/settings/backups">
                    Backups
                  </NavLink>
                )}
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
            <NavLink to="/intake">Front Desk Intake (LEGACY)</NavLink>
            <NavLink to="/patients">Patients (LEGACY)</NavLink>
            <NavLink to="/studies">Studies (LEGACY)</NavLink>
            <NavLink to="/templates">Templates</NavLink>
            <NavLink to="/receipt-settings">Receipt Settings</NavLink>
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

              <Route path="/settings/templates-v2" element={canAdmin ? <TemplatesV2 /> : <AccessDenied />} />
              <Route path="/settings/templates-v2/:id/builder" element={canAdmin ? <TemplateV2Builder /> : <AccessDenied />} />
              <Route path="/settings/block-library" element={canAdmin ? <BlockLibrary /> : <AccessDenied />} />
              <Route path="/settings/services" element={canAdmin ? <ServicesList /> : <AccessDenied />} />
              <Route path="/settings/services/:id" element={canAdmin ? <ServiceEditor /> : <AccessDenied />} />
              <Route path="/settings/users" element={canAdmin ? <UserSettings /> : <AccessDenied />} />
              <Route path="/settings/backups" element={canBackupAdmin ? <BackupOpsPage /> : <AccessDenied />} />

              {/* Legacy Routes */}
              <Route path="/patients" element={<Patients />} />
              <Route path="/receipt-settings" element={canAdmin ? <ReceiptSettings /> : <AccessDenied />} />

              {/* Legacy endpoints disabled in Phase 2 */}
              <Route path="/studies" element={<Navigate to="/" replace />} />
              <Route path="/reports/:reportId/edit" element={<Navigate to="/reports" replace />} />
              <Route path="/reporting/worklist" element={<ReportingWorklistPage />} />
              <Route path="/reporting/worklist/:service_visit_item_id/report" element={<ReportingPage />} />
              <Route path="/reports" element={<ReportPrintingWorklist />} />
            </Routes>

          </div>
          <Footer />
        </main>
      </div>
    </div>
  );
}

export default function App() {
  function PrintRouteGuard() {
    const { token } = useAuth();
    if (!token) return <Navigate to="/login" replace />;
    return <RadiologyReportPrintPage />;
  }

  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/print/report/:service_visit_item_id" element={<PrintRouteGuard />} />
        <Route path="/*" element={<Shell />} />
      </Routes>
    </AuthProvider>
  );
}
