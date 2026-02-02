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
    // Governance fields
    version?: number;
    status?: "draft" | "active" | "archived";
    is_frozen?: boolean;
    used_by_reports?: number;
    can_edit?: boolean;
    can_delete?: boolean;
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
    const [libraryItems, setLibraryItems] = useState<any[]>([]);

    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const importInputRef = useRef<HTMLInputElement | null>(null);

    // Parameter Modal
    const [showParamModal, setShowParamModal] = useState(false);
    const [currentParam, setCurrentParam] = useState<Parameter | null>(null); // null = new
    const [insertIndex, setInsertIndex] = useState<number | null>(null);

    // Library Modal
    const [showLibraryModal, setShowLibraryModal] = useState(false);

    const loadData = useCallback(async () => {
        setLoading(true);
        try {
            const data = await apiGet(`/reporting/profiles/${id}/`, token);
            setProfile(data);
            setParameters(data.parameters || []);

            // Load library items
            const libData = await apiGet("/reporting/parameter-library/", token);
            setLibraryItems(libData.results || libData);
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
            if (isNew) {
                const res = await apiPost("/reporting/profiles/", token, profile);
                navigate(`/settings/templates/${res.id}`, { replace: true });
                setSuccess("Profile created");
            } else {
                await apiPut(`/reporting/profiles/${id}/`, token, profile);
                setSuccess("Profile updated");
                loadData();
            }
        } catch (e: any) {
            setError(e.message);
        } finally {
            setSaving(false);
        }
    };

    const handleReorder = async (newParams: Parameter[]) => {
        // Update orders based on array index
        const orders = newParams.map((p, idx) => ({
            id: p.parameter_id || p.id,
            order: idx + 1
        }));

        try {
            await apiPost(`/reporting/profiles/${id}/reorder-parameters/`, token, { orders });
            setParameters(newParams.map((p, idx) => ({ ...p, order: idx + 1 })));
        } catch (e: any) {
            setError("Failed to save order: " + e.message);
        }
    };

    const moveParam = (index: number, direction: "up" | "down") => {
        const newParams = [...parameters];
        const targetIndex = direction === "up" ? index - 1 : index + 1;
        if (targetIndex < 0 || targetIndex >= newParams.length) return;

        const temp = newParams[index];
        newParams[index] = newParams[targetIndex];
        newParams[targetIndex] = temp;

        handleReorder(newParams);
    };

    const handleDeleteParam = async (paramId: string) => {
        if (!window.confirm("Delete this parameter?")) return;
        try {
            // Check if it's a library link or legacy parameter
            // Actually the endpoint /reporting/parameters handles both? 
            // Looking at backend, there are different models. 
            // I'll assume standard delete for now.
            await apiDelete(`/reporting/parameters/${paramId}/`, token);
            loadData();
        } catch (e: any) {
            setError(e.message);
        }
    };

    const openParamModal = (param?: Parameter, index?: number) => {
        if (param) {
            setCurrentParam({ ...param });
            setInsertIndex(null);
        } else {
            setCurrentParam({
                profile: id,
                section: index !== undefined && parameters[index] ? parameters[index].section : "General",
                name: "",
                parameter_type: "short_text",
                order: index !== undefined ? index + 1 : parameters.length + 1,
                is_required: false,
                normal_value: "",
                unit: ""
            });
            setInsertIndex(index !== undefined ? index : null);
        }
        setShowParamModal(true);
    };

    const handleSaveParam = async (paramData: Parameter) => {
        try {
            if (paramData.id || paramData.parameter_id) {
                const pid = paramData.parameter_id || paramData.id;
                await apiPut(`/reporting/parameters/${pid}/`, token, paramData);
            } else {
                await apiPost("/reporting/parameters/", token, paramData);
            }
            setShowParamModal(false);
            loadData();
        } catch (e: any) {
            setError("Failed to save parameter: " + e.message);
        }
    };

    const handleAddFromLibrary = async (libItem: any) => {
        try {
            const newParam = {
                profile: id,
                section: "General",
                name: libItem.name,
                parameter_type: libItem.parameter_type,
                unit: libItem.unit,
                normal_value: libItem.default_normal_value,
                order: parameters.length + 1,
                sentence_template: libItem.default_sentence_template,
                narrative_role: libItem.default_narrative_role,
                omit_if_values: libItem.default_omit_if_values,
                join_label: libItem.default_join_label,
                options: libItem.default_options_json || []
            };
            await apiPost("/reporting/parameters/", token, newParam);
            setShowLibraryModal(false);
            loadData();
        } catch (e: any) {
            setError("Failed to add from library: " + e.message);
        }
    };

    const handleDuplicateParam = async (param: Parameter) => {
        try {
            const { id: _, parameter_id: __, ...rest } = param;
            const newParam = {
                ...rest,
                profile: id,
                order: parameters.length + 1,
                name: `${param.name} (Copy)`
            };
            await apiPost("/reporting/parameters/", token, newParam);
            loadData();
        } catch (e: any) {
            setError("Failed to duplicate: " + e.message);
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
            if (!response.ok) throw new Error("Failed to export CSV");
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = url;
            link.download = `${profile.code}_parameters.csv`;
            link.click();
        } catch (e: any) {
            setError(e.message);
        }
    };

    const handleImportCsv = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file || !id) return;
        try {
            const formData = new FormData();
            formData.append("file", file);
            await apiUpload(`/reporting/profiles/${id}/parameters-csv/`, token, formData);
            setSuccess(`Imported CSV.`);
            loadData();
        } catch (e: any) {
            setError(e.message);
        }
    };

    if (loading) return <div>Loading...</div>;

    const isReadOnly = profile.is_frozen || (profile.status === "active" && (profile.used_by_reports || 0) > 0);
    const governanceReason = profile.is_frozen
        ? "This template is frozen and cannot be edited."
        : profile.status === "active" && (profile.used_by_reports || 0) > 0
            ? `This template is active and used by ${profile.used_by_reports} reports.`
            : null;

    return (
        <div style={{ padding: 20, maxWidth: 1100, margin: "0 auto" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
                <div>
                    <h1 style={{ fontSize: 24, margin: 0 }}>
                        {isNew ? "New Template" : `${isReadOnly ? "View" : "Edit"} Template: ${profile.code}`}
                        {profile.version && <span style={{ fontSize: 14, color: theme.colors.textSecondary, marginLeft: 8 }}>v{profile.version}</span>}
                    </h1>
                    {profile.status && (
                        <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                            <span style={{
                                padding: "2px 10px",
                                borderRadius: 9999,
                                fontSize: 12,
                                fontWeight: 600,
                                backgroundColor: profile.status === "active" ? "#dcfce7" : profile.status === "draft" ? "#fef3c7" : "#f3f4f6",
                                color: profile.status === "active" ? "#166534" : profile.status === "draft" ? "#92400e" : "#6b7280",
                            }}>
                                {profile.status}
                            </span>
                        </div>
                    )}
                </div>
                <Button variant="secondary" onClick={() => navigate("/settings/templates")}>Back to List</Button>
            </div>

            {error && <ErrorAlert message={error} />}
            {success && <SuccessAlert message={success} />}

            {isReadOnly && governanceReason && (
                <div style={{
                    padding: 16,
                    marginBottom: 20,
                    backgroundColor: "#fef3c7",
                    border: "1px solid #f59e0b",
                    borderRadius: theme.radius.md,
                    display: "flex",
                    alignItems: "center",
                    gap: 12,
                }}>
                    <span style={{ fontSize: 20 }}>⚠️</span>
                    <div>
                        <strong style={{ display: "block", marginBottom: 4 }}>Read-Only Mode</strong>
                        <span style={{ color: "#92400e" }}>{governanceReason}</span>
                    </div>
                </div>
            )}

            <div style={{ backgroundColor: "white", padding: 20, borderRadius: theme.radius.lg, border: `1px solid ${theme.colors.border}`, marginBottom: 20 }}>
                <h3 style={{ marginTop: 0 }}>Profile Details</h3>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>
                    <div>
                        <label style={{ display: "block", marginBottom: 5 }}>Code</label>
                        <input value={profile.code} onChange={e => setProfile({ ...profile, code: e.target.value })} style={{ width: "100%", padding: 8 }} readOnly={isReadOnly} />
                    </div>
                    <div>
                        <label style={{ display: "block", marginBottom: 5 }}>Name</label>
                        <input value={profile.name} onChange={e => setProfile({ ...profile, name: e.target.value })} style={{ width: "100%", padding: 8 }} readOnly={isReadOnly} />
                    </div>
                    <div>
                        <label style={{ display: "block", marginBottom: 5 }}>Modality</label>
                        <input value={profile.modality} onChange={e => setProfile({ ...profile, modality: e.target.value })} style={{ width: "100%", padding: 8 }} readOnly={isReadOnly} />
                    </div>
                </div>
                {!isReadOnly && (
                    <div style={{ marginTop: 20, textAlign: "right" }}>
                        <Button variant="primary" onClick={handleSaveProfile} disabled={saving}>
                            {saving ? "Saving..." : isNew ? "Create Profile" : "Update Profile"}
                        </Button>
                    </div>
                )}
            </div>

            {!isNew && (
                <div style={{ backgroundColor: "white", padding: 20, borderRadius: theme.radius.lg, border: `1px solid ${theme.colors.border}` }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                        <h3 style={{ margin: 0 }}>Parameters</h3>
                        <div style={{ display: "flex", gap: 8 }}>
                            <Button variant="secondary" onClick={handleExportCsv}>Export CSV</Button>
                            <Button variant="secondary" onClick={() => setShowLibraryModal(true)}>Add from Library</Button>
                            <Button variant="primary" onClick={() => openParamModal()} disabled={isReadOnly}>Add New Parameter</Button>
                        </div>
                    </div>

                    <table style={{ width: "100%", borderCollapse: "collapse" }}>
                        <thead>
                            <tr style={{ borderBottom: `1px solid ${theme.colors.border}`, backgroundColor: theme.colors.backgroundGray }}>
                                <th style={{ textAlign: "left", padding: 8, width: 60 }}>Order</th>
                                <th style={{ textAlign: "left", padding: 8 }}>Section</th>
                                <th style={{ textAlign: "left", padding: 8 }}>Name</th>
                                <th style={{ textAlign: "left", padding: 8 }}>Type</th>
                                <th style={{ textAlign: "center", padding: 8, width: 100 }}>Reorder</th>
                                <th style={{ textAlign: "right", padding: 8 }}>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {parameters.map((p: Parameter, idx) => (
                                <tr key={p.parameter_id || p.id} style={{ borderBottom: `1px solid ${theme.colors.borderLight}` }}>
                                    <td style={{ padding: 8 }}>{p.order}</td>
                                    <td style={{ padding: 8 }}>{p.section}</td>
                                    <td style={{ padding: 8 }}>{p.name}</td>
                                    <td style={{ padding: 8 }}>{p.type || p.parameter_type}</td>
                                    <td style={{ padding: 8, textAlign: "center" }}>
                                        <div style={{ display: "flex", gap: 4, justifyContent: "center" }}>
                                            <button onClick={() => moveParam(idx, "up")} disabled={idx === 0 || isReadOnly} style={{ padding: "2px 6px", cursor: "pointer" }}>↑</button>
                                            <button onClick={() => moveParam(idx, "down")} disabled={idx === parameters.length - 1 || isReadOnly} style={{ padding: "2px 6px", cursor: "pointer" }}>↓</button>
                                        </div>
                                    </td>
                                    <td style={{ padding: 8, textAlign: "right" }}>
                                        <Button variant="secondary" onClick={() => openParamModal(undefined, idx)} style={{ marginRight: 8, fontSize: 11, padding: "4px 8px" }} disabled={isReadOnly}>Insert Above</Button>
                                        <Button variant="secondary" onClick={() => handleDuplicateParam(p)} style={{ marginRight: 8, fontSize: 11, padding: "4px 8px" }} disabled={isReadOnly}>Duplicate</Button>
                                        <Button variant="secondary" onClick={() => openParamModal(p)} style={{ marginRight: 8, fontSize: 11, padding: "4px 8px" }}>Edit</Button>
                                        <Button variant="secondary" onClick={() => handleDeleteParam(p.parameter_id || p.id!)} style={{ color: theme.colors.danger, fontSize: 11, padding: "4px 8px" }} disabled={isReadOnly}>Del</Button>
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

            {showLibraryModal && (
                <LibraryModal
                    items={libraryItems}
                    onClose={() => setShowLibraryModal(false)}
                    onSelect={handleAddFromLibrary}
                />
            )}
        </div>
    );
}

function LibraryModal({ items, onClose, onSelect }: { items: any[], onClose: () => void, onSelect: (item: any) => void }) {
    const [search, setSearch] = useState("");
    const filtered = items.filter(i => i.name.toLowerCase().includes(search.toLowerCase()) || i.slug.toLowerCase().includes(search.toLowerCase()));

    return (
        <div style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, backgroundColor: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1001 }}>
            <div style={{ backgroundColor: "white", padding: 24, borderRadius: 8, width: 700, maxHeight: "80vh", display: "flex", flexDirection: "column" }}>
                <h3 style={{ marginTop: 0 }}>Add from Parameter Library</h3>
                <input
                    placeholder="Search library..."
                    value={search}
                    onChange={e => setSearch(e.target.value)}
                    style={{ width: "100%", padding: 10, marginBottom: 16 }}
                />
                <div style={{ flex: 1, overflowY: "auto", border: "1px solid #eee", borderRadius: 4 }}>
                    <table style={{ width: "100%", borderCollapse: "collapse" }}>
                        <thead style={{ position: "sticky", top: 0, backgroundColor: "#f9f9f9" }}>
                            <tr>
                                <th style={{ textAlign: "left", padding: 10 }}>Modality</th>
                                <th style={{ textAlign: "left", padding: 10 }}>Name</th>
                                <th style={{ textAlign: "left", padding: 10 }}>Type</th>
                                <th style={{ textAlign: "right", padding: 10 }}>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filtered.map(item => (
                                <tr key={item.id} style={{ borderBottom: "1px solid #eee" }}>
                                    <td style={{ padding: 10 }}>{item.modality}</td>
                                    <td style={{ padding: 10 }}>
                                        <strong>{item.name}</strong>
                                        <div style={{ fontSize: 11, color: "#666" }}>{item.slug}</div>
                                    </td>
                                    <td style={{ padding: 10 }}>{item.parameter_type}</td>
                                    <td style={{ padding: 10, textAlign: "right" }}>
                                        <Button variant="primary" onClick={() => onSelect(item)} style={{ fontSize: 12, padding: "5px 10px" }}>Add</Button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                <div style={{ marginTop: 20, textAlign: "right" }}>
                    <Button variant="secondary" onClick={onClose}>Close</Button>
                </div>
            </div>
        </div>
    );
}

function ParameterModal({ param, onClose, onSave, token }: { param: any, onClose: () => void, onSave: (p: any) => void, token: string | null }) {
    const [data, setData] = useState({
        ...param,
        parameter_type: param.parameter_type || param.type || "short_text"
    });
    const [options, setOptions] = useState<any[]>(param.options || []);

    const handleChange = (field: string, value: any) => {
        setData({ ...data, [field]: value });
    };

    const handleSave = () => {
        onSave({ ...data, options });
    };

    return (
        <div style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, backgroundColor: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}>
            <div style={{ backgroundColor: "white", padding: 24, borderRadius: 8, width: 700, maxHeight: "90vh", overflowY: "auto" }}>
                <h3 style={{ marginTop: 0 }}>{data.id || data.parameter_id ? "Edit Parameter" : "New Parameter"}</h3>

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
                </div>

                <div style={{ marginBottom: 16 }}>
                    <label style={{ display: "block", fontSize: 12 }}>Sentence Template (Optional)</label>
                    <input
                        placeholder="e.g. {name} is {value} {unit}."
                        value={data.sentence_template || ""}
                        onChange={e => handleChange("sentence_template", e.target.value)}
                        style={{ width: "100%", padding: 6 }}
                    />
                    <div style={{ fontSize: 10, color: "#666", marginTop: 4 }}>
                        Available placeholders: {"{name}, {value}, {unit}, {section}"}
                    </div>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 16 }}>
                    <div>
                        <label style={{ display: "block", fontSize: 12 }}>Narrative Role</label>
                        <select value={data.narrative_role || "finding"} onChange={e => handleChange("narrative_role", e.target.value)} style={{ width: "100%", padding: 6 }}>
                            <option value="finding">Finding</option>
                            <option value="impression_hint">Impression Hint</option>
                            <option value="limitation_hint">Limitation Hint</option>
                            <option value="ignore">Ignore</option>
                        </select>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", paddingTop: 15 }}>
                        <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
                            <input type="checkbox" checked={data.is_required} onChange={e => handleChange("is_required", e.target.checked)} />
                            Required
                        </label>
                    </div>
                </div>

                {(data.parameter_type === "dropdown" || data.parameter_type === "checklist") && (
                    <div style={{ marginBottom: 16, border: "1px solid #eee", padding: 12, borderRadius: 4 }}>
                        <h4 style={{ marginTop: 0, marginBottom: 10 }}>Options</h4>
                        {options.map((opt, i) => (
                            <div key={i} style={{ display: "flex", gap: 8, marginBottom: 8 }}>
                                <input placeholder="Label" value={opt.label} onChange={e => {
                                    const next = [...options];
                                    next[i].label = e.target.value;
                                    setOptions(next);
                                }} style={{ flex: 1, padding: 4 }} />
                                <input placeholder="Value" value={opt.value} onChange={e => {
                                    const next = [...options];
                                    next[i].value = e.target.value;
                                    setOptions(next);
                                }} style={{ flex: 1, padding: 4 }} />
                                <button onClick={() => setOptions(options.filter((_, idx) => idx !== i))} style={{ padding: "2px 8px" }}>X</button>
                            </div>
                        ))}
                        <Button variant="secondary" onClick={() => setOptions([...options, { label: "", value: "", order: options.length }])} style={{ fontSize: 12 }}>+ Add Option</Button>
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
