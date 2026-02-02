import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useAuth } from "../../ui/auth";
import { apiGet } from "../../ui/api";
import { theme } from "../../theme";
import Button from "../../ui/components/Button";
import ErrorAlert from "../../ui/components/ErrorAlert";
import SuccessAlert from "../../ui/components/SuccessAlert";
import {
  activateTemplateV2,
  createServiceTemplateV2,
  createTemplateV2,
  listServiceTemplatesV2,
  listTemplatesV2,
  setDefaultServiceTemplateV2,
  toggleServiceTemplateV2Active,
} from "../../services/api";

interface TemplateV2 {
  id: string;
  code?: string;
  name: string;
  status?: string;
  version?: number;
  is_active?: boolean;
}

interface ServiceSummary {
  id: string;
  code?: string;
  name: string;
}

interface ServiceTemplateV2 {
  id: string;
  service: string;
  template: string;
  is_active: boolean;
  is_default?: boolean;
}

const emptyTemplateForm = {
  code: "",
  name: "",
  jsonSchema: "",
  uiSchema: "",
};

const emptyMappingForm = {
  service: "",
  template: "",
  is_active: true,
};

export default function TemplatesV2() {
  const { token } = useAuth();
  const [templates, setTemplates] = useState<TemplateV2[]>([]);
  const [services, setServices] = useState<ServiceSummary[]>([]);
  const [mappings, setMappings] = useState<ServiceTemplateV2[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [templateForm, setTemplateForm] = useState(emptyTemplateForm);
  const [mappingForm, setMappingForm] = useState(emptyMappingForm);
  const [conflictTemplateId, setConflictTemplateId] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    if (!token) return;
    try {
      setLoading(true);
      setError(null);
      const [templateData, serviceData, mappingData] = await Promise.all([
        listTemplatesV2(token),
        apiGet("/services/", token),
        listServiceTemplatesV2(token),
      ]);
      setTemplates(Array.isArray(templateData) ? templateData : templateData.results || []);
      setServices(Array.isArray(serviceData) ? serviceData : serviceData.results || []);
      setMappings(Array.isArray(mappingData) ? mappingData : mappingData.results || []);
    } catch (e: any) {
      setError(e.message || "Failed to load TemplateV2 data");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const templateMap = useMemo(() => new Map(templates.map((template) => [template.id, template])), [templates]);
  const serviceMap = useMemo(() => new Map(services.map((service) => [service.id, service])), [services]);

  const parseJson = (value: string, label: string) => {
    if (!value.trim()) return null;
    try {
      return JSON.parse(value);
    } catch {
      throw new Error(`Invalid JSON in ${label}.`);
    }
  };

  const handleCreateTemplate = async () => {
    if (!token) return;
    setError(null);
    setSuccess(null);
    try {
      const jsonSchema = parseJson(templateForm.jsonSchema, "JSON schema");
      const uiSchema = parseJson(templateForm.uiSchema, "UI schema");
      const payload = {
        code: templateForm.code,
        name: templateForm.name,
        json_schema: jsonSchema,
        ui_schema: uiSchema,
      };
      await createTemplateV2(token, payload);
      setSuccess("TemplateV2 created.");
      setTemplateForm(emptyTemplateForm);
      loadData();
    } catch (e: any) {
      setError(e.message || "Failed to create TemplateV2");
    }
  };

  const handleActivate = async (templateId: string, force = false) => {
    if (!token) return;
    setError(null);
    setSuccess(null);
    try {
      await activateTemplateV2(token, templateId, force);
      setConflictTemplateId(null);
      setSuccess("Template activated.");
      loadData();
    } catch (e: any) {
      if (e.status === 409) {
        setConflictTemplateId(templateId);
        setError("Conflict while activating template.");
      } else {
        setError(e.message || "Failed to activate template");
      }
    }
  };

  const handleCreateMapping = async () => {
    if (!token) return;
    setError(null);
    setSuccess(null);
    try {
      const payload = {
        service: mappingForm.service,
        template: mappingForm.template,
        is_active: mappingForm.is_active,
      };
      await createServiceTemplateV2(token, payload);
      setSuccess("Service mapping created.");
      setMappingForm(emptyMappingForm);
      loadData();
    } catch (e: any) {
      setError(e.message || "Failed to create mapping");
    }
  };

  const handleSetDefault = async (mappingId: string) => {
    if (!token) return;
    setError(null);
    setSuccess(null);
    try {
      await setDefaultServiceTemplateV2(token, mappingId);
      setSuccess("Default mapping set.");
      loadData();
    } catch (e: any) {
      setError(e.message || "Failed to set default mapping");
    }
  };

  const handleToggleActive = async (mapping: ServiceTemplateV2) => {
    if (!token) return;
    setError(null);
    setSuccess(null);
    try {
      await toggleServiceTemplateV2Active(token, mapping.id, !mapping.is_active);
      setSuccess("Mapping updated.");
      loadData();
    } catch (e: any) {
      setError(e.message || "Failed to update mapping");
    }
  };

  return (
    <div style={{ padding: 20 }}>
      <div style={{ marginBottom: 20 }}>
        <h1 style={{ fontSize: 24, margin: 0 }}>Templates V2</h1>
        <p style={{ color: theme.colors.textSecondary, marginTop: 6 }}>
          Manage schema-driven templates and service mappings.
        </p>
      </div>

      {error && <ErrorAlert message={error} />}
      {success && <SuccessAlert message={success} />}

      {loading ? (
        <div>Loading...</div>
      ) : (
        <>
          <section style={{ marginBottom: 32 }}>
            <h2 style={{ fontSize: 20, marginBottom: 12 }}>Create TemplateV2</h2>
            <div
              style={{
                backgroundColor: "white",
                borderRadius: theme.radius.lg,
                border: `1px solid ${theme.colors.border}`,
                padding: 20,
                display: "grid",
                gap: 16,
              }}
            >
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                <div>
                  <label style={{ display: "block", marginBottom: 6 }}>Code</label>
                  <input
                    type="text"
                    value={templateForm.code}
                    onChange={(event) => setTemplateForm((prev) => ({ ...prev, code: event.target.value }))}
                    style={{ width: "100%", padding: 8 }}
                  />
                </div>
                <div>
                  <label style={{ display: "block", marginBottom: 6 }}>Name</label>
                  <input
                    type="text"
                    value={templateForm.name}
                    onChange={(event) => setTemplateForm((prev) => ({ ...prev, name: event.target.value }))}
                    style={{ width: "100%", padding: 8 }}
                  />
                </div>
              </div>
              <div>
                <label style={{ display: "block", marginBottom: 6 }}>JSON Schema</label>
                <textarea
                  value={templateForm.jsonSchema}
                  onChange={(event) => setTemplateForm((prev) => ({ ...prev, jsonSchema: event.target.value }))}
                  style={{ width: "100%", minHeight: 140, padding: 8, fontFamily: "monospace" }}
                  placeholder="Paste JSON schema..."
                />
              </div>
              <div>
                <label style={{ display: "block", marginBottom: 6 }}>UI Schema</label>
                <textarea
                  value={templateForm.uiSchema}
                  onChange={(event) => setTemplateForm((prev) => ({ ...prev, uiSchema: event.target.value }))}
                  style={{ width: "100%", minHeight: 120, padding: 8, fontFamily: "monospace" }}
                  placeholder="Optional UI schema JSON..."
                />
              </div>
              <div style={{ display: "flex", justifyContent: "flex-end" }}>
                <Button variant="primary" onClick={handleCreateTemplate}>
                  Create Template
                </Button>
              </div>
            </div>
          </section>

          <section style={{ marginBottom: 32 }}>
            <h2 style={{ fontSize: 20, marginBottom: 12 }}>Templates</h2>
            <div style={{ backgroundColor: "white", borderRadius: theme.radius.lg, border: `1px solid ${theme.colors.border}`, overflow: "hidden" }}>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ backgroundColor: theme.colors.backgroundGray, borderBottom: `1px solid ${theme.colors.border}` }}>
                    <th style={{ textAlign: "left", padding: 12, fontSize: 12 }}>Code</th>
                    <th style={{ textAlign: "left", padding: 12, fontSize: 12 }}>Name</th>
                    <th style={{ textAlign: "left", padding: 12, fontSize: 12 }}>Version</th>
                    <th style={{ textAlign: "left", padding: 12, fontSize: 12 }}>Status</th>
                    <th style={{ textAlign: "right", padding: 12, fontSize: 12 }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {templates.map((template) => (
                    <tr key={template.id} style={{ borderBottom: `1px solid ${theme.colors.borderLight}` }}>
                      <td style={{ padding: 12 }}>{template.code || "-"}</td>
                      <td style={{ padding: 12 }}>{template.name}</td>
                      <td style={{ padding: 12 }}>{template.version ?? "-"}</td>
                      <td style={{ padding: 12 }}>{template.status || (template.is_active ? "active" : "-")}</td>
                      <td style={{ padding: 12, textAlign: "right" }}>
                        <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, alignItems: "center" }}>
                          <Button variant="secondary" onClick={() => handleActivate(template.id)}>
                            Activate
                          </Button>
                          {conflictTemplateId === template.id && (
                            <Button
                              variant="primary"
                              onClick={() => handleActivate(template.id, true)}
                              style={{ backgroundColor: theme.colors.danger, borderColor: theme.colors.danger }}
                            >
                              Force Activate
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section>
            <h2 style={{ fontSize: 20, marginBottom: 12 }}>Service Template Mappings</h2>
            <div
              style={{
                backgroundColor: "white",
                borderRadius: theme.radius.lg,
                border: `1px solid ${theme.colors.border}`,
                padding: 20,
                marginBottom: 20,
              }}
            >
              <h3 style={{ marginTop: 0 }}>Create Mapping</h3>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                <div>
                  <label style={{ display: "block", marginBottom: 6 }}>Service</label>
                  <select
                    value={mappingForm.service}
                    onChange={(event) => setMappingForm((prev) => ({ ...prev, service: event.target.value }))}
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
                  <label style={{ display: "block", marginBottom: 6 }}>Template</label>
                  <select
                    value={mappingForm.template}
                    onChange={(event) => setMappingForm((prev) => ({ ...prev, template: event.target.value }))}
                    style={{ width: "100%", padding: 8 }}
                  >
                    <option value="">Select template</option>
                    {templates.map((template) => (
                      <option key={template.id} value={template.id}>
                        {template.code ? `${template.code} - ` : ""}{template.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <input
                    type="checkbox"
                    checked={mappingForm.is_active}
                    onChange={(event) => setMappingForm((prev) => ({ ...prev, is_active: event.target.checked }))}
                  />
                  <span>Active</span>
                </div>
              </div>
              <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 16 }}>
                <Button variant="primary" onClick={handleCreateMapping}>
                  Create Mapping
                </Button>
              </div>
            </div>

            <div style={{ backgroundColor: "white", borderRadius: theme.radius.lg, border: `1px solid ${theme.colors.border}`, overflow: "hidden" }}>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ backgroundColor: theme.colors.backgroundGray, borderBottom: `1px solid ${theme.colors.border}` }}>
                    <th style={{ textAlign: "left", padding: 12, fontSize: 12 }}>Service</th>
                    <th style={{ textAlign: "left", padding: 12, fontSize: 12 }}>Template</th>
                    <th style={{ textAlign: "left", padding: 12, fontSize: 12 }}>Status</th>
                    <th style={{ textAlign: "right", padding: 12, fontSize: 12 }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {mappings.map((mapping) => {
                    const service = serviceMap.get(mapping.service);
                    const template = templateMap.get(mapping.template);
                    return (
                      <tr key={mapping.id} style={{ borderBottom: `1px solid ${theme.colors.borderLight}` }}>
                        <td style={{ padding: 12 }}>
                          {service ? `${service.code ? `${service.code} - ` : ""}${service.name}` : mapping.service}
                        </td>
                        <td style={{ padding: 12 }}>
                          {template ? `${template.code ? `${template.code} - ` : ""}${template.name}` : mapping.template}
                        </td>
                        <td style={{ padding: 12 }}>
                          {mapping.is_default ? "Default" : mapping.is_active ? "Active" : "Inactive"}
                        </td>
                        <td style={{ padding: 12, textAlign: "right" }}>
                          <div style={{ display: "flex", justifyContent: "flex-end", gap: 8 }}>
                            <Button variant="secondary" onClick={() => handleSetDefault(mapping.id)}>
                              Set Default
                            </Button>
                            <Button variant="secondary" onClick={() => handleToggleActive(mapping)}>
                              {mapping.is_active ? "Deactivate" : "Activate"}
                            </Button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </div>
  );
}
