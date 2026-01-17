import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiGet, apiPost } from "../ui/api";
import { useAuth } from "../ui/auth";
import ErrorAlert from "../ui/components/ErrorAlert";
import SuccessAlert from "../ui/components/SuccessAlert";
import Button from "../ui/components/Button";
import { theme } from "../theme";

interface Template {
  id: string;
  code: string;
  name: string;
}

interface UsgStudy {
  id: string;
  service_code: string;
  status: string;
  created_at: string;
  created_by?: string;
  published_at?: string;
}

interface UsgVisitReportsTabProps {
  visitId: string;
  patientId?: string;
  patientName?: string;
  patientMrn?: string;
}

const formatDateTime = (value?: string) => {
  if (!value) return "-";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString();
};

export default function UsgVisitReportsTab({ visitId, patientId, patientName, patientMrn }: UsgVisitReportsTabProps) {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [studies, setStudies] = useState<UsgStudy[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [selectedTemplateId, setSelectedTemplateId] = useState("");

  const loadStudies = async () => {
    if (!token) return;
    try {
      const data = await apiGet(`/visits/${visitId}/usg-reports/`, token);
      setStudies(data || []);
    } catch (err: any) {
      setError(err.message || "Failed to load USG studies");
    }
  };

  const loadTemplates = async () => {
    if (!token) return;
    try {
      const data = await apiGet("/usg/templates/", token);
      const list = data.results || data || [];
      setTemplates(list);
      if (!selectedTemplateId && list.length > 0) {
        setSelectedTemplateId(list[0].id);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load templates");
    }
  };

  useEffect(() => {
    if (!token) return;
    loadStudies();
  }, [token, visitId]);

  useEffect(() => {
    if (!token || !showModal) return;
    loadTemplates();
  }, [token, showModal]);

  const handleCreateStudy = async () => {
    if (!token) return;
    if (!selectedTemplateId) {
      setError("Please select a template.");
      return;
    }
    if (!patientId) {
      setError("Patient information is missing for this visit.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const template = templates.find((item) => item.id === selectedTemplateId);
      const payload = {
        patient: patientId,
        visit: visitId,
        service_code: template?.code || "USG_ABDOMEN",
        template: selectedTemplateId,
      };
      const study = await apiPost("/usg/studies/", token, payload);
      setSuccess("USG study created.");
      setShowModal(false);
      await loadStudies();
      navigate(`/usg/studies/${study.id}`);
    } catch (err: any) {
      setError(err.message || "Failed to create study");
    } finally {
      setLoading(false);
    }
  };

  const latestStatus = useMemo(() => {
    return studies.length === 0 ? "No studies yet" : `${studies.length} study${studies.length === 1 ? "" : "ies"}`;
  }, [studies.length]);

  return (
    <div style={{
      border: `1px solid ${theme.colors.border}`,
      borderRadius: theme.radius.md,
      backgroundColor: theme.colors.background,
    }}>
      {error && <ErrorAlert message={error} onDismiss={() => setError("")} />}
      {success && <SuccessAlert message={success} onDismiss={() => setSuccess("")} />}

      <div style={{ padding: "12px 16px", borderBottom: `1px solid ${theme.colors.border}` }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap" }}>
          <div>
            <div style={{ fontWeight: theme.typography.fontWeight.semibold }}>Ultrasound Studies</div>
            <div style={{ fontSize: 12, color: theme.colors.textTertiary }}>{latestStatus}</div>
          </div>
          <Button onClick={() => setShowModal(true)}>Add Ultrasound Study</Button>
        </div>
      </div>

      <div style={{ padding: 16 }}>
        {studies.length === 0 ? (
          <div style={{ color: theme.colors.textTertiary }}>
            No ultrasound studies yet for this visit.
          </div>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ textAlign: "left", fontSize: 12, color: theme.colors.textSecondary }}>
                <th style={{ paddingBottom: 8 }}>Study Type</th>
                <th style={{ paddingBottom: 8 }}>Status</th>
                <th style={{ paddingBottom: 8 }}>Created</th>
                <th style={{ paddingBottom: 8 }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {studies.map((study) => (
                <tr key={study.id} style={{ borderTop: `1px solid ${theme.colors.borderLight}` }}>
                  <td style={{ padding: "10px 4px" }}>{study.service_code}</td>
                  <td style={{ padding: "10px 4px" }}>{study.status}</td>
                  <td style={{ padding: "10px 4px" }}>{formatDateTime(study.created_at)}</td>
                  <td style={{ padding: "10px 4px" }}>
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                      <Button variant="secondary" onClick={() => navigate(`/usg/studies/${study.id}`)}>
                        {study.status === "published" ? "View" : "Continue Draft"}
                      </Button>
                      <Button
                        variant="secondary"
                        onClick={() => navigate(`/usg/studies/${study.id}?preview=1`)}
                      >
                        Preview
                      </Button>
                      {study.status === "published" && (
                        <Button variant="secondary" onClick={() => navigate(`/usg/studies/${study.id}?pdf=1`)}>
                          View PDF
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showModal && (
        <div style={{
          position: "fixed",
          inset: 0,
          backgroundColor: "rgba(0,0,0,0.4)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 1000,
        }}>
          <div style={{
            width: "min(480px, 90vw)",
            backgroundColor: theme.colors.background,
            borderRadius: theme.radius.md,
            padding: 20,
            boxShadow: theme.shadows.md,
          }}>
            <h3 style={{ marginTop: 0 }}>Add Ultrasound Study</h3>
            <p style={{ marginTop: 4, color: theme.colors.textSecondary, fontSize: 13 }}>
              Patient: {patientName || ""} {patientMrn ? `• MRN ${patientMrn}` : ""}
            </p>
            <label style={{ display: "block", marginBottom: 6 }}>Select template</label>
            <select
              value={selectedTemplateId}
              onChange={(event) => setSelectedTemplateId(event.target.value)}
              style={{
                width: "100%",
                padding: 8,
                borderRadius: theme.radius.base,
                border: `1px solid ${theme.colors.border}`,
              }}
            >
              {templates.map((template) => (
                <option key={template.id} value={template.id}>
                  {template.name}
                </option>
              ))}
            </select>
            <div style={{ display: "flex", gap: 12, marginTop: 16 }}>
              <Button onClick={handleCreateStudy} disabled={loading}>
                {loading ? "Creating..." : "Create Study"}
              </Button>
              <Button variant="secondary" onClick={() => setShowModal(false)}>
                Cancel
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
