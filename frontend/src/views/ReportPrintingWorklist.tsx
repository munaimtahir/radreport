import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../ui/auth";
import { apiGet } from "../ui/api";
import { theme } from "../theme";
import PageHeader from "../ui/components/PageHeader";
import Button from "../ui/components/Button";
import ErrorAlert from "../ui/components/ErrorAlert";
import { fetchPublishedPdf, fetchReportPdf } from "../ui/reporting";

interface ServiceVisitItem {
    id: string;
    visit_id: string;
    patient_name: string;
    patient_mrn: string;
    service_name: string;
    department_snapshot: string;
    status: string;
    report_status: "draft" | "submitted" | "verified" | null;
    status_display: string;
    created_at: string;
    updated_at: string;
}

export default function ReportPrintingWorklist() {
    const { token } = useAuth();
    const [items, setItems] = useState<ServiceVisitItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [searchTerm, setSearchTerm] = useState("");

    useEffect(() => {
        if (token) {
            loadPublishedReports();
        }
    }, [token]);

    const loadPublishedReports = async () => {
        try {
            setLoading(true);
            setError(null);
            // We fetch all worklist items and filter for PUBLISHED
            // Or use a targeted backend endpoint if available. 
            // For now, based on ReportingWorklistPage logic:
            const data = await apiGet("/workflow/items/worklist/?status=PUBLISHED,FINALIZED", token);
            setItems(data || []);
        } catch (e: any) {
            setError(e.message || "Failed to load published reports");
        } finally {
            setLoading(false);
        }
    };

    const handlePrint = async (item: ServiceVisitItem) => {
        try {
            // Fetch history to get the latest version
            const history = await apiGet(`/reporting/workitems/${item.id}/publish-history/`, token);
            let blob: Blob;
            if (history && history.length > 0) {
                const latestVersion = history[0].version; // History is ordered by -version
                blob = await fetchPublishedPdf(item.id, latestVersion, token);
            } else {
                // Fallback to live report PDF if no snapshots found (might be legacy or not snapshotted)
                blob = await fetchReportPdf(item.id, token);
            }
            const url = window.URL.createObjectURL(blob);
            window.open(url, "_blank");
        } catch (e: any) {
            setError("Failed to fetch PDF: " + e.message);
        }
    };

    const filteredItems = items.filter(item =>
        item.patient_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.patient_mrn.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.visit_id.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div style={{ maxWidth: 1200, margin: "0 auto" }}>
            <PageHeader
                title="Print Reports"
                subtitle="View and print all published diagnostic reports"
            />

            <div style={{ marginBottom: 20 }}>
                {error && <ErrorAlert message={error} />}
            </div>

            <div style={{
                backgroundColor: "white",
                borderRadius: theme.radius.lg,
                boxShadow: theme.shadows.sm,
                border: `1px solid ${theme.colors.border}`,
                overflow: "hidden"
            }}>
                <div style={{
                    padding: 16,
                    borderBottom: `1px solid ${theme.colors.border}`,
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    backgroundColor: theme.colors.backgroundGray,
                    gap: 16
                }}>
                    <div style={{ position: "relative", flex: 1, maxWidth: 400 }}>
                        <input
                            type="text"
                            placeholder="Search by Patient Name, MRN or Visit ID..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            style={{
                                width: "100%",
                                padding: "10px 16px",
                                borderRadius: theme.radius.base,
                                border: `1px solid ${theme.colors.border}`,
                                fontSize: 14,
                                outline: "none"
                            }}
                        />
                    </div>
                    <Button variant="secondary" onClick={loadPublishedReports} disabled={loading} style={{ padding: "6px 16px", fontSize: 13 }}>
                        {loading ? "Refreshing..." : "Refresh"}
                    </Button>
                </div>

                <div style={{ overflowX: "auto" }}>
                    <table style={{ width: "100%", borderCollapse: "collapse" }}>
                        <thead>
                            <tr style={{ borderBottom: `2px solid ${theme.colors.border}`, backgroundColor: "white" }}>
                                <th style={thStyle}>Published Date</th>
                                <th style={thStyle}>Patient Info</th>
                                <th style={thStyle}>Service / Visit</th>
                                <th style={thStyle}>Department</th>
                                <th style={{ ...thStyle, textAlign: "right" }}>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading && items.length === 0 ? (
                                <tr>
                                    <td colSpan={5} style={{ padding: 40, textAlign: "center", color: theme.colors.textTertiary }}>
                                        Loading reports...
                                    </td>
                                </tr>
                            ) : filteredItems.length === 0 ? (
                                <tr>
                                    <td colSpan={5} style={{ padding: 40, textAlign: "center", color: theme.colors.textTertiary }}>
                                        No published reports found.
                                    </td>
                                </tr>
                            ) : (
                                filteredItems.map(item => (
                                    <tr key={item.id} style={{ borderBottom: `1px solid ${theme.colors.borderLight}`, transition: "background 0.2s" }} onMouseEnter={e => e.currentTarget.style.backgroundColor = "#f8f9fa"} onMouseLeave={e => e.currentTarget.style.backgroundColor = "transparent"}>
                                        <td style={tdStyle}>
                                            <div style={{ fontSize: 13, fontWeight: 500 }}>{new Date(item.updated_at).toLocaleDateString()}</div>
                                            <div style={{ fontSize: 11, color: theme.colors.textTertiary }}>{new Date(item.updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                                        </td>
                                        <td style={tdStyle}>
                                            <div style={{ fontWeight: 600, fontSize: 14 }}>{item.patient_name}</div>
                                            <div style={{ fontSize: 12, color: theme.colors.textSecondary }}>MRN: {item.patient_mrn}</div>
                                        </td>
                                        <td style={tdStyle}>
                                            <div style={{ fontSize: 14 }}>{item.service_name}</div>
                                            <div style={{ fontSize: 11, color: theme.colors.textTertiary }}>Visit: {item.visit_id}</div>
                                        </td>
                                        <td style={tdStyle}>
                                            <span style={{
                                                fontSize: 11,
                                                fontWeight: 600,
                                                padding: "2px 6px",
                                                borderRadius: 4,
                                                backgroundColor: "#f0f0f0",
                                                color: "#666"
                                            }}>
                                                {item.department_snapshot}
                                            </span>
                                        </td>
                                        <td style={{ ...tdStyle, textAlign: "right" }}>
                                            <Button
                                                variant="primary"
                                                style={{
                                                    padding: "8px 16px",
                                                    fontSize: 13,
                                                    backgroundColor: theme.colors.success,
                                                    borderColor: theme.colors.success
                                                }}
                                                onClick={() => handlePrint(item)}
                                            >
                                                Print Report
                                            </Button>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}

const thStyle: React.CSSProperties = {
    textAlign: "left",
    padding: "16px",
    fontSize: 12,
    fontWeight: 600,
    textTransform: "uppercase",
    color: theme.colors.textSecondary,
    letterSpacing: "0.5px"
};

const tdStyle: React.CSSProperties = {
    padding: "16px",
    verticalAlign: "middle"
};
