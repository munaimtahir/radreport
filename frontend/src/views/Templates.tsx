import React, { useEffect, useState } from "react";
import { useAuth } from "../ui/auth";
import { apiGet, apiPost, apiPatch, apiDelete } from "../ui/api";

interface FieldOption {
  id?: string;
  label: string;
  value: string;
  order: number;
}

interface TemplateField {
  id?: string;
  label: string;
  key: string;
  field_type: string;
  required: boolean;
  help_text: string;
  placeholder: string;
  unit: string;
  order: number;
  options?: FieldOption[];
}

interface TemplateSection {
  id?: string;
  title: string;
  order: number;
  fields?: TemplateField[];
}

interface Template {
  id: string;
  name: string;
  modality_code: string;
  is_active: boolean;
  sections?: TemplateSection[];
}

const FIELD_TYPES = [
  { value: "short_text", label: "Short Text" },
  { value: "number", label: "Number" },
  { value: "dropdown", label: "Dropdown (single)" },
  { value: "checklist", label: "Checklist (multi)" },
  { value: "paragraph", label: "Paragraph" },
  { value: "boolean", label: "Yes/No" },
];

export default function Templates() {
  const { token } = useAuth();
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Template | null>(null);
  const [formData, setFormData] = useState({
    name: "",
    modality_code: "",
    is_active: true,
    sections: [] as TemplateSection[],
  });

  const loadTemplates = async () => {
    if (!token) return;
    try {
      setLoading(true);
      const data = await apiGet("/templates/", token);
      setTemplates(data.results || data);
      setError("");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTemplates();
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    try {
      if (editing) {
        await apiPatch(`/templates/${editing.id}/`, token, formData);
      } else {
        await apiPost("/templates/", token, formData);
      }
      setShowForm(false);
      setEditing(null);
      setFormData({ name: "", modality_code: "", is_active: true, sections: [] });
      loadTemplates();
    } catch (e: any) {
      setError(e.message);
    }
  };

  const handlePublish = async (templateId: string) => {
    if (!token || !confirm("Publish this template version?")) return;
    try {
      await apiPost(`/templates/${templateId}/publish/`, token, {});
      loadTemplates();
      alert("Template version published successfully!");
    } catch (e: any) {
      setError(e.message);
    }
  };

  const addSection = () => {
    setFormData({
      ...formData,
      sections: [
        ...formData.sections,
        { title: "", order: formData.sections.length, fields: [] },
      ],
    });
  };

  const updateSection = (idx: number, updates: Partial<TemplateSection>) => {
    const sections = [...formData.sections];
    sections[idx] = { ...sections[idx], ...updates };
    setFormData({ ...formData, sections });
  };

  const deleteSection = (idx: number) => {
    const sections = formData.sections.filter((_, i) => i !== idx);
    setFormData({ ...formData, sections });
  };

  const addField = (sectionIdx: number) => {
    const sections = [...formData.sections];
    const section = sections[sectionIdx];
    section.fields = section.fields || [];
    section.fields.push({
      label: "",
      key: "",
      field_type: "short_text",
      required: false,
      help_text: "",
      placeholder: "",
      unit: "",
      order: section.fields.length,
      options: [],
    });
    setFormData({ ...formData, sections });
  };

  const updateField = (sectionIdx: number, fieldIdx: number, updates: Partial<TemplateField>) => {
    const sections = [...formData.sections];
    sections[sectionIdx].fields = sections[sectionIdx].fields || [];
    sections[sectionIdx].fields![fieldIdx] = {
      ...sections[sectionIdx].fields![fieldIdx],
      ...updates,
    };
    setFormData({ ...formData, sections });
  };

  const deleteField = (sectionIdx: number, fieldIdx: number) => {
    const sections = [...formData.sections];
    sections[sectionIdx].fields = sections[sectionIdx].fields?.filter((_, i) => i !== fieldIdx);
    setFormData({ ...formData, sections });
  };

  const addOption = (sectionIdx: number, fieldIdx: number) => {
    const sections = [...formData.sections];
    const field = sections[sectionIdx].fields![fieldIdx];
    field.options = field.options || [];
    field.options.push({ label: "", value: "", order: field.options.length });
    setFormData({ ...formData, sections });
  };

  const updateOption = (
    sectionIdx: number,
    fieldIdx: number,
    optIdx: number,
    updates: Partial<FieldOption>
  ) => {
    const sections = [...formData.sections];
    const field = sections[sectionIdx].fields![fieldIdx];
    field.options![optIdx] = { ...field.options![optIdx], ...updates };
    setFormData({ ...formData, sections });
  };

  const deleteOption = (sectionIdx: number, fieldIdx: number, optIdx: number) => {
    const sections = [...formData.sections];
    const field = sections[sectionIdx].fields![fieldIdx];
    field.options = field.options?.filter((_, i) => i !== optIdx);
    setFormData({ ...formData, sections });
  };

  const handleEdit = (t: Template) => {
    setEditing(t);
    setFormData({
      name: t.name,
      modality_code: t.modality_code,
      is_active: t.is_active,
      sections: t.sections || [],
    });
    setShowForm(true);
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <h1>Templates</h1>
        <button
          onClick={() => {
            setEditing(null);
            setFormData({ name: "", modality_code: "", is_active: true, sections: [] });
            setShowForm(!showForm);
          }}
          style={{ padding: "8px 16px", fontSize: 14 }}
        >
          {showForm ? "Cancel" : "Create Template"}
        </button>
      </div>

      {error && <div style={{ color: "red", marginBottom: 10 }}>{error}</div>}

      {showForm && (
        <form
          onSubmit={handleSubmit}
          style={{
            background: "#f9f9f9",
            padding: 20,
            borderRadius: 8,
            marginBottom: 20,
          }}
        >
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 20 }}>
            <div>
              <label>Template Name *</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
                style={{ width: "100%", padding: 8 }}
              />
            </div>
            <div>
              <label>Modality Code</label>
              <input
                type="text"
                value={formData.modality_code}
                onChange={(e) => setFormData({ ...formData, modality_code: e.target.value })}
                placeholder="USG, XRAY, CT, etc."
                style={{ width: "100%", padding: 8 }}
              />
            </div>
          </div>

          <div style={{ marginBottom: 20 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
              <h3>Sections</h3>
              <button type="button" onClick={addSection} style={{ padding: "6px 12px", fontSize: 14 }}>
                Add Section
              </button>
            </div>

            {formData.sections.map((section, secIdx) => (
              <div
                key={secIdx}
                style={{
                  border: "1px solid #ddd",
                  borderRadius: 8,
                  padding: 15,
                  marginBottom: 15,
                  background: "white",
                }}
              >
                <div style={{ display: "flex", gap: 10, marginBottom: 10 }}>
                  <input
                    type="text"
                    placeholder="Section Title"
                    value={section.title}
                    onChange={(e) => updateSection(secIdx, { title: e.target.value })}
                    style={{ flex: 1, padding: 8 }}
                  />
                  <button
                    type="button"
                    onClick={() => deleteSection(secIdx)}
                    style={{ padding: "8px 12px", background: "#dc3545", color: "white", border: "none" }}
                  >
                    Delete Section
                  </button>
                </div>

                <div style={{ marginTop: 15 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 10 }}>
                    <strong>Fields</strong>
                    <button
                      type="button"
                      onClick={() => addField(secIdx)}
                      style={{ padding: "6px 12px", fontSize: 12 }}
                    >
                      Add Field
                    </button>
                  </div>

                  {section.fields?.map((field, fieldIdx) => (
                    <div
                      key={fieldIdx}
                      style={{
                        border: "1px solid #eee",
                        borderRadius: 4,
                        padding: 12,
                        marginBottom: 10,
                        background: "#fafafa",
                      }}
                    >
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 8 }}>
                        <input
                          type="text"
                          placeholder="Field Label"
                          value={field.label}
                          onChange={(e) => updateField(secIdx, fieldIdx, { label: e.target.value })}
                          style={{ padding: 6 }}
                        />
                        <input
                          type="text"
                          placeholder="Field Key (slug)"
                          value={field.key}
                          onChange={(e) =>
                            updateField(secIdx, fieldIdx, { key: e.target.value.toLowerCase().replace(/\s+/g, "_") })
                          }
                          style={{ padding: 6 }}
                        />
                      </div>
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8, marginBottom: 8 }}>
                        <select
                          value={field.field_type}
                          onChange={(e) => updateField(secIdx, fieldIdx, { field_type: e.target.value })}
                          style={{ padding: 6 }}
                        >
                          {FIELD_TYPES.map((ft) => (
                            <option key={ft.value} value={ft.value}>
                              {ft.label}
                            </option>
                          ))}
                        </select>
                        <input
                          type="text"
                          placeholder="Unit (optional)"
                          value={field.unit}
                          onChange={(e) => updateField(secIdx, fieldIdx, { unit: e.target.value })}
                          style={{ padding: 6 }}
                        />
                        <label style={{ display: "flex", alignItems: "center", gap: 5 }}>
                          <input
                            type="checkbox"
                            checked={field.required}
                            onChange={(e) => updateField(secIdx, fieldIdx, { required: e.target.checked })}
                          />
                          Required
                        </label>
                      </div>
                      {(field.field_type === "dropdown" || field.field_type === "checklist") && (
                        <div style={{ marginTop: 10 }}>
                          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                            <strong style={{ fontSize: 12 }}>Options</strong>
                            <button
                              type="button"
                              onClick={() => addOption(secIdx, fieldIdx)}
                              style={{ padding: "4px 8px", fontSize: 11 }}
                            >
                              Add Option
                            </button>
                          </div>
                          {field.options?.map((opt, optIdx) => (
                            <div key={optIdx} style={{ display: "flex", gap: 8, marginBottom: 6 }}>
                              <input
                                type="text"
                                placeholder="Label"
                                value={opt.label}
                                onChange={(e) => updateOption(secIdx, fieldIdx, optIdx, { label: e.target.value })}
                                style={{ flex: 1, padding: 4, fontSize: 12 }}
                              />
                              <input
                                type="text"
                                placeholder="Value"
                                value={opt.value}
                                onChange={(e) => updateOption(secIdx, fieldIdx, optIdx, { value: e.target.value })}
                                style={{ flex: 1, padding: 4, fontSize: 12 }}
                              />
                              <button
                                type="button"
                                onClick={() => deleteOption(secIdx, fieldIdx, optIdx)}
                                style={{ padding: "4px 8px", fontSize: 11 }}
                              >
                                Delete
                              </button>
                            </div>
                          ))}
                        </div>
                      )}
                      <button
                        type="button"
                        onClick={() => deleteField(secIdx, fieldIdx)}
                        style={{
                          marginTop: 8,
                          padding: "4px 8px",
                          fontSize: 11,
                          background: "#dc3545",
                          color: "white",
                          border: "none",
                        }}
                      >
                        Delete Field
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <button type="submit" style={{ padding: "10px 20px", fontSize: 14 }}>
            {editing ? "Update" : "Create"} Template
          </button>
        </form>
      )}

      {loading ? (
        <div>Loading...</div>
      ) : (
        <div>
          {templates.map((t) => (
            <div
              key={t.id}
              style={{
                border: "1px solid #ddd",
                borderRadius: 8,
                padding: 15,
                marginBottom: 15,
                background: "white",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <h3 style={{ margin: 0 }}>{t.name}</h3>
                  <div style={{ color: "#666", fontSize: 14 }}>
                    Modality: {t.modality_code || "N/A"} | Sections: {t.sections?.length || 0}
                  </div>
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  <button onClick={() => handleEdit(t)} style={{ padding: "6px 12px", fontSize: 12 }}>
                    Edit
                  </button>
                  <button
                    onClick={() => handlePublish(t.id)}
                    style={{ padding: "6px 12px", fontSize: 12, background: "#28a745", color: "white", border: "none" }}
                  >
                    Publish Version
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      {!loading && templates.length === 0 && <div style={{ marginTop: 20 }}>No templates found.</div>}
    </div>
  );
}
