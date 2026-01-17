import React, { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { apiGet, apiPost } from "../ui/api";
import { useAuth } from "../ui/auth";
import PageHeader from "../ui/components/PageHeader";
import ErrorAlert from "../ui/components/ErrorAlert";
import SuccessAlert from "../ui/components/SuccessAlert";
import Button from "../ui/components/Button";
import { theme } from "../theme";

interface Patient {
  id: string;
  mrn: string;
  name: string;
  age?: number;
  gender?: string;
  phone?: string;
  address?: string;
  created_at?: string;
}

interface ServiceVisitItem {
  id: string;
  service_name_snapshot?: string;
  service_code?: string;
  department_snapshot?: string;
}

interface ServiceVisit {
  id: string;
  visit_id: string;
  patient: string;
  registered_at?: string;
  status?: string;
  items?: ServiceVisitItem[];
  created_by_name?: string;
}

interface UsgStudy {
  id: string;
  service_code: string;
  status: string;
  created_at: string;
  published_at?: string;
}

interface Service {
  id: string;
  name: string;
  code: string;
  price?: number | string;
  charges?: number | string;
  modality?: {
    code: string;
  };
}

const formatDateTime = (value?: string) => {
  if (!value) return "-";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString();
};

export default function UsgPatientProfilePage() {
  const { patientId } = useParams();
  const navigate = useNavigate();
  const { token } = useAuth();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [visits, setVisits] = useState<ServiceVisit[]>([]);
  const [visitReports, setVisitReports] = useState<Record<string, UsgStudy[]>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [expandedVisitIds, setExpandedVisitIds] = useState<string[]>([]);
  const [showVisitModal, setShowVisitModal] = useState(false);
  const [services, setServices] = useState<Service[]>([]);
  const [selectedServiceId, setSelectedServiceId] = useState("");

  useEffect(() => {
    if (!token || !patientId) return;
    const loadProfile = async () => {
      setLoading(true);
      setError("");
      try {
        const patientData = await apiGet(`/patients/${patientId}/`, token);
        setPatient(patientData);
      } catch (err: any) {
        setError(err.message || "Failed to load patient profile");
      } finally {
        setLoading(false);
      }
    };
    loadProfile();
  }, [token, patientId]);

  useEffect(() => {
    if (!token || !patient?.mrn) return;
    const loadVisits = async () => {
      setLoading(true);
      setError("");
      try {
        const visitsData = await apiGet(`/workflow/visits/?search=${encodeURIComponent(patient.mrn)}`, token);
        const patientVisits = (visitsData.results || visitsData || []).filter(
          (visit: ServiceVisit) => visit?.patient === patient.id
        );
        setVisits(patientVisits);
      } catch (err: any) {
        setError(err.message || "Failed to load visits");
      } finally {
        setLoading(false);
      }
    };
    loadVisits();
  }, [token, patient]);

  useEffect(() => {
    if (!token || visits.length === 0) return;
    const loadReports = async () => {
      try {
        const results = await Promise.all(
          visits.map((visit) => apiGet(`/visits/${visit.id}/usg-reports/`, token))
        );
        const reportMap: Record<string, UsgStudy[]> = {};
        visits.forEach((visit, index) => {
          reportMap[visit.id] = results[index] || [];
        });
        setVisitReports(reportMap);
      } catch (err: any) {
        setError(err.message || "Failed to load USG reports");
      }
    };
    loadReports();
  }, [token, visits]);

  const loadServices = async () => {
    if (!token) return;
    try {
      const data = await apiGet("/services/", token);
      const list = (data.results || data || []).filter(
        (service: Service) => service.modality?.code === "USG"
      );
      setServices(list);
      if (list.length > 0) {
        setSelectedServiceId(list[0].id);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load services");
    }
  };

  const createVisit = async () => {
    if (!token || !patient) return;
    if (!selectedServiceId) {
      setError("Select a USG service to create a visit.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const selectedService = services.find((service) => service.id === selectedServiceId);
      const priceValue = selectedService?.price ?? selectedService?.charges ?? 0;
      const subtotal = typeof priceValue === "number" ? priceValue : parseFloat(priceValue as any) || 0;
      const payload = {
        patient_id: patient.id,
        service_ids: [selectedServiceId],
        subtotal,
        total_amount: subtotal,
        discount: 0,
        discount_percentage: 0,
        net_amount: subtotal,
        amount_paid: subtotal,
        payment_method: "cash",
      };
      const visit = await apiPost("/workflow/visits/create_visit/", token, payload);
      setSuccess(`Visit ${visit.visit_id} created.`);
      setShowVisitModal(false);
      navigate(`/usg/visits/${visit.id}`);
    } catch (err: any) {
      setError(err.message || "Failed to create visit");
    } finally {
      setLoading(false);
    }
  };

  const toggleVisit = (visitId: string) => {
    setExpandedVisitIds((prev) =>
      prev.includes(visitId) ? prev.filter((id) => id !== visitId) : [...prev, visitId]
    );
  };

  const allReports = useMemo(() => {
    return visits.flatMap((visit) => (visitReports[visit.id] || []).map((report) => ({
      ...report,
      visitId: visit.id,
      visitNumber: visit.visit_id,
    })));
  }, [visits, visitReports]);

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto" }}>
      <PageHeader title="Patient Profile" subtitle="USG reporting history" />

      {error && <ErrorAlert message={error} onDismiss={() => setError("")} />}
      {success && <SuccessAlert message={success} onDismiss={() => setSuccess("")} />}

      {patient && (
        <div style={{
          border: `1px solid ${theme.colors.border}`,
          borderRadius: theme.radius.md,
          padding: 20,
          backgroundColor: theme.colors.background,
          marginBottom: 20,
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 16 }}>
            <div>
              <h2 style={{ margin: 0 }}>{patient.name}</h2>
              <div style={{ color: theme.colors.textSecondary, marginTop: 4 }}>
                MRN: {patient.mrn} {patient.gender ? `• ${patient.gender}` : ""} {patient.age ? `• ${patient.age}y` : ""}
              </div>
              <div style={{ color: theme.colors.textSecondary, marginTop: 4 }}>
                {patient.phone ? `Phone: ${patient.phone}` : ""} {patient.address ? `• ${patient.address}` : ""}
              </div>
            </div>
            <div style={{ display: "flex", alignItems: "center" }}>
              <Button
                onClick={() => {
                  setShowVisitModal(true);
                  loadServices();
                }}
                disabled={loading}
              >
                {loading ? "Loading..." : "Create New Visit"}
              </Button>
            </div>
          </div>
        </div>
      )}

      <div style={{
        display: "grid",
        gridTemplateColumns: "minmax(0, 2fr) minmax(280px, 1fr)",
        gap: 20,
      }}>
        <div style={{
          border: `1px solid ${theme.colors.border}`,
          borderRadius: theme.radius.md,
          backgroundColor: theme.colors.background,
        }}>
          <div style={{ padding: "12px 16px", borderBottom: `1px solid ${theme.colors.border}` }}>
            <strong>Visit Timeline</strong>
          </div>
          <div style={{ padding: 16 }}>
            {visits.length === 0 && (
              <div style={{ color: theme.colors.textTertiary }}>No visits yet.</div>
            )}
            {visits.map((visit) => {
              const reports = visitReports[visit.id] || [];
              const isExpanded = expandedVisitIds.includes(visit.id);
              return (
                <div
                  key={visit.id}
                  style={{
                    border: `1px solid ${theme.colors.borderLight}`,
                    borderRadius: theme.radius.base,
                    padding: 14,
                    marginBottom: 12,
                    backgroundColor: isExpanded ? theme.colors.brandBlueSoft : "transparent",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                    <div>
                      <div style={{ fontWeight: theme.typography.fontWeight.semibold }}>
                        Visit {visit.visit_id}
                      </div>
                      <div style={{ color: theme.colors.textSecondary, fontSize: 13, marginTop: 4 }}>
                        {formatDateTime(visit.registered_at)}
                      </div>
                      <div style={{ color: theme.colors.textTertiary, fontSize: 12, marginTop: 4 }}>
                        Status: {visit.status || "-"} {visit.created_by_name ? `• Created by ${visit.created_by_name}` : ""}
                      </div>
                      <div style={{ color: theme.colors.textTertiary, fontSize: 12, marginTop: 4 }}>
                        USG reports: {reports.length}
                      </div>
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                      <Button variant="secondary" onClick={() => navigate(`/usg/visits/${visit.id}`)}>
                        Open Visit
                      </Button>
                      <Button variant="secondary" onClick={() => toggleVisit(visit.id)}>
                        {isExpanded ? "Hide Reports" : "View Reports"}
                      </Button>
                    </div>
                  </div>
                  {isExpanded && (
                    <div style={{ marginTop: 12 }}>
                      {reports.length === 0 ? (
                        <div style={{ color: theme.colors.textTertiary }}>No USG reports yet.</div>
                      ) : (
                        <ul style={{ margin: 0, paddingLeft: 18 }}>
                          {reports.map((report) => (
                            <li key={report.id} style={{ marginBottom: 6 }}>
                              <Link to={`/usg/studies/${report.id}`} style={{ color: theme.colors.brandBlue }}>
                                {report.service_code}
                              </Link>{" "}
                              <span style={{ color: theme.colors.textSecondary }}>
                                • {report.status} • {formatDateTime(report.published_at || report.created_at)}
                              </span>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        <div style={{
          border: `1px solid ${theme.colors.border}`,
          borderRadius: theme.radius.md,
          backgroundColor: theme.colors.background,
        }}>
          <div style={{ padding: "12px 16px", borderBottom: `1px solid ${theme.colors.border}` }}>
            <strong>Latest USG Reports</strong>
          </div>
          <div style={{ padding: 16 }}>
            {allReports.length === 0 ? (
              <div style={{ color: theme.colors.textTertiary }}>No published reports yet.</div>
            ) : (
              <ul style={{ margin: 0, paddingLeft: 18 }}>
                {allReports.slice(0, 6).map((report) => (
                  <li key={report.id} style={{ marginBottom: 8 }}>
                    <Link to={`/usg/studies/${report.id}`} style={{ color: theme.colors.brandBlue }}>
                      {report.service_code}
                    </Link>
                    <div style={{ fontSize: 12, color: theme.colors.textTertiary }}>
                      Visit {report.visitNumber} • {formatDateTime(report.published_at || report.created_at)}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>

      {showVisitModal && (
        <div style={{
          position: "fixed",
          inset: 0,
          backgroundColor: "rgba(0,0,0,0.4)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 1000,
        }}>
          <div style={{
            width: "min(480px, 90vw)",
            backgroundColor: theme.colors.background,
            borderRadius: theme.radius.md,
            padding: 20,
            boxShadow: theme.shadows.md,
          }}>
            <h3 style={{ marginTop: 0 }}>Create New Visit</h3>
            <p style={{ color: theme.colors.textSecondary, fontSize: 13 }}>
              Choose the USG service for this visit.
            </p>
            <label style={{ display: "block", marginBottom: 6 }}>USG Service</label>
            <select
              value={selectedServiceId}
              onChange={(event) => setSelectedServiceId(event.target.value)}
              disabled={services.length === 0}
              style={{
                width: "100%",
                padding: 8,
                borderRadius: theme.radius.base,
                border: `1px solid ${theme.colors.border}`,
              }}
            >
              {services.length === 0 ? (
                <option value="">No USG services found</option>
              ) : (
                services.map((service) => (
                  <option key={service.id} value={service.id}>
                    {service.name}
                  </option>
                ))
              )}
            </select>
            <div style={{ display: "flex", gap: 12, marginTop: 16 }}>
              <Button onClick={createVisit} disabled={loading}>
                {loading ? "Creating..." : "Create Visit"}
              </Button>
              <Button variant="secondary" onClick={() => setShowVisitModal(false)}>
                Cancel
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
