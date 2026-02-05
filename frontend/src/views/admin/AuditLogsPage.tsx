import React, { useCallback, useEffect, useState } from "react";
import { useAuth } from "../../ui/auth";
import { apiGet, API_BASE } from "../../ui/api";
import { theme } from "../../theme";
import Button from "../../ui/components/Button";
import ErrorAlert from "../../ui/components/ErrorAlert";

interface AuditLog {
    id: string;
    actor: string | null;
    actor_username: string | null;
    actor_email: string | null;
    action: string;
    entity_type: string;
    entity_id: string;
    timestamp: string;
    metadata: Record<string, any>;
}

const ACTION_COLORS: Record<string, { bg: string; text: string }> = {
    clone: { bg: "#dbeafe", text: "#1d4ed8" },
    activate: { bg: "#dcfce7", text: "#166534" },
    freeze: { bg: "#e0e7ff", text: "#4338ca" },
    unfreeze: { bg: "#fef3c7", text: "#92400e" },
    archive: { bg: "#f3f4f6", text: "#6b7280" },
    import: { bg: "#fce7f3", text: "#be185d" },
    apply_baseline: { bg: "#f0fdf4", text: "#15803d" },
    delete_blocked: { bg: "#fee2e2", text: "#dc2626" },
    edit: { bg: "#fef9c3", text: "#a16207" },
    create: { bg: "#d1fae5", text: "#065f46" },
};

function ActionBadge({ action }: { action: string }) {
    const { bg, text } = ACTION_COLORS[action] || { bg: "#f3f4f6", text: "#6b7280" };

    return (
        <span style={{
            display: "inline-block",
            padding: "4px 10px",
            borderRadius: 9999,
            backgroundColor: bg,
            color: text,
            fontSize: 12,
            fontWeight: 600,
            textTransform: "capitalize",
        }}>
            {action.replace("_", " ")}
        </span>
    );
}

