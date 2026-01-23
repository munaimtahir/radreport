import React, { useEffect, useMemo, useState } from "react";
import { useAuth } from "../ui/auth";
import { apiGet, apiPost, apiPatch, apiDelete } from "../ui/api";
import PageHeader from "../ui/components/PageHeader";
import ErrorAlert from "../ui/components/ErrorAlert";
import SuccessAlert from "../ui/components/SuccessAlert";
import Button from "../ui/components/Button";

interface Service {
  id: string;
  name: string;
  code: string;
  category: string;
  is_active: boolean;
  modality_display?: string;
}

interface ReportTemplateSummary {
  id: string;
  name: string;
  code?: string | null;
  category?: string | null;
  is_active: boolean;
  version: number;
}

interface ServiceTemplateLink {
  id: string;
  template: ReportTemplateSummary;
  is_default: boolean;
  is_active: boolean;
}

export default function ServiceTemplates() {
  const { token } = useAuth();
  const [services, setServices] = useState<Service[]>([]);
  const [templates, setTemplates] = useState<ReportTemplateSummary[]>([]);
  const [links, setLinks] = useState<ServiceTemplateLink[]>([]);
  const [selectedService, setSelectedService] = useState<Service | null>(null);
  const [templateId, setTemplateId] = useState("");
  const [setDefault, setSetDefault] = useState(false);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const filteredServices = useMemo(() => {
    return services.filter((service) =>
      (service.name || "").toLowerCase().includes(search.toLowerCase()) ||
      (service.code || "").toLowerCase().includes(search.toLowerCase())
    );
  }, [services, search]);

  const loadServices = async () => {
    if (!token) return;
    const data = await apiGet("/services/?include_inactive=true", token);
    setServices(data.results || data || []);
  };

  const loadTemplates = async () => {
    if (!token) return;
    const data = await apiGet("/report-templates/?include_inactive=false", token);
    setTemplates(data.results || data || []);
  };

  const loadLinks = async (serviceId: string) => {
    if (!token) return;
    const data = await apiGet(`/services/${serviceId}/templates/`, token);
    setLinks(data || []);
  };

  useEffect(() => {
    loadServices();
    loadTemplates();
  }, [token]);

  const handleSelectService = async (service: Service) => {
    setSelectedService(service);
    await loadLinks(service.id);
  };

  const attachTemplate = async () => {
    if (!token || !selectedService || !templateId) return;
    try {
      await apiPost(`/services/${selectedService.id}/templates/`, token, {
        template_id: templateId,
        is_default: setDefault,
        is_active: true,
      });
      setSuccess("Template attached.");
      setTemplateId("");
      setSetDefault(false);
      loadLinks(selectedService.id);
    } catch (e: any) {
      setError(e.message || "Failed to attach template");
    }
  };

  const duplicateAndAttach = async () => {
    if (!token || !selectedService || !templateId) return;
    try {
      const duplicated = await apiPost(`/report-templates/${templateId}/duplicate/`, token, {});
      await apiPost(`/services/${selectedService.id}/templates/`, token, {
        template_id: duplicated.id,
        is_default: setDefault,
        is_active: true,
      });
      setSuccess("Template duplicated and attached.");
      setTemplateId("");
      setSetDefault(false);
      loadTemplates();
      loadLinks(selectedService.id);
    } catch (e: any) {
      setError(e.message || "Failed to duplicate and attach template");
    }
  };

  const makeDefault = async (linkId: string) => {
    if (!token || !selectedService) return;
    await apiPatch(`/services/${selectedService.id}/templates/${linkId}/`, token, { is_default: true });
    loadLinks(selectedService.id);
  };

  const deactivateLink = async (linkId: string) => {
    if (!token || !selectedService) return;
    await apiDelete(`/services/${selectedService.id}/templates/${linkId}/`, token);
    loadLinks(selectedService.id);
  };

  const isUsg = selectedService?.modality_display === 'USG';

  return (
    <div>
      <PageHeader title="Service Template Linking" subtitle="For flat templates only" />

      {/* WARNING: This page links to flat ReportTemplate, not sectioned Template */}
      <div style={{
        padding: 16,
        marginBottom: 20,
        backgroundColor: '#fff3cd',
        border: '1px solid #ffc107',
        borderRadius: 8
      }}>
        <strong>⚠️ For USG Services:</strong> Use backend command to link services to sectioned templates.
        <br />
        Command: <code style={{ background: '#f5f5f5', padding: '2px 6px', borderRadius: 3 }}>
          python manage.py import_usg_template /path/to/template.json --link-service=USG_XXX
        </code>
      </div>

      {error && <ErrorAlert message={error} onDismiss={() => setError("")} />}
      {success && <SuccessAlert message={success} onDismiss={() => setSuccess("")} />}

      <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: 20 }}>
        <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 16 }}>
          <input
            type="text"
            placeholder="Search services..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ width: "100%", padding: 8, marginBottom: 12 }}
          />
          <div style={{ display: "grid", gap: 8, maxHeight: "70vh", overflowY: "auto" }}>
            {filteredServices.map((service) => (
              <div
                key={service.id}
                onClick={() => handleSelectService(service)}
                style={{
                  padding: 10,
                  borderRadius: 6,
                  border: selectedService?.id === service.id ? "2px solid #0B5ED7" : "1px solid #e0e0e0",
                  cursor: "pointer",
                  background: selectedService?.id === service.id ? "#f0f7ff" : "#fff",
                }}
              >
                <div style={{ fontWeight: 600 }}>{service.name}</div>
                <div style={{ fontSize: 12, color: "#666" }}>
                  {service.modality_display || "UNK"} • {service.code}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 16 }}>
          {selectedService ? (
            <>
              <h3 style={{ marginTop: 0 }}>{selectedService.name} <span style={{ fontSize: '0.8em', color: '#666' }}>({selectedService.modality_display})</span></h3>

              {isUsg ? (
                <div style={{
                  padding: 20,
                  backgroundColor: '#ffebec',
                  color: '#dc3545',
                  border: '1px solid #ffc107',
                  borderRadius: 8,
                  marginBottom: 20,
                  textAlign: 'center'
                }}>
                  <h2>🚫 Action Blocked for USG</h2>
                  <p>
                    Ultrasound services require <strong>SECTIONED TEMPLATES</strong>.<br />
                    You cannot link them to flat reports here.
                  </p>
                  <p>
                    Please use the <strong>Template Import Manager</strong> or backend commands.
                  </p>
                </div>
              ) : (
                <div style={{ display: "grid", gap: 12, marginBottom: 16 }}>
                  <select value={templateId} onChange={(e) => setTemplateId(e.target.value)} style={{ padding: 8 }}>
                    <option value="">Select template...</option>
                    {templates.map((template) => (
                      <option key={template.id} value={template.id}>
                        {template.name}
                      </option>
                    ))}
                  </select>
                  <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <input
                      type="checkbox"
                      checked={setDefault}
                      onChange={(e) => setSetDefault(e.target.checked)}
                    />
                    Set as default
                  </label>
                  <div style={{ display: "flex", gap: 8 }}>
                    <Button onClick={attachTemplate} disabled={!templateId}>
                      Attach
                    </Button>
                    <Button variant="secondary" onClick={duplicateAndAttach} disabled={!templateId}>
                      Duplicate & Attach
                    </Button>
                  </div>
                </div>
              )}

              <h4>Linked Templates (Flat)</h4>
              {links.length === 0 ? (
                <p>No flat templates linked.</p>
              ) : (
                <div style={{ display: "grid", gap: 8 }}>
                  {links.map((link) => (
                    <div
                      key={link.id}
                      style={{
                        border: "1px solid #e0e0e0",
                        borderRadius: 6,
                        padding: 10,
                        background: link.is_default ? "#f0f7ff" : "#fff",
                        opacity: isUsg ? 0.6 : 1
                      }}
                    >
                      <div style={{ fontWeight: 600 }}>{link.template.name}</div>
                      <div style={{ fontSize: 12, color: "#666" }}>
                        {link.template.code || "No code"} • {link.template.category || "Uncategorized"}
                      </div>
                      {!isUsg && (
                        <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                          {!link.is_default && (
                            <Button variant="secondary" onClick={() => makeDefault(link.id)}>
                              Set Default
                            </Button>
                          )}
                          <Button variant="secondary" onClick={() => deactivateLink(link.id)}>
                            Deactivate
                          </Button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </>
          ) : (
            <div>Select a service to manage templates.</div>
          )}
        </div>
      </div>
    </div>
  );
}
