import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useAuth } from "../../ui/auth";
import { apiDelete, apiGet, apiPost, apiPut, API_BASE } from "../../ui/api";
import { theme } from "../../theme";
import Button from "../../ui/components/Button";
import ErrorAlert from "../../ui/components/ErrorAlert";
import { downloadFile } from "../../utils/download";
import ImportModal from "../../ui/components/ImportModal";

interface ServiceSummary {
  id: string;
  code: string;
  name: string;
}

interface ProfileSummary {
  id: string;
  code: string;
  name: string;
}

interface ServiceTemplateLink {
  id: string;
  service: string;
  profile: string;
  enforce_single_profile: boolean;
  is_default: boolean;
}

const emptyForm = {
  id: "",
  service: "",
  profile: "",
  enforce_single_profile: true,
  is_default: true,
};

export default function ServiceTemplateLinksList() {
  const { token } = useAuth();
  const [links, setLinks] = useState<ServiceTemplateLink[]>([]);
  const [services, setServices] = useState<ServiceSummary[]>([]);
  const [profiles, setProfiles] = useState<ProfileSummary[]>([]);
  const [form, setForm] = useState(emptyForm);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [isImportModalOpen, setImportModalOpen] = useState(false);

  const loadData = useCallback(async () => {
    if (!token) return;
    try {
      setLoading(true);
      const [linksData, servicesData, profilesData] = await Promise.all([
        apiGet("/reporting/service-profiles/", token),
        apiGet("/catalog/services/", token),
        apiGet("/reporting/profiles/", token),
      ]);
      setLinks(Array.isArray(linksData) ? linksData : linksData.results || []);
      setServices(Array.isArray(servicesData) ? servicesData : servicesData.results || []);
      setProfiles(Array.isArray(profilesData) ? profilesData : profilesData.results || []);
    } catch (e: any) {
      setError(e.message || "Failed to load service template links");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const serviceMap = useMemo(() => {
    return new Map(services.map((service) => [service.id, service]));
  }, [services]);

  const profileMap = useMemo(() => {
    return new Map(profiles.map((profile) => [profile.id, profile]));
  }, [profiles]);

  const resetForm = (clearStatus = true) => {
    setForm(emptyForm);
    if (clearStatus) {
      setStatus(null);
    }
    setError(null);
  };

  const handleSubmit = async () => {
    if (!token) return;
    setError(null);
    setStatus(null);
    try {
      const payload = {
        service: form.service,
        profile: form.profile,
        enforce_single_profile: form.enforce_single_profile,
        is_default: form.is_default,
      };
      if (form.id) {
        await apiPut(`/reporting/service-profiles/${form.id}/`, token, payload);
        setStatus("Link updated.");
      } else {
        await apiPost("/reporting/service-profiles/", token, payload);
        setStatus("Link created.");
      }
      resetForm(false);
      loadData();
    } catch (e: any) {
      setError(e.message || "Failed to save link");
    }
  };

  const handleEdit = (link: ServiceTemplateLink) => {
    setForm({ ...link });
    setStatus(null);
    setError(null);
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm("Delete this link?")) return;
    try {
      await apiDelete(`/reporting/service-profiles/${id}/`, token);
      loadData();
    } catch (e: any) {
      setError(e.message || "Failed to delete link");
    }
  };

  const handleImportSuccess = () => {
    setImportModalOpen(false);
    loadData();
  };

  return (
    <div style={{ padding: 20 }}>
      <ImportModal
        isOpen={isImportModalOpen}
        onClose={() => setImportModalOpen(false)}
        onImportSuccess={handleImportSuccess}
        importUrl="/reporting/service-profiles/import-csv/"
        title="Import Service-Template Links"
      />
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <h1 style={{ fontSize: 24, margin: 0 }}>Service-Template Links</h1>
        <div style={{ display: "flex", gap: 12 }}>
          <Button
            variant="secondary"
            onClick={() => downloadFile(`${API_BASE}/reporting/service-profiles/template-csv/`, "service_template_links_template.csv", token)}
          >
            Download CSV Template
          </Button>
          <Button
            variant="secondary"
            onClick={() => downloadFile(`${API_BASE}/reporting/service-profiles/export-csv/`, "service_template_links_export.csv", token)}
          >
            Export CSV
          </Button>
          <Button variant="secondary" onClick={() => setImportModalOpen(true)}>
            Import CSV
          </Button>
        </div>
      </div>

      {error && <ErrorAlert message={error} />}
      {status && <div style={{ marginBottom: 12, color: theme.colors.textSecondary }}>{status}</div>}
      
      <div style={{ backgroundColor: "white", borderRadius: theme.radius.lg, border: `1px solid ${theme.colors.border}`, padding: 20, marginBottom: 24 }}>
        <h3 style={{ marginTop: 0 }}>{form.id ? "Edit Link" : "Create Link"}</h3>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <div>
            <label style={{ display: "block", marginBottom: 5 }}>Service</label>
            <select
              value={form.service}
              onChange={(event) => setForm({ ...form, service: event.target.value })}
              style={{ width: "100%", padding: 8 }}
            >
              <option value="">Select service</option>
              {services.map((service) => (
                <option key={service.id} value={service.id}>
                  {service.code ? `${service.code} - ` : ""}{service.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label style={{ display: "block", marginBottom: 5 }}>Template</label>
            <select
              value={form.profile}
              onChange={(event) => setForm({ ...form, profile: event.target.value })}
              style={{ width: "100%", padding: 8 }}
            >
              <option value="">Select template</option>
              {profiles.map((profile) => (
                <option key={profile.id} value={profile.id}>
                  {profile.code} - {profile.name}
                </option>
              ))}
            </select>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <input
                type="checkbox"
                checked={form.enforce_single_profile}
                onChange={(event) => setForm({ ...form, enforce_single_profile: event.target.checked })}
              />
              Enforce single profile
            </label>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <input
                type="checkbox"
                checked={form.is_default}
                onChange={(event) => setForm({ ...form, is_default: event.target.checked })}
              />
              Default profile
            </label>
          </div>
        </div>
        <div style={{ marginTop: 16, display: "flex", justifyContent: "flex-end", gap: 12 }}>
          {form.id && (
            <Button variant="secondary" onClick={() => resetForm()}>
              Cancel
            </Button>
          )}
          <Button
            variant="primary"
            onClick={handleSubmit}
            disabled={!form.service || !form.profile}
          >
            {form.id ? "Update Link" : "Create Link"}
          </Button>
        </div>
      </div>

      <div style={{ backgroundColor: "white", borderRadius: theme.radius.lg, border: `1px solid ${theme.colors.border}`, overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ backgroundColor: theme.colors.backgroundGray, borderBottom: `1px solid ${theme.colors.border}` }}>
              <th style={{ padding: 12, textAlign: "left" }}>Service</th>
              <th style={{ padding: 12, textAlign: "left" }}>Template</th>
              <th style={{ padding: 12, textAlign: "left" }}>Enforced</th>
              <th style={{ padding: 12, textAlign: "left" }}>Default</th>
              <th style={{ padding: 12, textAlign: "right" }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {links.map((link) => {
              const service = serviceMap.get(link.service);
              const profile = profileMap.get(link.profile);
              return (
                <tr key={link.id} style={{ borderBottom: `1px solid ${theme.colors.borderLight}` }}>
                  <td style={{ padding: 12 }}>
                    {service ? `${service.code ? `${service.code} - ` : ""}${service.name}` : link.service}
                  </td>
                  <td style={{ padding: 12 }}>
                    {profile ? `${profile.code} - ${profile.name}` : link.profile}
                  </td>
                  <td style={{ padding: 12 }}>{link.enforce_single_profile ? "Yes" : "No"}</td>
                  <td style={{ padding: 12 }}>{link.is_default ? "Yes" : "No"}</td>
                  <td style={{ padding: 12, textAlign: "right" }}>
                    <Button variant="secondary" onClick={() => handleEdit(link)} style={{ marginRight: 8 }}>
                      Edit
                    </Button>
                    <Button variant="secondary" onClick={() => handleDelete(link.id)} style={{ color: theme.colors.danger }}>
                      Delete
                    </Button>
                  </td>
                </tr>
              );
            })}
            {!loading && links.length === 0 && (
              <tr>
                <td colSpan={5} style={{ padding: 20, textAlign: "center", color: theme.colors.textSecondary }}>
                  No links found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

