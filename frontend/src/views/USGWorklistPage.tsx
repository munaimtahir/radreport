import React, { useEffect, useState } from "react";
import { useAuth } from "../ui/auth";
import { apiGet, apiPost } from "../ui/api";
import PageHeader from "../ui/components/PageHeader";
import ErrorAlert from "../ui/components/ErrorAlert";
import SuccessAlert from "../ui/components/SuccessAlert";
import Button from "../ui/components/Button";

interface ServiceVisitItem {
  id: string;
  service_visit_id: string;
  department_snapshot: string;
  status: string;
  template_details?: {
    template_id: string;
    template_name: string;
    version_id?: string;
    version?: number | null;
    schema?: TemplateSchema | null;
  } | null;
}

interface ServiceVisit {
  id: string;
  visit_id: string;
  patient_name: string;
  patient_reg_no: string;
  service_name: string;
  service_code: string;
  status: string;
  registered_at: string;
  items?: ServiceVisitItem[];
}

interface USGReport {
  id: string;
  service_visit_id: string;
  item_id?: string;  // service_visit_item_id (canonical identifier)
  report_json: Record<string, any>;
  template_schema?: TemplateSchema | null;
  template_name?: string;
  return_reason?: string;
}

interface TemplateField {
  id: string;
  label: string;
  key: string;
  type: string;
  required: boolean;
  na_allowed?: boolean;
  help_text: string;
  placeholder: string;
  unit: string;
  options?: { label: string; value: string }[];
}

interface TemplateSection {
  id: string;
  title: string;
  fields: TemplateField[];
}

interface TemplateSchema {
  name?: string;
  sections: TemplateSection[];
}

interface ReportTemplateFieldOption {
  id: string;
  label: string;
  value: string;
}

interface ReportTemplateField {
  id: string;
  label: string;
  key: string;
  field_type: string;
  is_required: boolean;
  help_text: string;
  placeholder: string;
  default_value?: any;
  options?: ReportTemplateFieldOption[];
}

interface ReportTemplate {
  id: string;
  name: string;
  fields: ReportTemplateField[];
}

interface TemplateReport {
  id: string;
  status: string;
  values: Record<string, any>;
  narrative_text?: string;
}

