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
  type: "single_choice" | "multi_choice" | "number" | "text";
  required?: boolean;
  supports_not_applicable?: boolean;
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

const supportsMultiChoice = (field: TemplateField) => field.type === "multi_choice";
const usesSelectForSingleChoice = (field: TemplateField) => 
  (field.options || []).length > SINGLE_CHOICE_SELECT_THRESHOLD;
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
        const data = await apiGet(`/usg/studies/${studyId}/`, token);
        setStudy(data);
        const initialValues: Record<string, FieldValue> = {};
        (data.field_values || []).forEach((item: FieldValue) => {
          initialValues[item.field_key] = {
            field_key: item.field_key,
            value_json: item.value_json,
            is_not_applicable: item.is_not_applicable,
          };
        });
        const profileHidden = data.service_profile?.hidden_sections || data.hidden_sections || [];
        const profileForced = data.service_profile?.forced_na_fields || data.forced_na_fields || [];
        setHiddenSections(profileHidden);
        setForcedNaFields(profileForced);
        const enforcedDirty = new Set<string>();
        profileForced.forEach((fieldKey) => {
          const current = initialValues[fieldKey];
          const needsOverride = !current || !current.is_not_applicable || current.value_json !== null;
          if (needsOverride) {
            initialValues[fieldKey] = {
              field_key: fieldKey,
              value_json: null,
              is_not_applicable: true,
            };
            enforcedDirty.add(fieldKey);
          }
        });
        setValues(initialValues);
        setDirtyKeys(enforcedDirty);
        const sections = data.template_detail?.schema_json.sections || [];
        const includes: Record<string, boolean> = {};
        sections.forEach((section: TemplateSection) => {
          includes[section.section_key] = true;
        });
        setSectionIncludes(includes);
        const firstVisible = sections.find((section: TemplateSection) => !profileHidden.includes(section.section_key));
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
  const isPublished = study?.status === "published" || study?.is_locked;
  const canAutosave = study?.status === "draft" || study?.status === "verified";
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
    const fieldKeys = keys ? Array.from(keys) : Object.keys(currentValues);
    try {
      const payload = {
        values: fieldKeys.map((fieldKey) => ({
          field_key: fieldKey,
          value_json: currentValues[fieldKey]?.value_json ?? null,
          is_not_applicable: currentValues[fieldKey]?.is_not_applicable || false,
        })),
      };
      await apiPut(`/usg/studies/${studyId}/values/`, token, payload);
      
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
    if (!token || !studyId) return;
    setPreviewError("");
    try {
      const data = await apiPost(`/usg/studies/${studyId}/render/`, token, {});
      setPreviewText(data.full_report || data.narrative || "");
      setShowPreview(true);
    } catch (err: any) {
      setPreviewError(getErrorMessage(err, "Failed to render preview"));
    }
  };

  const publishReport = async () => {
    if (!token || !studyId) return;
    if (!canPublish) return;
    setPublishing(true);
    setError("");
    try {
      await apiPost(`/usg/studies/${studyId}/publish/`, token, {});
      setSuccess("Report published. Editing locked.");
      setShowPublishConfirm(false);
      const refreshed = await apiGet(`/usg/studies/${studyId}/`, token);
      setStudy(refreshed);
    } catch (err: any) {
      setError(getErrorMessage(err, "Publish failed"));
    } finally {
      setPublishing(false);
    }
  };

  const handleViewPdf = async () => {
    if (!studyId) return;
    const apiBase = (import.meta as any).env.VITE_API_BASE || ((import.meta as any).env.PROD ? "/api" : "http://localhost:8000/api");
    const url = `${apiBase}/usg/studies/${studyId}/pdf/`;
    setError("");
    // Open an empty window first to avoid popup blockers and show smoother UX
    const openedWindow = window.open("", "_blank", "noopener,noreferrer");
    if (!token) {
      if (openedWindow) openedWindow.close();
      return;
    }
    try {
      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
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
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <label style={{ fontWeight: theme.typography.fontWeight.medium }}>{field.label}</label>
                          {field.supports_not_applicable && (
                            <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12 }}>
                              <input
                                type="checkbox"
                                checked={isNA}
                                onChange={(event) => handleNotApplicable(field, event.target.checked)}
                                disabled={isEditingDisabled || isForcedNA}
                              />
                              Not applicable
                            </label>
                          )}
                        </div>
                        {field.type === "single_choice" && usesSelectForSingleChoice(field) && (
                          <select
                            value={value ?? ""}
                            onChange={(event) => handleFieldChange(field, event.target.value || null)}
                            disabled={isDisabled}
                            style={{
                              padding: 8,
                              borderRadius: theme.radius.base,
                              border: `1px solid ${theme.colors.border}`,
                              backgroundColor: isDisabled ? theme.colors.backgroundGray : theme.colors.background,
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
                        {field.type === "single_choice" && !usesSelectForSingleChoice(field) && (
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
                                    disabled={isDisabled}
                                    onChange={() => handleFieldChange(field, option.value)}
                                  />
                                  {option.label}
                                </label>
                              ))}
                            </div>
                          </fieldset>
                        )}
                        {supportsMultiChoice(field) && (
                          <div style={{ display: "grid", gap: 8 }}>
                            {(field.options || []).map((option) => {
                              const current = Array.isArray(value) ? value : [];
                              const checked = current.includes(option.value);
                              return (
                                <label key={option.value} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                  <input
                                    type="checkbox"
                                    checked={checked}
                                    disabled={isDisabled}
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
                            disabled={isDisabled}
                            style={{
                              padding: 8,
                              borderRadius: theme.radius.base,
                              border: `1px solid ${theme.colors.border}`,
                              backgroundColor: isDisabled ? theme.colors.backgroundGray : theme.colors.background,
                            }}
                          />
                        )}
                        {field.type === "text" && (
                          <input
                            type="text"
                            value={value ?? ""}
                            onChange={(event) => handleFieldChange(field, event.target.value)}
                            disabled={isDisabled}
                            style={{
                              padding: 8,
                              borderRadius: theme.radius.base,
                              border: `1px solid ${theme.colors.border}`,
                              backgroundColor: isDisabled ? theme.colors.backgroundGray : theme.colors.background,
                            }}
                          />
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
