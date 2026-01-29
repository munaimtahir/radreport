import React, { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../ui/auth";
import { apiGet, apiDelete } from "../../ui/api";
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

    if (loading) return <div style={{ padding: 20 }}>Loading...</div>;

    return (
        <div style={{ padding: 20 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
                <h1 style={{ fontSize: 24, margin: 0 }}>Report Templates</h1>
                <Button variant="primary" onClick={() => navigate("/admin/templates/new")}>
                    Create Template
                </Button>
            </div>

            {error && <ErrorAlert message={error} />}

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
                                    <Button variant="secondary" onClick={() => navigate(`/admin/templates/${p.id}`)} style={{ marginRight: 8 }}>
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
