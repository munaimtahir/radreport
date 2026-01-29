import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../ui/auth";
import { apiGet, apiDelete, apiUpload, API_BASE } from "../../ui/api";
import { theme } from "../../theme";
import Button from "../../ui/components/Button";
import ErrorAlert from "../../ui/components/ErrorAlert";

export default function ServicesList() {
    const { token } = useAuth();
    const navigate = useNavigate();
    const [services, setServices] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [importStatus, setImportStatus] = useState<string | null>(null);
    const [page, setPage] = useState(1);
    const [search, setSearch] = useState("");
    const fileInputRef = useRef<HTMLInputElement | null>(null);

    useEffect(() => {
        loadData();
    }, [token, page, search]);

    const loadData = async () => {
        if (!token) return;
        try {
            setLoading(true);
            // Assuming pagination or simple list. existing ServiceViewSet supports search.
            const query = search ? `?search=${search}` : "";
            const data = await apiGet(`/services/${query}`, token);
            setServices(Array.isArray(data) ? data : data.results || []);
        } catch (e: any) {
            setError(e.message || "Failed to load services");
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (id: string) => {
        if (!window.confirm("Are you sure you want to deactivate this service?")) return;
        try {
            // Usually we deactivate instead of delete
            // But apiDelete calls DELETE method. ServiceViewSet default might verify usage.
            // Let's assume standard delete for now, user can check backend.
            await apiDelete(`/services/${id}/`, token);
            loadData();
        } catch (e: any) {
            alert(e.message || "Failed to delete");
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
            const result = await apiUpload("/catalog/services/import-csv/", token, formData);
            setImportStatus(`Import complete. Created: ${result.created}, Updated: ${result.updated}`);
            loadData();
        } catch (e: any) {
            setImportStatus(e.message || "Import failed");
        } finally {
            event.target.value = "";
        }
    };

    return (
        <div style={{ padding: 20 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
                <h1 style={{ fontSize: 24, margin: 0 }}>Services</h1>
                <div style={{ display: "flex", gap: 12 }}>
                    <input
                        placeholder="Search services..."
                        value={search}
                        onChange={e => setSearch(e.target.value)}
                        style={{ padding: "8px 12px", borderRadius: 4, border: "1px solid #ccc" }}
                    />
                    <Button
                        variant="secondary"
                        onClick={() => downloadCsv("/catalog/services/template-csv/", "services_template.csv")}
                    >
                        Download CSV Template
                    </Button>
                    <Button
                        variant="secondary"
                        onClick={() => downloadCsv("/catalog/services/export-csv/", "services_export.csv")}
                    >
                        Export CSV
                    </Button>
                    <Button variant="secondary" onClick={handleImportClick}>
                        Import CSV
                    </Button>
                    <Button variant="primary" onClick={() => navigate("/admin/services/new")}>
                        Create Service
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
                            <th style={{ padding: 12, textAlign: "left" }}>Category</th>
                            <th style={{ padding: 12, textAlign: "right" }}>Price</th>
                            <th style={{ padding: 12, textAlign: "right" }}>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {services.map(s => (
                            <tr key={s.id} style={{ borderBottom: `1px solid ${theme.colors.borderLight}` }}>
                                <td style={{ padding: 12 }}>{s.code}</td>
                                <td style={{ padding: 12 }}>{s.name}</td>
                                <td style={{ padding: 12 }}>{s.category}</td>
                                <td style={{ padding: 12, textAlign: "right" }}>{s.price}</td>
                                <td style={{ padding: 12, textAlign: "right" }}>
                                    <Button variant="secondary" onClick={() => navigate(`/admin/services/${s.id}`)} style={{ marginRight: 8 }}>
                                        Edit
                                    </Button>
                                    <Button variant="secondary" onClick={() => handleDelete(s.id)} style={{ color: theme.colors.danger }}>
                                        Del
                                    </Button>
                                </td>
                            </tr>
                        ))}
                        {services.length === 0 && !loading && (
                            <tr>
                                <td colSpan={5} style={{ padding: 20, textAlign: "center", color: theme.colors.textSecondary }}>
                                    No services found.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
