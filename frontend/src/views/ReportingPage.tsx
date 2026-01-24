import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { apiGet, apiPost } from "../ui/api";
import { useAuth } from "../ui/auth";
import { theme } from "../theme";

interface ParameterOption {
    id: string;
    label: string;
    value: string;
}

interface Parameter {
    id: string;
    section: string;
    name: string;
    parameter_type: "number" | "dropdown" | "checklist" | "boolean" | "short_text" | "long_text" | "heading" | "separator";
    unit: string | null;
    normal_value: string | null;
    options: ParameterOption[];
    is_required: boolean;
}

interface ReportProfile {
    id: string;
    code: string;
    name: string;
    parameters: Parameter[];
}

interface ReportValue {
    parameter: string; // ID
    value: string;
}

export default function ReportingPage() {
    const { id } = useParams();
    const { token } = useAuth();
    const navigate = useNavigate();
    const [profile, setProfile] = useState<ReportProfile | null>(null);
    const [values, setValues] = useState<Record<string, string>>({});
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!id || !token) return;
        loadData();
    }, [id, token]);

    const loadData = async () => {
        try {
            setLoading(true);
            const [schemaData, valuesData] = await Promise.all([
                apiGet(`/reporting/workitems/${id}/schema/`, token),
                apiGet(`/reporting/workitems/${id}/values/`, token)
            ]);

            setProfile(schemaData);

            const valMap: Record<string, string> = {};
            // default values from profile
            schemaData.parameters.forEach((p: Parameter) => {
                if (p.normal_value) valMap[p.id] = p.normal_value;
                if (p.parameter_type === 'boolean' && !valMap[p.id]) valMap[p.id] = 'false';
            });

            // existing values override defaults
            valuesData.forEach((v: ReportValue) => {
                valMap[v.parameter] = v.value;
            });

            setValues(valMap);
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    };

    const handleChange = (paramId: string, value: string) => {
        setValues(prev => ({ ...prev, [paramId]: value }));
    };

    const handleSave = async () => {
        try {
            setSaving(true);
            await apiPost(`/reporting/workitems/${id}/save/`, token, { values });
            // maybe show toast
        } catch (e: any) {
            alert(e.message);
        } finally {
            setSaving(false);
        }
    };

    const handleSubmit = async () => {
        if (!confirm("Are you sure you want to submit this report? It will handle format validation and lock the report.")) return;
        try {
            setSaving(true);
            // First save to ensure backend has latest
            await apiPost(`/reporting/workitems/${id}/save/`, token, { values });
            await apiPost(`/reporting/workitems/${id}/submit/`, token, {});
            navigate("/patients/workflow"); // Go back to worklist
        } catch (e: any) {
            alert(e.message);
        } finally {
            setSaving(false);
        }
    };

    if (loading) return <div style={{ padding: 20 }}>Loading report...</div>;
    if (error) return <div style={{ padding: 20, color: "red" }}>Error: {error}</div>;
    if (!profile) return <div style={{ padding: 20 }}>No profile found.</div>;

    // Group by sections
    const sections: Record<string, Parameter[]> = {};
    profile.parameters.forEach(p => {
        if (!sections[p.section]) sections[p.section] = [];
        sections[p.section].push(p);
    });

    return (
        <div style={{ maxWidth: 900, margin: "0 auto", paddingBottom: 50 }}>
            <header style={{ marginBottom: 20, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                    <h1 style={{ fontSize: 24, fontWeight: "bold", margin: 0 }}>{profile.name}</h1>
                    <div style={{ color: theme.colors.textSecondary }}>{profile.code}</div>
                </div>
                <div style={{ display: "flex", gap: 10 }}>
                    <button
                        onClick={handleSave}
                        disabled={saving}
                        style={{
                            padding: "8px 16px",
                            borderRadius: theme.radius.base,
                            border: `1px solid ${theme.colors.brandBlue}`,
                            background: "white",
                            color: theme.colors.brandBlue,
                            cursor: "pointer"
                        }}>
                        Save Draft
                    </button>
                    <button
                        onClick={handleSubmit}
                        disabled={saving}
                        style={{
                            padding: "8px 16px",
                            borderRadius: theme.radius.base,
                            border: "none",
                            background: theme.colors.brandBlue,
                            color: "white",
                            cursor: "pointer"
                        }}>
                        Submit
                    </button>
                </div>
            </header>

            {Object.entries(sections).map(([sectionName, params]) => (
                <section key={sectionName} style={{
                    background: "white",
                    padding: 24,
                    borderRadius: theme.radius.md,
                    boxShadow: theme.shadows.sm,
                    marginBottom: 24
                }}>
                    <h2 style={{
                        fontSize: 18,
                        borderBottom: `1px solid ${theme.colors.border}`,
                        paddingBottom: 10,
                        marginBottom: 20,
                        color: theme.colors.textPrimary
                    }}>
                        {sectionName}
                    </h2>
                    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                        {params.map(p => (
                            <div key={p.id}>
                                {renderField(p, values[p.id] || "", handleChange)}
                            </div>
                        ))}
                    </div>
                </section>
            ))}
        </div>
    );
}

function renderField(p: Parameter, value: string, onChange: (id: string, v: string) => void) {
    if (p.parameter_type === "heading") {
        return <h3 style={{ margin: "20px 0 10px", fontSize: 16, fontWeight: "bold" }}>{p.name}</h3>;
    }
    if (p.parameter_type === "separator") {
        return <hr style={{ margin: "20px 0", borderTop: `1px solid ${theme.colors.border}` }} />;
    }

    const labelStyle = {
        display: "block",
        marginBottom: 6,
        fontWeight: 500,
        fontSize: 14,
        color: theme.colors.textPrimary
    };

    const inputStyle = {
        width: "100%",
        padding: "8px 12px",
        borderRadius: 6,
        border: `1px solid ${theme.colors.border}`,
        fontSize: 14,
        fontFamily: "inherit"
    };

    return (
        <div style={{ marginBottom: 10 }}>
            <label style={labelStyle}>
                {p.name} {p.unit && <span style={{ color: theme.colors.textTertiary, fontWeight: 400 }}>({p.unit})</span>}
                {p.is_required && <span style={{ color: "red" }}> *</span>}
            </label>

            {p.parameter_type === "short_text" && (
                <input
                    type="text"
                    value={value}
                    onChange={e => onChange(p.id, e.target.value)}
                    style={inputStyle}
                />
            )}

            {p.parameter_type === "long_text" && (
                <textarea
                    value={value}
                    onChange={e => onChange(p.id, e.target.value)}
                    style={{ ...inputStyle, minHeight: 80, resize: "vertical" }}
                />
            )}

            {p.parameter_type === "number" && (
                <input
                    type="number"
                    value={value}
                    onChange={e => onChange(p.id, e.target.value)}
                    style={{ ...inputStyle, width: 150 }}
                />
            )}

            {p.parameter_type === "dropdown" && (
                <select
                    value={value}
                    onChange={e => onChange(p.id, e.target.value)}
                    style={inputStyle}
                >
                    <option value="">Select...</option>
                    {p.options.map(opt => (
                        <option key={opt.id} value={opt.value}>{opt.label}</option>
                    ))}
                </select>
            )}

            {p.parameter_type === "boolean" && (
                <div style={{ display: "flex", gap: 20 }}>
                    <label style={{ fontWeight: 400 }}>
                        <input
                            type="radio"
                            name={p.id}
                            checked={value === "true"}
                            onChange={() => onChange(p.id, "true")}
                        /> Yes
                    </label>
                    <label style={{ fontWeight: 400 }}>
                        <input
                            type="radio"
                            name={p.id}
                            checked={value === "false"}
                            onChange={() => onChange(p.id, "false")}
                        /> No
                    </label>
                </div>
            )}

            {p.parameter_type === "checklist" && (
                <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
                    {/* Checklist logic requires parsing string to array - simplify for MVP: store as comma joined? */}
                    {p.options.map(opt => {
                        const currentArr = value ? value.split(",") : [];
                        const checked = currentArr.includes(opt.value);
                        return (
                            <label key={opt.id} style={{ display: "flex", alignItems: "center", gap: 8, fontWeight: 400, fontSize: 14 }}>
                                <input
                                    type="checkbox"
                                    checked={checked}
                                    onChange={e => {
                                        let newArr = [...currentArr];
                                        if (e.target.checked) newArr.push(opt.value);
                                        else newArr = newArr.filter(x => x !== opt.value);
                                        onChange(p.id, newArr.filter(Boolean).join(","));
                                    }}
                                />
                                {opt.label}
                            </label>
                        )
                    })}
                </div>
            )}
        </div>
    );
}
