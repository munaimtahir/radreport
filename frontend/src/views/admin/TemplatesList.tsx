import React, { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../ui/auth";
import { apiGet, apiDelete, apiPost, API_BASE } from "../../ui/api";
import { theme } from "../../theme";
import Button from "../../ui/components/Button";
import ErrorAlert from "../../ui/components/ErrorAlert";
import ImportModal from "../../ui/components/ImportModal";

interface TemplateProfile {
    id: string;
    code: string;
    name: string;
    modality: string;
    version: number;
    status: "draft" | "active" | "archived";
    is_frozen: boolean;
    used_by_reports: number;
    created_at: string;
    updated_at: string;
}

interface ConfirmModalProps {
    isOpen: boolean;
    title: string;
    message: string;
    confirmPhrase?: string;
    onConfirm: () => void;
    onCancel: () => void;
    loading?: boolean;
}

function ConfirmModal({ isOpen, title, message, confirmPhrase, onConfirm, onCancel, loading }: ConfirmModalProps) {
    const [inputValue, setInputValue] = useState("");

    useEffect(() => {
        if (!isOpen) setInputValue("");
    }, [isOpen]);

    if (!isOpen) return null;

    const canConfirm = !confirmPhrase || inputValue === confirmPhrase;

    return (
        <div style={{
            position: "fixed",
            top: 0, left: 0, right: 0, bottom: 0,
            backgroundColor: "rgba(0,0,0,0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
        }}>
            <div style={{
                backgroundColor: "white",
                borderRadius: theme.radius.lg,
                padding: 24,
                maxWidth: 450,
                width: "90%",
            }}>
                <h2 style={{ margin: "0 0 16px", fontSize: 20 }}>{title}</h2>
                <p style={{ marginBottom: 16, color: theme.colors.textSecondary }}>{message}</p>

                {confirmPhrase && (
                    <div style={{ marginBottom: 16 }}>
                        <label style={{ display: "block", marginBottom: 8, fontWeight: 500 }}>
                            Type <strong>{confirmPhrase}</strong> to confirm:
                        </label>
                        <input
                            type="text"
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            style={{
                                width: "100%",
                                padding: "10px 12px",
                                border: `1px solid ${theme.colors.border}`,
                                borderRadius: theme.radius.md,
                                fontSize: 14,
                            }}
                            placeholder={confirmPhrase}
                        />
                    </div>
                )}

                <div style={{ display: "flex", gap: 12, justifyContent: "flex-end" }}>
                    <Button variant="secondary" onClick={onCancel} disabled={loading}>
                        Cancel
                    </Button>
                    <Button
                        variant="primary"
                        onClick={onConfirm}
                        disabled={!canConfirm || loading}
                    >
                        {loading ? "Processing..." : "Confirm"}
                    </Button>
                </div>
            </div>
        </div>
    );
}

function StatusBadge({ status }: { status: string }) {
    const colors: Record<string, { bg: string; text: string }> = {
        active: { bg: "#dcfce7", text: "#166534" },
        draft: { bg: "#fef3c7", text: "#92400e" },
        archived: { bg: "#f3f4f6", text: "#6b7280" },
    };
    const { bg, text } = colors[status] || colors.archived;

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
            {status}
        </span>
    );
}

function FrozenBadge() {
    return (
        <span style={{
            display: "inline-block",
            padding: "4px 10px",
            borderRadius: 9999,
            backgroundColor: "#dbeafe",
            color: "#1d4ed8",
            fontSize: 12,
            fontWeight: 600,
            marginLeft: 8,
        }}>
            🔒 Frozen
        </span>
    );
}

