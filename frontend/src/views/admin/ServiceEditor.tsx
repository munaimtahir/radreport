import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../../ui/auth";
import { apiGet, apiPost, apiPut } from "../../ui/api";
import { theme } from "../../theme";
import Button from "../../ui/components/Button";
import ErrorAlert from "../../ui/components/ErrorAlert";
import SuccessAlert from "../../ui/components/SuccessAlert";
import ServiceLinkage from "./ServiceLinkage";

export default function ServiceEditor() {
    const { id } = useParams<{ id: string }>();
    const isNew = !id || id === "new";
    const { token } = useAuth();
    const navigate = useNavigate();

    const [service, setService] = useState<any>({
        code: "",
        name: "",
        category: "Radiology",
        modality: "", // This needs to be ID or object? ServiceViewSet expects ID usually.
        // Note: ServiceViewSet uses Modality model.
        // I need to load modalities for dropdown.
        price: 0,
        tat_value: 1,
        tat_unit: "hours",
        is_active: true
    });

    const [modalities, setModalities] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    useEffect(() => {
        loadModalities();
        if (!isNew && token) {
            loadData();
        }
    }, [id, token]);

    const loadModalities = async () => {
        // Need ModalityViewSet. Assuming /catalog/modalities/
        try {
            const data = await apiGet("/catalog/modalities/", token);
            setModalities(Array.isArray(data) ? data : data.results || []);
        } catch (e) {}
    };

    const loadData = async () => {
        setLoading(true);
        try {
            const data = await apiGet(`/catalog/services/${id}/`, token);
            // Transform data if needed. Modality might be object.
            const s = { ...data };
            if (s.modality && typeof s.modality === 'object') {
                s.modality = s.modality.id;
            }
            setService(s);
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        setSaving(true);
        setError(null);
        setSuccess(null);
        try {
            let res;
            if (isNew) {
                res = await apiPost("/catalog/services/", token, service);
                navigate(`/admin/services/${res.id}`, { replace: true });
                setSuccess("Service created");
            } else {
                res = await apiPut(`/catalog/services/${id}/`, token, service);
                setSuccess("Service updated");
            }
        } catch (e: any) {
            setError(e.message);
        } finally {
            setSaving(false);
        }
    };

    if (loading) return <div>Loading...</div>;

    return (
        <div style={{ padding: 20, maxWidth: 800, margin: "0 auto" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
                <h1 style={{ fontSize: 24, margin: 0 }}>{isNew ? "New Service" : `Edit Service: ${service.code}`}</h1>
                <Button variant="secondary" onClick={() => navigate("/admin/services")}>Back to List</Button>
            </div>

            {error && <ErrorAlert message={error} />}
            {success && <SuccessAlert message={success} />}

            <div style={{ backgroundColor: "white", padding: 20, borderRadius: theme.radius.lg, border: `1px solid ${theme.colors.border}` }}>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                    <div>
                        <label style={{ display: "block", marginBottom: 5 }}>Code</label>
                        <input
                            value={service.code || ""}
                            onChange={e => setService({...service, code: e.target.value})}
                            style={{ width: "100%", padding: 8 }}
                        />
                    </div>
                    <div>
                        <label style={{ display: "block", marginBottom: 5 }}>Name</label>
                        <input
                            value={service.name}
                            onChange={e => setService({...service, name: e.target.value})}
                            style={{ width: "100%", padding: 8 }}
                        />
                    </div>
                    <div>
                        <label style={{ display: "block", marginBottom: 5 }}>Category</label>
                        <select
                            value={service.category}
                            onChange={e => setService({...service, category: e.target.value})}
                            style={{ width: "100%", padding: 8 }}
                        >
                            <option value="Radiology">Radiology</option>
                            <option value="Lab">Lab</option>
                            <option value="OPD">OPD</option>
                            <option value="Procedure">Procedure</option>
                        </select>
                    </div>
                    <div>
                        <label style={{ display: "block", marginBottom: 5 }}>Modality</label>
                        <select
                            value={service.modality || ""}
                            onChange={e => setService({...service, modality: e.target.value})}
                            style={{ width: "100%", padding: 8 }}
                        >
                            <option value="">Select Modality</option>
                            {modalities.map(m => (
                                <option key={m.id} value={m.id}>{m.code} - {m.name}</option>
                            ))}
                        </select>
                    </div>
                    <div>
                        <label style={{ display: "block", marginBottom: 5 }}>Price</label>
                        <input
                            type="number"
                            value={service.price}
                            onChange={e => setService({...service, price: parseFloat(e.target.value)})}
                            style={{ width: "100%", padding: 8 }}
                        />
                    </div>
                    <div>
                        <label style={{ display: "block", marginBottom: 5 }}>Turnaround Time</label>
                        <div style={{ display: "flex", gap: 8 }}>
                            <input
                                type="number"
                                value={service.tat_value}
                                onChange={e => setService({...service, tat_value: parseInt(e.target.value)})}
                                style={{ width: "60%", padding: 8 }}
                            />
                            <select
                                value={service.tat_unit}
                                onChange={e => setService({...service, tat_unit: e.target.value})}
                                style={{ width: "40%", padding: 8 }}
                            >
                                <option value="hours">Hours</option>
                                <option value="days">Days</option>
                            </select>
                        </div>
                    </div>
                </div>

                <div style={{ marginTop: 16 }}>
                    <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <input
                            type="checkbox"
                            checked={service.is_active}
                            onChange={e => setService({...service, is_active: e.target.checked})}
                        />
                        Active
                    </label>
                </div>

                <div style={{ marginTop: 20, textAlign: "right" }}>
                    <Button variant="primary" onClick={handleSave} disabled={saving}>
                        {saving ? "Saving..." : isNew ? "Create Service" : "Update Service"}
                    </Button>
                </div>
            </div>

            {!isNew && (
                <ServiceLinkage serviceId={id!} token={token} />
            )}
        </div>
    );
}
