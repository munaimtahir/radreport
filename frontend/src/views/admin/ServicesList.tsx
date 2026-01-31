import React, { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../ui/auth";
import { apiGet, apiDelete, API_BASE } from "../../ui/api";
import { theme } from "../../theme";
import Button from "../../ui/components/Button";
import ErrorAlert from "../../ui/components/ErrorAlert";
import ImportModal from "../../ui/components/ImportModal";
import { downloadFile } from "../../utils/download";

interface Service {
    id: string;
    code: string;
    name: string;
    category: string;
    price: number;
}

export default function ServicesList() {
    const { token } = useAuth();
    const navigate = useNavigate();
    const [services, setServices] = useState<Service[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [search, setSearch] = useState("");
    const [isImportModalOpen, setImportModalOpen] = useState(false);

    const loadData = useCallback(async () => {
        if (!token) return;
        try {
            setLoading(true);
            const query = search ? `?search=${encodeURIComponent(search)}` : "";
            const data = await apiGet(`/catalog/services/${query}`, token);
            setServices(Array.isArray(data) ? data : data.results || []);
        } catch (e: any) {
            setError(e.message || "Failed to load services");
        } finally {
            setLoading(false);
        }
    }, [token, search]);

    useEffect(() => {
        loadData();
    }, [loadData]);

    const handleDeactivate = async (id: string) => {
        if (!window.confirm("Are you sure you want to deactivate this service?")) return;
        try {
            await apiDelete(`/catalog/services/${id}/`, token);
            loadData();
        } catch (e: any) {
            setError(e.message || "Failed to deactivate");
        }
    };
    
    const handleImportSuccess = () => {
        setImportModalOpen(false);
        loadData();
    };

    return (
        <div style={{ padding: 20 }}>
            <ImportModal
                isOpen={isImportModalOpen}
                onClose={() => setImportModalOpen(false)}
                onImportSuccess={handleImportSuccess}
                importUrl="/catalog/services/import-csv/"
                title="Import Services"
            />
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
                        onClick={() => downloadFile(`${API_BASE}/catalog/services/template-csv/`, "services_template.csv", token)}
                    >
                        Download CSV Template
                    </Button>
                    <Button
                        variant="secondary"
                        onClick={() => downloadFile(`${API_BASE}/catalog/services/export-csv/`, "services_export.csv", token)}
                    >
                        Export CSV
                    </Button>
                    <Button variant="secondary" onClick={() => setImportModalOpen(true)}>
                        Import CSV
                    </Button>
                    <Button variant="primary" onClick={() => navigate("/settings/services/new")}>
                        Create Service
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
                                    <Button variant="secondary" onClick={() => navigate(`/settings/services/${s.id}`)} style={{ marginRight: 8 }}>
                                        Edit
                                    </Button>
                                    <Button variant="secondary" onClick={() => handleDeactivate(s.id)} style={{ color: theme.colors.danger }}>
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