export default function TemplatesList() {
    const { token } = useAuth();
    const navigate = useNavigate();
    const [profiles, setProfiles] = useState<TemplateProfile[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [isImportModalOpen, setImportModalOpen] = useState(false);
    const [showAll, setShowAll] = useState(false);
    const [actionLoading, setActionLoading] = useState(false);

    // Confirmation modal state
    const [confirmModal, setConfirmModal] = useState<{
        isOpen: boolean;
        title: string;
        message: string;
        confirmPhrase?: string;
        action: () => Promise<void>;
    }>({
        isOpen: false,
        title: "",
        message: "",
        action: async () => { },
    });

    const loadData = useCallback(async () => {
        if (!token) return;
        try {
            setLoading(true);
            setError(null);
            const params = showAll ? "?show_all=true" : "";
            const data = await apiGet(`/reporting/profiles/${params}`, token);
            setProfiles(Array.isArray(data) ? data : data.results || []);
        } catch (e: any) {
            setError(e.message || "Failed to load templates");
        } finally {
            setLoading(false);
        }
    }, [token, showAll]);

    useEffect(() => {
        loadData();
    }, [loadData]);

    const handleDelete = async (id: string) => {
        if (!window.confirm("Are you sure you want to delete this template?")) return;
        try {
            await apiDelete(`/reporting/profiles/${id}/`, token);
            loadData();
        } catch (e: any) {
            setError(e.message || "Failed to delete");
        }
    };

    const handleClone = async (profile: TemplateProfile) => {
        try {
            setActionLoading(true);
            await apiPost(`/reporting/governance/${profile.id}/clone/`, token, {});
            loadData();
        } catch (e: any) {
            setError(e.message || "Failed to clone template");
        } finally {
            setActionLoading(false);
        }
    };

    const handleActivate = (profile: TemplateProfile) => {
        setConfirmModal({
            isOpen: true,
            title: "Activate Template Version",
            message: `This will make ${profile.code} v${profile.version} the active version and archive any other active versions.`,
            confirmPhrase: "ACTIVATE",
            action: async () => {
                await apiPost(`/reporting/governance/${profile.id}/activate/`, token, { confirmation: "ACTIVATE" });
                loadData();
            },
        });
    };

    const handleFreeze = async (profile: TemplateProfile) => {
        try {
            setActionLoading(true);
            await apiPost(`/reporting/governance/${profile.id}/freeze/`, token, {});
            loadData();
        } catch (e: any) {
            setError(e.message || "Failed to freeze template");
        } finally {
            setActionLoading(false);
        }
    };

    const handleUnfreeze = async (profile: TemplateProfile) => {
        try {
            setActionLoading(true);
            await apiPost(`/reporting/governance/${profile.id}/unfreeze/`, token, {});
            loadData();
        } catch (e: any) {
            setError(e.message || "Failed to unfreeze template");
        } finally {
            setActionLoading(false);
        }
    };

    const handleArchive = (profile: TemplateProfile) => {
        setConfirmModal({
            isOpen: true,
            title: "Archive Template",
            message: `This will archive ${profile.code} v${profile.version}. Archived templates cannot be used for new reports.`,
            confirmPhrase: "ARCHIVE",
            action: async () => {
                await apiPost(`/reporting/governance/${profile.id}/archive/`, token, { confirmation: "ARCHIVE" });
                loadData();
            },
        });
    };

    const executeConfirmAction = async () => {
        try {
            setActionLoading(true);
            await confirmModal.action();
            setConfirmModal({ ...confirmModal, isOpen: false });
        } catch (e: any) {
            setError(e.message || "Action failed");
        } finally {
            setActionLoading(false);
        }
    };

    const downloadCsv = async (path: string, filename: string) => {
        if (!token) return;
        const response = await fetch(`${API_BASE}${path}`, {
            headers: { Authorization: `Bearer ${token}` }
        });
        if (!response.ok) {
            const text = await response.text();
            throw new Error(text || "Download failed");
        }
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
    };

    const handleImportSuccess = () => {
        setImportModalOpen(false);
        loadData();
    };

    if (loading) return <div style={{ padding: 20 }}>Loading...</div>;

    return (
        <div style={{ padding: 20 }}>
            <ConfirmModal
                isOpen={confirmModal.isOpen}
                title={confirmModal.title}
                message={confirmModal.message}
                confirmPhrase={confirmModal.confirmPhrase}
                onConfirm={executeConfirmAction}
                onCancel={() => setConfirmModal({ ...confirmModal, isOpen: false })}
                loading={actionLoading}
            />
            <ImportModal
                isOpen={isImportModalOpen}
                onClose={() => setImportModalOpen(false)}
                onImportSuccess={handleImportSuccess}
                importUrl="/reporting/profiles/import-csv/"
                title="Import Report Profiles"
            />
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
                <div>
                    <h1 style={{ fontSize: 24, margin: 0 }}>Report Templates</h1>
                    <p style={{ margin: "8px 0 0", color: theme.colors.textSecondary, fontSize: 14 }}>
                        Manage report templates with versioning and governance
                    </p>
                </div>
                <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                    <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 14 }}>
                        <input
                            type="checkbox"
                            checked={showAll}
                            onChange={(e) => setShowAll(e.target.checked)}
                        />
                        Show all versions
                    </label>
                    <Button
                        variant="secondary"
                        onClick={() => downloadCsv("/reporting/profiles/template-csv/", "report_profiles_template.csv")}
                    >
                        Download CSV Template
                    </Button>
                    <Button
                        variant="secondary"
                        onClick={() => downloadCsv("/reporting/profiles/export-csv/", "report_profiles_export.csv")}
                    >
                        Export CSV
                    </Button>
                    <Button variant="secondary" onClick={() => setImportModalOpen(true)}>
                        Import CSV
                    </Button>
                    <Button variant="primary" onClick={() => navigate("/settings/templates/new")}>
                        Create Template
                    </Button>
                </div>
            </div>

            {error && <ErrorAlert message={error} />}

            <div style={{ backgroundColor: "white", borderRadius: theme.radius.lg, border: `1px solid ${theme.colors.border}`, overflow: "hidden" }}>
                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                    <thead>
                        <tr style={{ backgroundColor: theme.colors.backgroundGray, borderBottom: `1px solid ${theme.colors.border}` }}>
                            <th style={{ padding: 12, textAlign: "left" }}>Code</th>
                            <th style={{ padding: 12, textAlign: "left" }}>Name</th>
                            <th style={{ padding: 12, textAlign: "center" }}>Version</th>
                            <th style={{ padding: 12, textAlign: "center" }}>Status</th>
                            <th style={{ padding: 12, textAlign: "center" }}>Reports</th>
                            <th style={{ padding: 12, textAlign: "right" }}>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {profiles.map(p => (
                            <tr key={p.id} style={{ borderBottom: `1px solid ${theme.colors.borderLight}` }}>
                                <td style={{ padding: 12 }}>
                                    <span style={{ fontWeight: 600 }}>{p.code}</span>
                                </td>
                                <td style={{ padding: 12 }}>{p.name}</td>
                                <td style={{ padding: 12, textAlign: "center" }}>
                                    <span style={{
                                        display: "inline-block",
                                        padding: "2px 8px",
                                        borderRadius: 4,
                                        backgroundColor: theme.colors.backgroundGray,
                                        fontWeight: 500,
                                        fontSize: 13,
                                    }}>
                                        v{p.version}
                                    </span>
                                </td>
                                <td style={{ padding: 12, textAlign: "center" }}>
                                    <StatusBadge status={p.status} />
                                    {p.is_frozen && <FrozenBadge />}
                                </td>
                                <td style={{ padding: 12, textAlign: "center" }}>
                                    <span style={{
                                        color: p.used_by_reports > 0 ? theme.colors.primary : theme.colors.textSecondary,
                                        fontWeight: p.used_by_reports > 0 ? 600 : 400,
                                    }}>
                                        {p.used_by_reports}
                                    </span>
                                </td>
                                <td style={{ padding: 12, textAlign: "right" }}>
                                    <div style={{ display: "flex", gap: 8, justifyContent: "flex-end", flexWrap: "wrap" }}>
                                        <Button
                                            variant="secondary"
                                            onClick={() => handleClone(p)}
                                            disabled={actionLoading}
                                            style={{ fontSize: 13, padding: "6px 12px" }}
                                        >
                                            Clone
                                        </Button>

                                        {p.status === "draft" && (
                                            <Button
                                                variant="primary"
                                                onClick={() => handleActivate(p)}
                                                disabled={actionLoading}
                                                style={{ fontSize: 13, padding: "6px 12px" }}
                                            >
                                                Activate
                                            </Button>
                                        )}

                                        {!p.is_frozen ? (
                                            <Button
                                                variant="secondary"
                                                onClick={() => handleFreeze(p)}
                                                disabled={actionLoading}
                                                style={{ fontSize: 13, padding: "6px 12px" }}
                                            >
                                                Freeze
                                            </Button>
                                        ) : (
                                            <Button
                                                variant="secondary"
                                                onClick={() => handleUnfreeze(p)}
                                                disabled={actionLoading}
                                                style={{ fontSize: 13, padding: "6px 12px" }}
                                            >
                                                Unfreeze
                                            </Button>
                                        )}

                                        {p.status !== "active" && p.status !== "archived" && (
                                            <Button
                                                variant="secondary"
                                                onClick={() => handleArchive(p)}
                                                disabled={actionLoading}
                                                style={{ fontSize: 13, padding: "6px 12px", color: theme.colors.warning }}
                                            >
                                                Archive
                                            </Button>
                                        )}

                                        <Button
                                            variant="secondary"
                                            onClick={() => navigate(`/settings/templates/${p.id}`)}
                                            style={{ fontSize: 13, padding: "6px 12px" }}
                                        >
                                            {p.is_frozen || (p.status === "active" && p.used_by_reports > 0) ? "View" : "Edit"}
                                        </Button>

                                        {p.status !== "active" && p.used_by_reports === 0 && (
                                            <Button
                                                variant="secondary"
                                                onClick={() => handleDelete(p.id)}
                                                style={{ fontSize: 13, padding: "6px 12px", color: theme.colors.danger }}
                                            >
                                                Delete
                                            </Button>
                                        )}
                                    </div>
                                </td>
                            </tr>
                        ))}
                        {profiles.length === 0 && (
                            <tr>
                                <td colSpan={6} style={{ padding: 20, textAlign: "center", color: theme.colors.textSecondary }}>
                                    No templates found.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            {/* Governance Workflow Guide */}
            <div style={{
                marginTop: 24,
                padding: 20,
                backgroundColor: theme.colors.backgroundGray,
                borderRadius: theme.radius.lg,
                border: `1px solid ${theme.colors.border}`,
            }}>
                <h3 style={{ margin: "0 0 12px", fontSize: 16 }}>📋 Template Governance Workflow</h3>
                <ol style={{ margin: 0, paddingLeft: 20, color: theme.colors.textSecondary, lineHeight: 1.8 }}>
                    <li><strong>Clone</strong> an existing template to create a new draft version</li>
                    <li><strong>Edit</strong> the draft version with your changes</li>
                    <li><strong>Preview</strong> the template to verify changes</li>
                    <li><strong>Activate</strong> the new version (automatically archives the old active version)</li>
                    <li><strong>Freeze</strong> active templates to prevent accidental changes</li>
                </ol>
            </div>
        </div>
    );
}
