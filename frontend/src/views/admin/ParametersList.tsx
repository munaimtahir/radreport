import React, { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../ui/auth";
import { apiGet, apiUpload, API_BASE } from "../../ui/api";
import { theme } from "../../theme";
import Button from "../../ui/components/Button";
import ErrorAlert from "../../ui/components/ErrorAlert";

interface ProfileSummary {
  id: string;
  code: string;
  name: string;
  modality: string;
}

interface ParameterItem {
  id?: string;
  parameter_id?: string;
  section: string;
  name: string;
  parameter_type?: string;
  type?: string;
  order?: number;
  is_required?: boolean;
}

export default function ParametersList() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [profiles, setProfiles] = useState<ProfileSummary[]>([]);
  const [selectedProfileId, setSelectedProfileId] = useState("");
  const [parameters, setParameters] = useState<ParameterItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const importInputRef = useRef<HTMLInputElement | null>(null);

  const loadProfiles = useCallback(async () => {
    if (!token) return;
    try {
      const data = await apiGet("/reporting/profiles/", token);
      const list = Array.isArray(data) ? data : data.results || [];
      setProfiles(list);
      if (!selectedProfileId && list.length > 0) {
        setSelectedProfileId(list[0].id);
      }
    } catch (e: any) {
      setError(e.message || "Failed to load templates");
    }
  }, [token, selectedProfileId]);

  const loadParameters = useCallback(async () => {
    if (!token || !selectedProfileId) return;
    try {
      setLoading(true);
      const data = await apiGet(`/reporting/profiles/${selectedProfileId}/`, token);
      setParameters(data.parameters || []);
    } catch (e: any) {
      setError(e.message || "Failed to load parameters");
    } finally {
      setLoading(false);
    }
  }, [selectedProfileId, token]);

  useEffect(() => {
    loadProfiles();
  }, [loadProfiles]);

  useEffect(() => {
    if (selectedProfileId) {
      loadParameters();
    }
  }, [loadParameters, selectedProfileId]);

  const downloadCsv = async () => {
    if (!token || !selectedProfileId) return;
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/reporting/profiles/${selectedProfileId}/parameters-csv/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || "Download failed");
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "template_parameters.csv";
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (e: any) {
      setError(e.message || "Download failed");
    }
  };

  const triggerImport = () => {
    importInputRef.current?.click();
  };

  const handleImport = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !selectedProfileId) return;
    setStatus(null);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const result = await apiUpload(`/reporting/profiles/${selectedProfileId}/parameters-csv/`, token, formData);
      setStatus(`Import complete. Added ${result.fields_created} and updated ${result.fields_updated} parameters.`);
      loadParameters();
    } catch (e: any) {
      setError(e.message || "Import failed");
    } finally {
      event.target.value = "";
    }
  };

  const activeProfile = profiles.find((profile) => profile.id === selectedProfileId);

  return (
    <div style={{ padding: 20 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <h1 style={{ fontSize: 24, margin: 0 }}>Parameters</h1>
        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <select
            value={selectedProfileId}
            onChange={(event) => setSelectedProfileId(event.target.value)}
            style={{ padding: "8px 12px", borderRadius: 4, border: "1px solid #ccc", minWidth: 220 }}
          >
            <option value="">Select Template</option>
            {profiles.map((profile) => (
              <option key={profile.id} value={profile.id}>
                {profile.code} - {profile.name}
              </option>
            ))}
          </select>
          <Button variant="secondary" onClick={downloadCsv} disabled={!selectedProfileId}>
            Export CSV
          </Button>
          <Button variant="secondary" onClick={triggerImport} disabled={!selectedProfileId}>
            Import CSV
          </Button>
          <Button
            variant="primary"
            onClick={() => selectedProfileId && navigate(`/settings/templates/${selectedProfileId}`)}
            disabled={!selectedProfileId}
          >
            Manage Template
          </Button>
        </div>
      </div>

      {error && <ErrorAlert message={error} />}
      {status && <div style={{ marginBottom: 12, color: theme.colors.textSecondary }}>{status}</div>}
      <input ref={importInputRef} type="file" accept=".csv" style={{ display: "none" }} onChange={handleImport} />

      <div style={{ marginBottom: 12, color: theme.colors.textSecondary }}>
        {activeProfile ? (
          <span>
            Viewing parameters for <strong>{activeProfile.code}</strong> ({activeProfile.modality})
          </span>
        ) : (
          "Select a template to view parameters."
        )}
      </div>

      <div style={{ backgroundColor: "white", borderRadius: theme.radius.lg, border: `1px solid ${theme.colors.border}`, overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ backgroundColor: theme.colors.backgroundGray, borderBottom: `1px solid ${theme.colors.border}` }}>
              <th style={{ padding: 12, textAlign: "left" }}>Order</th>
              <th style={{ padding: 12, textAlign: "left" }}>Section</th>
              <th style={{ padding: 12, textAlign: "left" }}>Name</th>
              <th style={{ padding: 12, textAlign: "left" }}>Type</th>
              <th style={{ padding: 12, textAlign: "left" }}>Required</th>
            </tr>
          </thead>
          <tbody>
            {parameters.map((param) => (
              <tr key={param.parameter_id || param.id} style={{ borderBottom: `1px solid ${theme.colors.borderLight}` }}>
                <td style={{ padding: 12 }}>{param.order ?? "-"}</td>
                <td style={{ padding: 12 }}>{param.section}</td>
                <td style={{ padding: 12 }}>{param.name}</td>
                <td style={{ padding: 12 }}>{param.type || param.parameter_type}</td>
                <td style={{ padding: 12 }}>{param.is_required ? "Yes" : "No"}</td>
              </tr>
            ))}
            {!loading && parameters.length === 0 && (
              <tr>
                <td colSpan={5} style={{ padding: 20, textAlign: "center", color: theme.colors.textSecondary }}>
                  No parameters found for this template.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
