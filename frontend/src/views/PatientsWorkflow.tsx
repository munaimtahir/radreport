import React, { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { getPatientTimeline, listWorkflowPatients } from "../ui/api";
import { useAuth } from "../ui/auth";
import PageHeader from "../ui/components/PageHeader";
import ErrorAlert from "../ui/components/ErrorAlert";
import Button from "../ui/components/Button";
import { theme } from "../theme";

interface WorkflowReceipt {
  available: boolean;
  receipt_id?: string | null;
  pdf_url?: string | null;
}

interface WorkflowReportItem {
  service_name: string;
  status: string;
  pdf_url?: string | null;
}

interface WorkflowReports {
  available: boolean;
  items: WorkflowReportItem[];
}

interface WorkflowPatientRow {
  patient_id: string;
  mrn: string;
  reg_no?: string | null;
  name: string;
  age?: number | null;
  sex?: string | null;
  phone?: string | null;
  last_visit_at?: string | null;
  latest_visit_id: string;
  workflow_status: string;
  receipt: WorkflowReceipt;
  reports: WorkflowReports;
}

interface TimelineVisit {
  visit_id: string;
  visit_code: string;
  registered_at: string;
  workflow_status: string;
  receipt: WorkflowReceipt;
  reports: WorkflowReports;
}

interface TimelineResponse {
  patient: {
    id: string;
    mrn: string;
    reg_no?: string | null;
    name: string;
    age?: number | null;
    sex?: string | null;
    phone?: string | null;
  };
  visits: TimelineVisit[];
}

const STATUS_OPTIONS = [
  { value: "", label: "All statuses" },
  { value: "registered", label: "Registered" },
  { value: "services_added", label: "Services added" },
  { value: "paid", label: "Paid" },
  { value: "sample_collected", label: "Sample collected" },
  { value: "report_pending", label: "Report pending" },
  { value: "report_ready", label: "Report ready" },
  { value: "report_published", label: "Report published" },
];

const API_BASE = (import.meta as any).env.VITE_API_BASE
  || ((import.meta as any).env.PROD ? "/api" : "http://localhost:8000/api");

const resolveApiUrl = (path?: string | null) => {
  if (!path) return "";
  if (path.startsWith("http")) return path;
  if (path.startsWith("/api")) {
    const baseRoot = API_BASE.replace(/\/api$/, "");
    return `${baseRoot}${path}`;
  }
  return `${API_BASE}${path.startsWith("/") ? "" : "/"}${path}`;
};

export default function PatientsWorkflow() {
  const { token } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchInput, setSearchInput] = useState(searchParams.get("search") || "");
  const [dateFrom, setDateFrom] = useState(searchParams.get("date_from") || "");
  const [dateTo, setDateTo] = useState(searchParams.get("date_to") || "");
  const [status, setStatus] = useState(searchParams.get("status") || "");
  const [rows, setRows] = useState<WorkflowPatientRow[]>([]);
  const [count, setCount] = useState(0);
  const [next, setNext] = useState<string | null>(null);
  const [previous, setPrevious] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [timelinePatientId, setTimelinePatientId] = useState<string | null>(null);
  const [timelineData, setTimelineData] = useState<TimelineResponse | null>(null);
  const [timelineLoading, setTimelineLoading] = useState(false);

  useEffect(() => {
    setSearchInput(searchParams.get("search") || "");
    setDateFrom(searchParams.get("date_from") || "");
    setDateTo(searchParams.get("date_to") || "");
    setStatus(searchParams.get("status") || "");
  }, [searchParams]);

  const updateParams = (updates: Record<string, string | null>, resetPage = false) => {
    const params = new URLSearchParams(searchParams);
    Object.entries(updates).forEach(([key, value]) => {
      if (!value) {
        params.delete(key);
      } else {
        params.set(key, value);
      }
    });
    if (resetPage) {
      params.set("page", "1");
    }
    setSearchParams(params, { replace: true });
  };

  useEffect(() => {
    const timer = window.setTimeout(() => {
      updateParams({ search: searchInput.trim() || null }, true);
    }, 350);
    return () => window.clearTimeout(timer);
  }, [searchInput]);

  useEffect(() => {
    if (!token) return;
    const fetchData = async () => {
      setLoading(true);
      setError("");
      try {
        const data = await listWorkflowPatients(token, {
          search: searchParams.get("search") || "",
          date_from: searchParams.get("date_from") || "",
          date_to: searchParams.get("date_to") || "",
          status: searchParams.get("status") || "",
          page: searchParams.get("page") ? Number(searchParams.get("page")) : 1,
          page_size: 20,
        });
        setRows(data.results || []);
        setCount(data.count || 0);
        setNext(data.next || null);
        setPrevious(data.previous || null);
      } catch (err: any) {
        setError(err.message || "Failed to load workflow list");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [token, searchParams]);

  const handleOpenPdf = async (pdfUrl?: string | null, filename?: string) => {
    if (!token || !pdfUrl) return;
    try {
      const resolvedUrl = resolveApiUrl(pdfUrl);
      const res = await fetch(resolvedUrl, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (!res.ok) {
        throw new Error(`Failed to fetch PDF: ${res.status} ${res.statusText}`);
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const win = window.open(url, "_blank");
      if (!win) {
        const link = document.createElement("a");
        link.href = url;
        link.target = "_blank";
        link.download = filename || "document.pdf";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }
      // Revoke blob URL after 15 seconds (sufficient for browser to load PDF)
      setTimeout(() => window.URL.revokeObjectURL(url), 15000);
    } catch (err: any) {
      setError(err.message || "Failed to open PDF");
    }
  };

  const handleViewTimeline = async (patientId: string) => {
    if (!token) return;
    setTimelinePatientId(patientId);
    setTimelineLoading(true);
    setError("");
    try {
      const data = await getPatientTimeline(token, patientId, {
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
      });
      setTimelineData(data as TimelineResponse);
    } catch (err: any) {
      setError(err.message || "Failed to load patient timeline");
    } finally {
      setTimelineLoading(false);
    }
  };

  const clearTimeline = () => {
    setTimelinePatientId(null);
    setTimelineData(null);
  };

  const pageSummary = useMemo(() => {
    if (loading) return "Loading patient workflows...";
    if (!rows.length) return "No patients found for the selected filters";
    return `${rows.length} of ${count} patients`;
  }, [loading, rows.length, count]);

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto" }}>
      <PageHeader title="Patient workflow" subtitle="Search, filter, and reprint receipts and reports" />

      {error && <ErrorAlert message={error} onDismiss={() => setError("")} />}

      <div style={{
        border: `1px solid ${theme.colors.border}`,
        borderRadius: theme.radius.md,
        padding: 16,
        backgroundColor: theme.colors.background,
        boxShadow: theme.shadows.sm,
        marginBottom: 20,
      }}>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 12, alignItems: "flex-end" }}>
          <div style={{ flex: "1 1 240px" }}>
            <label style={{ display: "block", marginBottom: 6, color: theme.colors.textSecondary, fontSize: 13 }}>
              Search
            </label>
            <input
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
              placeholder="Search name, MRN, phone, receipt"
              style={{
                width: "100%",
                padding: "10px 12px",
                borderRadius: theme.radius.base,
                border: `1px solid ${theme.colors.border}`,
                fontSize: 14,
              }}
            />
          </div>
          <div>
            <label style={{ display: "block", marginBottom: 6, color: theme.colors.textSecondary, fontSize: 13 }}>
              From
            </label>
            <input
              type="date"
              value={dateFrom}
              onChange={(event) => {
                setDateFrom(event.target.value);
                updateParams({ date_from: event.target.value || null }, true);
              }}
              style={{
                padding: "10px 12px",
                borderRadius: theme.radius.base,
                border: `1px solid ${theme.colors.border}`,
                fontSize: 14,
              }}
            />
          </div>
          <div>
            <label style={{ display: "block", marginBottom: 6, color: theme.colors.textSecondary, fontSize: 13 }}>
              To
            </label>
            <input
              type="date"
              value={dateTo}
              onChange={(event) => {
                setDateTo(event.target.value);
                updateParams({ date_to: event.target.value || null }, true);
              }}
              style={{
                padding: "10px 12px",
                borderRadius: theme.radius.base,
                border: `1px solid ${theme.colors.border}`,
                fontSize: 14,
              }}
            />
          </div>
          <div>
            <label style={{ display: "block", marginBottom: 6, color: theme.colors.textSecondary, fontSize: 13 }}>
              Status
            </label>
            <select
              value={status}
              onChange={(event) => {
                setStatus(event.target.value);
                updateParams({ status: event.target.value || null }, true);
              }}
              style={{
                padding: "10px 12px",
                borderRadius: theme.radius.base,
                border: `1px solid ${theme.colors.border}`,
                fontSize: 14,
                minWidth: 180,
              }}
            >
              {STATUS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          <Button
            variant="secondary"
            onClick={() => {
              setSearchInput("");
              setDateFrom("");
              setDateTo("");
              setStatus("");
              setSearchParams({}, { replace: true });
            }}
          >
            Clear filters
          </Button>
        </div>
        <div style={{ marginTop: 10, fontSize: 12, color: theme.colors.textTertiary }}>{pageSummary}</div>
      </div>

      <div style={{
        border: `1px solid ${theme.colors.border}`,
        borderRadius: theme.radius.md,
        backgroundColor: theme.colors.background,
        overflow: "hidden",
      }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead style={{ backgroundColor: theme.colors.backgroundGray }}>
            <tr>
              <th style={{ textAlign: "left", padding: 12, fontSize: 12, textTransform: "uppercase", color: theme.colors.textTertiary }}>
                MRN / Reg
              </th>
              <th style={{ textAlign: "left", padding: 12, fontSize: 12, textTransform: "uppercase", color: theme.colors.textTertiary }}>
                Patient
              </th>
              <th style={{ textAlign: "left", padding: 12, fontSize: 12, textTransform: "uppercase", color: theme.colors.textTertiary }}>
                Phone
              </th>
              <th style={{ textAlign: "left", padding: 12, fontSize: 12, textTransform: "uppercase", color: theme.colors.textTertiary }}>
                Last visit
              </th>
              <th style={{ textAlign: "left", padding: 12, fontSize: 12, textTransform: "uppercase", color: theme.colors.textTertiary }}>
                Status
              </th>
              <th style={{ textAlign: "left", padding: 12, fontSize: 12, textTransform: "uppercase", color: theme.colors.textTertiary }}>
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const statusLabel = row.workflow_status.replace(/_/g, " ");
              return (
                <tr key={row.patient_id} style={{ borderTop: `1px solid ${theme.colors.borderLight}` }}>
                  <td style={{ padding: 12, fontSize: 14 }}>
                    <div style={{ fontWeight: 600 }}>{row.mrn}</div>
                    <div style={{ fontSize: 12, color: theme.colors.textTertiary }}>{row.reg_no || "-"}</div>
                  </td>
                  <td style={{ padding: 12, fontSize: 14 }}>
                    <div style={{ fontWeight: 600 }}>{row.name}</div>
                    <div style={{ fontSize: 12, color: theme.colors.textTertiary }}>{row.age ? `${row.age} yrs` : "Age N/A"}</div>
                  </td>
                  <td style={{ padding: 12, fontSize: 14 }}>{row.phone || "-"}</td>
                  <td style={{ padding: 12, fontSize: 14 }}>
                    {row.last_visit_at ? new Date(row.last_visit_at).toLocaleString() : "-"}
                  </td>
                  <td style={{ padding: 12 }}>
                    <span style={{
                      display: "inline-block",
                      padding: "4px 10px",
                      borderRadius: 999,
                      backgroundColor: theme.colors.brandBlueSoft,
                      color: theme.colors.brandBlue,
                      fontSize: 12,
                      textTransform: "capitalize",
                    }}>
                      {statusLabel}
                    </span>
                  </td>
                  <td style={{ padding: 12 }}>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                      <Button
                        variant="secondary"
                        disabled={!row.receipt.available}
                        onClick={() => handleOpenPdf(row.receipt.pdf_url || undefined, `receipt_${row.mrn}.pdf`)}
                      >
                        {row.receipt.available ? "Reprint receipt" : "Receipt not available"}
                      </Button>
                      <Button
                        variant="secondary"
                        disabled={
                          !row.reports.available ||
                          !row.reports.items ||
                          row.reports.items.length === 0
                        }
                        onClick={() => {
                          const firstReport =
                            row.reports.items && row.reports.items.length > 0
                              ? row.reports.items[0]
                              : undefined;
                          const pdfUrl = firstReport?.pdf_url || undefined;
                          handleOpenPdf(pdfUrl, `report_${row.mrn}.pdf`);
                        }}
                      >
                        {row.reports.available ? "Print report" : "Report not published yet"}
                      </Button>
                      <Button variant="primary" onClick={() => handleViewTimeline(row.patient_id)}>
                        View timeline
                      </Button>
                    </div>
                  </td>
                </tr>
              );
            })}
            {!rows.length && !loading && (
              <tr>
                <td colSpan={6} style={{ padding: 20, textAlign: "center", color: theme.colors.textSecondary }}>
                  No patients found for the selected filters
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 16 }}>
        <Button
          variant="secondary"
          disabled={!previous}
          onClick={() => updateParams({ page: String(Math.max(1, Number(searchParams.get("page") || "1") - 1)) })}
        >
          Previous
        </Button>
        <Button
          variant="secondary"
          disabled={!next}
          onClick={() => updateParams({ page: String(Number(searchParams.get("page") || "1") + 1) })}
        >
          Next
        </Button>
      </div>

      {timelinePatientId && (
        <div style={{
          marginTop: 24,
          border: `1px solid ${theme.colors.border}`,
          borderRadius: theme.radius.md,
          backgroundColor: theme.colors.backgroundGray,
          padding: 16,
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <h3 style={{ margin: 0 }}>Patient timeline</h3>
              {timelineData?.patient && (
                <div style={{ fontSize: 13, color: theme.colors.textSecondary }}>
                  {timelineData.patient.name} · {timelineData.patient.mrn}
                </div>
              )}
            </div>
            <Button variant="secondary" onClick={clearTimeline}>Close</Button>
          </div>

          {timelineLoading && (
            <div style={{ marginTop: 12, color: theme.colors.textSecondary }}>Loading timeline...</div>
          )}

          {!timelineLoading && timelineData?.visits && timelineData.visits.length === 0 && (
            <div style={{ marginTop: 12, color: theme.colors.textSecondary }}>No visits found in this range.</div>
          )}

          {!timelineLoading && timelineData?.visits && timelineData.visits.length > 0 && (
            <div style={{ marginTop: 16, display: "grid", gap: 12 }}>
              {timelineData.visits.map((visit) => (
                <div key={visit.visit_id} style={{
                  border: `1px solid ${theme.colors.border}`,
                  borderRadius: theme.radius.base,
                  padding: 12,
                  backgroundColor: theme.colors.background,
                }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div>
                      <div style={{ fontWeight: 600 }}>{visit.visit_code}</div>
                      <div style={{ fontSize: 12, color: theme.colors.textTertiary }}>
                        {new Date(visit.registered_at).toLocaleString()}
                      </div>
                    </div>
                    <span style={{
                      display: "inline-block",
                      padding: "4px 10px",
                      borderRadius: 999,
                      backgroundColor: theme.colors.brandBlueSoft,
                      color: theme.colors.brandBlue,
                      fontSize: 12,
                      textTransform: "capitalize",
                    }}>
                      {visit.workflow_status.replace(/_/g, " ")}
                    </span>
                  </div>
                  <div style={{ marginTop: 10, display: "flex", flexWrap: "wrap", gap: 8 }}>
                    <Button
                      variant="secondary"
                      disabled={!visit.receipt.available}
                      onClick={() => handleOpenPdf(visit.receipt.pdf_url || undefined, `receipt_${visit.visit_code}.pdf`)}
                    >
                      {visit.receipt.available ? "Reprint receipt" : "Receipt not available"}
                    </Button>
                    <Button
                      variant="secondary"
                      disabled={
                        !visit.reports.available ||
                        !visit.reports.items ||
                        visit.reports.items.length === 0
                      }
                      onClick={() => {
                        const firstReport =
                          visit.reports.items && visit.reports.items.length > 0
                            ? visit.reports.items[0]
                            : undefined;
                        const pdfUrl = firstReport?.pdf_url || undefined;
                        handleOpenPdf(pdfUrl, `report_${visit.visit_code}.pdf`);
                      }}
                    >
                      {visit.reports.available ? "Print report" : "Report not published yet"}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
