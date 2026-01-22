import React, { useEffect, useMemo, useState } from "react";
import { useAuth } from "../ui/auth";
import { apiGet, apiPost, apiPatch, apiPut, API_BASE } from "../ui/api";
import { Link } from "react-router-dom";
import PageHeader from "../ui/components/PageHeader";
import ErrorAlert from "../ui/components/ErrorAlert";
import SuccessAlert from "../ui/components/SuccessAlert";
import Button from "../ui/components/Button";

interface FieldOption {
  id?: string;
  label: string;
  value: string;
  order: number;
  is_active: boolean;
}

interface TemplateField {
  id?: string;
  label: string;
  key: string;
  field_type: string;
  is_required: boolean;
  help_text: string;
  default_value: string;
  placeholder: string;
  order: number;
  validation?: string;
  is_active: boolean;
  options?: FieldOption[];
}

interface ReportTemplate {
  id: string;
  name: string;
  code?: string | null;
  description?: string;
  category?: string;
  is_active: boolean;
  version: number;
  fields?: TemplateField[];
}

const FIELD_TYPES = [
  { value: "short_text", label: "Short Text" },
  { value: "long_text", label: "Long Text" },
  { value: "number", label: "Number" },
  { value: "date", label: "Date" },
  { value: "dropdown", label: "Dropdown" },
  { value: "checkbox", label: "Checkbox" },
  { value: "radio", label: "Radio" },
  { value: "heading", label: "Heading" },
  { value: "separator", label: "Separator" },
];

const makeEmptyField = (order: number): TemplateField => ({
  label: "",
  key: "",
  field_type: "short_text",
  is_required: false,
  help_text: "",
  default_value: "",
  placeholder: "",
  order,
  validation: "",
  is_active: true,
  options: [],
});