export default function AuditLogsPage() {
    const { token } = useAuth();
    const [logs, setLogs] = useState<AuditLog[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Filters
    const [entityFilter, setEntityFilter] = useState("");
    const [actionFilter, setActionFilter] = useState("");
    const [actorFilter, setActorFilter] = useState("");

    const loadData = useCallback(async () => {
        if (!token) return;
        try {
            setLoading(true);
            setError(null);

            let url = "/reporting/audit-logs/";
            const params = new URLSearchParams();
            if (entityFilter) params.set("entity", entityFilter);
            if (actionFilter) params.set("action", actionFilter);
            if (actorFilter) params.set("actor", actorFilter);
            const query = params.toString();
            if (query) url += `?${query}`;

            const data = await apiGet(url, token);
            setLogs(Array.isArray(data) ? data : data.results || []);
        } catch (e: any) {
            setError(e.message || "Failed to load audit logs");
        } finally {
            setLoading(false);
        }
    }, [token, entityFilter, actionFilter, actorFilter]);

    useEffect(() => {
        loadData();
    }, [loadData]);

    const downloadCsv = async () => {
        if (!token) return;
        let url = "/reporting/audit-logs/export-csv/";
        const params = new URLSearchParams();
        if (entityFilter) params.set("entity", entityFilter);
        if (actionFilter) params.set("action", actionFilter);
        if (actorFilter) params.set("actor", actorFilter);
        const query = params.toString();
        if (query) url += `?${query}`;

        const response = await fetch(`${API_BASE}${url}`, {
            headers: { Authorization: `Bearer ${token}` }
        });
        if (!response.ok) {
            const text = await response.text();
            throw new Error(text || "Download failed");
        }
        const blob = await response.blob();
        const blobUrl = window.URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = blobUrl;
        link.download = "audit_logs.csv";
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(blobUrl);
    };

    const formatTimestamp = (ts: string) => {
        const date = new Date(ts);
        return date.toLocaleString();
    };

    const formatMetadata = (metadata: Record<string, any>) => {
        if (!metadata || Object.keys(metadata).length === 0) return "-";
        return Object.entries(metadata)
            .map(([k, v]) => `${k}: ${JSON.stringify(v)}`)
            .join(", ");
    };

    return (
        <div style={{ padding: 20 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
                <div>
                    <h1 style={{ fontSize: 24, margin: 0 }}>Audit Logs</h1>
                    <p style={{ margin: "8px 0 0", color: theme.colors.textSecondary, fontSize: 14 }}>
                        Template governance audit trail
                    </p>
                </div>
                <Button variant="secondary" onClick={downloadCsv}>
                    Export CSV
                </Button>
            </div>

            {/* Filters */}
            <div style={{
                display: "flex",
                gap: 16,
                marginBottom: 20,
                padding: 16,
                backgroundColor: theme.colors.backgroundGray,
                borderRadius: theme.radius.md,
            }}>
                <div>
                    <label style={{ display: "block", marginBottom: 4, fontSize: 12, fontWeight: 500 }}>
                        Entity Type
                    </label>
                    <select
                        value={entityFilter}
                        onChange={(e) => setEntityFilter(e.target.value)}
                        style={{
                            padding: "8px 12px",
                            borderRadius: theme.radius.md,
                            border: `1px solid ${theme.colors.border}`,
                            minWidth: 150,
                        }}
                    >
                        <option value="">All</option>
                        <option value="report_profile">Report Profile</option>
                        <option value="report_parameter">Report Parameter</option>
                        <option value="service_profile">Service Profile</option>
                    </select>
                </div>

                <div>
                    <label style={{ display: "block", marginBottom: 4, fontSize: 12, fontWeight: 500 }}>
                        Action
                    </label>
                    <select
                        value={actionFilter}
                        onChange={(e) => setActionFilter(e.target.value)}
                        style={{
                            padding: "8px 12px",
                            borderRadius: theme.radius.md,
                            border: `1px solid ${theme.colors.border}`,
                            minWidth: 150,
                        }}
                    >
                        <option value="">All</option>
                        <option value="clone">Clone</option>
                        <option value="activate">Activate</option>
                        <option value="freeze">Freeze</option>
                        <option value="unfreeze">Unfreeze</option>
                        <option value="archive">Archive</option>
                        <option value="import">Import</option>
                        <option value="apply_baseline">Apply Baseline</option>
                        <option value="delete_blocked">Delete Blocked</option>
                        <option value="edit">Edit</option>
                        <option value="create">Create</option>
                    </select>
                </div>

                <div>
                    <label style={{ display: "block", marginBottom: 4, fontSize: 12, fontWeight: 500 }}>
                        Actor
                    </label>
                    <input
                        type="text"
                        value={actorFilter}
                        onChange={(e) => setActorFilter(e.target.value)}
                        placeholder="Username..."
                        style={{
                            padding: "8px 12px",
                            borderRadius: theme.radius.md,
                            border: `1px solid ${theme.colors.border}`,
                            minWidth: 150,
                        }}
                    />
                </div>

                <div style={{ display: "flex", alignItems: "flex-end" }}>
                    <Button variant="secondary" onClick={loadData}>
                        Apply Filters
                    </Button>
                </div>
            </div>

            {error && <ErrorAlert message={error} />}

            {loading ? (
                <div style={{ padding: 40, textAlign: "center" }}>Loading...</div>
            ) : (
                <div style={{
                    backgroundColor: "white",
                    borderRadius: theme.radius.lg,
                    border: `1px solid ${theme.colors.border}`,
                    overflow: "hidden"
                }}>
                    <table style={{ width: "100%", borderCollapse: "collapse" }}>
                        <thead>
                            <tr style={{ backgroundColor: theme.colors.backgroundGray, borderBottom: `1px solid ${theme.colors.border}` }}>
                                <th style={{ padding: 12, textAlign: "left" }}>Timestamp</th>
                                <th style={{ padding: 12, textAlign: "left" }}>Actor</th>
                                <th style={{ padding: 12, textAlign: "center" }}>Action</th>
                                <th style={{ padding: 12, textAlign: "left" }}>Entity</th>
                                <th style={{ padding: 12, textAlign: "left" }}>Details</th>
                            </tr>
                        </thead>
                        <tbody>
                            {logs.map(log => (
                                <tr key={log.id} style={{ borderBottom: `1px solid ${theme.colors.borderLight}` }}>
                                    <td style={{ padding: 12, fontSize: 13, color: theme.colors.textSecondary }}>
                                        {formatTimestamp(log.timestamp)}
                                    </td>
                                    <td style={{ padding: 12 }}>
                                        <span style={{ fontWeight: 500 }}>{log.actor_username || "-"}</span>
                                        {log.actor_email && (
                                            <span style={{ display: "block", fontSize: 12, color: theme.colors.textSecondary }}>
                                                {log.actor_email}
                                            </span>
                                        )}
                                    </td>
                                    <td style={{ padding: 12, textAlign: "center" }}>
                                        <ActionBadge action={log.action} />
                                    </td>
                                    <td style={{ padding: 12 }}>
                                        <span style={{ fontWeight: 500 }}>{log.entity_type}</span>
                                        <span style={{
                                            display: "block",
                                            fontSize: 12,
                                            color: theme.colors.textSecondary,
                                            fontFamily: "monospace",
                                        }}>
                                            {log.entity_id.substring(0, 8)}...
                                        </span>
                                    </td>
                                    <td style={{ padding: 12, fontSize: 12, color: theme.colors.textSecondary }}>
                                        {formatMetadata(log.metadata)}
                                    </td>
                                </tr>
                            ))}
                            {logs.length === 0 && (
                                <tr>
                                    <td colSpan={5} style={{ padding: 40, textAlign: "center", color: theme.colors.textSecondary }}>
                                        No audit logs found.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}
