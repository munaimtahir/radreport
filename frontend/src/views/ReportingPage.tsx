import React, { useEffect, useState, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "../ui/auth";
import { theme } from "../theme";
import {
    getReportSchema,
    getReportValues,
    saveReport,
    submitReport,
    generateNarrative,
    getNarrative,
    ReportSchema,
    ReportParameter,
    ReportValueEntry,
    NarrativeResponse,
    fetchReportPdf
} from "../ui/reporting";
import Button from "../ui/components/Button";
import ErrorAlert from "../ui/components/ErrorAlert";
import SuccessAlert from "../ui/components/SuccessAlert";

export default function ReportingPage() {
    const { service_visit_item_id: id } = useParams<{ service_visit_item_id: string }>(); // This is service_visit_item_id
    const { token } = useAuth();
    const navigate = useNavigate();

    const [schema, setSchema] = useState<ReportSchema | null>(null);
    const [valuesByParamId, setValuesByParamId] = useState<Record<string, any>>({});
    const [status, setStatus] = useState<"draft" | "submitted" | "verified">("draft");
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

    const [showSubmitModal, setShowSubmitModal] = useState(false);

    // Stage 2: Narrative State
    const [narrative, setNarrative] = useState<NarrativeResponse['narrative'] | null>(null);
    const [generatingNarrative, setGeneratingNarrative] = useState(false);

    useEffect(() => {
        if (!id || !token) return;
        loadData();
    }, [id, token]);

    const loadData = async () => {
        if (!id) return;
        try {
            setLoading(true);
            setError(null);
            // Parallel Fetching (MANDATORY)

            // Parallel Fetching (MANDATORY)
            const [schemaData, valuesResponse, narrativeResponse] = await Promise.all([
                getReportSchema(id, token),
                getReportValues(id, token),
                getNarrative(id, token)
            ]);

            setSchema(schemaData);
            setStatus(valuesResponse.status);
            setNarrative(narrativeResponse.narrative);

            // Defaulting Logic (MANDATORY)
            const initialValues: Record<string, any> = {};
            const existingValuesMap: Record<string, any> = {};
            (valuesResponse.values || []).forEach(v => {
                // Try to parse JSON if it looks like an array (for checklist)
                let val = v.value;
                if (typeof val === "string" && (val.startsWith("[") || val.startsWith("{"))) {
                    try { val = JSON.parse(val); } catch (e) { }
                }
                existingValuesMap[v.parameter_id] = val;
            });

            schemaData.parameters.forEach((param: ReportParameter) => {
                const existingValue = existingValuesMap[param.parameter_id];

                // If value exists from backend -> use it
                if (existingValue !== undefined && existingValue !== null) {
                    initialValues[param.parameter_id] = existingValue;
                    return;
                }

                // Else if normal_value exists -> initialize from normal_value
                if (param.normal_value !== null && param.normal_value !== undefined) {
                    if (param.type === "boolean") {
                        initialValues[param.parameter_id] = param.normal_value.toLowerCase() === "true" || param.normal_value === "1";
                    } else if (param.type === "checklist") {
                        initialValues[param.parameter_id] = param.normal_value.split(",").map(s => s.trim()).filter(Boolean);
                    } else if (param.type === "number") {
                        initialValues[param.parameter_id] = parseFloat(param.normal_value);
                    } else {
                        initialValues[param.parameter_id] = param.normal_value;
                    }
                } else {
                    // Else initialize as:
                    switch (param.type) {
                        case "short_text":
                        case "long_text":
                            initialValues[param.parameter_id] = "";
                            break;
                        case "number":
                            initialValues[param.parameter_id] = null;
                            break;
                        case "boolean":
                            initialValues[param.parameter_id] = false;
                            break;
                        case "dropdown":
                            const hasNA = param.options.some(opt => opt.value === "na");
                            initialValues[param.parameter_id] = hasNA ? "na" : "";
                            break;
                        case "checklist":
                            initialValues[param.parameter_id] = [];
                            break;
                        default:
                            initialValues[param.parameter_id] = "";
                    }
                }
            });

            setValuesByParamId(initialValues);
        } catch (e: any) {
            setError(e.message || "Failed to load report data");
        } finally {
            setLoading(false);
        }
    };

    const handleValueChange = (paramId: string, value: any) => {
        if (status !== "draft") return;
        setValuesByParamId(prev => ({ ...prev, [paramId]: value }));
        if (validationErrors[paramId]) {
            setValidationErrors(prev => {
                const next = { ...prev };
                delete next[paramId];
                return next;
            });
        }
    };

    const preparePayload = () => {
        const values: ReportValueEntry[] = Object.entries(valuesByParamId).map(([paramId, value]) => ({
            parameter_id: paramId,
            value: value
        }));
        return { values };
    };

    const handleSaveDraft = async () => {
        if (!id || status !== "draft") return;
        try {
            setSaving(true);
            setError(null);
            setSuccess(null);
            await saveReport(id, preparePayload(), token);
            setSuccess("Draft saved successfully");
        } catch (e: any) {
            setError(e.message || "Failed to save draft");
        } finally {
            setSaving(false);
        }
    };

    const handleSubmit = async () => {
        if (!id || status !== "draft") return;
        try {
            setSaving(true);
            setError(null);
            setValidationErrors({});

            // Path for Submission as per spec
            await saveReport(id, preparePayload(), token);
            await submitReport(id, token);

            setStatus("submitted");
            setSuccess("Report submitted and locked");
            setShowSubmitModal(false);
            window.scrollTo({ top: 0, behavior: "smooth" });
        } catch (e: any) {
            // Updated behavior for validation failure as per spec
            if (e.message.includes("validation_failed") || (typeof e === 'object' && e !== null && 'missing' in e)) {
                // If it's a JSON response with 'missing'
                try {
                    // Some fetch wrappers might throw error with body attached
                    // If not, we need to handle it based on how api.ts behaves
                } catch (err) { }
            }

            // Checking for the spec'ed error structure
            // Note: api.ts current implementation might obscure the JSON body if it's not "detail"
            setError("Validation failed. Please check required fields.");
            setShowSubmitModal(false);
        } finally {
            setSaving(false);
        }
    };

    const handleGenerateNarrative = async () => {
        if (!id || !token) return;
        try {
            setGeneratingNarrative(true);
            setError(null);

            // If draft, save first to ensure DB has latest values for generator
            if (status === "draft") {
                await saveReport(id, preparePayload(), token);
            }

            const response = await generateNarrative(id, token);
            setNarrative(response.narrative);
            setSuccess("Narrative generated and saved.");
        } catch (e: any) {
            setError(e.message || "Failed to generate narrative");
        } finally {
            setGeneratingNarrative(false);
        }
    };

    const handlePreviewPdf = async () => {
        if (!id || !token) return;
        try {
            if (status === 'draft') {
                setSaving(true);
                await saveReport(id, preparePayload(), token);
                setSaving(false);
            }

            const blob = await fetchReportPdf(id, token);
            const url = window.URL.createObjectURL(blob);
            window.open(url, '_blank');
        } catch (e: any) {
            setError("Failed to load PDF: " + e.message);
            setSaving(false);
        }
    };

    const groupedParameters = useMemo(() => {
        if (!schema) return [];
        const sections: Record<string, ReportParameter[]> = {};
        schema.parameters.forEach(p => {
            const sec = p.section || "General";
            if (!sections[sec]) sections[sec] = [];
            sections[sec].push(p);
        });
        return Object.entries(sections);
    }, [schema]);

    if (loading) {
        return (
            <div style={{ padding: 40, textAlign: "center", color: theme.colors.textSecondary }}>
                Loading report template...
            </div>
        );
    }

    if (!schema) {
        return (
            <div style={{ padding: 40, textAlign: "center" }}>
                <ErrorAlert message={error || "Could not load report schema."} />
                <Button onClick={() => navigate(-1)} variant="secondary" style={{ marginTop: 20 }}>
                    Go Back
                </Button>
            </div>
        );
    }

    const isReadOnly = status !== "draft";

    return (
        <div style={{ maxWidth: 1000, margin: "0 auto", paddingBottom: 100 }}>
            {/* Header */}
            <div style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: 24,
                paddingBottom: 20,
                borderBottom: `1px solid ${theme.colors.border}`
            }}>
                <div>
                    <h1 style={{ fontSize: 28, fontWeight: 700, margin: 0, color: theme.colors.textPrimary }}>
                        {schema.name}
                    </h1>
                    <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 4 }}>
                        <span style={{ color: theme.colors.textSecondary, fontSize: 14 }}>Code: {schema.code}</span>
                        <span style={{
                            padding: "2px 8px",
                            borderRadius: 4,
                            fontSize: 12,
                            fontWeight: 600,
                            textTransform: "uppercase",
                            backgroundColor: status === "draft" ? theme.colors.brandBlueSoft :
                                status === "submitted" ? "#fff3cd" : "#d1e7dd",
                            color: status === "draft" ? theme.colors.brandBlue :
                                status === "submitted" ? "#856404" : "#0f5132"
                        }}>
                            {status}
                        </span>
                    </div>
                </div>
                <div style={{ display: "flex", gap: 12 }}>
                    <Button
                        variant="secondary"
                        onClick={() => navigate("/reporting/worklist")}
                    >
                        Back to Worklist
                    </Button>
                    <Button
                        variant="secondary"
                        onClick={handlePreviewPdf}
                        disabled={loading || saving}
                    >
                        Preview PDF
                    </Button>
                    {!isReadOnly && (
                        <>
                            <Button
                                variant="secondary"
                                onClick={handleSaveDraft}
                                disabled={saving}
                            >
                                {saving ? "Saving..." : "Save Draft"}
                            </Button>
                            <Button
                                variant="primary"
                                onClick={() => setShowSubmitModal(true)}
                                disabled={saving}
                            >
                                Submit Report
                            </Button>
                        </>
                    )}
                </div>
            </div>

            <div style={{ marginBottom: 20 }}>
                {error && <ErrorAlert message={error} />}
                {success && <SuccessAlert message={success} />}
            </div>

            {/* Dynamic Form */}
            <div style={{ display: "flex", flexDirection: "column", gap: 32 }}>
                {groupedParameters.map(([sectionName, params]) => (
                    <div key={sectionName} style={{
                        backgroundColor: "white",
                        borderRadius: theme.radius.lg,
                        boxShadow: theme.shadows.sm,
                        border: `1px solid ${theme.colors.border}`,
                        overflow: "hidden"
                    }}>
                        <div style={{
                            padding: "16px 24px",
                            backgroundColor: theme.colors.backgroundGray,
                            borderBottom: `1px solid ${theme.colors.border}`,
                            fontWeight: 600,
                            fontSize: 16,
                            color: theme.colors.textPrimary
                        }}>
                            {sectionName}
                        </div>
                        <div style={{ padding: "24px", display: "flex", flexDirection: "column", gap: 20 }}>
                            {params.map(param => (
                                <div key={param.parameter_id}>
                                    {renderParameter(param, valuesByParamId[param.parameter_id], handleValueChange, isReadOnly, validationErrors[param.parameter_id])}
                                </div>
                            ))}
                        </div>
                    </div>
                ))}
            </div>



            {/* Narrative Preview Panel - Stage 2 */}
            <div style={{
                marginTop: 40,
                backgroundColor: "white",
                borderRadius: theme.radius.lg,
                boxShadow: theme.shadows.sm,
                border: `1px solid ${theme.colors.border}`,
                overflow: "hidden"
            }}>
                <div style={{
                    padding: "16px 24px",
                    backgroundColor: theme.colors.brandBlueDark,
                    color: "white",
                    fontWeight: 600,
                    fontSize: 16,
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center"
                }}>
                    <span>Narrative Preview</span>
                    <Button
                        onClick={handleGenerateNarrative}
                        disabled={generatingNarrative}
                        style={{ backgroundColor: "rgba(255,255,255,0.2)", border: "none", color: "white", padding: "6px 12px", fontSize: 13 }}
                    >
                        {generatingNarrative ? "Generating..." : "Generate Preview"}
                    </Button>
                </div>

                {narrative && (
                    <div style={{ padding: 24, display: "flex", flexDirection: "column", gap: 20 }}>
                        <div>
                            <label style={{ display: "block", fontSize: 13, fontWeight: 700, color: theme.colors.textSecondary, marginBottom: 8, textTransform: "uppercase" }}>
                                Findings
                            </label>
                            <textarea
                                value={narrative.findings_text}
                                readOnly
                                style={{
                                    width: "100%",
                                    minHeight: 150,
                                    padding: 12,
                                    borderRadius: 8,
                                    border: `1px solid ${theme.colors.border}`,
                                    backgroundColor: theme.colors.backgroundGray,
                                    fontFamily: "monospace",
                                    fontSize: 14,
                                    lineHeight: 1.5,
                                    resize: "vertical"
                                }}
                            />
                        </div>

                        {(narrative.impression_text || status === 'submitted' || status === 'verified') && (
                            <div>
                                <label style={{ display: "block", fontSize: 13, fontWeight: 700, color: theme.colors.textSecondary, marginBottom: 8, textTransform: "uppercase" }}>
                                    Impression
                                </label>
                                <textarea
                                    value={narrative.impression_text}
                                    readOnly
                                    style={{
                                        width: "100%",
                                        minHeight: 80,
                                        padding: 12,
                                        borderRadius: 8,
                                        border: `1px solid ${theme.colors.border}`,
                                        backgroundColor: theme.colors.backgroundGray,
                                        fontFamily: "monospace",
                                        fontSize: 14
                                    }}
                                />
                            </div>
                        )}

                        {(narrative.limitations_text || status === 'submitted' || status === 'verified') && (
                            <div>
                                <label style={{ display: "block", fontSize: 13, fontWeight: 700, color: theme.colors.textSecondary, marginBottom: 8, textTransform: "uppercase" }}>
                                    Limitations
                                </label>
                                <textarea
                                    value={narrative.limitations_text}
                                    readOnly
                                    style={{
                                        width: "100%",
                                        minHeight: 60,
                                        padding: 12,
                                        borderRadius: 8,
                                        border: `1px solid ${theme.colors.border}`,
                                        backgroundColor: theme.colors.backgroundGray,
                                        fontFamily: "monospace",
                                        fontSize: 14
                                    }}
                                />
                            </div>
                        )}

                        <div style={{ fontSize: 12, color: theme.colors.textTertiary, textAlign: "right" }}>
                            Version: {narrative.version}
                        </div>
                    </div>
                )}
            </div>

            {/* Confirmation Modal */}
            {
                showSubmitModal && (
                    <div style={{
                        position: "fixed",
                        top: 0,
                        left: 0,
                        right: 0,
                        bottom: 0,
                        backgroundColor: "rgba(0,0,0,0.5)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        zIndex: 1000,
                        backdropFilter: "blur(4px)"
                    }}>
                        <div style={{
                            backgroundColor: "white",
                            padding: 32,
                            borderRadius: theme.radius.lg,
                            maxWidth: 400,
                            width: "90%",
                            boxShadow: theme.shadows.lg
                        }}>
                            <h3 style={{ marginTop: 0, fontSize: 20 }}>Confirm Submission</h3>
                            <p style={{ color: theme.colors.textSecondary, lineHeight: 1.5 }}>
                                Are you sure you want to submit this report? Submitting will lock all values and move the report to the verification queue.
                            </p>
                            <div style={{ display: "flex", justifyContent: "flex-end", gap: 12, marginTop: 24 }}>
                                <Button variant="secondary" onClick={() => setShowSubmitModal(false)}>
                                    Cancel
                                </Button>
                                <Button variant="primary" onClick={handleSubmit} disabled={saving}>
                                    {saving ? "Submitting..." : "Yes, Submit"}
                                </Button>
                            </div>
                        </div>
                    </div>
                )
            }
        </div >
    );
}

