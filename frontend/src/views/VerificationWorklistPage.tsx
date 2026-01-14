import React, { useEffect, useState } from "react";
import { useAuth } from "../ui/auth";
import { apiGet, apiPost } from "../ui/api";
import PageHeader from "../ui/components/PageHeader";
import ErrorAlert from "../ui/components/ErrorAlert";
import SuccessAlert from "../ui/components/SuccessAlert";
import Button from "../ui/components/Button";

interface ServiceVisit {
  id: string;
  visit_id: string;
  patient_name: string;
  patient_reg_no: string;
  service_name: string;
  status: string;
  registered_at: string;
}

interface USGReport {
  id: string;
  service_visit_id: string;
  report_json: Record<string, any>;
  template_schema?: TemplateSchema | null;
  template_name?: string;
}

interface TemplateField {
  id: string;
  label: string;
  key: string;
  type: string;
  required: boolean;
  unit: string;
}

interface TemplateSection {
  id: string;
  title: string;
  fields: TemplateField[];
}

interface TemplateSchema {
  name?: string;
  sections: TemplateSection[];
}

export default function VerificationWorklistPage() {
  const { token } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const [success, setSuccess] = useState<string>("");
  const [visits, setVisits] = useState<ServiceVisit[]>([]);
  const [selectedVisit, setSelectedVisit] = useState<ServiceVisit | null>(null);
  const [report, setReport] = useState<USGReport | null>(null);
  const [returnReason, setReturnReason] = useState("");

  useEffect(() => {
    if (token) {
      loadVisits();
    }
  }, [token]);

  const loadVisits = async () => {
    if (!token) return;
    try {
      const data = await apiGet("/workflow/visits/?workflow=USG&status=PENDING_VERIFICATION", token);
      setVisits(data.results || data || []);
    } catch (err: any) {
      setError(err.message || "Failed to load visits");
    }
  };

  const loadReport = async (visitId: string) => {
    if (!token) return;
    try {
      const data = await apiGet(`/workflow/usg/?visit_id=${visitId}`, token);
      if (data && data.length > 0) {
        setReport(data[0]);
      } else {
        setReport(null);
      }
    } catch (err: any) {
      setReport(null);
    }
  };

  const handleSelectVisit = async (visit: ServiceVisit) => {
    setSelectedVisit(visit);
    await loadReport(visit.id);
    setReturnReason("");
  };

  const publish = async () => {
    if (!token || !selectedVisit || !report) return;
    setLoading(true);
    setError("");
    try {
      await apiPost(`/workflow/usg/${report.id}/publish/`, token, {});
      setSuccess("Report published successfully!");
      
      // Fetch PDF with auth token and open in new window
      const API_BASE = (import.meta as any).env.VITE_API_BASE || ((import.meta as any).env.PROD ? "/api" : "http://localhost:8000/api");
      const reportUrl = `${API_BASE}/pdf/${selectedVisit.id}/report/`;
      
      fetch(reportUrl, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
        .then((res) => {
          if (!res.ok) throw new Error("Failed to fetch report PDF");
          return res.blob();
        })
        .then((blob) => {
          const url = window.URL.createObjectURL(blob);
          const win = window.open(url, "_blank");
          if (win) {
            // Clean up blob URL after a delay
            setTimeout(() => window.URL.revokeObjectURL(url), 100);
          }
        })
        .catch((err) => {
          console.error("Failed to load report:", err);
          setError("Failed to load report PDF. Please try again.");
        });
      
      setSelectedVisit(null);
      setReport(null);
      await loadVisits();
    } catch (err: any) {
      setError(err.message || "Failed to publish report");
    } finally {
      setLoading(false);
    }
  };

  const returnForCorrection = async () => {
    if (!token || !selectedVisit || !report) return;
    if (!returnReason.trim()) {
      setError("Please provide a reason for return");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await apiPost(`/workflow/usg/${report.id}/return_for_correction/`, token, {
        reason: returnReason,
      });
      setSuccess("Report returned for correction");
      setSelectedVisit(null);
      setReport(null);
      setReturnReason("");
      await loadVisits();
    } catch (err: any) {
      setError(err.message || "Failed to return report");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 1400, margin: "0 auto" }}>
      <PageHeader title="Verification Worklist" subtitle="Verification Desk" />
      
      {error && <ErrorAlert message={error} onDismiss={() => setError("")} />}
      {success && <SuccessAlert message={success} onDismiss={() => setSuccess("")} />}
      
      <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: 20 }}>
        {/* Visit List */}
        <div style={{ border: "1px solid #ddd", padding: 16, borderRadius: 8, maxHeight: "80vh", overflowY: "auto" }}>
          <h2>Pending Verification ({visits.length})</h2>
          {visits.length === 0 ? (
            <p>No reports pending verification</p>
          ) : (
            <div style={{ display: "grid", gap: 8 }}>
              {visits.map((visit) => (
                <div
                  key={visit.id}
                  onClick={() => handleSelectVisit(visit)}
                  style={{
                    padding: 12,
                    border: selectedVisit?.id === visit.id ? "2px solid #0B5ED7" : "1px solid #ddd",
                    borderRadius: 4,
                    cursor: "pointer",
                    backgroundColor: selectedVisit?.id === visit.id ? "#f0f7ff" : "white",
                  }}
                >
                  <div><strong>{visit.visit_id}</strong></div>
                  <div style={{ fontSize: 14, color: "#666" }}>
                    {visit.patient_name} ({visit.patient_reg_no})
                  </div>
                  <div style={{ fontSize: 12, color: "#999" }}>
                    {new Date(visit.registered_at).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        
        {/* Report Review */}
        {selectedVisit && report && (
          <div style={{ border: "1px solid #ddd", padding: 20, borderRadius: 8, maxHeight: "80vh", overflowY: "auto" }}>
            <h2>USG Report Review - {selectedVisit.visit_id}</h2>
            <div style={{ marginBottom: 16, padding: 12, backgroundColor: "#f5f5f5", borderRadius: 4 }}>
              <div><strong>Patient:</strong> {selectedVisit.patient_name} ({selectedVisit.patient_reg_no})</div>
              <div><strong>Service:</strong> {selectedVisit.service_name}</div>
            </div>
            
            {!report.template_schema && (
              <div style={{ marginBottom: 16, padding: 12, backgroundColor: "#fff3cd", borderRadius: 4, border: "1px solid #ffeeba" }}>
                No template schema available for this report.
              </div>
            )}

            {report.template_schema && (
              <div style={{ display: "grid", gap: 16, marginBottom: 16 }}>
                {report.template_schema.sections.map((section) => (
                  <div key={section.id} style={{ border: "1px solid #ddd", padding: 16, borderRadius: 4 }}>
                    <h3 style={{ marginTop: 0 }}>{section.title}</h3>
                    <div style={{ display: "grid", gap: 10 }}>
                      {section.fields.map((field) => {
                        const value = report.report_json?.[field.key];
                        const displayValue = Array.isArray(value) ? value.join(", ") : value ?? "—";
                        return (
                          <div key={field.id}>
                            <div style={{ fontSize: 13, color: "#666" }}>
                              {field.label}
                              {field.unit ? ` (${field.unit})` : ""}
                            </div>
                            <div style={{ padding: "6px 0" }}>{String(displayValue)}</div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            )}
            
            <div style={{ marginBottom: 16 }}>
              <label><strong>Return Reason (if returning for correction):</strong></label>
              <textarea
                value={returnReason}
                onChange={(e) => setReturnReason(e.target.value)}
                rows={3}
                style={{ width: "100%", padding: 8 }}
                placeholder="Enter reason for return..."
              />
            </div>
            
            <div style={{ display: "flex", gap: 8 }}>
              <Button variant="success" onClick={publish} disabled={loading}>
                Publish Report
              </Button>
              <Button variant="warning" onClick={returnForCorrection} disabled={loading || !returnReason.trim()}>
                Return for Correction
              </Button>
            </div>
          </div>
        )}
        
        {selectedVisit && !report && (
          <div style={{ border: "1px solid #ddd", padding: 20, borderRadius: 8, textAlign: "center", color: "#999" }}>
            Report not found for this visit
          </div>
        )}
        
        {!selectedVisit && (
          <div style={{ border: "1px solid #ddd", padding: 20, borderRadius: 8, textAlign: "center", color: "#999" }}>
            Select a report from the list to verify
          </div>
        )}
      </div>
    </div>
  );
}
