import React, { useEffect, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { apiGet, apiPost, apiPut } from "../ui/api";
import { useAuth } from "../ui/auth";
import PageHeader from "../ui/components/PageHeader";
import ErrorAlert from "../ui/components/ErrorAlert";
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

const supportsMultiChoice = (field: TemplateField) => field.type === "multi_choice";

export default function UsgStudyEditorPage() {
  const { studyId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const { token } = useAuth();
  const [study, setStudy] = useState<UsgStudy | null>(null);
  const [values, setValues] = useState<Record<string, FieldValue>>({});
  const [sectionIncludes, setSectionIncludes] = useState<Record<string, boolean>>({});
  const [activeSection, setActiveSection] = useState<string>("");
  const [previewText, setPreviewText] = useState<string>("");
  const [showPreview, setShowPreview] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [saving, setSaving] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [showPublishConfirm, setShowPublishConfirm] = useState(false);

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
        setValues(initialValues);
        const sections = data.template_detail?.schema_json.sections || [];
        const includes: Record<string, boolean> = {};
        sections.forEach((section: TemplateSection) => {
          includes[section.section_key] = true;
        });
        setSectionIncludes(includes);
        if (sections.length > 0) {
          setActiveSection(sections[0].section_key);
        }
      } catch (err: any) {
        setError(err.message || "Failed to load study");
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

  const schema = study?.template_detail?.schema_json;
  const sections = schema?.sections || [];
  const isPublished = study?.status === "published" || study?.is_locked;

  const handleFieldChange = (field: TemplateField, value: any) => {
    setValues((prev) => ({
      ...prev,
      [field.field_key]: {
        field_key: field.field_key,
        value_json: value,
        is_not_applicable: prev[field.field_key]?.is_not_applicable || false,
      },
    }));
  };

  const handleNotApplicable = (field: TemplateField, checked: boolean) => {
    setValues((prev) => ({
      ...prev,
      [field.field_key]: {
        field_key: field.field_key,
        value_json: checked ? null : prev[field.field_key]?.value_json,
        is_not_applicable: checked,
      },
    }));
  };

  const handleSectionToggle = (sectionKey: string, enabled: boolean) => {
    setSectionIncludes((prev) => ({
      ...prev,
      [sectionKey]: enabled,
    }));
  };

  const saveDraft = async () => {
    if (!token || !studyId) return;
    if (isPublished) return;
    setSaving(true);
    setError("");
    try {
      const payload = {
        values: Object.values(values).map((item) => ({
          field_key: item.field_key,
          value_json: item.value_json,
          is_not_applicable: item.is_not_applicable,
        })),
      };
      await apiPut(`/usg/studies/${studyId}/values/`, token, payload);
      setSuccess("Saved");
    } catch (err: any) {
      setError(err.message || "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const renderPreview = async () => {
    if (!token || !studyId) return;
    setError("");
    try {
      const data = await apiPost(`/usg/studies/${studyId}/render/`, token, {});
      setPreviewText(data.full_report || data.narrative || "");
      setShowPreview(true);
    } catch (err: any) {
      setError(err.message || "Failed to render preview");
    }
  };

  const publishReport = async () => {
    if (!token || !studyId) return;
    setPublishing(true);
    setError("");
    try {
      await apiPost(`/usg/studies/${studyId}/publish/`, token, {});
      setSuccess("Report published. Editing locked.");
      setShowPublishConfirm(false);
      const refreshed = await apiGet(`/usg/studies/${studyId}/`, token);
      setStudy(refreshed);
    } catch (err: any) {
      setError(err.message || "Publish failed");
    } finally {
      setPublishing(false);
    }
  };

  const handleViewPdf = async () => {
    if (!studyId) return;
    const apiBase = (import.meta as any).env.VITE_API_BASE || ((import.meta as any).env.PROD ? "/api" : "http://localhost:8000/api");
    const url = `${apiBase}/usg/studies/${studyId}/pdf/`;
    window.open(url, "_blank", "noopener,noreferrer");
  };

  const handleCopyPreview = async () => {
    if (!previewText) return;
    try {
      await navigator.clipboard.writeText(previewText);
      setSuccess("Preview text copied.");
    } catch (err: any) {
      setError(err.message || "Copy failed");
    }
  };

  const activeSectionData = sections.find((section) => section.section_key === activeSection);

  return (
    <div style={{ maxWidth: 1400, margin: "0 auto" }}>
      <PageHeader
        title="USG Study Editor"
        subtitle={`${study?.patient_name || ""} • MRN ${study?.patient_mrn || ""} • Visit ${study?.visit_number || ""}`}
      />

      {error && <ErrorAlert message={error} onDismiss={() => setError("")} />}
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
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <Button variant="secondary" onClick={() => navigate(-1)}>
            Back to Visit
          </Button>
          <Button variant="secondary" onClick={saveDraft} disabled={saving || isPublished}>
            {saving ? "Saving..." : "Save Draft"}
          </Button>
          <Button variant="secondary" onClick={renderPreview}>
            Preview Narrative
          </Button>
          <Button variant="primary" onClick={() => setShowPublishConfirm(true)} disabled={publishing || isPublished}>
            Publish
          </Button>
          {isPublished && (
            <Button variant="secondary" onClick={handleViewPdf}>
              View PDF
            </Button>
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
          {sections.map((section) => (
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
                      disabled={isPublished}
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
                    const isNA = values[field.field_key]?.is_not_applicable || false;
                    const isDisabled = isPublished || isNA;
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
                                disabled={isPublished}
                              />
                              Not applicable
                            </label>
                          )}
                        </div>
                        {field.type === "single_choice" && (
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
              <input type="checkbox" checked={showPreview} onChange={(event) => setShowPreview(event.target.checked)} />
              Show
            </label>
          </div>
          {showPreview ? (
            <div style={{ marginTop: 12 }}>
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
