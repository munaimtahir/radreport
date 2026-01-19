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

interface ServiceProfile {
  id: string;
  service_code: string;
  template: string;
  template_detail?: {
    id: string;
    code: string;
    name: string;
  };
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
  const [serviceProfiles, setServiceProfiles] = useState<ServiceProfile[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [selectedOptionId, setSelectedOptionId] = useState("");

  const loadStudies = async () => {
    if (!token) return;
    try {
      // Use Workflow API to fetch reports for this ServiceVisit
      const data = await apiGet(`/workflow/usg/?visit_id=${visitId}`, token);

      // Adapt USGReport (workflow) to UsgStudy (frontend interface)
      const adaptedList = (data.results || data || []).map((report: any) => ({
        id: report.id,
        // Fallback to service code/name or template name
        service_code: report.study_title || report.template_name || report.service_visit_item?.service_code || "USG Study",
        status: report.report_status?.toLowerCase(), // DRAFT -> draft
        created_at: report.created_at || report.saved_at, // USGReport uses saved_at/created_at
        created_by: report.created_by_name,
        published_at: report.verified_at // workflow uses verified_at/published_at logic, simplifying for display
      }));
      setStudies(adaptedList);
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
    } catch (err: any) {
      setError(err.message || "Failed to load templates");
    }
  };

  const loadServiceProfiles = async () => {
    if (!token) return;
    try {
      const data = await apiGet("/usg/service-profiles/", token);
      const list = data.results || data || [];
      setServiceProfiles(list);
    } catch (err: any) {
      setError(err.message || "Failed to load service profiles");
    }
  };

  useEffect(() => {
    if (!token) return;
    loadStudies();
  }, [token, visitId]);

  useEffect(() => {
    if (!token || !showModal) return;
    loadTemplates();
    loadServiceProfiles();
  }, [token, showModal]);

  const studyOptions = useMemo(() => {
    if (serviceProfiles.length > 0) {
      return serviceProfiles.map((profile) => ({
        id: profile.id,
        label: `${profile.service_code} — ${profile.template_detail?.name || "Template"}`,
        serviceCode: profile.service_code,
        templateId: profile.template,
      }));
    }
    return templates.map((template) => ({
      id: template.id,
      label: template.name,
      serviceCode: template.code === "USG_PELVIS_BASE" ? "USG_PELVIS" : template.code,
      templateId: template.id,
    }));
  }, [serviceProfiles, templates]);

  useEffect(() => {
    if (!selectedOptionId && studyOptions.length > 0) {
      setSelectedOptionId(studyOptions[0].id);
    }
  }, [selectedOptionId, studyOptions]);

  const handleCreateStudy = async () => {
    if (!token) return;
    if (!selectedOptionId) {
      setError("Please select a study type.");
      return;
    }
    // We strictly use visitId (ServiceVisit UUID)
    if (!visitId) {
      setError("Visit information is missing.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const selected = studyOptions.find((item) => item.id === selectedOptionId);
      if (!selected) {
        throw new Error("Selected study option is unavailable.");
      }

      // Workflow API: create report (and optionally item if missing)
      const payload = {
        visit_id: visitId,
      };

      // NOTE: If USGReportViewSet requires an existing item, and one doesn't exist, this might fail.
      // However, usually USG visits have items created at Registration.
      // If the user wants to ADD a new study not in Registration, they should use "Add Service" workflow?
      // Assuming Registration phase happened.

      const study = await apiPost("/workflow/usg/", token, payload);
      setSuccess("USG report created.");
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
                        {study.status === "published" || study.status === "final" ? "View" : "Continue Draft"}
                      </Button>
                      <Button
                        variant="secondary"
                        onClick={() => navigate(`/usg/studies/${study.id}?preview=1`)}
                      >
                        Preview
                      </Button>
                      {(study.status === "published" || study.status === "final") && (
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
            <label style={{ display: "block", marginBottom: 6 }}>Select study type</label>
            <select
              value={selectedOptionId}
              onChange={(event) => setSelectedOptionId(event.target.value)}
              style={{
                width: "100%",
                padding: 8,
                borderRadius: theme.radius.base,
                border: `1px solid ${theme.colors.border}`,
              }}
            >
              {studyOptions.map((option) => (
                <option key={option.id} value={option.id}>
                  {option.label}
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
