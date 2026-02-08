import React, { useEffect, useState } from "react";
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
    ReportSchemaV2,
    fetchReportPdf,
    verifyReport,
    returnReport,
    publishReport,
    getPublishHistory,
    fetchPublishedPdf,
    checkIntegrity,
    NarrativeResponseV2
} from "../ui/reporting";
import SchemaFormV2 from "../components/reporting/SchemaFormV2";
import SmartSchemaFormV2 from "../components/reporting/SmartSchemaFormV2";
import { getUiSpec } from "../reporting_ui/registry";
import { specLint } from "../reporting_ui/specLint";
import Button from "../ui/components/Button";
import ErrorAlert from "../ui/components/ErrorAlert";
import SuccessAlert from "../ui/components/SuccessAlert";
import { resolveReportingErrorMessage } from "../utils/reporting/errors";

export default function ReportingPage() {
    const { service_visit_item_id: id } = useParams<{ service_visit_item_id: string }>();
    const { token, user } = useAuth();
    const navigate = useNavigate();

    const [schema, setSchema] = useState<ReportSchemaV2 | null>(null);
    const [valuesJson, setValuesJson] = useState<Record<string, any>>({});
    const [status, setStatus] = useState<"draft" | "submitted" | "verified">("draft");
    const [isPublished, setIsPublished] = useState(false);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    const [lastSavedAt, setLastSavedAt] = useState<string | null>(null);
    const [lastPublishedAt, setLastPublishedAt] = useState<string | null>(null);
    const [integrityStatus, setIntegrityStatus] = useState<Record<number, boolean>>({});

    const [showSubmitModal, setShowSubmitModal] = useState(false);

    const [showReturnModal, setShowReturnModal] = useState(false);
    const [showPublishModal, setShowPublishModal] = useState(false);
    const [returnReason, setReturnReason] = useState("");
    const [publishNotes, setPublishNotes] = useState("");
    const [publishConfirm, setPublishConfirm] = useState("");
    const [publishHistory, setPublishHistory] = useState<any[]>([]);

    const [narrative, setNarrative] = useState<NarrativeResponseV2 | null>(null);
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

            if (schemaData.schema_version !== "v2") {
                throw new Error("Only V2 templates are supported.");
            }

            setSchema(schemaData);
            setStatus(valuesResponse.status);
            const published = !!valuesResponse.is_published;
            setIsPublished(published);
            setNarrative(narrativeResponse);
            setLastSavedAt(valuesResponse.last_saved_at || null);
            setLastPublishedAt(valuesResponse.last_published_at || null);
            setValuesJson(valuesResponse.values_json || {});

            if (published) {
                const history = await getPublishHistory(id, token);
                setPublishHistory(history);
                history.forEach((snap: any) => {
                    checkIntegrity(id, snap.version, token)
                        .then(res => setIntegrityStatus(prev => ({ ...prev, [snap.version]: !!res.content_hash })))
                        .catch(console.error);
                });
            }
        } catch (e: any) {
            setError(resolveReportingErrorMessage(e));
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if ((import.meta as any).env.DEV && schema) {
            const uiSpec = getUiSpec(schema.code || "");
            if (uiSpec) {
                specLint(schema.code || "", schema.json_schema, uiSpec);
            }
        }
    }, [schema]);

    const preparePayload = () => ({ schema_version: "v2" as const, values_json: valuesJson });

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

            await saveReport(id, preparePayload(), token);
            await submitReport(id, token);
            setStatus("submitted");
            setShowSubmitModal(false);
        } catch (e: any) {
            setError(e.message || "Failed to submit report");
        } finally {
            setSaving(false);
        }
    };

    const handleGenerateNarrative = async () => {
        if (!id) return;
        try {
            setGeneratingNarrative(true);
            setError(null);
            const response = await generateNarrative(id, token);
            setNarrative(response);
        } catch (e: any) {
            setError(e.message || "Failed to generate narrative");
        } finally {
            setGeneratingNarrative(false);
        }
    };

    const handleVerify = async () => {
        if (!id) return;
        try {
            await verifyReport(id, "", token);
            setStatus("verified");
        } catch (e: any) {
            setError(e.message || "Failed to verify report");
        }
    };

    const handleReturn = async () => {
        if (!id) return;
        try {
            await returnReport(id, returnReason, token);
            setStatus("draft");
            setShowReturnModal(false);
        } catch (e: any) {
            setError(e.message || "Failed to return report");
        }
    };

    const handlePublish = async () => {
        if (!id) return;
        try {
            await publishReport(id, publishNotes, token);
            setShowPublishModal(false);
            await loadData();
        } catch (e: any) {
            setError(e.message || "Failed to publish report");
        }
    };

    const handleFetchPdf = async () => {
        if (!id) return;
        try {
            const blob = await fetchReportPdf(id, token);
            const url = URL.createObjectURL(blob);
            window.open(url, "_blank");
        } catch (e: any) {
            setError(e.message || "Failed to fetch PDF");
        }
    };

    const handleOpenPublishedPdf = async (version: number) => {
        if (!id) return;
        try {
            const blob = await fetchPublishedPdf(id, version, token);
            const url = URL.createObjectURL(blob);
            window.open(url, "_blank");
        } catch (e: any) {
            setError(e.message || "Failed to fetch published PDF");
        }
    };

    if (loading) {
        return <div style={{ padding: 20 }}>Loading...</div>;
    }

    if (!schema) {
        return <div style={{ padding: 20 }}>No template found for this service.</div>;
    }

    return (
        <div data-testid="reporting-v2" style={{ padding: 20, display: "flex", flexDirection: "column", gap: 16 }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div>
                    <h2 data-testid="report-template-name" style={{ margin: 0 }}>{schema.name}</h2>
                    <div data-testid="report-template-code" style={{ fontSize: 12, color: theme.colors.textTertiary }}>{schema.code}</div>
                    <div data-testid="report-status" style={{ fontSize: 12, color: theme.colors.textTertiary }}>
                        Status: {status}{isPublished ? " (published)" : ""}
                    </div>
                </div>
                <Button variant="secondary" onClick={() => navigate("/reporting/worklist")}>Worklist</Button>
            </div>

            {error && (
                <div data-testid="report-error">
                    <ErrorAlert message={error} />
                </div>
            )}
            {success && (
                <div data-testid="report-success">
                    <SuccessAlert message={success} />
                </div>
            )}

            <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                <Button data-testid="report-save" onClick={handleSaveDraft} disabled={saving || status !== "draft"}>Save Draft</Button>
                <Button data-testid="report-submit" variant="secondary" onClick={() => setShowSubmitModal(true)} disabled={status !== "draft"}>Submit</Button>
                <Button variant="secondary" onClick={handleGenerateNarrative} disabled={generatingNarrative}>Generate Narrative</Button>
                <Button data-testid="report-preview" variant="secondary" onClick={handleFetchPdf}>Preview PDF</Button>
                {(user?.is_superuser || user?.groups?.includes("reporting_verifier")) && (
                    <>
                        <Button variant="secondary" onClick={() => setShowReturnModal(true)} disabled={status === "draft"}>Return</Button>
                        <Button data-testid="report-verify" variant="secondary" onClick={handleVerify} disabled={status !== "submitted"}>Verify</Button>
                        <Button data-testid="report-publish" variant="secondary" onClick={() => setShowPublishModal(true)} disabled={status !== "verified"}>Publish</Button>
                    </>
                )}
            </div>

            {(lastSavedAt || lastPublishedAt) && (
                <div style={{ fontSize: 12, color: theme.colors.textTertiary }}>
                    {lastSavedAt && <span>Last saved: {new Date(lastSavedAt).toLocaleString()} </span>}
                    {lastPublishedAt && <span>Last published: {new Date(lastPublishedAt).toLocaleString()}</span>}
                </div>
            )}

            <div style={{ border: `1px solid ${theme.colors.border}`, borderRadius: 8, padding: 12 }}>
                <SmartSchemaFormV2
                    jsonSchema={schema.json_schema}
                    uiSchema={schema.ui_schema}
                    values={valuesJson}
                    onChange={(data: any) => setValuesJson(data)}
                    isReadOnly={status !== "draft"}
                    uiSpec={getUiSpec(schema.code || "")}
                />
            </div>

            {narrative && (
                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                    <div style={{ fontWeight: 600 }}>Narrative JSON</div>
                    <textarea
                        value={JSON.stringify(narrative.narrative_json, null, 2)}
                        readOnly
                        style={{ width: "100%", minHeight: 180, padding: 12, borderRadius: 8, border: `1px solid ${theme.colors.border}`, backgroundColor: theme.colors.backgroundGray, fontFamily: "monospace", fontSize: 13, lineHeight: 1.4, resize: "vertical" }}
                    />
                </div>
            )}

            {isPublished && publishHistory.length > 0 && (
                <div data-testid="publish-history" style={{ marginTop: 20 }}>
                    <h3>Publish History</h3>
                    <ul>
                        {publishHistory.map((snap: any) => (
                            <li key={snap.version} style={{ marginBottom: 8 }}>
                                <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                                    <span>Version {snap.version}</span>
                                    <span>{snap.published_at ? new Date(snap.published_at).toLocaleString() : ""}</span>
                                    <span>{integrityStatus[snap.version] ? "Integrity OK" : "Integrity pending"}</span>
                                    <Button variant="secondary" onClick={() => handleOpenPublishedPdf(snap.version)}>Open PDF</Button>
                                </div>
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {showSubmitModal && (
                <div data-testid="submit-modal" style={{ background: "rgba(0,0,0,0.4)", position: "fixed", inset: 0, display: "flex", justifyContent: "center", alignItems: "center" }}>
                    <div style={{ background: "white", padding: 20, borderRadius: 8, width: 360 }}>
                        <h3>Submit report?</h3>
                        <p>Once submitted, the report cannot be edited until returned.</p>
                        <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
                            <Button variant="secondary" onClick={() => setShowSubmitModal(false)}>Cancel</Button>
                            <Button data-testid="submit-confirm" onClick={handleSubmit} disabled={saving}>Submit</Button>
                        </div>
                    </div>
                </div>
            )}

            {showReturnModal && (
                <div style={{ background: "rgba(0,0,0,0.4)", position: "fixed", inset: 0, display: "flex", justifyContent: "center", alignItems: "center" }}>
                    <div style={{ background: "white", padding: 20, borderRadius: 8, width: 360 }}>
                        <h3>Return report</h3>
                        <textarea
                            placeholder="Reason"
                            value={returnReason}
                            onChange={e => setReturnReason(e.target.value)}
                            style={{ width: "100%", minHeight: 80, marginBottom: 12 }}
                        />
                        <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
                            <Button variant="secondary" onClick={() => setShowReturnModal(false)}>Cancel</Button>
                            <Button onClick={handleReturn} disabled={!returnReason}>Return</Button>
                        </div>
                    </div>
                </div>
            )}

            {showPublishModal && (
                <div data-testid="publish-modal" style={{ background: "rgba(0,0,0,0.4)", position: "fixed", inset: 0, display: "flex", justifyContent: "center", alignItems: "center" }}>
                    <div style={{ background: "white", padding: 20, borderRadius: 8, width: 360 }}>
                        <h3>Publish report</h3>
                        <textarea
                            data-testid="publish-notes"
                            placeholder="Notes"
                            value={publishNotes}
                            onChange={e => setPublishNotes(e.target.value)}
                            style={{ width: "100%", minHeight: 80, marginBottom: 12 }}
                        />
                        <input
                            data-testid="publish-confirm"
                            placeholder="Type PUBLISH to confirm"
                            value={publishConfirm}
                            onChange={e => setPublishConfirm(e.target.value)}
                            style={{ width: "100%", marginBottom: 12 }}
                        />
                        <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
                            <Button variant="secondary" onClick={() => setShowPublishModal(false)}>Cancel</Button>
                            <Button data-testid="publish-confirm-button" onClick={handlePublish} disabled={publishConfirm !== "PUBLISH"}>Publish</Button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