export default function USGWorklistPage() {
  const { token } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const [success, setSuccess] = useState<string>("");
  const [visits, setVisits] = useState<ServiceVisit[]>([]);
  const [selectedVisit, setSelectedVisit] = useState<ServiceVisit | null>(null);
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);  // service_visit_item_id (canonical)
  const [report, setReport] = useState<USGReport | null>(null);
  const [templateSchema, setTemplateSchema] = useState<TemplateSchema | null>(null);
  const [reportValues, setReportValues] = useState<Record<string, any>>({});
  const [reportTemplate, setReportTemplate] = useState<ReportTemplate | null>(null);
  const [templateReport, setTemplateReport] = useState<TemplateReport | null>(null);
  const [templateReportValues, setTemplateReportValues] = useState<Record<string, any>>({});
  const [templateNarrative, setTemplateNarrative] = useState("");
  const [naState, setNaState] = useState<Record<string, boolean>>({});





  useEffect(() => {
    if (token) {
      loadVisits();
    }
  }, [token]);

  const loadVisits = async () => {
    if (!token) return;
    try {
      // Use repeated query params for multiple status values (preferred format)
      // This creates: ?workflow=USG&status=REGISTERED&status=RETURNED
      // NOT comma-separated: ?status=REGISTERED,RETURNED
      const params = new URLSearchParams();
      params.append("workflow", "USG");
      params.append("status", "REGISTERED");
      params.append("status", "RETURNED");
      // URLSearchParams.toString() will create repeated params correctly: ?key=value1&key=value2
      const queryString = params.toString();
      const data = await apiGet(`/workflow/visits/?${queryString}`, token);
      setVisits(data.results || data || []);
    } catch (err: any) {
      setError(err.message || "Failed to load visits");
    }
  };

  const loadReport = async (visitId: string, itemId?: string) => {
    if (!token) return;
    try {
      // Try item-centric lookup first (canonical), fallback to visit_id
      const queryParam = itemId ? `service_visit_item_id=${itemId}` : `visit_id=${visitId}`;
      const data = await apiGet(`/workflow/usg/?${queryParam}`, token);
      if (data && data.length > 0) {
        const r = data[0];
        setReport(r);
        if (r.template_schema) {
          setTemplateSchema(r.template_schema);
        }
        // Use item_id from report if available, otherwise use the one we found
        if (r.item_id && !selectedItemId) {
          setSelectedItemId(r.item_id);
        }
        setReportValues(r.report_json || {});
        // Init NA logic moved to useEffect or here?
        // Let's do it here to avoid dependency cycles or overwrites.
        if (r.template_schema) {
          const schema = r.template_schema as TemplateSchema;
          const values = r.report_json || {};
          const nextNa = {} as Record<string, boolean>;
          schema.sections.forEach(s => s.fields.forEach(f => {
            if (f.na_allowed) {
              nextNa[f.key] = !(f.key in values);
            }
          }));
          setNaState(nextNa);
        }
      } else {
        setReport(null);
        setReportValues({});
        setNaState({});
      }
    } catch (err: any) {
      // Report might not exist yet
      setReport(null);
      setReportValues({});
    }
  };

  const loadTemplateReport = async (itemId: string) => {
    if (!token) return null;
    try {
      const data = await apiGet(`/reporting/${itemId}/template/`, token);
      if (data?.template) {
        setReportTemplate(data.template);
        setTemplateReport(data.report || null);
        setTemplateReportValues(data.report?.values || {});
        setTemplateNarrative(data.report?.narrative_text || "");
        return data.template as ReportTemplate;
      }
      setReportTemplate(null);
      setTemplateReport(null);
      setTemplateReportValues({});
      setTemplateNarrative("");
      return null;
    } catch (err: any) {
      setReportTemplate(null);
      setTemplateReport(null);
      setTemplateReportValues({});
      setTemplateNarrative("");
      return null;
    }
  };

  const handleSelectVisit = async (visit: ServiceVisit) => {
    setSelectedVisit(visit);

    // Find USG item (canonical identifier) - prefer department_snapshot="USG"
    const usgItem = visit.items?.find(item => item.department_snapshot === "USG");
    if (usgItem) {
      setSelectedItemId(usgItem.id);
      const dynamicTemplate = await loadTemplateReport(usgItem.id);
      if (dynamicTemplate) {
        setTemplateSchema(null);
      } else {
        setTemplateSchema(usgItem.template_details?.schema || null);
      }
      // Load report by service_visit_item_id (canonical)
      await loadReport(visit.id, usgItem.id);
    } else {
      // Fallback: use visit_id (legacy compatibility)
      setSelectedItemId(null);
      setTemplateSchema(null);
      setReportTemplate(null);
      setTemplateReport(null);
      setTemplateReportValues({});
      setTemplateNarrative("");
      await loadReport(visit.id);
    }
  };

  const handleFieldChange = (key: string, value: any) => {
    setReportValues(prev => ({ ...prev, [key]: value }));
    // Auto-uncheck NA
    if (naState[key]) {
      setNaState(prev => ({ ...prev, [key]: false }));
    }
  };

  const toggleNA = (key: string, checked: boolean) => {
    setNaState(prev => ({ ...prev, [key]: checked }));
    // We don't clear value from state, just rely on payload filter.
  };

  const handleTemplateFieldChange = (key: string, value: any) => {
    setTemplateReportValues({ ...templateReportValues, [key]: value });
  };

  const getTemplateValue = (field: ReportTemplateField) => {
    const existing = templateReportValues[field.key];
    if (existing !== undefined) return existing;
    if (field.default_value !== undefined && field.default_value !== null) return field.default_value;
    if (field.field_type === "checkbox") return false;
    return "";
  };

  const isMissingRequiredField = (field: TemplateField, value: any) => {
    if (!field.required) return false;
    if (field.type === "checklist") {
      return !value || (Array.isArray(value) && value.length === 0);
    }
    if (field.type === "number") {
      return value === null || value === undefined || value === "";
    }
    if (field.type === "boolean") {
      return value === null || value === undefined;
    }
    return value === null || value === undefined || (typeof value === "string" && !value.trim());
  };

  const isMissingRequiredTemplateField = (field: ReportTemplateField, value: any) => {
    if (!field.is_required) return false;
    if (field.field_type === "checkbox") {
      return value !== true;
    }
    if (field.field_type === "number") {
      return value === null || value === undefined || value === "";
    }
    return value === null || value === undefined || (typeof value === "string" && !value.toString().trim());
  };

  const isReadyToSubmit = () => {
    if (!templateSchema) return false;
    return !templateSchema.sections.some((section) =>
      section.fields.some((field) => isMissingRequiredField(field, reportValues[field.key]))
    );
  };

  const isReadyToSubmitTemplate = () => {
    if (!reportTemplate) return false;
    return !reportTemplate.fields.some((field) =>
      isMissingRequiredTemplateField(field, templateReportValues[field.key] ?? getTemplateValue(field))
    );
  };

  const saveDraft = async () => {
    if (!token || !selectedVisit) return;
    setLoading(true);
    setError("");
    try {
      if (reportTemplate && selectedItemId) {
        await apiPost(`/reporting/${selectedItemId}/save-template-report/`, token, {
          template_id: reportTemplate.id,
          values: templateReportValues,
          narrative_text: templateNarrative,
          submit: false,
        });
        setSuccess("Draft saved successfully");
        await loadTemplateReport(selectedItemId);
        return;
      }

      // First ensure report exists by creating/updating it
      // Filter out NA fields from payload
      const filteredValues = { ...reportValues };
      Object.keys(naState).forEach(key => {
        if (naState[key]) {
          delete filteredValues[key];
          // Also ensure we don't send nulls if undefined? 
          // But filteredValues comes from reportValues which has real data.
        }
      });

      const reportPayload: any = {
        values: filteredValues,
      };

      if (selectedItemId) {
        reportPayload.service_visit_item_id = selectedItemId;
      } else {
        reportPayload.visit_id = selectedVisit.id;  // Legacy fallback
      }

      // Create/update report first
      const savedReport = await apiPost("/workflow/usg/", token, reportPayload);

      // Update selectedItemId from saved report if available
      if (savedReport.item_id) {
        setSelectedItemId(savedReport.item_id);
      }

      // Use save_draft endpoint to properly transition status if needed
      await apiPost(`/workflow/usg/${savedReport.id}/save_draft/`, token, reportPayload);

      setSuccess("Draft saved successfully");

      // Reload report using canonical identifier
      if (selectedItemId || savedReport.item_id) {
        await loadReport(selectedVisit.id, selectedItemId || savedReport.item_id);
      } else {
        await loadReport(selectedVisit.id);
      }
    } catch (err: any) {
      setError(err.message || "Failed to save draft");
    } finally {
      setLoading(false);
    }
  };

  const submitForVerification = async () => {
    if (!token || !selectedVisit) return;
    setLoading(true);
    setError("");
    try {
      if (reportTemplate && selectedItemId) {
        await apiPost(`/reporting/${selectedItemId}/save-template-report/`, token, {
          template_id: reportTemplate.id,
          values: templateReportValues,
          narrative_text: templateNarrative,
          submit: true,
        });
        setSuccess("Report submitted for verification");
        setSelectedVisit(null);
        setSelectedItemId(null);
        setReport(null);
        setReportTemplate(null);
        setTemplateReport(null);
        setTemplateReportValues({});
        setTemplateNarrative("");
        await loadVisits();
        return;
      }

      // Use service_visit_item_id (canonical) if available, fallback to visit_id (compatibility)
      const reportPayload: any = {
        values: reportValues,
      };

      if (selectedItemId) {
        reportPayload.service_visit_item_id = selectedItemId;
      } else {
        reportPayload.visit_id = selectedVisit.id;  // Legacy fallback
      }

      // First create/update report (ensures same record is used)
      const savedReport = await apiPost("/workflow/usg/", token, reportPayload);

      // Update selectedItemId from saved report if available
      const canonicalItemId = savedReport.item_id || selectedItemId;
      if (savedReport.item_id) {
        setSelectedItemId(savedReport.item_id);
      }

      // Submit for verification using report ID (now handled correctly by fixed get_object())
      // OR use service_visit_item_id directly if supported (defensive approach)
      await apiPost(`/workflow/usg/${savedReport.id}/submit_for_verification/`, token, {
        values: reportPayload.values,  // Include latest data
      });

      setSuccess("Report submitted for verification");
      setSelectedVisit(null);
      setSelectedItemId(null);
      setReport(null);
      await loadVisits();
    } catch (err: any) {
      setError(err.message || "Failed to submit for verification");
    } finally {
      setLoading(false);
    }
  };

  const handlePreventEnter = (event: React.KeyboardEvent) => {
    if (event.key === "Enter" && (event.target as HTMLElement).tagName !== "TEXTAREA") {
      event.preventDefault();
    }
  };

  return (
    <div style={{ maxWidth: 1400, margin: "0 auto" }}>
      <PageHeader title="USG Worklist" subtitle="Performance Desk" />

      {error && <ErrorAlert message={error} onDismiss={() => setError("")} />}
      {success && <SuccessAlert message={success} onDismiss={() => setSuccess("")} />}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: 20 }}>
        {/* Visit List */}
        <div style={{ border: "1px solid #ddd", padding: 16, borderRadius: 8, maxHeight: "80vh", overflowY: "auto" }}>
          <h2>Pending Visits ({visits.length})</h2>
          {visits.length === 0 ? (
            <p>No visits pending</p>
          ) : (
            <div style={{ display: "grid", gap: 8 }}>
              {visits.map((visit) => (
                <div
                  key={visit.id}
                  onClick={() => handleSelectVisit(visit)}
                  style={{
                    padding: 12,
                    border: selectedVisit?.id === visit.id ? "2px solid #0B5ED7" : "1px solid #ddd",
                    borderRadius: 4,
                    cursor: "pointer",
                    backgroundColor: selectedVisit?.id === visit.id ? "#f0f7ff" : "white",
                  }}
                >
                  <div><strong>{visit.visit_id}</strong></div>
                  <div style={{ fontSize: 14, color: "#666" }}>
                    {visit.patient_name} ({visit.patient_reg_no})
                  </div>
                  <div style={{ fontSize: 12, color: "#999" }}>
                    {new Date(visit.registered_at).toLocaleString()}
                  </div>
                  {visit.status === "RETURNED" && (
                    <div style={{ fontSize: 12, color: "red", marginTop: 4 }}>
                      Returned for correction
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Report Form */}
        {selectedVisit && (
          <div style={{ border: "1px solid #ddd", padding: 20, borderRadius: 8 }}>
            <h2>USG Report - {selectedVisit.visit_id}</h2>
            <div style={{ marginBottom: 16, padding: 12, backgroundColor: "#f5f5f5", borderRadius: 4 }}>
              <div><strong>Patient:</strong> {selectedVisit.patient_name} ({selectedVisit.patient_reg_no})</div>
              <div><strong>Service:</strong> {selectedVisit.service_name}</div>
            </div>

            {report?.return_reason && (
              <div style={{ marginBottom: 16, padding: 12, backgroundColor: "#fff3cd", borderRadius: 4, border: "1px solid #ffc107" }}>
                <strong>Return Reason:</strong> {report.return_reason}
              </div>
            )}

            {!reportTemplate && !templateSchema && (
              <div style={{ marginBottom: 16, padding: 12, backgroundColor: "#fff3cd", borderRadius: 4, border: "1px solid #ffeeba" }}>
                No published template found for this service. Please assign and publish a template before reporting.
              </div>
            )}

            {reportTemplate && (
              <div style={{ display: "grid", gap: 20, marginBottom: 16 }}>
                <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 16, background: "white" }}>
                  <h3 style={{ marginTop: 0, marginBottom: 12 }}>{reportTemplate.name}</h3>
                  <div style={{ display: "grid", gap: 12 }}>
                    {reportTemplate.fields.map((field) => {
                      const value = getTemplateValue(field);
                      const missing = isMissingRequiredTemplateField(field, value);
                      if (field.field_type === "heading") {
                        return <h4 key={field.id} style={{ margin: "8px 0" }}>{field.label}</h4>;
                      }
                      if (field.field_type === "separator") {
                        return <hr key={field.id} style={{ border: "none", borderTop: "1px solid #eee" }} />;
                      }
                      return (
                        <div key={field.id}>
                          <label style={{ display: "block", marginBottom: 6, fontWeight: field.is_required ? "bold" : "normal" }}>
                            {field.label}
                            {field.is_required && <span style={{ color: "red" }}> *</span>}
                          </label>
                          {field.field_type === "short_text" && (
                            <input
                              type="text"
                              value={value}
                              onChange={(e) => handleTemplateFieldChange(field.key, e.target.value)}
                              onKeyDown={handlePreventEnter}
                              placeholder={field.placeholder}
                              style={{ width: "100%", padding: 8, borderColor: missing ? "#dc3545" : "#ccc" }}
                            />
                          )}
                          {field.field_type === "long_text" && (
                            <textarea
                              value={value}
                              onChange={(e) => handleTemplateFieldChange(field.key, e.target.value)}
                              placeholder={field.placeholder}
                              rows={4}
                              style={{ width: "100%", padding: 8, borderColor: missing ? "#dc3545" : "#ccc" }}
                            />
                          )}
                          {field.field_type === "number" && (
                            <input
                              type="number"
                              value={value}
                              onChange={(e) => {
                                const rawValue = e.target.value;
                                if (rawValue === "") {
                                  handleTemplateFieldChange(field.key, "");
                                  return;
                                }
                                const parsed = Number(rawValue);
                                handleTemplateFieldChange(
                                  field.key,
                                  Number.isNaN(parsed) ? "" : parsed
                                );
                              }}
                              onKeyDown={handlePreventEnter}
                              placeholder={field.placeholder}
                              style={{ width: "100%", padding: 8, borderColor: missing ? "#dc3545" : "#ccc" }}
                            />
                          )}
                          {field.field_type === "date" && (
                            <input
                              type="date"
                              value={value}
                              onChange={(e) => handleTemplateFieldChange(field.key, e.target.value)}
                              onKeyDown={handlePreventEnter}
                              style={{ width: "100%", padding: 8, borderColor: missing ? "#dc3545" : "#ccc" }}
                            />
                          )}
                          {field.field_type === "checkbox" && (
                            <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
                              <input
                                type="checkbox"
                                checked={Boolean(value)}
                                onChange={(e) => handleTemplateFieldChange(field.key, e.target.checked)}
                              />
                              Yes
                            </label>
                          )}
                          {field.field_type === "dropdown" && (
                            <select
                              value={value}
                              onChange={(e) => handleTemplateFieldChange(field.key, e.target.value)}
                              onKeyDown={handlePreventEnter}
                              style={{ width: "100%", padding: 8, borderColor: missing ? "#dc3545" : "#ccc" }}
                            >
                              <option value="">Select...</option>
                              {field.options?.map((opt) => (
                                <option key={opt.value} value={opt.value}>
                                  {opt.label}
                                </option>
                              ))}
                            </select>
                          )}
                          {field.field_type === "radio" && (
                            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                              {field.options?.map((opt) => (
                                <label key={opt.value} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                  <input
                                    type="radio"
                                    name={field.key}
                                    value={opt.value}
                                    checked={value === opt.value}
                                    onChange={(e) => handleTemplateFieldChange(field.key, e.target.value)}
                                  />
                                  {opt.label}
                                </label>
                              ))}
                            </div>
                          )}
                          {field.help_text && <div style={{ fontSize: 12, color: "#666", marginTop: 4 }}>{field.help_text}</div>}
                        </div>
                      );
                    })}
                  </div>
                </div>
                <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 16, background: "white" }}>
                  <h3 style={{ marginTop: 0, marginBottom: 12 }}>Narrative</h3>
                  <textarea
                    value={templateNarrative}
                    onChange={(e) => setTemplateNarrative(e.target.value)}
                    placeholder="Optional narrative text..."
                    rows={4}
                    style={{ width: "100%", padding: 8 }}
                  />
                </div>
              </div>
            )}

            {!reportTemplate && templateSchema && (
              <div style={{ display: "grid", gap: 20, marginBottom: 16 }}>
                {templateSchema.sections.map((section) => (
                  <div key={section.id} style={{ border: "1px solid #ddd", borderRadius: 8, padding: 16, background: "white" }}>
                    <h3 style={{ marginTop: 0, marginBottom: 12 }}>{section.title}</h3>
                    <div style={{ display: "grid", gap: 12 }}>
                      {section.fields.map((field) => {
                        const value = reportValues[field.key] ?? (field.type === "boolean" ? false : field.type === "checklist" ? [] : "");
                        const missing = isMissingRequiredField(field, value);
                        const isNA = naState[field.key] || false;

                        return (
                          <div key={field.id}>
                            <div style={{ display: "flex", alignItems: "center", marginBottom: 6 }}>
                              {field.na_allowed && (
                                <label style={{ display: "flex", alignItems: "center", gap: 4, marginRight: 10, fontSize: 13, fontWeight: 500, color: "#666" }}>
                                  <input
                                    type="checkbox"
                                    checked={isNA}
                                    onChange={(e) => toggleNA(field.key, e.target.checked)}
                                  />
                                  N/A
                                </label>
                              )}
                              <label style={{ fontWeight: field.required ? "bold" : "normal" }}>
                                {field.label}
                                {field.required && <span style={{ color: "red" }}> *</span>}
                                {field.unit && <span style={{ color: "#666" }}> ({field.unit})</span>}
                              </label>
                            </div>

                            <div style={isNA ? { opacity: 0.6 } : {}}>
                              {field.type === "short_text" && (
                                <input
                                  type="text"
                                  value={value}
                                  onChange={(e) => handleFieldChange(field.key, e.target.value)}
                                  onKeyDown={handlePreventEnter}
                                  placeholder={field.placeholder}
                                  style={{ width: "100%", padding: 8, borderColor: missing ? "#dc3545" : "#ccc" }}
                                />
                              )}
                              {field.type === "number" && (
                                <input
                                  type="number"
                                  value={value}
                                  onChange={(e) => handleFieldChange(field.key, e.target.value === "" ? "" : Number(e.target.value))}
                                  onKeyDown={handlePreventEnter}
                                  placeholder={field.placeholder}
                                  style={{ width: "100%", padding: 8, borderColor: missing ? "#dc3545" : "#ccc" }}
                                />
                              )}
                              {field.type === "paragraph" && (
                                <textarea
                                  value={value}
                                  onChange={(e) => handleFieldChange(field.key, e.target.value)}
                                  placeholder={field.placeholder}
                                  rows={4}
                                  style={{ width: "100%", padding: 8, borderColor: missing ? "#dc3545" : "#ccc" }}
                                />
                              )}
                              {field.type === "boolean" && (
                                <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                  <input
                                    type="checkbox"
                                    checked={Boolean(value)}
                                    onChange={(e) => handleFieldChange(field.key, e.target.checked)}
                                  />
                                  Yes
                                </label>
                              )}
                              {field.type === "dropdown" && (
                                <select
                                  value={value}
                                  onChange={(e) => handleFieldChange(field.key, e.target.value)}
                                  onKeyDown={handlePreventEnter}
                                  style={{ width: "100%", padding: 8, borderColor: missing ? "#dc3545" : "#ccc" }}
                                >
                                  <option value="">Select...</option>
                                  {field.options?.map((opt) => (
                                    <option key={opt.value} value={opt.value}>
                                      {opt.label}
                                    </option>
                                  ))}
                                </select>
                              )}
                              {field.type === "checklist" && (
                                <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
                                  {field.options?.map((opt) => {
                                    const selected = Array.isArray(value) ? value : [];
                                    return (
                                      <label key={opt.value} style={{ display: "flex", alignItems: "center", gap: 6, minWidth: "fit-content" }}>
                                        <input
                                          type="checkbox"
                                          checked={selected.includes(opt.value)}
                                          onChange={(e) => {
                                            const nextValue = e.target.checked
                                              ? [...selected, opt.value]
                                              : selected.filter((v: string) => v !== opt.value);
                                            handleFieldChange(field.key, nextValue);
                                          }}
                                        />
                                        {opt.label}
                                      </label>
                                    );
                                  })}
                                </div>
                              )}
                              {field.help_text && <div style={{ fontSize: 12, color: "#666", marginTop: 4 }}>{field.help_text}</div>}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div style={{ display: "flex", gap: 8 }}>
              <Button variant="secondary" onClick={saveDraft} disabled={loading || (!templateSchema && !reportTemplate)}>
                Save Draft
              </Button>
              <Button
                onClick={submitForVerification}
                disabled={
                  loading ||
                  (!templateSchema && !reportTemplate) ||
                  (reportTemplate ? !isReadyToSubmitTemplate() : !isReadyToSubmit())
                }
              >
                Submit for Verification
              </Button>
            </div>
          </div>
        )}

        {!selectedVisit && (
          <div style={{ border: "1px solid #ddd", padding: 20, borderRadius: 8, textAlign: "center", color: "#999" }}>
            Select a visit from the list to start reporting
          </div>
        )}
      </div>
    </div>
  );
}
