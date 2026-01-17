import React, { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { apiGet } from "../ui/api";
import { useAuth } from "../ui/auth";
import PageHeader from "../ui/components/PageHeader";
import ErrorAlert from "../ui/components/ErrorAlert";
import Button from "../ui/components/Button";
import { theme } from "../theme";
import UsgVisitReportsTab from "./UsgVisitReportsTab";

interface ServiceVisitItem {
  id: string;
  service_name_snapshot?: string;
  service_code?: string;
  department_snapshot?: string;
}

interface ServiceVisit {
  id: string;
  visit_id: string;
  patient: string;
  patient_name?: string;
  patient_mrn?: string;
  registered_at?: string;
  status?: string;
  created_by_name?: string;
  items?: ServiceVisitItem[];
}

const formatDateTime = (value?: string) => {
  if (!value) return "-";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString();
};

export default function UsgVisitDetailPage() {
  const { visitId } = useParams();
  const { token } = useAuth();
  const navigate = useNavigate();
  const [visit, setVisit] = useState<ServiceVisit | null>(null);
  const [activeTab, setActiveTab] = useState("usg");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token || !visitId) return;
    const loadVisit = async () => {
      setError("");
      try {
        const data = await apiGet(`/workflow/visits/${visitId}/`, token);
        setVisit(data);
      } catch (err: any) {
        setError(err.message || "Failed to load visit");
      }
    };
    loadVisit();
  }, [token, visitId]);

  const tabButtonStyle = (tab: string): React.CSSProperties => ({
    padding: "10px 14px",
    borderRadius: theme.radius.base,
    border: `1px solid ${activeTab === tab ? theme.colors.brandBlue : theme.colors.border}`,
    backgroundColor: activeTab === tab ? theme.colors.brandBlueSoft : "transparent",
    color: activeTab === tab ? theme.colors.brandBlue : theme.colors.textSecondary,
    cursor: "pointer",
    fontSize: 13,
    fontWeight: activeTab === tab ? theme.typography.fontWeight.semibold : theme.typography.fontWeight.normal,
  });

  const patientInfo = useMemo(() => {
    if (!visit) return "";
    return `${visit.patient_name || ""} (${visit.patient_mrn || ""})`;
  }, [visit]);

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto" }}>
      <PageHeader
        title={`Visit ${visit?.visit_id || ""}`}
        subtitle={patientInfo}
      />

      {error && <ErrorAlert message={error} onDismiss={() => setError("")} />}

      {visit && (
        <div style={{
          border: `1px solid ${theme.colors.border}`,
          borderRadius: theme.radius.md,
          padding: 16,
          marginBottom: 20,
          backgroundColor: theme.colors.background,
          display: "flex",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: 12,
        }}>
          <div>
            <div style={{ fontWeight: theme.typography.fontWeight.semibold }}>
              Status: {visit.status || "-"}
            </div>
            <div style={{ color: theme.colors.textSecondary, fontSize: 13, marginTop: 4 }}>
              Registered: {formatDateTime(visit.registered_at)}
            </div>
            {visit.created_by_name && (
              <div style={{ color: theme.colors.textSecondary, fontSize: 13, marginTop: 4 }}>
                Created by: {visit.created_by_name}
              </div>
            )}
          </div>
          <div style={{ display: "flex", alignItems: "center" }}>
            <Button variant="secondary" onClick={() => navigate(-1)}>
              Back to Patient
            </Button>
          </div>
        </div>
      )}

      <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
        <button type="button" style={tabButtonStyle("overview")} onClick={() => setActiveTab("overview")}>
          Overview
        </button>
        <button type="button" style={tabButtonStyle("orders")} onClick={() => setActiveTab("orders")}>
          Orders / Services
        </button>
        <button type="button" style={tabButtonStyle("usg")} onClick={() => setActiveTab("usg")}>
          Ultrasound Reports (USG)
        </button>
        <button type="button" style={tabButtonStyle("other")} onClick={() => setActiveTab("other")}>
          Other Reports
        </button>
      </div>

      {activeTab === "usg" && visitId && (
        <UsgVisitReportsTab
          visitId={visitId}
          patientId={visit?.patient}
          patientName={visit?.patient_name}
          patientMrn={visit?.patient_mrn}
        />
      )}
      {activeTab !== "usg" && (
        <div style={{
          border: `1px solid ${theme.colors.border}`,
          borderRadius: theme.radius.md,
          padding: 20,
          backgroundColor: theme.colors.background,
          color: theme.colors.textTertiary,
        }}>
          This tab is a placeholder for future workflow modules.
        </div>
      )}
    </div>
  );
}
