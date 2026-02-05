import React, { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../ui/auth";
import { apiGet, API_BASE } from "../../ui/api";
import { theme } from "../../theme";
import Button from "../../ui/components/Button";
import ErrorAlert from "../../ui/components/ErrorAlert";
import { downloadFile } from "../../utils/download";
import ImportModal from "../../ui/components/ImportModal";

interface ProfileSummary {
  id: string;
  code: string;
  name: string;
}

interface ParameterItem {
  id: string;
  profile: string;
  section: string;
  name: string;
  parameter_type: string;
  order: number;
  is_required: boolean;
}

export default function ParametersList() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [profiles, setProfiles] = useState<ProfileSummary[]>([]);
  const [selectedProfileId, setSelectedProfileId] = useState("");
  const [parameters, setParameters] = useState<ParameterItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isImportModalOpen, setImportModalOpen] = useState(false);

  const loadProfiles = useCallback(async () => {
    if (!token) return;
    try {
      const data = await apiGet("/reporting/profiles/", token);
      const list = Array.isArray(data) ? data : data.results || [];
      setProfiles(list);
    } catch (e: any) {
      setError(e.message || "Failed to load templates");
    }
  }, [token]);

  const loadParameters = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    try {
      const url = selectedProfileId ? `/reporting/parameters/?profile=${selectedProfileId}` : "/reporting/parameters/";
      const data = await apiGet(url, token);
      setParameters(Array.isArray(data) ? data : data.results || []);
    } catch (e: any) {
      setError(e.message || "Failed to load parameters");
    } finally {
      setLoading(false);
    }
  }, [selectedProfileId, token]);

  useEffect(() => {
    loadProfiles();
    loadParameters();
  }, [loadProfiles, loadParameters]);

  const handleImportSuccess = () => {
    setImportModalOpen(false);
    loadParameters();
  };

  const activeProfile = profiles.find((profile) => profile.id === selectedProfileId);

  return (
    <div style={{ padding: 20 }}>
      <ImportModal
        isOpen={isImportModalOpen}
        onClose={() => setImportModalOpen(false)}
        onImportSuccess={handleImportSuccess}
        importUrl="/reporting/parameters/import-csv/"
        title="Import Report Parameters"
      />
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <h1 style={{ fontSize: 24, margin: 0 }}>Parameters</h1>
        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <select
            value={selectedProfileId}
            onChange={(event) => setSelectedProfileId(event.target.value)}
            style={{ padding: "8px 12px", borderRadius: 4, border: "1px solid #ccc", minWidth: 220 }}
          >
            <option value="">All Templates</option>
            {profiles.map((profile) => (
              <option key={profile.id} value={profile.id}>
                {profile.code} - {profile.name}
              </option>
            ))}
          </select>
          <Button variant="secondary" onClick={() => downloadFile("/reporting/parameters/template-csv/", "parameters_template.csv", token)}>
            Download Template
          </Button>
          <Button variant="secondary" onClick={() => downloadFile("/reporting/parameters/export-csv/", "parameters_export.csv", token)}>
            Export CSV
          </Button>
          <Button variant="secondary" onClick={() => setImportModalOpen(true)}>
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

      <div style={{ marginBottom: 12, color: theme.colors.textSecondary }}>
        {activeProfile ? (
          <span>
            Viewing parameters for <strong>{activeProfile.code}</strong>
          </span>
        ) : (
          "Viewing parameters for all templates."
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
              <tr key={param.id} style={{ borderBottom: `1px solid ${theme.colors.borderLight}` }}>
                <td style={{ padding: 12 }}>{param.order ?? "-"}</td>
                <td style={{ padding: 12 }}>{param.section}</td>
                <td style={{ padding: 12 }}>{param.name}</td>
                <td style={{ padding: 12 }}>{param.parameter_type}</td>
                <td style={{ padding: 12 }}>{param.is_required ? "Yes" : "No"}</td>
              </tr>
            ))}
            {!loading && parameters.length === 0 && (
              <tr>
                <td colSpan={5} style={{ padding: 20, textAlign: "center", color: theme.colors.textSecondary }}>
                  No parameters found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

