import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "../ui/auth";
import { apiGet, apiPost } from "../ui/api";
import PageHeader from "../ui/components/PageHeader";
import ErrorAlert from "../ui/components/ErrorAlert";
import Button from "../ui/components/Button";

interface Field {
  id: string;
  label: string;
  key: string;
  type: string;
  required: boolean;
  help_text: string;
  placeholder: string;
  unit: string;
  options?: { label: string; value: string }[];
}

interface Section {
  id: string;
  title: string;
  fields: Field[];
}

interface Report {
  id: string;
  study: { accession: string; patient_name: string; service_name: string };
  template_version: { schema: { sections: Section[] } };
  status: string;
  values: Record<string, any>;
  narrative: string;
  impression: string;
}

export default function ReportEditor() {
  const { reportId } = useParams<{ reportId: string }>();
  const navigate = useNavigate();
  const { token } = useAuth();
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [values, setValues] = useState<Record<string, any>>({});
  const [narrative, setNarrative] = useState("");
  const [impression, setImpression] = useState("");

  useEffect(() => {
    if (!token || !reportId) return;
    loadReport();
  }, [token, reportId]);

  const loadReport = async () => {
    try {
      setLoading(true);
      const data = await apiGet(`/reports/${reportId}/`, token);
      setReport(data);
      setValues(data.values || {});
      setNarrative(data.narrative || "");
      setImpression(data.impression || "");
      setError("");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFieldChange = (key: string, value: any) => {
    setValues({ ...values, [key]: value });
  };

  const handleSaveDraft = async () => {
    if (!token || !reportId) return;
    try {
      setSaving(true);
      await apiPost(`/reports/${reportId}/save_draft/`, token, {
        values,
        narrative,
        impression,
      });
      alert("Draft saved successfully!");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  const handleFinalize = async () => {
    if (!token || !reportId || !confirm("Finalize this report? This will generate a PDF and cannot be undone."))
      return;
    try {
      setSaving(true);
      await apiPost(`/reports/${reportId}/finalize/`, token, {});
      alert("Report finalized! PDF generated.");
      navigate("/studies");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div>Loading report...</div>;
  if (!report) return <div>Report not found</div>;

  const schema = report.template_version?.schema;
  const sections = schema?.sections || [];

  const renderField = (field: Field) => {
    const value = values[field.key] ?? (field.type === "boolean" ? false : field.type === "checklist" ? [] : "");

    switch (field.type) {
      case "short_text":
        return (
          <input
            type="text"
            value={value}
            onChange={(e) => handleFieldChange(field.key, e.target.value)}
            placeholder={field.placeholder}
            required={field.required}
            style={{ width: "100%", padding: 8 }}
          />
        );
      case "number":
        return (
          <input
            type="number"
            value={value}
            onChange={(e) => handleFieldChange(field.key, parseFloat(e.target.value) || 0)}
            placeholder={field.placeholder}
            required={field.required}
            style={{ width: "100%", padding: 8 }}
          />
        );
      case "paragraph":
        return (
          <textarea
            value={value}
            onChange={(e) => handleFieldChange(field.key, e.target.value)}
            placeholder={field.placeholder}
            required={field.required}
            style={{ width: "100%", padding: 8, minHeight: 100 }}
          />
        );
      case "boolean":
        return (
          <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <input
              type="checkbox"
              checked={value}
              onChange={(e) => handleFieldChange(field.key, e.target.checked)}
              required={field.required}
            />
            Yes
          </label>
        );
      case "dropdown":
        return (
          <select
            value={value}
            onChange={(e) => handleFieldChange(field.key, e.target.value)}
            required={field.required}
            style={{ width: "100%", padding: 8 }}
          >
            <option value="">Select...</option>
            {field.options?.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        );
      case "checklist":
        const selected = Array.isArray(value) ? value : [];
        return (
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {field.options?.map((opt) => (
              <label key={opt.value} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <input
                  type="checkbox"
                  checked={selected.includes(opt.value)}
                  onChange={(e) => {
                    const newValue = e.target.checked
                      ? [...selected, opt.value]
                      : selected.filter((v) => v !== opt.value);
                    handleFieldChange(field.key, newValue);
                  }}
                />
                {opt.label}
              </label>
            ))}
          </div>
        );
      default:
        return <div>Unknown field type: {field.type}</div>;
    }
  };

  return (
    <div>
      <PageHeader
        title="Report Editor"
        subtitle={`Accession: ${report.study.accession} | Patient: ${report.study.patient_name} | Service: ${report.study.service_name} | Status: ${report.status}`}
        actions={
          <>
            <Button
              variant="secondary"
              onClick={handleSaveDraft}
              disabled={saving || report.status === "final"}
            >
              {saving ? "Saving..." : "Save Draft"}
            </Button>
            {report.status === "draft" && (
              <Button variant="success" onClick={handleFinalize} disabled={saving}>
                {saving ? "Finalizing..." : "Finalize Report"}
              </Button>
            )}
          </>
        }
      />

      {error && <ErrorAlert message={error} onDismiss={() => setError("")} />}

      {report.status === "final" && (
        <div style={{ background: "#d4edda", border: "1px solid #c3e6cb", padding: 12, borderRadius: 4, marginBottom: 20 }}>
          This report has been finalized and cannot be edited.{" "}
          <a
            href={`${(window as any).__API_BASE__ || "http://localhost:8000"}/api/reports/${reportId}/download_pdf/`}
            target="_blank"
            rel="noopener noreferrer"
          >
            Download PDF
          </a>
        </div>
      )}

      <div style={{ display: "grid", gap: 20 }}>
        {sections.map((section) => (
          <div key={section.id} style={{ border: "1px solid #ddd", borderRadius: 8, padding: 20, background: "white" }}>
            <h2 style={{ marginTop: 0, marginBottom: 15 }}>{section.title}</h2>
            <div style={{ display: "grid", gap: 15 }}>
              {section.fields.map((field) => (
                <div key={field.id}>
                  <label style={{ display: "block", marginBottom: 5, fontWeight: field.required ? "bold" : "normal" }}>
                    {field.label}
                    {field.required && <span style={{ color: "red" }}> *</span>}
                    {field.unit && <span style={{ color: "#666" }}> ({field.unit})</span>}
                  </label>
                  {renderField(field)}
                  {field.help_text && <div style={{ fontSize: 12, color: "#666", marginTop: 4 }}>{field.help_text}</div>}
                </div>
              ))}
            </div>
          </div>
        ))}

        <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 20, background: "white" }}>
          <h2 style={{ marginTop: 0 }}>Narrative</h2>
          <textarea
            value={narrative}
            onChange={(e) => setNarrative(e.target.value)}
            placeholder="Enter findings and description..."
            style={{ width: "100%", padding: 8, minHeight: 150 }}
            disabled={report.status === "final"}
          />
        </div>

        <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 20, background: "white" }}>
          <h2 style={{ marginTop: 0 }}>Impression</h2>
          <textarea
            value={impression}
            onChange={(e) => setImpression(e.target.value)}
            placeholder="Enter impression and conclusion..."
            style={{ width: "100%", padding: 8, minHeight: 100 }}
            disabled={report.status === "final"}
          />
        </div>
      </div>
    </div>
  );
}

