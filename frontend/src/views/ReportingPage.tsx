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
    ReportSchemaV2,
    ReportParameter,
    ReportValueEntry,
    NarrativeResponse,
    fetchReportPdf,
    verifyReport,
    returnReport,
    publishReport,
    getPublishHistory,
    fetchPublishedPdf,
    checkIntegrity
} from "../ui/reporting";
import SchemaFormV2 from "../components/reporting/SchemaFormV2";
import Button from "../ui/components/Button";
import ErrorAlert from "../ui/components/ErrorAlert";
import SuccessAlert from "../ui/components/SuccessAlert";

export default function ReportingPage() {
    const { service_visit_item_id: id } = useParams<{ service_visit_item_id: string }>();
    const { token, user } = useAuth(); // Assume user object has groups/permissions
    const navigate = useNavigate();

    const [schema, setSchema] = useState<ReportSchema | ReportSchemaV2 | null>(null);
    const [valuesByParamId, setValuesByParamId] = useState<Record<string, any>>({});
    const [valuesJson, setValuesJson] = useState<Record<string, any>>({});
    const [status, setStatus] = useState<"draft" | "submitted" | "verified">("draft");
    const [isPublished, setIsPublished] = useState(false);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);
    const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

    const [lastSavedAt, setLastSavedAt] = useState<string | null>(null);
    const [narrativeUpdatedAt, setNarrativeUpdatedAt] = useState<string | null>(null);
    const [lastPublishedAt, setLastPublishedAt] = useState<string | null>(null);
    const [integrityStatus, setIntegrityStatus] = useState<Record<number, boolean>>({});

    const [showSubmitModal, setShowSubmitModal] = useState(false);

    // Stage 4 Modals
    const [showReturnModal, setShowReturnModal] = useState(false);
    const [showPublishModal, setShowPublishModal] = useState(false);
    const [returnReason, setReturnReason] = useState("");
    const [publishNotes, setPublishNotes] = useState("");
    const [publishConfirm, setPublishConfirm] = useState("");
    const [publishHistory, setPublishHistory] = useState<any[]>([]);

    const isSchemaV2 = (schema as ReportSchemaV2 | null)?.schema_version === "v2";

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

            const [schemaData, valuesResponse, narrativeResponse] = await Promise.all([
                getReportSchema(id, token),
                getReportValues(id, token),
                getNarrative(id, token)
            ]);

            setSchema(schemaData);
            setStatus(valuesResponse.status);
            const published = !!valuesResponse.is_published;
            setIsPublished(published);
            setNarrative(narrativeResponse.narrative);
            setLastSavedAt(valuesResponse.last_saved_at || null);
            setNarrativeUpdatedAt(valuesResponse.narrative_updated_at || null);
            setLastPublishedAt(valuesResponse.last_published_at || null);

            if (published) {
                const history = await getPublishHistory(id, token);
                setPublishHistory(history);
                // Trigger background integrity checks
                history.forEach((snap: any) => {
                    checkIntegrity(id, snap.version, token)
                        .then(res => setIntegrityStatus(prev => ({ ...prev, [snap.version]: res.match })))
                        .catch(console.error);
                });
            }

            if ("schema_version" in schemaData && schemaData.schema_version === "v2") {
                setValuesJson(valuesResponse.values_json || {});
                setValuesByParamId({});
            } else {
                setValuesJson({});
                // Defaulting Logic
                const initialValues: Record<string, any> = {};
                const existingValuesMap: Record<string, any> = {};
                (valuesResponse.values || []).forEach(v => {
                    let val = v.value;
                    if (typeof val === "string" && (val.startsWith("[") || val.startsWith("{"))) {
                        try { val = JSON.parse(val); } catch (e) { }
                    }
                    existingValuesMap[v.parameter_id] = val;
                });

                (schemaData as ReportSchema).parameters.forEach((param: ReportParameter) => {
                    const existingValue = existingValuesMap[param.parameter_id];
                    if (existingValue !== undefined && existingValue !== null) {
                        initialValues[param.parameter_id] = existingValue;
                        return;
                    }
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
                        switch (param.type) {
                            case "short_text":
                            case "text":
                            case "long_text":
                            case "multiline":
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
            }
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

    const preparePayload = (): { values: ReportValueEntry[] } | { schema_version: "v2"; values_json: Record<string, any> } => {
        if (isSchemaV2) {
            return { schema_version: "v2", values_json: valuesJson };
        }
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
            setLastSavedAt(new Date().toISOString());
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

            await saveReport(id, preparePayload(), token);
            await submitReport(id, token);

            setStatus("submitted");
            setSuccess("Report submitted and locked for verification");
            setShowSubmitModal(false);
            window.scrollTo({ top: 0, behavior: "smooth" });
        } catch (e: any) {
            if (e.message.includes("validation_failed") || (typeof e === 'object' && e !== null && 'missing' in e)) {
                // handle validation
            }
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

    // Stage 4 Handlers
    const handleVerify = async () => {
        if (!id) return;
        try {
            setSaving(true);
            const res = await verifyReport(id, "", token);
            setStatus("verified");
            setIsPublished(true);
            setSuccess("Report verified and published successfully.");
            // Reload to get new version/history
            await loadData();
        } catch (e: any) {
            setError(e.message || "Verification failed");
        } finally {
            setSaving(false);
        }
    };

    const handleReturn = async () => {
        if (!id) return;
        if (!returnReason.trim()) {
            alert("Reason is required");
            return;
        }
        try {
            setSaving(true);
            await returnReport(id, returnReason, token);
            setStatus("draft");
            setSuccess("Report returned for correction.");
            setShowReturnModal(false);
            setReturnReason("");
            window.scrollTo({ top: 0, behavior: "smooth" });
        } catch (e: any) {
            setError(e.message || "Return failed");
        } finally {
            setSaving(false);
        }
    };

    const handlePublish = async () => {
        if (!id) return;
        if (publishConfirm !== "PUBLISH") return;
        try {
            setSaving(true);
            await publishReport(id, publishNotes, token);
            setIsPublished(true);
            setSuccess("Report published successfully!");
            setShowPublishModal(false);
            // Reload history
            getPublishHistory(id, token).then(setPublishHistory).catch(console.error);
        } catch (e: any) {
            if (e.status === 409) {
                setError("Another publish occurred. Please refresh.");
            } else {
                setError(e.message || "Publish failed");
            }
        } finally {
            setSaving(false);
        }
    };

    const handleViewPublishedPdf = async (version: number) => {
        if (!id) return;
        try {
            const blob = await fetchPublishedPdf(id, version, token);
            const url = window.URL.createObjectURL(blob);
            window.open(url, '_blank');
        } catch (e: any) {
            setError("Failed to fetch published PDF: " + e.message);
        }
    };

    const groupedParameters = useMemo(() => {
        if (!schema || isSchemaV2) return [];
        const v1Schema = schema as ReportSchema;
        const sections: Record<string, ReportParameter[]> = {};
        v1Schema.parameters.forEach((p: ReportParameter) => {
            const sec = p.section || "General";
            if (!sections[sec]) sections[sec] = [];
            sections[sec].push(p);
        });
        return Object.entries(sections);
    }, [schema, isSchemaV2]);

    if (loading) return <div style={{ padding: 40, textAlign: "center" }}>Loading report...</div>;
    if (!schema) return <div style={{ padding: 40, textAlign: "center" }}><ErrorAlert message={error || "Error loading."} /></div>;

    const isReadOnly = status !== "draft";
    const statusColor = status === "draft" ? theme.colors.brandBlue : status === "submitted" ? "#856404" : "#0f5132";
    const statusBg = status === "draft" ? theme.colors.brandBlueSoft : status === "submitted" ? "#fff3cd" : "#d1e7dd";

    return (
        <div style={{ maxWidth: 1000, margin: "0 auto", paddingBottom: 100 }}>
            {/* Header */}
            <div style={{
                display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24, paddingBottom: 20, borderBottom: `1px solid ${theme.colors.border}`
            }}>
                <div>
                    <h1 style={{ fontSize: 28, fontWeight: 700, margin: 0, color: theme.colors.textPrimary }}>{schema.name}</h1>
                    <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 4 }}>
                        <span style={{ color: theme.colors.textSecondary, fontSize: 14 }}>Code: {schema.code}</span>
                        <span style={{
                            padding: "2px 8px", borderRadius: 4, fontSize: 12, fontWeight: 600, textTransform: "uppercase",
                            backgroundColor: isPublished ? theme.colors.success : statusBg,
                            color: isPublished ? "white" : statusColor
                        }}>
                            {isPublished ? `Published (Draft: ${status})` : status}
                        </span>
                    </div>
                    {(lastSavedAt || narrativeUpdatedAt || lastPublishedAt) && (
                        <div style={{ display: "flex", gap: 16, marginTop: 8, fontSize: 11, color: theme.colors.textTertiary }}>
                            {lastSavedAt && <span>Saved: {new Date(lastSavedAt).toLocaleString()}</span>}
                            {narrativeUpdatedAt && <span>Narrative: {new Date(narrativeUpdatedAt).toLocaleString()}</span>}
                            {lastPublishedAt && <span style={{ color: theme.colors.success }}>Published: {new Date(lastPublishedAt).toLocaleString()}</span>}
                        </div>
                    )}
                </div>
                <div style={{ display: "flex", gap: 12 }}>
                    <Button variant="secondary" onClick={() => navigate("/reporting/worklist")}>Worklist</Button>

                    {/* Actions based on status */}
                    {status === "draft" && (
                        <>
                            <Button variant="secondary" onClick={handleSaveDraft} disabled={saving}>Save Draft</Button>
                            <Button variant="primary" onClick={() => setShowSubmitModal(true)} disabled={saving}>Submit Report</Button>
                        </>
                    )}

                    {status === "submitted" && (
                        <>
                            <Button variant="secondary" onClick={handlePreviewPdf}>Preview PDF</Button>
                            <Button variant="secondary" onClick={() => setShowReturnModal(true)} style={{ color: theme.colors.danger, borderColor: theme.colors.danger }}>Return</Button>
                            <Button variant="primary" onClick={handleVerify} disabled={saving}>Verify</Button>
                        </>
                    )}

                    {status === "verified" && (
                        <>
                            <Button variant="secondary" onClick={handlePreviewPdf}>Preview PDF</Button>
                            <Button variant="secondary" onClick={() => setShowReturnModal(true)} style={{ color: theme.colors.danger, borderColor: theme.colors.danger }}>Return</Button>
                            <Button variant="primary" onClick={() => setShowPublishModal(true)} disabled={saving} style={{ backgroundColor: theme.colors.success, borderColor: theme.colors.success }}>Publish</Button>
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
                {isSchemaV2 ? (
                    <SchemaFormV2
                        jsonSchema={(schema as ReportSchemaV2).json_schema}
                        uiSchema={(schema as ReportSchemaV2).ui_schema}
                        values={valuesJson}
                        onChange={setValuesJson}
                        onSave={status === "draft" ? handleSaveDraft : undefined}
                        saving={saving}
                        isReadOnly={isReadOnly}
                    />
                ) : (
                    groupedParameters.map(([sectionName, params]) => (
                        <div key={sectionName} style={{ backgroundColor: "white", borderRadius: theme.radius.lg, boxShadow: theme.shadows.sm, border: `1px solid ${theme.colors.border}`, overflow: "hidden" }}>
                            <div style={{ padding: "16px 24px", backgroundColor: theme.colors.backgroundGray, borderBottom: `1px solid ${theme.colors.border}`, fontWeight: 600, fontSize: 16 }}>{sectionName}</div>
                            <div style={{ padding: "24px", display: "flex", flexDirection: "column", gap: 20 }}>
                                {params.map(param => (
                                    <div key={param.parameter_id}>
                                        {renderParameter(param, valuesByParamId[param.parameter_id], handleValueChange, isReadOnly, validationErrors[param.parameter_id])}
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* Narrative Preview */}
            <div style={{ marginTop: 40, backgroundColor: "white", borderRadius: theme.radius.lg, boxShadow: theme.shadows.sm, border: `1px solid ${theme.colors.border}`, overflow: "hidden" }}>
                <div style={{ padding: "16px 24px", backgroundColor: theme.colors.brandBlueDark, color: "white", fontWeight: 600, fontSize: 16, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span>Narrative Preview</span>
                    <Button onClick={handleGenerateNarrative} disabled={generatingNarrative} style={{ backgroundColor: "rgba(255,255,255,0.2)", border: "none", color: "white", padding: "6px 12px", fontSize: 13 }}>
                        {generatingNarrative ? "Generating..." : "Generate Preview"}
                    </Button>
                </div>
                {narrative && (
                    <div style={{ padding: 24, display: "flex", flexDirection: "column", gap: 20 }}>
                        <div>
                            <label style={{ display: "block", fontSize: 13, fontWeight: 700, color: theme.colors.textSecondary, marginBottom: 8, textTransform: "uppercase" }}>Findings</label>
                            <textarea value={narrative.findings_text} readOnly style={{ width: "100%", minHeight: 150, padding: 12, borderRadius: 8, border: `1px solid ${theme.colors.border}`, backgroundColor: theme.colors.backgroundGray, fontFamily: "monospace", fontSize: 14, lineHeight: 1.5, resize: "vertical" }} />
                        </div>
                        {/* Impression & Limitations omitted for brevity but logic same as before or collapsed */}
                        <div>
                            <label style={{ display: "block", fontSize: 13, fontWeight: 700, color: theme.colors.textSecondary, marginBottom: 8, textTransform: "uppercase" }}>Impression</label>
                            <textarea value={narrative.impression_text} readOnly style={{ width: "100%", minHeight: 80, padding: 12, borderRadius: 8, border: `1px solid ${theme.colors.border}`, backgroundColor: theme.colors.backgroundGray, fontFamily: "monospace", fontSize: 14 }} />
                        </div>
                        <div>
                            <label style={{ display: "block", fontSize: 13, fontWeight: 700, color: theme.colors.textSecondary, marginBottom: 8, textTransform: "uppercase" }}>Limitations</label>
                            <textarea value={narrative.limitations_text} readOnly style={{ width: "100%", minHeight: 60, padding: 12, borderRadius: 8, border: `1px solid ${theme.colors.border}`, backgroundColor: theme.colors.backgroundGray, fontFamily: "monospace", fontSize: 14 }} />
                        </div>
                        <div style={{ fontSize: 12, color: theme.colors.textTertiary, textAlign: "right" }}>Version: {narrative.version}</div>
                    </div>
                )}
            </div>

            {/* Publish History */}
            {publishHistory.length > 0 && (
                <div style={{ marginTop: 40 }}>
                    <h3 style={{ fontSize: 20, marginBottom: 16 }}>Publish History</h3>
                    <div style={{ backgroundColor: "white", borderRadius: theme.radius.lg, boxShadow: theme.shadows.sm, border: `1px solid ${theme.colors.border}`, overflow: "hidden" }}>
                        <table style={{ width: "100%", borderCollapse: "collapse" }}>
                            <thead>
                                <tr style={{ borderBottom: `1px solid ${theme.colors.border}`, backgroundColor: theme.colors.backgroundGray }}>
                                    <th style={{ textAlign: "left", padding: 12, fontSize: 12 }}>Version</th>
                                    <th style={{ textAlign: "left", padding: 12, fontSize: 12 }}>Published At</th>
                                    <th style={{ textAlign: "left", padding: 12, fontSize: 12 }}>By</th>
                                    <th style={{ textAlign: "left", padding: 12, fontSize: 12 }}>Notes</th>
                                    <th style={{ textAlign: "left", padding: 12, fontSize: 12 }}>Integrity</th>
                                    <th style={{ textAlign: "right", padding: 12, fontSize: 12 }}>Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                {publishHistory.map((snap) => (
                                    <tr key={snap.version} style={{ borderBottom: `1px solid ${theme.colors.borderLight}` }}>
                                        <td style={{ padding: 12 }}>v{snap.version}</td>
                                        <td style={{ padding: 12 }}>{new Date(snap.published_at).toLocaleString()}</td>
                                        <td style={{ padding: 12 }}>{snap.published_by}</td>
                                        <td style={{ padding: 12 }}>{snap.notes}</td>
                                        <td style={{ padding: 12 }}>
                                            {integrityStatus[snap.version] === true && (
                                                <span style={{ color: theme.colors.success, fontSize: 11 }}>● OK</span>
                                            )}
                                            {integrityStatus[snap.version] === false && (
                                                <span style={{ color: theme.colors.danger, fontSize: 11, fontWeight: 700, backgroundColor: "#fee2e2", padding: "2px 6px", borderRadius: 4 }}>! MISMATCH</span>
                                            )}
                                            {integrityStatus[snap.version] === undefined && (
                                                <span style={{ color: theme.colors.textTertiary, fontSize: 11 }}>Checking...</span>
                                            )}
                                        </td>
                                        <td style={{ padding: 12, textAlign: "right" }}>
                                            <Button variant="secondary" style={{ padding: "4px 8px", fontSize: 12 }} onClick={() => handleViewPublishedPdf(snap.version)}>
                                                View PDF
                                            </Button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* Submit Modal */}
            {showSubmitModal && (
                <div style={modalOverlayStyle}>
                    <div style={modalContentStyle}>
                        <h3 style={{ marginTop: 0 }}>Confirm Submission</h3>
                        <p style={{ color: theme.colors.textSecondary }}>Submit report? This locks the report.</p>
                        <div style={modalFooterStyle}>
                            <Button variant="secondary" onClick={() => setShowSubmitModal(false)}>Cancel</Button>
                            <Button variant="primary" onClick={handleSubmit} disabled={saving}>{saving ? "Submitting..." : "Submit"}</Button>
                        </div>
                    </div>
                </div>
            )}

            {/* Return Modal */}
            {showReturnModal && (
                <div style={modalOverlayStyle}>
                    <div style={modalContentStyle}>
                        <h3 style={{ marginTop: 0 }}>Return for Correction</h3>
                        <p style={{ color: theme.colors.textSecondary }}>Please specify the reason for return:</p>
                        <textarea
                            value={returnReason}
                            onChange={e => setReturnReason(e.target.value)}
                            style={{ width: "100%", minHeight: 80, padding: 10, borderRadius: 6, border: `1px solid ${theme.colors.border}`, marginBottom: 20 }}
                            placeholder="Correction notes..."
                        />
                        <div style={modalFooterStyle}>
                            <Button variant="secondary" onClick={() => setShowReturnModal(false)}>Cancel</Button>
                            <Button variant="primary" onClick={handleReturn} disabled={saving} style={{ backgroundColor: theme.colors.danger, borderColor: theme.colors.danger }}>Return</Button>
                        </div>
                    </div>
                </div>
            )}

            {/* Publish Modal */}
            {showPublishModal && (
                <div style={modalOverlayStyle}>
                    <div style={modalContentStyle}>
                        <h3 style={{ marginTop: 0 }}>Publish Report</h3>
                        <p style={{ color: theme.colors.textSecondary }}>
                            You are about to publish an immutable snapshot of this report.
                            Changes cannot be made to this version after publishing.
                        </p>
                        <div style={{ marginBottom: 16 }}>
                            <label style={{ display: "block", fontSize: 13, marginBottom: 4 }}>Notes (Optional)</label>
                            <input
                                type="text"
                                value={publishNotes}
                                onChange={e => setPublishNotes(e.target.value)}
                                style={{ width: "100%", padding: 8, borderRadius: 6, border: `1px solid ${theme.colors.border}` }}
                            />
                        </div>
                        <div style={{ marginBottom: 20 }}>
                            <label style={{ display: "block", fontSize: 13, marginBottom: 4 }}>Type "PUBLISH" to confirm</label>
                            <input
                                type="text"
                                value={publishConfirm}
                                onChange={e => setPublishConfirm(e.target.value)}
                                style={{ width: "100%", padding: 8, borderRadius: 6, border: `1px solid ${theme.colors.border}` }}
                                placeholder="PUBLISH"
                            />
                        </div>
                        <div style={modalFooterStyle}>
                            <Button variant="secondary" onClick={() => setShowPublishModal(false)}>Cancel</Button>
                            <Button
                                variant="primary"
                                onClick={handlePublish}
                                disabled={saving || publishConfirm !== "PUBLISH"}
                                style={{ backgroundColor: theme.colors.success, borderColor: theme.colors.success }}
                            >
                                {saving ? "Publishing..." : "Publish"}
                            </Button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

// Helper Styles
const modalOverlayStyle: React.CSSProperties = {
    position: "fixed", top: 0, left: 0, right: 0, bottom: 0, backgroundColor: "rgba(0,0,0,0.5)",
    display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000, backdropFilter: "blur(4px)"
};
const modalContentStyle: React.CSSProperties = {
    backgroundColor: "white", padding: 32, borderRadius: theme.radius.lg, maxWidth: 450, width: "90%", boxShadow: theme.shadows.lg
};
const modalFooterStyle: React.CSSProperties = {
    display: "flex", justifyContent: "flex-end", gap: 12, marginTop: 24
};

function renderParameter(
    param: ReportParameter,
    value: any,
    onChange: (id: string, val: any) => void,
    isReadOnly: boolean,
    error?: string
) {
    if (param.type === "heading") {
        return <h4 style={{ marginTop: 10, marginBottom: 5, fontSize: 15, fontWeight: 700, color: theme.colors.brandBlue, textTransform: "uppercase" }}>{param.name}</h4>;
    }
    if (param.type === "separator") {
        return <hr style={{ border: 0, borderTop: `1px solid ${theme.colors.border}`, margin: "10px 0" }} />;
    }

    const labelStyle = { display: "block", marginBottom: 6, fontWeight: 500, fontSize: 14, color: theme.colors.textPrimary };
    const inputBaseStyle: React.CSSProperties = {
        width: "100%", padding: "10px 14px", borderRadius: 8, border: `1px solid ${error ? theme.colors.danger : theme.colors.border}`,
        fontSize: 14, fontFamily: "inherit", backgroundColor: isReadOnly ? theme.colors.backgroundGray : "white",
        color: isReadOnly ? theme.colors.textSecondary : theme.colors.textPrimary, outline: "none", transition: "border-color 0.2s"
    };

    return (
        <div style={{ position: "relative" }}>
            <label style={labelStyle}>
                {param.name}
                {param.unit && <span style={{ color: theme.colors.textTertiary, marginLeft: 4 }}>({param.unit})</span>}
                {param.is_required && <span style={{ color: theme.colors.danger, marginLeft: 4 }}>*</span>}
            </label>
            {(param.type === "short_text" || param.type === "text") && <input type="text" value={value || ""} disabled={isReadOnly} onChange={e => onChange(param.parameter_id, e.target.value)} style={inputBaseStyle} />}
            {(param.type === "long_text" || param.type === "multiline") && <textarea value={value || ""} disabled={isReadOnly} onChange={e => onChange(param.parameter_id, e.target.value)} style={{ ...inputBaseStyle, minHeight: 100, resize: "vertical" }} />}
            {param.type === "number" && (
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                    <input type="number" value={value === null ? "" : value} disabled={isReadOnly} onChange={e => onChange(param.parameter_id, e.target.value === "" ? null : parseFloat(e.target.value))} style={{ ...inputBaseStyle, width: 200 }} />
                    {param.unit && <span style={{ fontSize: 14, color: theme.colors.textSecondary }}>{param.unit}</span>}
                </div>
            )}
            {param.type === "boolean" && (
                <div style={{ padding: "8px 0" }}>
                    <label style={{ display: "flex", alignItems: "center", gap: 10, cursor: isReadOnly ? "default" : "pointer" }}>
                        <input type="checkbox" checked={!!value} disabled={isReadOnly} onChange={e => onChange(param.parameter_id, e.target.checked)} style={{ width: 20, height: 20 }} />
                        <span style={{ fontSize: 14 }}>{param.name}</span>
                    </label>
                </div>
            )}
            {param.type === "dropdown" && (
                <select value={value || ""} disabled={isReadOnly} onChange={e => onChange(param.parameter_id, e.target.value)} style={inputBaseStyle}>
                    <option value="">Select...</option>
                    {param.options.map(opt => <option key={opt.id} value={opt.value}>{opt.label}</option>)}
                </select>
            )}
            {param.type === "checklist" && (
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 12, padding: "8px 0" }}>
                    {param.options.map(opt => {
                        const currentSelected = Array.isArray(value) ? value : [];
                        const isChecked = currentSelected.includes(opt.value);
                        return (
                            <label key={opt.id} style={{ display: "flex", alignItems: "center", gap: 10, cursor: isReadOnly ? "default" : "pointer", padding: "8px 12px", borderRadius: 6, backgroundColor: isChecked ? theme.colors.brandBlueSoft : "transparent", border: `1px solid ${isChecked ? theme.colors.brandBlue : "transparent"}` }}>
                                <input type="checkbox" checked={isChecked} disabled={isReadOnly} onChange={e => {
                                    if (e.target.checked) onChange(param.parameter_id, [...currentSelected, opt.value]);
                                    else onChange(param.parameter_id, currentSelected.filter(v => v !== opt.value));
                                }} style={{ width: 16, height: 16 }} />
                                <span style={{ fontSize: 13, color: isChecked ? theme.colors.brandBlue : theme.colors.textPrimary }}>{opt.label}</span>
                            </label>
                        );
                    })}
                </div>
            )}
            {error && <div style={{ color: theme.colors.danger, fontSize: 12, marginTop: 4, fontWeight: 500 }}>{error}</div>}
        </div>
    );
}
