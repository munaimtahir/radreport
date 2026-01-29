import React, { useEffect, useState } from "react";
import { apiGet, apiPost, apiPut, apiDelete } from "../../ui/api";
import { theme } from "../../theme";
import Button from "../../ui/components/Button";
import ErrorAlert from "../../ui/components/ErrorAlert";

export default function ServiceLinkage({ serviceId, token }: { serviceId: string, token: string | null }) {
    const [profiles, setProfiles] = useState<any[]>([]);
    const [currentLink, setCurrentLink] = useState<any>(null);
    const [selectedProfileId, setSelectedProfileId] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadProfiles();
        loadCurrentLink();
    }, [serviceId]);

    const loadProfiles = async () => {
        try {
            const data = await apiGet("/reporting/profiles/", token);
            setProfiles(Array.isArray(data) ? data : data.results || []);
        } catch (e) {
            console.error(e);
        }
    };

    const loadCurrentLink = async () => {
        try {
            // Need a way to filter by service.
            // Assuming ServiceReportProfileViewSet supports filtering by service
            const data = await apiGet(`/reporting/service-profiles/?service=${serviceId}`, token);
            const results = Array.isArray(data) ? data : data.results || [];
            if (results.length > 0) {
                setCurrentLink(results[0]);
                setSelectedProfileId(results[0].profile);
            } else {
                setCurrentLink(null);
                setSelectedProfileId("");
            }
        } catch (e) {
            console.error(e);
        }
    };

    const handleSaveLink = async () => {
        setLoading(true);
        setError(null);
        try {
            if (currentLink) {
                // Update or Delete?
                if (!selectedProfileId) {
                    // Unlink
                    await apiDelete(`/reporting/service-profiles/${currentLink.id}/`, token);
                    setCurrentLink(null);
                } else {
                    // Update
                    await apiPut(`/reporting/service-profiles/${currentLink.id}/`, token, {
                        service: serviceId,
                        profile: selectedProfileId
                    });
                    loadCurrentLink();
                }
            } else {
                // Create
                if (selectedProfileId) {
                    await apiPost("/reporting/service-profiles/", token, {
                        service: serviceId,
                        profile: selectedProfileId
                    });
                    loadCurrentLink();
                }
            }
        } catch (e: any) {
            setError("Failed to save linkage: " + e.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ marginTop: 20, padding: 20, border: `1px solid ${theme.colors.border}`, borderRadius: theme.radius.lg, backgroundColor: "white" }}>
            <h3 style={{ marginTop: 0 }}>Report Template Linkage</h3>
            <p style={{ color: theme.colors.textSecondary, fontSize: 14 }}>
                Select the report template to be used when reporting on this service.
            </p>
            {error && <ErrorAlert message={error} />}
            <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                <select
                    value={selectedProfileId}
                    onChange={e => setSelectedProfileId(e.target.value)}
                    style={{ padding: 8, borderRadius: 4, border: "1px solid #ccc", minWidth: 200 }}
                >
                    <option value="">-- No Template --</option>
                    {profiles.map(p => (
                        <option key={p.id} value={p.id}>{p.code} - {p.name}</option>
                    ))}
                </select>
                <Button variant="primary" onClick={handleSaveLink} disabled={loading}>
                    {loading ? "Saving..." : "Save Linkage"}
                </Button>
            </div>
            {currentLink && (
                <div style={{ marginTop: 8, fontSize: 12, color: theme.colors.success }}>
                    Currently linked.
                </div>
            )}
        </div>
    );
}