function renderParameter(
    param: ReportParameter,
    value: any,
    onChange: (id: string, val: any) => void,
    isReadOnly: boolean,
    error?: string
) {
    if (param.type === "heading") {
        return (
            <h4 style={{
                marginTop: 10,
                marginBottom: 5,
                fontSize: 15,
                fontWeight: 700,
                color: theme.colors.brandBlue,
                textTransform: "uppercase",
                letterSpacing: "0.5px"
            }}>
                {param.name}
            </h4>
        );
    }

    if (param.type === "separator") {
        return <hr style={{ border: 0, borderTop: `1px solid ${theme.colors.border}`, margin: "10px 0" }} />;
    }

    const labelStyle = {
        display: "block",
        marginBottom: 6,
        fontWeight: 500,
        fontSize: 14,
        color: theme.colors.textPrimary
    };

    const inputBaseStyle: React.CSSProperties = {
        width: "100%",
        padding: "10px 14px",
        borderRadius: 8,
        border: `1px solid ${error ? theme.colors.danger : theme.colors.border}`,
        fontSize: 14,
        fontFamily: "inherit",
        backgroundColor: isReadOnly ? theme.colors.backgroundGray : "white",
        color: isReadOnly ? theme.colors.textSecondary : theme.colors.textPrimary,
        outline: "none",
        transition: "border-color 0.2s, box-shadow 0.2s"
    };

    return (
        <div style={{ position: "relative" }}>
            <label style={labelStyle}>
                {param.name}
                {param.unit && (
                    <span style={{ color: theme.colors.textTertiary, fontWeight: 400, marginLeft: 4 }}>
                        ({param.unit})
                    </span>
                )}
                {param.is_required && <span style={{ color: theme.colors.danger, marginLeft: 4 }}>*</span>}
            </label>

            {/* Render logic by type strictly following spec */}
            {param.type === "short_text" && (
                <input
                    type="text"
                    value={value || ""}
                    disabled={isReadOnly}
                    onChange={e => onChange(param.parameter_id, e.target.value)}
                    style={inputBaseStyle}
                />
            )}

            {param.type === "long_text" && (
                <textarea
                    value={value || ""}
                    disabled={isReadOnly}
                    onChange={e => onChange(param.parameter_id, e.target.value)}
                    style={{ ...inputBaseStyle, minHeight: 100, resize: "vertical" }}
                />
            )}

            {param.type === "number" && (
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                    <input
                        type="number"
                        value={value === null ? "" : value}
                        disabled={isReadOnly}
                        onChange={e => onChange(param.parameter_id, e.target.value === "" ? null : parseFloat(e.target.value))}
                        style={{ ...inputBaseStyle, width: 200 }}
                    />
                    {param.unit && <span style={{ fontSize: 14, color: theme.colors.textSecondary }}>{param.unit}</span>}
                </div>
            )}

            {param.type === "boolean" && (
                <div style={{ padding: "8px 0" }}>
                    <label style={{ display: "flex", alignItems: "center", gap: 10, cursor: isReadOnly ? "default" : "pointer" }}>
                        <input
                            type="checkbox"
                            checked={!!value}
                            disabled={isReadOnly}
                            onChange={e => onChange(param.parameter_id, e.target.checked)}
                            style={{ width: 20, height: 20 }}
                        />
                        <span style={{ fontSize: 14 }}>{param.name}</span>
                    </label>
                </div>
            )}

            {param.type === "dropdown" && (
                <select
                    value={value || ""}
                    disabled={isReadOnly}
                    onChange={e => onChange(param.parameter_id, e.target.value)}
                    style={inputBaseStyle}
                >
                    <option value="">Select...</option>
                    {param.options.map(opt => (
                        <option key={opt.id} value={opt.value}>
                            {opt.label}
                        </option>
                    ))}
                </select>
            )}

            {param.type === "checklist" && (
                <div style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
                    gap: 12,
                    padding: "8px 0"
                }}>
                    {param.options.map(opt => {
                        const currentSelected = Array.isArray(value) ? value : [];
                        const isChecked = currentSelected.includes(opt.value);
                        return (
                            <label key={opt.id} style={{
                                display: "flex",
                                alignItems: "center",
                                gap: 10,
                                cursor: isReadOnly ? "default" : "pointer",
                                padding: "8px 12px",
                                borderRadius: 6,
                                backgroundColor: isChecked ? theme.colors.brandBlueSoft : "transparent",
                                border: `1px solid ${isChecked ? theme.colors.brandBlue : "transparent"}`,
                                transition: "all 0.2s"
                            }}>
                                <input
                                    type="checkbox"
                                    checked={isChecked}
                                    disabled={isReadOnly}
                                    style={{ width: 16, height: 16 }}
                                    onChange={e => {
                                        if (e.target.checked) {
                                            onChange(param.parameter_id, [...currentSelected, opt.value]);
                                        } else {
                                            onChange(param.parameter_id, currentSelected.filter(v => v !== opt.value));
                                        }
                                    }}
                                />
                                <span style={{ fontSize: 13, color: isChecked ? theme.colors.brandBlue : theme.colors.textPrimary }}>
                                    {opt.label}
                                </span>
                            </label>
                        );
                    })}
                </div>
            )}

            {error && (
                <div style={{ color: theme.colors.danger, fontSize: 12, marginTop: 4, fontWeight: 500 }}>
                    {error}
                </div>
            )}
        </div>
    );
}
