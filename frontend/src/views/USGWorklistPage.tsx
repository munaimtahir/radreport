import React, { useEffect, useState } from "react";
import { useAuth } from "../ui/auth";
import { apiGet, apiPost } from "../ui/api";
import PageHeader from "../ui/components/PageHeader";
import ErrorAlert from "../ui/components/ErrorAlert";
import SuccessAlert from "../ui/components/SuccessAlert";
import Button from "../ui/components/Button";

interface ServiceVisitItem {
  id: string;
  service_visit_id: string;
  department_snapshot: string;
  status: string;
}

interface ServiceVisit {
  id: string;
  visit_id: string;
  patient_name: string;
  patient_reg_no: string;
  service_name: string;
  service_code: string;
  status: string;
  registered_at: string;
  items?: ServiceVisitItem[];
}

interface USGReport {
  id: string;
  service_visit_id: string;
  item_id?: string;  // service_visit_item_id (canonical identifier)
  report_json: any;
  return_reason?: string;
}

export default function USGWorklistPage() {
  const { token } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const [success, setSuccess] = useState<string>("");
  const [visits, setVisits] = useState<ServiceVisit[]>([]);
  const [selectedVisit, setSelectedVisit] = useState<ServiceVisit | null>(null);
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);  // service_visit_item_id (canonical)
  const [report, setReport] = useState<USGReport | null>(null);
  const [reportData, setReportData] = useState({
    findings: "",
    impression: "",
  });

  useEffect(() => {
    if (token) {
      loadVisits();
    }
  }, [token]);

  const loadVisits = async () => {
    if (!token) return;
    try {
      // Use repeated query params for multiple status values (preferred format)
      // This creates: ?workflow=USG&status=REGISTERED&status=RETURNED
      // NOT comma-separated: ?status=REGISTERED,RETURNED
      const params = new URLSearchParams();
      params.append("workflow", "USG");
      params.append("status", "REGISTERED");
      params.append("status", "RETURNED");
      // URLSearchParams.toString() will create repeated params correctly: ?key=value1&key=value2
      const queryString = params.toString();
      const data = await apiGet(`/workflow/visits/?${queryString}`, token);
      setVisits(data.results || data || []);
    } catch (err: any) {
      setError(err.message || "Failed to load visits");
    }
  };

  const loadReport = async (visitId: string, itemId?: string) => {
    if (!token) return;
    try {
      // Try item-centric lookup first (canonical), fallback to visit_id
      const queryParam = itemId ? `service_visit_item_id=${itemId}` : `visit_id=${visitId}`;
      const data = await apiGet(`/workflow/usg/?${queryParam}`, token);
      if (data && data.length > 0) {
        const r = data[0];
        setReport(r);
        // Use item_id from report if available, otherwise use the one we found
        if (r.item_id && !selectedItemId) {
          setSelectedItemId(r.item_id);
        }
        setReportData({
          findings: r.report_json?.findings || "",
          impression: r.report_json?.impression || "",
        });
      } else {
        setReport(null);
        setReportData({ findings: "", impression: "" });
      }
    } catch (err: any) {
      // Report might not exist yet
      setReport(null);
      setReportData({ findings: "", impression: "" });
    }
  };

  const handleSelectVisit = async (visit: ServiceVisit) => {
    setSelectedVisit(visit);
    
    // Find USG item (canonical identifier) - prefer department_snapshot="USG"
    const usgItem = visit.items?.find(item => item.department_snapshot === "USG");
    if (usgItem) {
      setSelectedItemId(usgItem.id);
      // Load report by service_visit_item_id (canonical)
      await loadReport(visit.id, usgItem.id);
    } else {
      // Fallback: use visit_id (legacy compatibility)
      setSelectedItemId(null);
      await loadReport(visit.id);
    }
  };

  const saveDraft = async () => {
    if (!token || !selectedVisit) return;
    setLoading(true);
    setError("");
    try {
      // First ensure report exists by creating/updating it
      const reportPayload: any = {
        report_json: {
          findings: reportData.findings,
          impression: reportData.impression,
        },
      };
      
      if (selectedItemId) {
        reportPayload.service_visit_item_id = selectedItemId;
      } else {
        reportPayload.visit_id = selectedVisit.id;  // Legacy fallback
      }
      
      // Create/update report first
      const savedReport = await apiPost("/workflow/usg/", token, reportPayload);
      
      // Update selectedItemId from saved report if available
      if (savedReport.item_id) {
        setSelectedItemId(savedReport.item_id);
      }
      
      // Use save_draft endpoint to properly transition status if needed
      await apiPost(`/workflow/usg/${savedReport.id}/save_draft/`, token, reportPayload);
      
      setSuccess("Draft saved successfully");
      
      // Reload report using canonical identifier
      if (selectedItemId || savedReport.item_id) {
        await loadReport(selectedVisit.id, selectedItemId || savedReport.item_id);
      } else {
        await loadReport(selectedVisit.id);
      }
    } catch (err: any) {
      setError(err.message || "Failed to save draft");
    } finally {
      setLoading(false);
    }
  };

  const submitForVerification = async () => {
    if (!token || !selectedVisit) return;
    setLoading(true);
    setError("");
    try {
      // Use service_visit_item_id (canonical) if available, fallback to visit_id (compatibility)
      const reportPayload: any = {
        report_json: {
          findings: reportData.findings,
          impression: reportData.impression,
        },
      };
      
      if (selectedItemId) {
        reportPayload.service_visit_item_id = selectedItemId;
      } else {
        reportPayload.visit_id = selectedVisit.id;  // Legacy fallback
      }
      
      // First create/update report (ensures same record is used)
      const savedReport = await apiPost("/workflow/usg/", token, reportPayload);
      
      // Update selectedItemId from saved report if available
      const canonicalItemId = savedReport.item_id || selectedItemId;
      if (savedReport.item_id) {
        setSelectedItemId(savedReport.item_id);
      }
      
      // Submit for verification using report ID (now handled correctly by fixed get_object())
      // OR use service_visit_item_id directly if supported (defensive approach)
      await apiPost(`/workflow/usg/${savedReport.id}/submit_for_verification/`, token, {
        report_json: reportPayload.report_json,  // Include latest data
      });
      
      setSuccess("Report submitted for verification");
      setSelectedVisit(null);
      setSelectedItemId(null);
      setReport(null);
      await loadVisits();
    } catch (err: any) {
      setError(err.message || "Failed to submit for verification");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 1400, margin: "0 auto" }}>
      <PageHeader title="USG Worklist" subtitle="Performance Desk" />
      
      {error && <ErrorAlert message={error} onDismiss={() => setError("")} />}
      {success && <SuccessAlert message={success} onDismiss={() => setSuccess("")} />}
      
      <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: 20 }}>
        {/* Visit List */}
        <div style={{ border: "1px solid #ddd", padding: 16, borderRadius: 8, maxHeight: "80vh", overflowY: "auto" }}>
          <h2>Pending Visits ({visits.length})</h2>
          {visits.length === 0 ? (
            <p>No visits pending</p>
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
                  {visit.status === "RETURNED" && (
                    <div style={{ fontSize: 12, color: "red", marginTop: 4 }}>
                      Returned for correction
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
        
        {/* Report Form */}
        {selectedVisit && (
          <div style={{ border: "1px solid #ddd", padding: 20, borderRadius: 8 }}>
            <h2>USG Report - {selectedVisit.visit_id}</h2>
            <div style={{ marginBottom: 16, padding: 12, backgroundColor: "#f5f5f5", borderRadius: 4 }}>
              <div><strong>Patient:</strong> {selectedVisit.patient_name} ({selectedVisit.patient_reg_no})</div>
              <div><strong>Service:</strong> {selectedVisit.service_name}</div>
            </div>
            
            {report?.return_reason && (
              <div style={{ marginBottom: 16, padding: 12, backgroundColor: "#fff3cd", borderRadius: 4, border: "1px solid #ffc107" }}>
                <strong>Return Reason:</strong> {report.return_reason}
              </div>
            )}
            
            <div style={{ marginBottom: 16 }}>
              <label><strong>Findings:</strong></label>
              <textarea
                value={reportData.findings}
                onChange={(e) => setReportData({ ...reportData, findings: e.target.value })}
                rows={10}
                style={{ width: "100%", padding: 8, fontSize: 14, fontFamily: "monospace" }}
                placeholder="Enter findings..."
              />
            </div>
            
            <div style={{ marginBottom: 16 }}>
              <label><strong>Impression:</strong></label>
              <textarea
                value={reportData.impression}
                onChange={(e) => setReportData({ ...reportData, impression: e.target.value })}
                rows={6}
                style={{ width: "100%", padding: 8, fontSize: 14, fontFamily: "monospace" }}
                placeholder="Enter impression..."
              />
            </div>
            
            <div style={{ display: "flex", gap: 8 }}>
              <Button variant="secondary" onClick={saveDraft} disabled={loading}>
                Save Draft
              </Button>
              <Button onClick={submitForVerification} disabled={loading || !reportData.findings.trim()}>
                Submit for Verification
              </Button>
            </div>
          </div>
        )}
        
        {!selectedVisit && (
          <div style={{ border: "1px solid #ddd", padding: 20, borderRadius: 8, textAlign: "center", color: "#999" }}>
            Select a visit from the list to start reporting
          </div>
        )}
      </div>
    </div>
  );
}
