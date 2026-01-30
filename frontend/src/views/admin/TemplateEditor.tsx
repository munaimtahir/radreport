import React, { useEffect, useState, useCallback, useRef } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../../ui/auth";
import { apiGet, apiPost, apiPut, apiDelete, apiUpload, API_BASE } from "../../ui/api";
import { theme } from "../../theme";
import Button from "../../ui/components/Button";
import ErrorAlert from "../../ui/components/ErrorAlert";
import SuccessAlert from "../../ui/components/SuccessAlert";

interface Profile {
    code: string;
    name: string;
    modality: string;
    enable_narrative: boolean;
    narrative_mode: string;
}

interface Parameter {
    parameter_id?: string;
    id?: string;
    profile?: string;
    section: string;
    name: string;
    type?: string;
    parameter_type?: string;
    unit?: string;
    normal_value?: string;
    order?: number;
    is_required?: boolean;
    options?: any[];
    slug?: string;
    sentence_template?: string;
    narrative_role?: string;
    omit_if_values?: string;
    join_label?: string;
}

export default function TemplateEditor() {
    const { id } = useParams<{ id: string }>();
    const isNew = !id || id === "new";
    const { token } = useAuth();
    const navigate = useNavigate();

    const [profile, setProfile] = useState<Profile>({
        code: "",
        name: "",
        modality: "",
        enable_narrative: true,
        narrative_mode: "rule_based"
    });
    const [parameters, setParameters] = useState<Parameter[]>([]);

    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const importInputRef = useRef<HTMLInputElement | null>(null);

    // Parameter Modal
    const [showParamModal, setShowParamModal] = useState(false);
    const [currentParam, setCurrentParam] = useState<Parameter | null>(null); // null = new

    const loadData = useCallback(async () => {
        setLoading(true);
        try {
            const data = await apiGet(`/reporting/profiles/${id}/`, token);
            setProfile(data);
            setParameters(data.parameters || []);
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    }, [id, token]);

    useEffect(() => {
        if (!isNew && token) {
            loadData();
        }
    }, [loadData, isNew, token]);

    const handleSaveProfile = async () => {
        setSaving(true);
        setError(null);
        setSuccess(null);
        try {
            let res;
            if (isNew) {
                res = await apiPost("/reporting/profiles/", token, profile);
                navigate(`/settings/templates/${res.id}`, { replace: true });
                setSuccess("Profile created");
            } else {
                res = await apiPut(`/reporting/profiles/${id}/`, token, profile);
                setSuccess("Profile updated");
                loadData(); // Reload to refresh parameters if needed
            }
        } catch (e: any) {
            setError(e.message);
        } finally {
            setSaving(false);
        }
    };

    const handleDeleteParam = async (paramId: string) => {
        if (!window.confirm("Delete this parameter?")) return;
        try {
            await apiDelete(`/reporting/parameters/${paramId}/`, token);
            loadData();
        } catch (e: any) {
            setError(e.message);
        }
    };

    const openParamModal = (param?: Parameter) => {
        if (param) {
            setCurrentParam({ ...param });
        } else {
            setCurrentParam({
                profile: id, // Linking to this profile
                section: "General",
                name: "",
                parameter_type: "short_text",
                order: parameters.length + 1,
                is_required: false,
                normal_value: "",
                unit: ""
            });
        }
        setShowParamModal(true);
    };

    const handleSaveParam = async (paramData: Parameter) => {
        try {
            if (paramData.id) {
                await apiPut(`/reporting/parameters/${paramData.id}/`, token, paramData);
            } else {
                await apiPost("/reporting/parameters/", token, paramData);
            }
            setShowParamModal(false);
            loadData();
        } catch (e: any) {
            setError("Failed to save parameter: " + e.message);
        }
    };

    const handleExportCsv = async () => {
        if (!token || !id) return;
        setError(null);
        try {
            const response = await fetch(`${API_BASE}/reporting/profiles/${id}/parameters-csv/`, {
                method: "GET",
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (!response.ok) {
                const text = await response.text();
                throw new Error(text || "Failed to export CSV");
            }
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement("a");
            const disposition = response.headers.get("Content-Disposition") || "";
            const match = disposition.match(/filename="?([^"]+)"?/);
            const filename = match?.[1] || `${profile.code || "report"}_parameters.csv`;
            link.href = url;
            link.download = filename;
            link.click();
            window.URL.revokeObjectURL(url);
        } catch (e: any) {
            setError(e.message);
        }
    };

    const handleImportCsv = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file || !id) return;
        setError(null);
        setSuccess(null);
        try {
            const formData = new FormData();
            formData.append("file", file);
            const result = await apiUpload(`/reporting/profiles/${id}/parameters-csv/`, token, formData);
            setSuccess(`Imported CSV. Added ${result.fields_created} and updated ${result.fields_updated} parameters.`);
            loadData();
        } catch (e: any) {
            setError(e.message);
        } finally {
            if (importInputRef.current) {
                importInputRef.current.value = "";
            }
        }
    };

    const triggerImport = () => {
        importInputRef.current?.click();
    };

    if (loading) return <div>Loading...</div>;

    return (
        <div style={{ padding: 20, maxWidth: 1000, margin: "0 auto" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
                <h1 style={{ fontSize: 24, margin: 0 }}>{isNew ? "New Template" : `Edit Template: ${profile.code}`}</h1>
                <Button variant="secondary" onClick={() => navigate("/settings/templates")}>Back to List</Button>
            </div>

            {error && <ErrorAlert message={error} />}
            {success && <SuccessAlert message={success} />}

            <div style={{ backgroundColor: "white", padding: 20, borderRadius: theme.radius.lg, border: `1px solid ${theme.colors.border}`, marginBottom: 20 }}>
                <h3 style={{ marginTop: 0 }}>Profile Details</h3>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                    <div>
                        <label style={{ display: "block", marginBottom: 5 }}>Code</label>
                        <input
                            value={profile.code}
                            onChange={e => setProfile({...profile, code: e.target.value})}
                            style={{ width: "100%", padding: 8 }}
                        />
                    </div>
                    <div>
                        <label style={{ display: "block", marginBottom: 5 }}>Name</label>
                        <input
                            value={profile.name}
                            onChange={e => setProfile({...profile, name: e.target.value})}
                            style={{ width: "100%", padding: 8 }}
                        />
                    </div>
                    <div>
                        <label style={{ display: "block", marginBottom: 5 }}>Modality</label>
                        <input
                            value={profile.modality}
                            onChange={e => setProfile({...profile, modality: e.target.value})}
                            style={{ width: "100%", padding: 8 }}
                        />
                    </div>
                    <div>
                        <label style={{ display: "block", marginBottom: 5 }}>Narrative Mode</label>
                        <select
                            value={profile.narrative_mode}
                            onChange={e => setProfile({...profile, narrative_mode: e.target.value})}
                            style={{ width: "100%", padding: 8 }}
                        >
                            <option value="rule_based">Rule Based</option>
                        </select>
                    </div>
                </div>
                <div style={{ marginTop: 20, textAlign: "right" }}>
                    <Button variant="primary" onClick={handleSaveProfile} disabled={saving}>
                        {saving ? "Saving..." : isNew ? "Create Profile" : "Update Profile"}
                    </Button>
                </div>
            </div>

            {!isNew && (
                <div style={{ backgroundColor: "white", padding: 20, borderRadius: theme.radius.lg, border: `1px solid ${theme.colors.border}` }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                        <h3 style={{ margin: 0 }}>Parameters</h3>
                        <div style={{ display: "flex", gap: 8 }}>
                            <Button variant="secondary" onClick={handleExportCsv}>Export CSV</Button>
                            <Button variant="secondary" onClick={triggerImport}>Import CSV</Button>
                            <Button variant="primary" onClick={() => openParamModal()}>Add Parameter</Button>
                        </div>
                    </div>
                    <input
                        ref={importInputRef}
                        type="file"
                        accept=".csv"
                        style={{ display: "none" }}
                        onChange={handleImportCsv}
                    />

                    <table style={{ width: "100%", borderCollapse: "collapse" }}>
                        <thead>
                            <tr style={{ borderBottom: `1px solid ${theme.colors.border}`, backgroundColor: theme.colors.backgroundGray }}>
                                <th style={{ textAlign: "left", padding: 8 }}>Order</th>
                                <th style={{ textAlign: "left", padding: 8 }}>Section</th>
                                <th style={{ textAlign: "left", padding: 8 }}>Name</th>
                                <th style={{ textAlign: "left", padding: 8 }}>Type</th>
                                <th style={{ textAlign: "right", padding: 8 }}>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {parameters.map((p: Parameter) => (
                                <tr key={p.parameter_id || p.id} style={{ borderBottom: `1px solid ${theme.colors.borderLight}` }}>
                                    <td style={{ padding: 8 }}>{p.order}</td>
                                    <td style={{ padding: 8 }}>{p.section}</td>
                                    <td style={{ padding: 8 }}>{p.name}</td>
                                    <td style={{ padding: 8 }}>{p.type || p.parameter_type}</td>
                                    <td style={{ padding: 8, textAlign: "right" }}>
                                        <Button variant="secondary" onClick={() => openParamModal(p)} style={{ marginRight: 8, fontSize: 12, padding: "4px 8px" }}>Edit</Button>
                                        <Button variant="secondary" onClick={() => handleDeleteParam(p.parameter_id || p.id!)} style={{ color: theme.colors.danger, fontSize: 12, padding: "4px 8px" }}>Del</Button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {showParamModal && (
                <ParameterModal
                    param={currentParam}
                    onClose={() => setShowParamModal(false)}
                    onSave={handleSaveParam}
                    token={token}
                />
            )}
        </div>
    );
}

function ParameterModal({ param, onClose, onSave, token }: { param: any, onClose: () => void, onSave: (p: any) => void, token: string | null }) {
    const [data, setData] = useState({ ...param });
    const [options, setOptions] = useState<any[]>(param.options || []);

    // If it's a link parameter (from library), editing might be restricted or different.
    // For now, assuming basic parameters.

    const handleChange = (field: string, value: any) => {
        setData({ ...data, [field]: value });
    };

    const handleAddOption = () => {
        setOptions([...options, { label: "", value: "", order: options.length }]);
    };

    const handleOptionChange = (idx: number, field: string, value: any) => {
        const newOpts = [...options];
        newOpts[idx] = { ...newOpts[idx], [field]: value };
        setOptions(newOpts);
    };

    const handleRemoveOption = (idx: number) => {
        setOptions(options.filter((_, i) => i !== idx));
    };

    const handleSave = async () => {
        // If we need to save options, we might need to do it separately or via nested serializer.
        // If backend supports nested writable serializer, great.
        // Assuming ReportParameterSerializer does NOT support writable nested options by default unless implemented.
        // I will implement writable nested options in backend in Phase 4.
        onSave({ ...data, options });
    };

    return (
        <div style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, backgroundColor: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}>
            <div style={{ backgroundColor: "white", padding: 24, borderRadius: 8, width: 600, maxHeight: "90vh", overflowY: "auto" }}>
                <h3 style={{ marginTop: 0 }}>{data.id ? "Edit Parameter" : "New Parameter"}</h3>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 16 }}>
                    <div>
                        <label style={{ display: "block", fontSize: 12 }}>Section</label>
                        <input value={data.section} onChange={e => handleChange("section", e.target.value)} style={{ width: "100%", padding: 6 }} />
                    </div>
                    <div>
                        <label style={{ display: "block", fontSize: 12 }}>Name</label>
                        <input value={data.name} onChange={e => handleChange("name", e.target.value)} style={{ width: "100%", padding: 6 }} />
                    </div>
                    <div>
                        <label style={{ display: "block", fontSize: 12 }}>Type</label>
                        <select value={data.parameter_type} onChange={e => handleChange("parameter_type", e.target.value)} style={{ width: "100%", padding: 6 }}>
                            <option value="short_text">Short Text</option>
                            <option value="long_text">Long Text</option>
                            <option value="number">Number</option>
                            <option value="boolean">Boolean</option>
                            <option value="dropdown">Dropdown</option>
                            <option value="checklist">Checklist</option>
                            <option value="heading">Heading</option>
                            <option value="separator">Separator</option>
                        </select>
                    </div>
                    <div>
                        <label style={{ display: "block", fontSize: 12 }}>Order</label>
                        <input type="number" value={data.order} onChange={e => handleChange("order", parseInt(e.target.value))} style={{ width: "100%", padding: 6 }} />
                    </div>
                    <div>
                        <label style={{ display: "block", fontSize: 12 }}>Unit</label>
                        <input value={data.unit || ""} onChange={e => handleChange("unit", e.target.value)} style={{ width: "100%", padding: 6 }} />
                    </div>
                    <div>
                        <label style={{ display: "block", fontSize: 12 }}>Normal Value</label>
                        <input value={data.normal_value || ""} onChange={e => handleChange("normal_value", e.target.value)} style={{ width: "100%", padding: 6 }} />
                    </div>
                    <div style={{ display: "flex", alignItems: "center" }}>
                        <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
                            <input type="checkbox" checked={data.is_required} onChange={e => handleChange("is_required", e.target.checked)} />
                            Required
                        </label>
                    </div>
                </div>

                {(data.parameter_type === "dropdown" || data.parameter_type === "checklist") && (
                    <div style={{ marginBottom: 16, border: "1px solid #eee", padding: 12, borderRadius: 4 }}>
                        <h4 style={{ marginTop: 0 }}>Options</h4>
                        {options.map((opt, i) => (
                            <div key={i} style={{ display: "flex", gap: 8, marginBottom: 8 }}>
                                <input placeholder="Label" value={opt.label} onChange={e => handleOptionChange(i, "label", e.target.value)} style={{ flex: 1, padding: 4 }} />
                                <input placeholder="Value" value={opt.value} onChange={e => handleOptionChange(i, "value", e.target.value)} style={{ flex: 1, padding: 4 }} />
                                <Button variant="secondary" onClick={() => handleRemoveOption(i)} style={{ padding: "2px 8px", fontSize: 12 }}>X</Button>
                            </div>
                        ))}
                        <Button variant="secondary" onClick={handleAddOption} style={{ fontSize: 12 }}>+ Add Option</Button>
                    </div>
                )}

                <div style={{ display: "flex", justifyContent: "flex-end", gap: 12 }}>
                    <Button variant="secondary" onClick={onClose}>Cancel</Button>
                    <Button variant="primary" onClick={handleSave}>Save Parameter</Button>
                </div>
            </div>
        </div>
    );
}
