import React, { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../ui/auth";
import { apiGet, apiDelete, apiUpload, API_BASE } from "../../ui/api";
import { theme } from "../../theme";
import Button from "../../ui/components/Button";
import ErrorAlert from "../../ui/components/ErrorAlert";

interface TemplateProfile {
    id: string;
    code: string;
    name: string;
    modality: string;
}

export default function TemplatesList() {
    const { token } = useAuth();
    const navigate = useNavigate();
    const [profiles, setProfiles] = useState<TemplateProfile[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [importStatus, setImportStatus] = useState<string | null>(null);
    const [useLibrary, setUseLibrary] = useState(false);
    const fileInputRef = useRef<HTMLInputElement | null>(null);

    const loadData = useCallback(async () => {
        if (!token) return;
        try {
            setLoading(true);
            const data = await apiGet("/reporting/profiles/", token);
            setProfiles(Array.isArray(data) ? data : data.results || []);
        } catch (e: any) {
            setError(e.message || "Failed to load templates");
        } finally {
            setLoading(false);
        }
    }, [token]);

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

    const handleImportClick = () => {
        fileInputRef.current?.click();
    };

    const handleImport = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file || !token) return;
        setImportStatus(null);
        try {
            const formData = new FormData();
            formData.append("file", file);
            formData.append("use_library", useLibrary ? "true" : "false");
            const result = await apiUpload("/reporting/profiles/import-csv/", token, formData);
            setImportStatus(`Import complete. Profiles created: ${result.profiles_created}, updated: ${result.profiles_updated}`);
            loadData();
        } catch (e: any) {
            setImportStatus(e.message || "Import failed");
        } finally {
            event.target.value = "";
        }
    };

    if (loading) return <div style={{ padding: 20 }}>Loading...</div>;

    return (
        <div style={{ padding: 20 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
                <h1 style={{ fontSize: 24, margin: 0 }}>Report Templates</h1>
                <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                    <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12 }}>
                        <input
                            type="checkbox"
                            checked={useLibrary}
                            onChange={(event) => setUseLibrary(event.target.checked)}
                        />
                        Use Library Strategy
                    </label>
                    <Button
                        variant="secondary"
                        onClick={() => downloadCsv("/reporting/profiles/template-csv/", "report_templates_template.csv")}
                    >
                        Download CSV Template
                    </Button>
                    <Button
                        variant="secondary"
                        onClick={() => downloadCsv("/reporting/profiles/export-csv/", "report_templates_export.csv")}
                    >
                        Export CSV
                    </Button>
                    <Button variant="secondary" onClick={handleImportClick}>
                        Import CSV
                    </Button>
                    <Button variant="primary" onClick={() => navigate("/settings/templates/new")}>
                        Create Template
                    </Button>
                </div>
            </div>

            {error && <ErrorAlert message={error} />}
            {importStatus && <div style={{ marginBottom: 12, color: theme.colors.textSecondary }}>{importStatus}</div>}
            <input ref={fileInputRef} type="file" accept=".csv" style={{ display: "none" }} onChange={handleImport} />

            <div style={{ backgroundColor: "white", borderRadius: theme.radius.lg, border: `1px solid ${theme.colors.border}`, overflow: "hidden" }}>
                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                    <thead>
                        <tr style={{ backgroundColor: theme.colors.backgroundGray, borderBottom: `1px solid ${theme.colors.border}` }}>
                            <th style={{ padding: 12, textAlign: "left" }}>Code</th>
                            <th style={{ padding: 12, textAlign: "left" }}>Name</th>
                            <th style={{ padding: 12, textAlign: "left" }}>Modality</th>
                            <th style={{ padding: 12, textAlign: "right" }}>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {profiles.map(p => (
                            <tr key={p.id} style={{ borderBottom: `1px solid ${theme.colors.borderLight}` }}>
                                <td style={{ padding: 12 }}>{p.code}</td>
                                <td style={{ padding: 12 }}>{p.name}</td>
                                <td style={{ padding: 12 }}>{p.modality}</td>
                                <td style={{ padding: 12, textAlign: "right" }}>
                                    <Button variant="secondary" onClick={() => navigate(`/settings/templates/${p.id}`)} style={{ marginRight: 8 }}>
                                        Edit
                                    </Button>
                                    <Button variant="secondary" onClick={() => handleDelete(p.id)} style={{ color: theme.colors.danger }}>
                                        Delete
                                    </Button>
                                </td>
                            </tr>
                        ))}
                        {profiles.length === 0 && (
                            <tr>
                                <td colSpan={4} style={{ padding: 20, textAlign: "center", color: theme.colors.textSecondary }}>
                                    No templates found.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