export default function ReportTemplates() {
  const { token } = useAuth();
  const [templates, setTemplates] = useState<ReportTemplate[]>([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<"active" | "inactive" | "all">("active");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [editing, setEditing] = useState<ReportTemplate | null>(null);
  const [formData, setFormData] = useState<ReportTemplate>({
    id: "",
    name: "",
    code: "",
    description: "",
    category: "",
    is_active: true,
    version: 1,
    fields: [],
  });

  const filteredTemplates = useMemo(() => {
    return templates.filter((template) => {
      const matchesSearch =
        template.name.toLowerCase().includes(search.toLowerCase()) ||
        (template.code || "").toLowerCase().includes(search.toLowerCase()) ||
        (template.category || "").toLowerCase().includes(search.toLowerCase());
      if (!matchesSearch) return false;
      if (statusFilter === "active") return template.is_active;
      if (statusFilter === "inactive") return !template.is_active;
      return true;
    });
  }, [templates, search, statusFilter]);

  const loadTemplates = async () => {
    if (!token) return;
    try {
      setLoading(true);
      const data = await apiGet("/report-templates/?include_inactive=true", token);
      setTemplates(data.results || data);
    } catch (e: any) {
      setError(e.message || "Failed to load templates");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTemplates();
  }, [token]);

  const resetForm = () => {
    setEditing(null);
    setFormData({
      id: "",
      name: "",
      code: "",
      description: "",
      category: "",
      is_active: true,
      version: 1,
      fields: [],
    });
  };

  const handleEdit = async (template: ReportTemplate) => {
    if (!token) return;
    try {
      setLoading(true);
      const data = await apiGet(`/report-templates/${template.id}/`, token);
      setEditing(data);
      setFormData({
        ...data,
        fields: data.fields || [],
      });
    } catch (e: any) {
      setError(e.message || "Failed to load template");
    } finally {
      setLoading(false);
    }
  };

  const updateField = (index: number, updates: Partial<TemplateField>) => {
    const fields = [...(formData.fields || [])];
    fields[index] = { ...fields[index], ...updates };
    setFormData({ ...formData, fields });
  };

  const addField = () => {
    const fields = [...(formData.fields || [])];
    fields.push(makeEmptyField(fields.length));
    setFormData({ ...formData, fields });
  };

  const removeField = (index: number) => {
    const fields = [...(formData.fields || [])].filter((_, idx) => idx !== index);
    fields.forEach((field, idx) => {
      field.order = idx;
    });
    setFormData({ ...formData, fields });
  };

  const moveField = (index: number, direction: "up" | "down") => {
    const fields = [...(formData.fields || [])];
    const targetIndex = direction === "up" ? index - 1 : index + 1;
    if (targetIndex < 0 || targetIndex >= fields.length) return;
    [fields[index], fields[targetIndex]] = [fields[targetIndex], fields[index]];
    fields.forEach((field, idx) => (field.order = idx));
    setFormData({ ...formData, fields });
  };

  const addOption = (fieldIdx: number) => {
    const fields = [...(formData.fields || [])];
    const field = fields[fieldIdx];
    const options = field.options ? [...field.options] : [];
    options.push({ label: "", value: "", order: options.length, is_active: true });
    field.options = options;
    setFormData({ ...formData, fields });
  };

  const updateOption = (fieldIdx: number, optionIdx: number, updates: Partial<FieldOption>) => {
    const fields = [...(formData.fields || [])];
    const field = fields[fieldIdx];
    const options = field.options ? [...field.options] : [];
    options[optionIdx] = { ...options[optionIdx], ...updates };
    field.options = options;
    setFormData({ ...formData, fields });
  };

  const removeOption = (fieldIdx: number, optionIdx: number) => {
    const fields = [...(formData.fields || [])];
    const field = fields[fieldIdx];
    const options = field.options ? field.options.filter((_, idx) => idx !== optionIdx) : [];
    field.options = options;
    setFormData({ ...formData, fields });
  };

  const saveTemplate = async () => {
    if (!token) return;
    setError("");
    setSuccess("");
    try {
      setLoading(true);
      const payload = {
        name: formData.name,
        code: formData.code || null,
        description: formData.description || "",
        category: formData.category || "",
        is_active: formData.is_active,
        version: formData.version || 1,
      };
      let templateId = editing?.id;
      if (editing) {
        await apiPatch(`/report-templates/${editing.id}/`, token, payload);
      } else {
        const created = await apiPost("/report-templates/", token, payload);
        templateId = created.id;
      }
      if (templateId) {
        const fieldsPayload = (formData.fields || []).map((field, idx) => ({
          ...field,
          order: idx,
        }));
        await apiPut(`/report-templates/${templateId}/fields/`, token, fieldsPayload);
      }
      setSuccess("Template saved successfully.");
      resetForm();
      loadTemplates();
    } catch (e: any) {
      setError(e.message || "Failed to save template");
    } finally {
      setLoading(false);
    }
  };

  const duplicateTemplate = async (templateId: string) => {
    if (!token) return;
    try {
      await apiPost(`/report-templates/${templateId}/duplicate/`, token, {});
      loadTemplates();
      setSuccess("Template duplicated.");
    } catch (e: any) {
      setError(e.message || "Failed to duplicate template");
    }
  };

  const toggleTemplateActive = async (template: ReportTemplate) => {
    if (!token) return;
    try {
      await apiPatch(`/report-templates/${template.id}/`, token, {
        is_active: !template.is_active,
      });
      loadTemplates();
    } catch (e: any) {
      setError(e.message || "Failed to update template");
    }
  };

  const exportTemplate = async (template: ReportTemplate) => {
    if (!token) return;
    if (!template.code) {
      setError("Template has no code, cannot export.");
      return;
    }
    try {
      const response = await fetch(`${API_BASE}/template-packages/export/?code=${template.code}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || "Export failed");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const contentDisp = response.headers.get('Content-Disposition');
      let filename = `${template.code}.json`;
      if (contentDisp && contentDisp.indexOf('filename=') !== -1) {
        filename = contentDisp.split('filename=')[1].replace(/"/g, '');
      }
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (e: any) {
      setError(e.message || "Export failed");
    }
  };

  return (
    <div>
      <PageHeader title="Report Templates" subtitle="For non-sectioned templates only" />
      
      {/* WARNING: This page is for flat templates only */}
      <div style={{ 
        padding: 16, 
        marginBottom: 20, 
        backgroundColor: '#fff3cd', 
        border: '1px solid #ffc107', 
        borderRadius: 8 
      }}>
        <strong>⚠️ Important:</strong> This page manages flat templates without sections.
        <br />
        <strong>For USG templates (with sections):</strong> Use <Link to="/admin/templates/import" style={{ color: '#0B5ED7', fontWeight: 'bold' }}>Template Import Manager</Link> instead!
      </div>
      
      {error && <ErrorAlert message={error} onDismiss={() => setError("")} />}
      {success && <SuccessAlert message={success} onDismiss={() => setSuccess("")} />}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: 20 }}>
        <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 16, background: "#fff" }}>
          <div style={{ display: "grid", gap: 8, marginBottom: 12 }}>
            <input
              type="text"
              placeholder="Search templates..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ padding: 8 }}
            />
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value as any)} style={{ padding: 8 }}>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="all">All</option>
            </select>
            <Button variant="primary" onClick={resetForm}>
              Create Template
            </Button>
            <Link to="/admin/templates/import" style={{ textDecoration: 'none' }}>
              <Button variant="secondary">Import JSON</Button>
            </Link>
          </div>
          {loading && <div>Loading templates...</div>}
          {!loading && filteredTemplates.length === 0 && <div>No templates found.</div>}
          <div style={{ display: "grid", gap: 8 }}>
            {filteredTemplates.map((template) => (
              <div
                key={template.id}
                style={{
                  border: "1px solid #e0e0e0",
                  borderRadius: 6,
                  padding: 10,
                  background: template.is_active ? "#fff" : "#f8f8f8",
                }}
              >
                <div style={{ fontWeight: 600 }}>{template.name}</div>
                <div style={{ fontSize: 12, color: "#666" }}>
                  {template.code || "No code"} • {template.category || "Uncategorized"}
                </div>
                <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                  <Button variant="secondary" onClick={() => handleEdit(template)}>
                    Edit
                  </Button>
                  <Button variant="secondary" onClick={() => duplicateTemplate(template.id)}>
                    Duplicate
                  </Button>
                  <Button variant="secondary" onClick={() => toggleTemplateActive(template)}>
                    {template.is_active ? "Deactivate" : "Activate"}
                  </Button>
                  <Button variant="secondary" onClick={() => exportTemplate(template)}>
                    Export
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 16, background: "#fff" }}>
          <h3 style={{ marginTop: 0 }}>{editing ? `Edit Template: ${editing.name}` : "Create Template"}</h3>
          <div style={{ display: "grid", gap: 12 }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              <div>
                <label>Name *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  style={{ width: "100%", padding: 8 }}
                />
              </div>
              <div>
                <label>Code</label>
                <input
                  type="text"
                  value={formData.code || ""}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                  style={{ width: "100%", padding: 8 }}
                />
              </div>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              <div>
                <label>Category</label>
                <input
                  type="text"
                  value={formData.category || ""}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  style={{ width: "100%", padding: 8 }}
                />
              </div>
              <div>
                <label>Version</label>
                <input
                  type="number"
                  value={formData.version}
                  onChange={(e) => setFormData({ ...formData, version: Number(e.target.value) })}
                  style={{ width: "100%", padding: 8 }}
                />
              </div>
            </div>
            <div>
              <label>Description</label>
              <textarea
                value={formData.description || ""}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                style={{ width: "100%", padding: 8, minHeight: 80 }}
              />
            </div>
            <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <input
                type="checkbox"
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
              />
              Active
            </label>
          </div>

          <div style={{ marginTop: 20 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <h4 style={{ margin: 0 }}>Fields</h4>
              <Button variant="secondary" onClick={addField}>
                Add Field
              </Button>
            </div>
            <div style={{ display: "grid", gap: 12, marginTop: 12 }}>
              {(formData.fields || []).map((field, idx) => (
                <div key={field.id || idx} style={{ border: "1px solid #e0e0e0", borderRadius: 6, padding: 12 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                    <strong>Field {idx + 1}</strong>
                    <div style={{ display: "flex", gap: 6 }}>
                      <Button variant="secondary" onClick={() => moveField(idx, "up")}>↑</Button>
                      <Button variant="secondary" onClick={() => moveField(idx, "down")}>↓</Button>
                      <Button variant="secondary" onClick={() => removeField(idx)}>Remove</Button>
                    </div>
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                    <div>
                      <label>Label *</label>
                      <input
                        type="text"
                        value={field.label}
                        onChange={(e) => updateField(idx, { label: e.target.value })}
                        style={{ width: "100%", padding: 8 }}
                      />
                    </div>
                    <div>
                      <label>Key *</label>
                      <input
                        type="text"
                        value={field.key}
                        onChange={(e) => updateField(idx, { key: e.target.value })}
                        style={{ width: "100%", padding: 8 }}
                      />
                    </div>
                    <div>
                      <label>Field Type</label>
                      <select
                        value={field.field_type}
                        onChange={(e) => updateField(idx, { field_type: e.target.value })}
                        style={{ width: "100%", padding: 8 }}
                      >
                        {FIELD_TYPES.map((type) => (
                          <option key={type.value} value={type.value}>
                            {type.label}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label>Placeholder</label>
                      <input
                        type="text"
                        value={field.placeholder}
                        onChange={(e) => updateField(idx, { placeholder: e.target.value })}
                        style={{ width: "100%", padding: 8 }}
                      />
                    </div>
                    <div>
                      <label>Help Text</label>
                      <input
                        type="text"
                        value={field.help_text}
                        onChange={(e) => updateField(idx, { help_text: e.target.value })}
                        style={{ width: "100%", padding: 8 }}
                      />
                    </div>
                    <div>
                      <label>Default Value</label>
                      <input
                        type="text"
                        value={field.default_value}
                        onChange={(e) => updateField(idx, { default_value: e.target.value })}
                        style={{ width: "100%", padding: 8 }}
                      />
                    </div>
                    <div>
                      <label>Validation (JSON)</label>
                      <input
                        type="text"
                        value={field.validation || ""}
                        onChange={(e) => updateField(idx, { validation: e.target.value })}
                        style={{ width: "100%", padding: 8 }}
                      />
                    </div>
                    <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <input
                        type="checkbox"
                        checked={field.is_required}
                        onChange={(e) => updateField(idx, { is_required: e.target.checked })}
                      />
                      Required
                    </label>
                  </div>
                  {(field.field_type === "dropdown" || field.field_type === "radio") && (
                    <div style={{ marginTop: 12 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <strong>Options</strong>
                        <Button variant="secondary" onClick={() => addOption(idx)}>Add Option</Button>
                      </div>
                      <div style={{ display: "grid", gap: 8, marginTop: 8 }}>
                        {(field.options || []).map((option, optIdx) => (
                          <div key={optIdx} style={{ display: "grid", gridTemplateColumns: "1fr 1fr auto", gap: 8 }}>
                            <input
                              type="text"
                              value={option.label}
                              onChange={(e) => updateOption(idx, optIdx, { label: e.target.value })}
                              placeholder="Label"
                              style={{ padding: 8 }}
                            />
                            <input
                              type="text"
                              value={option.value}
                              onChange={(e) => updateOption(idx, optIdx, { value: e.target.value })}
                              placeholder="Value"
                              style={{ padding: 8 }}
                            />
                            <Button variant="secondary" onClick={() => removeOption(idx, optIdx)}>Remove</Button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div style={{ display: "flex", gap: 8, marginTop: 20 }}>
            <Button onClick={saveTemplate} disabled={loading || !formData.name}>
              {loading ? "Saving..." : "Save Template"}
            </Button>
            <Button variant="secondary" onClick={resetForm}>
              Reset
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
