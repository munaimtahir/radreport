import React, { useEffect, useState } from "react";
import { useAuth } from "../ui/auth";
import { apiGet } from "../ui/api";
import PageHeader from "../ui/components/PageHeader";
import ErrorAlert from "../ui/components/ErrorAlert";
import Button from "../ui/components/Button";

interface ServiceVisit {
  id: string;
  visit_id: string;
  patient_name: string;
  patient_reg_no: string;
  service_name: string;
  service_code: string;
  status: string;
  registered_at: string;
  usg_report?: {
    published_pdf_url?: string;
  };
  opd_consult?: {
    published_pdf_url?: string;
  };
}

export default function FinalReportsPage() {
  const { token } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const [visits, setVisits] = useState<ServiceVisit[]>([]);
  const [filter, setFilter] = useState<"all" | "USG" | "OPD">("all");

  useEffect(() => {
    if (token) {
      loadVisits();
    }
  }, [token, filter]);

  const loadVisits = async () => {
    if (!token) return;
    setLoading(true);
    try {
      let url = "/workflow/visits/?status=PUBLISHED";
      if (filter !== "all") {
        url += `&workflow=${filter}`;
      }
      const data = await apiGet(url, token);
      setVisits(data.results || data || []);
      setError("");
    } catch (err: any) {
      setError(err.message || "Failed to load reports");
    } finally {
      setLoading(false);
    }
  };

  const getPdfUrl = (visit: ServiceVisit) => {
    if (visit.service_code === "USG" && visit.usg_report?.published_pdf_url) {
      return visit.usg_report.published_pdf_url;
    }
    if (visit.service_code === "OPD" && visit.opd_consult?.published_pdf_url) {
      return visit.opd_consult.published_pdf_url;
    }
    return null;
  };

  const downloadPdf = (visit: ServiceVisit) => {
    if (!token) {
      setError("Authentication required. Please log in again.");
      return;
    }
    
    const url = getPdfUrl(visit);
    if (!url) return;
    
    window.open(url, "_blank");
  };

  return (
    <div style={{ maxWidth: 1400, margin: "0 auto" }}>
      <PageHeader title="Final Reports" />
      
      {error && <ErrorAlert message={error} onDismiss={() => setError("")} />}
      
      <div style={{ marginBottom: 16, display: "flex", gap: 8, alignItems: "center" }}>
        <label><strong>Filter:</strong></label>
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value as "all" | "USG" | "OPD")}
          style={{ padding: "6px 12px", fontSize: 14 }}
        >
          <option value="all">All Reports</option>
          <option value="USG">USG Reports</option>
          <option value="OPD">OPD Prescriptions</option>
        </select>
        <div style={{ marginLeft: "auto", color: "#666" }}>
          Total: {visits.length} reports
        </div>
      </div>
      
      {loading ? (
        <div style={{ textAlign: "center", padding: 40 }}>Loading...</div>
      ) : visits.length === 0 ? (
        <div style={{ textAlign: "center", padding: 40, color: "#999" }}>
          No published reports found
        </div>
      ) : (
        <div style={{ border: "1px solid #ddd", borderRadius: 8, overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ backgroundColor: "#f5f5f5" }}>
                <th style={{ padding: 12, textAlign: "left", borderBottom: "2px solid #ddd" }}>Visit ID</th>
                <th style={{ padding: 12, textAlign: "left", borderBottom: "2px solid #ddd" }}>Patient</th>
                <th style={{ padding: 12, textAlign: "left", borderBottom: "2px solid #ddd" }}>Service</th>
                <th style={{ padding: 12, textAlign: "left", borderBottom: "2px solid #ddd" }}>Date</th>
                <th style={{ padding: 12, textAlign: "center", borderBottom: "2px solid #ddd" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {visits.map((visit) => (
                <tr key={visit.id} style={{ borderBottom: "1px solid #eee" }}>
                  <td style={{ padding: 12 }}>
                    <strong>{visit.visit_id}</strong>
                  </td>
                  <td style={{ padding: 12 }}>
                    {visit.patient_name}
                    <br />
                    <small style={{ color: "#666" }}>{visit.patient_reg_no}</small>
                  </td>
                  <td style={{ padding: 12 }}>
                    {visit.service_name}
                    <br />
                    <small style={{ color: "#666" }}>{visit.service_code}</small>
                  </td>
                  <td style={{ padding: 12 }}>
                    {new Date(visit.registered_at).toLocaleDateString()}
                    <br />
                    <small style={{ color: "#666" }}>
                      {new Date(visit.registered_at).toLocaleTimeString()}
                    </small>
                  </td>
                  <td style={{ padding: 12, textAlign: "center" }}>
                    {getPdfUrl(visit) ? (
                      <Button onClick={() => downloadPdf(visit)} style={{ padding: "6px 12px", fontSize: 13 }}>
                        View PDF
                      </Button>
                    ) : (
                      <span style={{ color: "#999" }}>PDF not available</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
