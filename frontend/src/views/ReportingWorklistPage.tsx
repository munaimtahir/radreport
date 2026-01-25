import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../ui/auth";
import { apiGet } from "../ui/api";
import { theme } from "../theme";
import PageHeader from "../ui/components/PageHeader";
import Button from "../ui/components/Button";
import ErrorAlert from "../ui/components/ErrorAlert";

interface ServiceVisitItem {
    id: string;
    visit_id: string;
    patient_name: string;
    patient_mrn: string;
    service_name: string;
    department: string;
    status: string;
    status_display: string;
    created_at: string;
    updated_at: string;
}

export default function ReportingWorklistPage() {
    const { token } = useAuth();
    const navigate = useNavigate();
    const [items, setItems] = useState<ServiceVisitItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [filter, setFilter] = useState("ALL");

    useEffect(() => {
        if (token) {
            loadWorklist();
        }
    }, [token]);

    const loadWorklist = async () => {
        try {
            setLoading(true);
            setError(null);
            // Fetching from the item-centric worklist endpoint
            // We filter for reporting-related statuses
            const data = await apiGet("/workflow/items/worklist/", token);
            setItems(data || []);
        } catch (e: any) {
            setError(e.message || "Failed to load reporting worklist");
        } finally {
            setLoading(false);
        }
    };

    const getActionLabel = (item: ServiceVisitItem) => {
        const status = item.status;
        if (["REGISTERED", "IN_PROGRESS", "RETURNED_FOR_CORRECTION"].includes(status)) {
            return "Enter Report";
        }
        return "View Report";
    };

    const filteredItems = items.filter(item => {
        if (filter === "ALL") return true;
        if (filter === "PENDING") return ["REGISTERED", "IN_PROGRESS", "RETURNED_FOR_CORRECTION"].includes(item.status);
        if (filter === "COMPLETED") return ["PENDING_VERIFICATION", "FINALIZED", "PUBLISHED"].includes(item.status);
        return true;
    });

    const getStatusColor = (status: string) => {
        switch (status) {
            case "REGISTERED": return { bg: theme.colors.backgroundGray, text: theme.colors.textSecondary };
            case "IN_PROGRESS": return { bg: "#fff3cd", text: "#856404" };
            case "RETURNED_FOR_CORRECTION": return { bg: "#f8d7da", text: "#842029" };
            case "PENDING_VERIFICATION": return { bg: theme.colors.brandBlueSoft, text: theme.colors.brandBlue };
            case "PUBLISHED": return { bg: "#d1e7dd", text: "#0f5132" };
            default: return { bg: theme.colors.backgroundGray, text: theme.colors.textPrimary };
        }
    };

    return (
        <div style={{ maxWidth: 1200, margin: "0 auto" }}>
            <PageHeader
                title="Reporting Worklist"
                subtitle="Manage radiology and diagnostic reports"
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
                {/* Toolbar */}
                <div style={{
                    padding: 16,
                    borderBottom: `1px solid ${theme.colors.border}`,
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    backgroundColor: theme.colors.backgroundGray
                }}>
                    <div style={{ display: "flex", gap: 8 }}>
                        <Button
                            variant={filter === "ALL" ? "primary" : "secondary"}
                            onClick={() => setFilter("ALL")}
                            style={{ padding: "6px 16px", fontSize: 13 }}
                        >
                            All Items
                        </Button>
                        <Button
                            variant={filter === "PENDING" ? "primary" : "secondary"}
                            onClick={() => setFilter("PENDING")}
                            style={{ padding: "6px 16px", fontSize: 13 }}
                        >
                            Pending
                        </Button>
                        <Button
                            variant={filter === "COMPLETED" ? "primary" : "secondary"}
                            onClick={() => setFilter("COMPLETED")}
                            style={{ padding: "6px 16px", fontSize: 13 }}
                        >
                            Completed
                        </Button>
                    </div>
                    <Button variant="secondary" onClick={loadWorklist} disabled={loading} style={{ padding: "6px 16px", fontSize: 13 }}>
                        {loading ? "Refreshing..." : "Refresh"}
                    </Button>
                </div>

                {/* Table */}
                <div style={{ overflowX: "auto" }}>
                    <table style={{ width: "100%", borderCollapse: "collapse" }}>
                        <thead>
                            <tr style={{ borderBottom: `2px solid ${theme.colors.border}`, backgroundColor: "white" }}>
                                <th style={thStyle}>Date</th>
                                <th style={thStyle}>Patient Info</th>
                                <th style={thStyle}>Service</th>
                                <th style={thStyle}>Department</th>
                                <th style={thStyle}>Status</th>
                                <th style={{ ...thStyle, textAlign: "right" }}>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading && items.length === 0 ? (
                                <tr>
                                    <td colSpan={6} style={{ padding: 40, textAlign: "center", color: theme.colors.textTertiary }}>
                                        Loading worklist items...
                                    </td>
                                </tr>
                            ) : filteredItems.length === 0 ? (
                                <tr>
                                    <td colSpan={6} style={{ padding: 40, textAlign: "center", color: theme.colors.textTertiary }}>
                                        No items found matching your filters.
                                    </td>
                                </tr>
                            ) : (
                                filteredItems.map(item => {
                                    const statusColors = getStatusColor(item.status);
                                    return (
                                        <tr key={item.id} style={{ borderBottom: `1px solid ${theme.colors.borderLight}`, transition: "background 0.2s" }} onMouseEnter={e => e.currentTarget.style.backgroundColor = "#f8f9fa"} onMouseLeave={e => e.currentTarget.style.backgroundColor = "transparent"}>
                                            <td style={tdStyle}>
                                                <div style={{ fontSize: 13 }}>{new Date(item.created_at).toLocaleDateString()}</div>
                                                <div style={{ fontSize: 11, color: theme.colors.textTertiary }}>{new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                                            </td>
                                            <td style={tdStyle}>
                                                <div style={{ fontWeight: 600, fontSize: 14 }}>{item.patient_name}</div>
                                                <div style={{ fontSize: 12, color: theme.colors.textSecondary }}>{item.patient_mrn}</div>
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
                                                    {item.department}
                                                </span>
                                            </td>
                                            <td style={tdStyle}>
                                                <span style={{
                                                    fontSize: 12,
                                                    fontWeight: 600,
                                                    padding: "4px 10px",
                                                    borderRadius: 999,
                                                    backgroundColor: statusColors.bg,
                                                    color: statusColors.text,
                                                    display: "inline-block",
                                                    whiteSpace: "nowrap"
                                                }}>
                                                    {item.status_display}
                                                </span>
                                            </td>
                                            <td style={{ ...tdStyle, textAlign: "right" }}>
                                                <Button
                                                    variant={["REGISTERED", "IN_PROGRESS", "RETURNED_FOR_CORRECTION"].includes(item.status) ? "primary" : "secondary"}
                                                    style={{ padding: "6px 12px", fontSize: 13 }}
                                                    onClick={() => navigate(`/worklist/${item.id}/report`)}
                                                >
                                                    {getActionLabel(item)}
                                                </Button>
                                            </td>
                                        </tr>
                                    );
                                })
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
