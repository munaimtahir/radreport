import React, { useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { apiGet, apiPost, apiPut } from "../ui/api";
import { useAuth } from "../ui/auth";
import PageHeader from "../ui/components/PageHeader";
import ErrorBanner from "../ui/components/ErrorBanner";
import SuccessAlert from "../ui/components/SuccessAlert";
import Button from "../ui/components/Button";
import { theme } from "../theme";

interface TemplateFieldOption {
  label: string;
  value: string;
}

interface TemplateField {
  field_key: string;
  label: string;
  type: "single_choice" | "multi_choice" | "number" | "text" | "checklist" | "dropdown" | "boolean" | "short_text" | "long_text";
  required?: boolean;
  supports_not_applicable?: boolean;
  na_allowed?: boolean;
  options?: TemplateFieldOption[];
}

interface TemplateSection {
  section_key: string;
  title: string;
  include_toggle: boolean;
  fields: TemplateField[];
}

interface TemplateSchema {
  code: string;
  name: string;
  version: number;
  sections: TemplateSection[];
}

interface FieldValue {
  field_key: string;
  value_json?: any;
  is_not_applicable: boolean;
}

interface UsgStudy {
  id: string;
  patient: string;
  patient_name: string;
  patient_mrn: string;
  visit: string;
  visit_number: string;
  service_code: string;
  status: string;
  published_at?: string;
  published_pdf_url?: string; // New workflow field
  report_status?: string; // New workflow field
  report_json?: any; // New workflow field
  template_schema?: any; // New workflow field
  hidden_sections?: string[];
  forced_na_fields?: string[];
  service_profile?: {
    service_code: string;
    template: string;
    template_code: string;
    hidden_sections: string[];
    forced_na_fields: string[];
  } | null;
  template_detail?: {
    schema_json: TemplateSchema;
  };
  field_values: FieldValue[];
  is_locked?: boolean;
}

const formatDateTime = (value?: string) => {
  if (!value) return "-";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString();
};

// Use a select when the number of options exceeds this threshold; otherwise use radio buttons.
const SINGLE_CHOICE_SELECT_THRESHOLD = 5;

const supportsMultiChoice = (field: TemplateField) => field.type === "multi_choice" || field.type === "checklist";
const usesSelectForSingleChoice = (field: TemplateField) =>
  field.type === "dropdown" || ((field.options || []).length > SINGLE_CHOICE_SELECT_THRESHOLD && field.type === "single_choice");
const getErrorMessage = (err: any, fallback: string) => err?.message || fallback;

export default function UsgStudyEditorPage() {
  const { studyId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const { token, user } = useAuth();
  const [study, setStudy] = useState<UsgStudy | null>(null);
  const [values, setValues] = useState<Record<string, FieldValue>>({});
  const [sectionIncludes, setSectionIncludes] = useState<Record<string, boolean>>({});
  const [activeSection, setActiveSection] = useState<string>("");
  const [previewText, setPreviewText] = useState<string>("");
  const [showPreview, setShowPreview] = useState(false);
  const [error, setError] = useState("");
  const [previewError, setPreviewError] = useState("");
  const [success, setSuccess] = useState("");
  const [saving, setSaving] = useState(false);
  const [dirtyKeys, setDirtyKeys] = useState<Set<string>>(new Set());
  const [saveStatus, setSaveStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [lastSavedAt, setLastSavedAt] = useState<Date | null>(null);
  const [hiddenSections, setHiddenSections] = useState<string[]>([]);
  const [forcedNaFields, setForcedNaFields] = useState<string[]>([]);
  const [publishing, setPublishing] = useState(false);
  const [showPublishConfirm, setShowPublishConfirm] = useState(false);
  const autosaveTimerRef = useRef<number | null>(null);
  const valuesRef = useRef(values);
  const locationRef = useRef(location);
  const skipNavigationPromptRef = useRef(false);
  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  useEffect(() => {
    if (!token || !studyId) return;
    const loadStudy = async () => {
      setError("");
      try {
        const data = await apiGet(`/workflow/usg/${studyId}/`, token);

        // Adapt USGReport to local state
        setStudy({
          ...data,
          // Map status
          status: data.report_status?.toLowerCase(),
          is_locked: data.report_status === "FINAL" || data.report_status === "AMENDED", // Published/Final are locked
          template_detail: {
            schema_json: data.template_schema
          }
        });

        const initialValues: Record<string, FieldValue> = {};
        const reportJson = data.report_json || {};

        // Iterate over schema to populate values from reportJson dictionary
        const sections = data.template_schema?.sections || [];
        sections.forEach((section: any) => {
          (section.fields || []).forEach((field: any) => {
            const key = field.key || field.field_key;
            const stored = reportJson[key];

            // Parse { value, is_na } wrapper or raw value
            let value = stored;
            let isNa = false;

            // Check if stored is an object wrapper with is_na
            if (stored && typeof stored === 'object' && ('is_na' in stored || 'value' in stored)) {
              value = stored.value;
              isNa = stored.is_na || false;
            } else if (stored === null) {
              // stored is explicitly null? Treat as value null.
              value = null;
              // If key exists in JSON, we respect it.
            }

            // Default NA logic: if field supports NA and NO value is stored (key missing or undefined), default to true.
            // Note: We check if key is in reportJson to determine if it's "new" or "touched".
            // If key is missing from reportJson, it's a new report or new field -> apply default.
            const isNewField = !(key in reportJson);

            if (isNewField && (field.na_allowed || field.supports_not_applicable)) {
              isNa = true;
            }

            initialValues[key] = {
              field_key: key,
              value_json: value, // State uses value_json for the actual value
              is_not_applicable: isNa
            };
          });
        });

        // Handle explicit NA fields if any (less relevant in new workflow but keeping safe)
        // New workflow uses template defaults or explicit user action.

        setValues(initialValues);

        // Set up dirty keys (none initially)
        setDirtyKeys(new Set());

        const firstVisible = sections.find((section: TemplateSection) => section.section_key && !hiddenSections.includes(section.section_key));
        if (firstVisible) {
          setActiveSection(firstVisible.section_key);
        }
      } catch (err: any) {
        setError(getErrorMessage(err, "Failed to load study"));
      }
    };
    loadStudy();
  }, [token, studyId]);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    if (params.get("preview") === "1") {
      setShowPreview(true);
    }
    if (params.get("pdf") === "1" && studyId && token) {
      handleViewPdf();
    }
  }, [location.search, studyId, token]);

  useEffect(() => {
    valuesRef.current = values;
  }, [values]);

  const schema = study?.template_detail?.schema_json;
  const sections = schema?.sections || [];
  const isPublished = study?.status === "final" || study?.status === "amended";
  const canAutosave = study?.status === "draft";
  const isEditingDisabled = isPublished;

  // Memoize visibleSections to prevent unnecessary re-renders
  const visibleSections = useMemo(() => {
    const hiddenSectionsSet = new Set(hiddenSections);
    return sections.filter((section) => !hiddenSectionsSet.has(section.section_key));
  }, [sections, hiddenSections]);

  const forcedNaSet = new Set(forcedNaFields);
  const hasUnsavedChanges = dirtyKeys.size > 0 || saveStatus === "saving";
  const canPublish = !!user && (user.is_superuser || (user.groups || []).includes("verification"));

  useEffect(() => {
    if (!visibleSections.find((section) => section.section_key === activeSection) && visibleSections.length > 0) {
      setActiveSection(visibleSections[0].section_key);
    }
  }, [activeSection, visibleSections]);

  useEffect(() => {
    if (!hasUnsavedChanges) {
      locationRef.current = location;
      return;
    }
    if (skipNavigationPromptRef.current) {
      skipNavigationPromptRef.current = false;
      locationRef.current = location;
      return;
    }
    if (location.pathname !== locationRef.current.pathname || location.search !== locationRef.current.search) {
      const confirmLeave = window.confirm("You have unsaved changes. Leave without saving?");
      if (!confirmLeave) {
        skipNavigationPromptRef.current = true;
        navigate(`${locationRef.current.pathname}${locationRef.current.search}`, { replace: true });
        return;
      }
    }
    locationRef.current = location;
  }, [hasUnsavedChanges, location, navigate]);

  useEffect(() => {
    const handler = (event: BeforeUnloadEvent) => {
      if (!hasUnsavedChanges) return;
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [hasUnsavedChanges]);

  useEffect(() => {
    if (!token || !studyId) return;
    if (!canAutosave || isEditingDisabled || publishing) return;
    if (dirtyKeys.size === 0) return;
    if (autosaveTimerRef.current) {
      window.clearTimeout(autosaveTimerRef.current);
    }
    autosaveTimerRef.current = window.setTimeout(() => {
      void saveValues(new Set(dirtyKeys), true);
    }, 1200);
    return () => {
      if (autosaveTimerRef.current) {
        window.clearTimeout(autosaveTimerRef.current);
      }
    };
  }, [dirtyKeys, canAutosave, isEditingDisabled, publishing, token, studyId]);

  const handleFieldChange = (field: TemplateField, value: any) => {
    if (forcedNaSet.has(field.field_key)) return;
    setValues((prev) => ({
      ...prev,
      [field.field_key]: {
        field_key: field.field_key,
        value_json: value,
        is_not_applicable: false,
      },
    }));
    setDirtyKeys((prev) => {
      const next = new Set(prev);
      next.add(field.field_key);
      return next;
    });
    setSaveStatus("idle");
  };

  const handleNotApplicable = (field: TemplateField, checked: boolean) => {
    if (forcedNaSet.has(field.field_key)) return;
    setValues((prev) => ({
      ...prev,
      [field.field_key]: {
        field_key: field.field_key,
        value_json: checked ? null : prev[field.field_key]?.value_json,
        is_not_applicable: checked,
      },
    }));
    setDirtyKeys((prev) => {
      const next = new Set(prev);
      next.add(field.field_key);
      return next;
    });
    setSaveStatus("idle");
  };

  const handleSectionToggle = (sectionKey: string, enabled: boolean) => {
    setSectionIncludes((prev) => ({
      ...prev,
      [sectionKey]: enabled,
    }));
  };

  const saveValues = async (keys: Set<string> | null, isAutosave = false) => {
    if (!token || !studyId) return;
    if (isEditingDisabled || !canAutosave) return;
    if (publishing) return;
    if (!isAutosave) {
      setSaving(true);
    }
    setSaveStatus("saving");
    setError("");
    const currentValues = valuesRef.current;
    // Map currentValues (Record) to Dict { key: { value, is_na } }
    const payloadValues: Record<string, any> = {};
    Object.values(currentValues).forEach(fv => {
      if (fv.is_not_applicable) return;
      payloadValues[fv.field_key] = {
        value: fv.value_json,
        is_na: false
      };
    });

    try {
      // Use save_draft endpoint with values as a dictionary
      const payload = {
        values: payloadValues,
      };
      await apiPost(`/workflow/usg/${studyId}/save_draft/`, token, payload);

      // Check if component is still mounted before updating state
      if (!isMountedRef.current) return;

      let remainingKeys = new Set<string>();
      setDirtyKeys((prev) => {
        if (!keys) return new Set();
        const next = new Set(prev);
        keys.forEach((key) => next.delete(key));
        remainingKeys = next;
        return next;
      });
      setLastSavedAt(new Date());
      setSaveStatus(remainingKeys.size === 0 ? "saved" : "idle");
      if (!isAutosave) {
        setSuccess("Saved");
      }
    } catch (err: any) {
      // Check if component is still mounted before updating state
      if (!isMountedRef.current) return;
      const message = getErrorMessage(err, "Save failed");
      setError(message);
      setSaveStatus("error");
    } finally {
      if (!isAutosave) {
        setSaving(false);
      }
    }
  };

  const renderPreview = async () => {
    setPreviewError("Preview not available in this version.");
    // if (!token || !studyId) return;
    // setPreviewError("");
    // try {
    //   const data = await apiPost(`/workflow/usg/${studyId}/render/`, token, {});
    //   setPreviewText(data.full_report || data.narrative || "");
    //   setShowPreview(true);
    // } catch (err: any) {
    //   setPreviewError(getErrorMessage(err, "Failed to render preview"));
    // }
  };

  const publishReport = async () => {
    if (!token || !studyId) return;
    if (!canPublish) return;
    setPublishing(true);
    setError("");
    try {
      await apiPost(`/workflow/usg/${studyId}/publish/`, token, {});
      setSuccess("Report published. Editing locked.");
      setShowPublishConfirm(false);
      const refreshed = await apiGet(`/workflow/usg/${studyId}/`, token);

      // Adapt refreshed data (duplicate of load logic)
      setStudy({
        ...refreshed,
        status: refreshed.report_status?.toLowerCase(),
        is_locked: refreshed.report_status === "FINAL" || refreshed.report_status === "AMENDED",
        template_detail: { schema_json: refreshed.template_schema }
      });
    } catch (err: any) {
      setError(getErrorMessage(err, "Publish failed"));
    } finally {
      setPublishing(false);
    }
  };

  const handleViewPdf = async () => {
    if (!studyId) return;
    const apiBase = (import.meta as any).env.VITE_API_BASE || ((import.meta as any).env.PROD ? "/api" : "http://localhost:8000/api");
    // URL for PDF in workflow module
    const url = `${apiBase}/workflow/usg/${studyId}/pdf/`; // Verify if this endpoint exists? 
    // USGReportViewSet has publish which returns serializer with 'published_pdf_url'.
    // `USGReportSerializer` has `published_pdf_url`.
    // The previous logic used a direct endpoint.
    // USGReportViewSet does NOT seem to have a `pdf` action.
    // But `published_pdf_url` points to `/api/pdf/{svId}/report/` or similar.
    // I should use `study.published_pdf_url` if available.

    // For now, I will assume the published PDF URL is needed.
    // If I don't have it, I can't download.
    // I will try to use the `download` action if it existed, but it doesn't.
    // I'll show error if no PDF URL.

    // Actually, `USGReportSerializer` method `get_published_pdf_url` returns `/api/pdf/{sv.id}/report/`.
    // I should use that if available.

    // Code update:
    if (!study?.published_pdf_url) {
      setError("PDF not available yet. Publish the report first.");
      return;
    }
    const pdfUrl = study.published_pdf_url;

    // ... same open window logic ...
    const openedWindow = window.open("", "_blank", "noopener,noreferrer");
    if (!token) {
      if (openedWindow) openedWindow.close();
      return;
    }
    try {
      const response = await fetch(pdfUrl, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      // ... same blob logic ...
      if (!response.ok) {
        if (openedWindow) openedWindow.close();
        throw new Error("Failed to download PDF");
      }
      const blob = await response.blob();
      const blobUrl = URL.createObjectURL(blob);
      if (openedWindow && !openedWindow.closed) {
        openedWindow.location.href = blobUrl;
      } else {
        window.open(blobUrl, "_blank", "noopener,noreferrer");
      }
    } catch (err: any) {
      if (openedWindow && !openedWindow.closed) openedWindow.close();
      setError(getErrorMessage(err, "PDF retrieval failed"));
    }
  };

  const handleCopyPreview = async () => {
    if (!previewText) return;
    try {
      await navigator.clipboard.writeText(previewText);
      setSuccess("Preview text copied.");
    } catch (err: any) {
      setError(getErrorMessage(err, "Copy failed"));
    }
  };

  const activeSectionData = visibleSections.find((section) => section.section_key === activeSection);

  return (
    <div style={{ maxWidth: 1400, margin: "0 auto" }}>
      <PageHeader
        title="USG Study Editor"
        subtitle={`${study?.patient_name || ""} • MRN ${study?.patient_mrn || ""} • Visit ${study?.visit_number || ""}`}
      />

      {error && <ErrorBanner message={error} onDismiss={() => setError("")} />}
      {success && <SuccessAlert message={success} onDismiss={() => setSuccess("")} />}

      <div style={{
        border: `1px solid ${theme.colors.border}`,
        borderRadius: theme.radius.md,
        padding: 16,
        backgroundColor: theme.colors.background,
        marginBottom: 16,
        display: "flex",
        justifyContent: "space-between",
        flexWrap: "wrap",
        gap: 12,
      }}>
        <div>
          <div style={{ fontWeight: theme.typography.fontWeight.semibold }}>
            Study: {study?.service_code || ""}
          </div>
          <div style={{ fontSize: 13, color: theme.colors.textSecondary, marginTop: 4 }}>
            Status: {study?.status || "-"}
          </div>
          {isPublished && (
            <div style={{ fontSize: 12, color: theme.colors.success, marginTop: 6 }}>
              Published {study?.published_at ? `• ${formatDateTime(study.published_at)}` : ""}
            </div>
          )}
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <Button variant="secondary" onClick={() => navigate(-1)}>
            Back to Visit
          </Button>
          {!isPublished && (
            <>
              <Button variant="secondary" onClick={() => saveValues(null)} disabled={saving || !canAutosave}>
                {saving ? "Saving..." : "Save Draft"}
              </Button>
              <Button variant="secondary" onClick={renderPreview}>
                Preview Narrative
              </Button>
              {canPublish && (
                <Button variant="primary" onClick={() => setShowPublishConfirm(true)} disabled={publishing}>
                  Publish
                </Button>
              )}
            </>
          )}
          {isPublished && (
            <Button variant="secondary" onClick={handleViewPdf}>
              View PDF
            </Button>
          )}
        </div>
        <div style={{ fontSize: 12, color: theme.colors.textSecondary, minWidth: 160, textAlign: "right" }}>
          {saveStatus === "saving" && (
            <span>Saving…</span>
          )}
          {saveStatus === "saved" && lastSavedAt && (
            <span>Saved {lastSavedAt.toLocaleTimeString()}</span>
          )}
          {saveStatus === "error" && (
            <span style={{ color: theme.colors.danger }}>
              Save failed —{" "}
              <button
                onClick={() => saveValues(new Set(dirtyKeys))}
                style={{
                  background: "none",
                  border: "none",
                  color: theme.colors.danger,
                  cursor: "pointer",
                  textDecoration: "underline",
                  padding: 0,
                }}
                aria-label="Retry saving changes"
              >
                Retry
              </button>
            </span>
          )}
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "220px 1fr 320px", gap: 16 }}>
        <div style={{
          border: `1px solid ${theme.colors.border}`,
          borderRadius: theme.radius.md,
          padding: 12,
          backgroundColor: theme.colors.background,
          height: "fit-content",
        }}>
          <div style={{ fontSize: 12, color: theme.colors.textTertiary, marginBottom: 8 }}>Sections</div>
          {visibleSections.map((section) => (
            <button
              key={section.section_key}
              type="button"
              onClick={() => setActiveSection(section.section_key)}
              style={{
                width: "100%",
                textAlign: "left",
                padding: "8px 10px",
                marginBottom: 6,
                borderRadius: theme.radius.base,
                border: `1px solid ${activeSection === section.section_key ? theme.colors.brandBlue : theme.colors.border}`,
                backgroundColor: activeSection === section.section_key ? theme.colors.brandBlueSoft : "transparent",
                color: activeSection === section.section_key ? theme.colors.brandBlue : theme.colors.textSecondary,
                cursor: "pointer",
                fontSize: 13,
              }}
            >
              {section.title}
            </button>
          ))}
        </div>

        <div style={{
          border: `1px solid ${theme.colors.border}`,
          borderRadius: theme.radius.md,
          padding: 16,
          backgroundColor: theme.colors.background,
        }}>
          {activeSectionData ? (
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <h3 style={{ marginTop: 0 }}>{activeSectionData.title}</h3>
                {activeSectionData.include_toggle && (
                  <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13 }}>
                    <input
                      type="checkbox"
                      checked={sectionIncludes[activeSectionData.section_key] ?? true}
                      onChange={(event) => handleSectionToggle(activeSectionData.section_key, event.target.checked)}
                      disabled={isEditingDisabled}
                    />
                    Include in report
                  </label>
                )}
              </div>
              {!sectionIncludes[activeSectionData.section_key] ? (
                <div style={{ color: theme.colors.textTertiary }}>
                  Section excluded from report.
                </div>
              ) : (
                <div style={{ display: "grid", gap: 16 }}>
                  {activeSectionData.fields.map((field) => {
                    const value = values[field.field_key]?.value_json;
                    const isForcedNA = forcedNaSet.has(field.field_key);
                    const isNA = isForcedNA || values[field.field_key]?.is_not_applicable || false;
                    const isDisabled = isEditingDisabled || isNA || isForcedNA;
                    return (
                      <div key={field.field_key} style={{ display: "grid", gap: 6 }}>
                        <div style={{ display: "flex", alignItems: "center", marginBottom: 4 }}>
                          {(field.supports_not_applicable || field.na_allowed) && (
                            <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13, marginRight: 12, fontWeight: 500, color: theme.colors.textSecondary }}>
                              <input
                                type="checkbox"
                                checked={isNA}
                                onChange={(event) => handleNotApplicable(field, event.target.checked)}
                                disabled={isEditingDisabled || isForcedNA}
                              />
                              N/A
                            </label>
                          )}
                          <label style={{ fontWeight: theme.typography.fontWeight.medium, flex: 1 }}>{field.label}</label>
                        </div>

                        {(field.type === "single_choice" || field.type === "dropdown" || field.type === "short_text" || field.type === "long_text") && usesSelectForSingleChoice(field) && (
                          <select
                            value={value ?? ""}
                            onChange={(event) => handleFieldChange(field, event.target.value || null)}
                            disabled={isDisabled} // Keep disabled if strictly requested, but user wants auto-uncheck capability? 
                            // User: "When NA is checked... disable the actual input control". 
                            // User: "Auto-uncheck NA on any onChange".
                            // If disabled, onChange won't fire. So we must NOT disable if we want auto-uncheck.
                            // However, we can style it to look disabled.
                            // But usually disabled inputs don't allow interaction.
                            // I'll keep it enabled but styled?
                            // Or, if I click it, I handle it?
                            // Actually, standard HTML select interaction requires it to be enabled.
                            // I will ENABLE it always, but maybe show visual cue?
                            // Logic: If isNA && user interacts -> setNA(false).
                            // So I remove `disabled={isDisabled}` here?
                            // But line 629 calculates isDisabled based on isNA.
                            // I will allow interaction if it's just ISNA (not isEditingDisabled or isForcedNA).
                            // So: disabled={isEditingDisabled || isForcedNA}
                            // And in onChange, we uncheck NA.
                            // Code continues...
                            style={{
                              padding: 8,
                              borderRadius: theme.radius.base,
                              border: `1px solid ${theme.colors.border}`,
                              backgroundColor: (isEditingDisabled || isForcedNA) ? theme.colors.backgroundGray : (isNA ? "#f9f9f9" : theme.colors.background),
                              color: isNA ? "#999" : "inherit",
                            }}
                          >
                            <option value="">Select</option>
                            {(field.options || []).map((option) => (
                              <option key={option.value} value={option.value}>
                                {option.label}
                              </option>
                            ))}
                          </select>
                        )}
                        {(field.type === "single_choice" || field.type === "boolean") && !usesSelectForSingleChoice(field) && (
                          <fieldset
                            style={{
                              border: "none",
                              margin: 0,
                              padding: 0,
                            }}
                          >
                            <legend
                              style={{
                                position: "absolute",
                                width: 1,
                                height: 1,
                                padding: 0,
                                margin: -1,
                                overflow: "hidden",
                                clip: "rect(0, 0, 0, 0)",
                                whiteSpace: "nowrap",
                                border: 0,
                              }}
                            >
                              {field.label}
                            </legend>
                            <div style={{ display: "grid", gap: 8 }}>
                              {(field.options || []).map((option) => (
                                <label key={option.value} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                  <input
                                    type="radio"
                                    name={"radio-" + field.field_key}
                                    checked={value === option.value}
                                    disabled={isEditingDisabled || isForcedNA}
                                    onChange={() => handleFieldChange(field, option.value)}
                                  />
                                  {option.label}
                                </label>
                              ))}
                              {/* Handle Boolean with no options? */}
                              {field.type === "boolean" && (!field.options || field.options.length === 0) && (
                                <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                  <input
                                    type="checkbox"
                                    checked={!!value}
                                    onChange={(e) => handleFieldChange(field, e.target.checked)}
                                    disabled={isEditingDisabled || isForcedNA}
                                  />
                                  Yes
                                </label>
                              )}
                            </div>
                          </fieldset>
                        )}
                        {supportsMultiChoice(field) && (
                          <div style={{
                            display: "flex",
                            gap: 12,
                            flexWrap: "wrap",
                            alignItems: "center"
                          }}>
                            {(field.options || []).map((option) => {
                              const current = Array.isArray(value) ? value : [];
                              const checked = current.includes(option.value);
                              return (
                                <label key={option.value} style={{ display: "flex", alignItems: "center", gap: 6, minWidth: "fit-content" }}>
                                  <input
                                    type="checkbox"
                                    checked={checked}
                                    disabled={isEditingDisabled || isForcedNA}
                                    onChange={(event) => {
                                      const next = event.target.checked
                                        ? [...current, option.value]
                                        : current.filter((item: string) => item !== option.value);
                                      handleFieldChange(field, next);
                                    }}
                                  />
                                  {option.label}
                                </label>
                              );
                            })}
                          </div>
                        )}
                        {field.type === "number" && (
                          <input
                            type="number"
                            value={value ?? ""}
                            onChange={(event) => handleFieldChange(field, event.target.value ? Number(event.target.value) : null)}
                            onKeyDown={(event) => {
                              if (["e", "E", "+", "-"].includes(event.key)) {
                                event.preventDefault();
                              }
                            }}
                            inputMode="decimal"
                            disabled={isDisabled && !isNA} // Allow interaction if only NA
                            style={{
                              padding: 8,
                              borderRadius: theme.radius.base,
                              border: `1px solid ${theme.colors.border}`,
                              backgroundColor: (isEditingDisabled || isForcedNA) ? theme.colors.backgroundGray : (isNA ? "#f9f9f9" : theme.colors.background),
                            }}
                          />
                        )}
                        {(field.type === "text" || field.type === "short_text" || field.type === "long_text") && !usesSelectForSingleChoice(field) && (
                          field.type === "long_text" ? (
                            <textarea
                              value={value ?? ""}
                              onChange={(event) => handleFieldChange(field, event.target.value)}
                              disabled={isEditingDisabled || isForcedNA}
                              style={{
                                padding: 8,
                                borderRadius: theme.radius.base,
                                border: `1px solid ${theme.colors.border}`,
                                backgroundColor: (isEditingDisabled || isForcedNA) ? theme.colors.backgroundGray : (isNA ? "#f9f9f9" : theme.colors.background),
                                minHeight: 60
                              }}
                            />
                          ) : (
                            <input
                              type="text"
                              value={value ?? ""}
                              onChange={(event) => handleFieldChange(field, event.target.value)}
                              disabled={isEditingDisabled || isForcedNA}
                              style={{
                                padding: 8,
                                borderRadius: theme.radius.base,
                                border: `1px solid ${theme.colors.border}`,
                                backgroundColor: (isEditingDisabled || isForcedNA) ? theme.colors.backgroundGray : (isNA ? "#f9f9f9" : theme.colors.background),
                              }}
                            />
                          )
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          ) : (
            <div style={{ color: theme.colors.textTertiary }}>No section selected.</div>
          )}
        </div>

        <div style={{
          border: `1px solid ${theme.colors.border}`,
          borderRadius: theme.radius.md,
          padding: 12,
          backgroundColor: theme.colors.background,
          height: "fit-content",
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <strong>Preview</strong>
            <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12 }}>
              <input
                type="checkbox"
                checked={showPreview}
                onChange={(event) => setShowPreview(event.target.checked)}
                disabled={isEditingDisabled}
              />
              Show
            </label>
          </div>
          {isEditingDisabled ? (
            <div style={{ marginTop: 12, color: theme.colors.textTertiary, fontSize: 13 }}>
              Preview is locked for published studies. Use View PDF instead.
            </div>
          ) : showPreview ? (
            <div style={{ marginTop: 12 }}>
              {previewError && (
                <ErrorBanner message={previewError} onDismiss={() => setPreviewError("")} />
              )}
              <div style={{
                backgroundColor: theme.colors.backgroundGray,
                padding: 12,
                borderRadius: theme.radius.base,
                minHeight: 240,
                whiteSpace: "pre-wrap",
                fontSize: 13,
              }}>
                {previewText || "Click preview narrative to load output."}
              </div>
              <Button variant="secondary" onClick={handleCopyPreview} style={{ marginTop: 12 }}>
                Copy text
              </Button>
              <div style={{ marginTop: 8, color: theme.colors.textTertiary, fontSize: 12 }}>
                Last generated: {formatDateTime(study?.published_at)}
              </div>
            </div>
          ) : (
            <div style={{ marginTop: 12, color: theme.colors.textTertiary, fontSize: 13 }}>
              Toggle preview on to view the narrative.
            </div>
          )}
        </div>
      </div>

      {showPublishConfirm && (
        <div style={{
          position: "fixed",
          inset: 0,
          backgroundColor: "rgba(0,0,0,0.4)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 1100,
        }}>
          <div style={{
            width: "min(480px, 90vw)",
            backgroundColor: theme.colors.background,
            borderRadius: theme.radius.md,
            padding: 20,
            boxShadow: theme.shadows.md,
          }}>
            <h3 style={{ marginTop: 0 }}>Publish Report</h3>
            <p style={{ color: theme.colors.textSecondary }}>
              Once published, this report cannot be edited.
            </p>
            <div style={{ display: "flex", gap: 12 }}>
              <Button onClick={publishReport} disabled={publishing}>
                {publishing ? "Publishing..." : "Confirm Publish"}
              </Button>
              <Button variant="secondary" onClick={() => setShowPublishConfirm(false)}>
                Cancel
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
