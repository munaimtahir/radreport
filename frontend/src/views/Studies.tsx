import React, { useEffect, useState } from "react";
import { useAuth } from "../ui/auth";
import { apiGet, apiPost, apiPatch } from "../ui/api";
import { Link } from "react-router-dom";
import PageHeader from "../ui/components/PageHeader";
import ErrorAlert from "../ui/components/ErrorAlert";
import Button from "../ui/components/Button";

interface Patient {
  id: string;
  mrn: string;
  name: string;
}

interface Service {
  id: string;
  name: string;
  modality: { code: string };
}

interface Study {
  id: string;
  accession: string;
  patient: Patient;
  patient_name: string;
  service: Service;
  service_name: string;
  modality: string;
  indication: string;
  status: string;
  performed_by: string;
  reported_by: string;
  created_at: string;
  report?: { id: string; status: string };
}

export default function Studies() {
  const { token } = useAuth();
  const [studies, setStudies] = useState<Study[]>([]);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [services, setServices] = useState<Service[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Study | null>(null);
  const [formData, setFormData] = useState({
    patient: "",
    service: "",
    indication: "",
    status: "registered",
    performed_by: "",
    reported_by: "",
  });
  const [statusFilter, setStatusFilter] = useState<string>("");

  const loadData = async () => {
    if (!token) return;
    try {
      setLoading(true);
      const [studiesData, patientsData, servicesData, reportsData] = await Promise.all([
        apiGet(`/studies/${statusFilter ? `?status=${statusFilter}` : ""}`, token),
        apiGet("/patients/", token),
        apiGet("/services/", token),
        apiGet("/reports/", token).catch(() => ({ results: [] })), // Load reports to link them
      ]);
      const studies = studiesData.results || studiesData;
      const reports = reportsData.results || reportsData || [];
      // Map reports to studies by study_id
      const reportsMap = new Map(reports.map((r: any) => [r.study_id || r.study?.id || r.study, r]));
      const studiesWithReports = studies.map((s: Study) => ({
        ...s,
        report: reportsMap.get(s.id),
      }));
      setStudies(studiesWithReports);
      setPatients(patientsData.results || patientsData);
      setServices(servicesData.results || servicesData);
      setError("");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [token, statusFilter]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    try {
      const payload = {
        ...formData,
        patient: formData.patient,
        service: formData.service,
      };
      if (editing) {
        await apiPatch(`/studies/${editing.id}/`, token, payload);
      } else {
        await apiPost("/studies/", token, payload);
      }
      setShowForm(false);
      setEditing(null);
      setFormData({
        patient: "",
        service: "",
        indication: "",
        status: "registered",
        performed_by: "",
        reported_by: "",
      });
      loadData();
    } catch (e: any) {
      setError(e.message);
    }
  };

  const handleEdit = (s: Study) => {
    setEditing(s);
    setFormData({
      patient: s.patient.id,
      service: s.service.id,
      indication: s.indication,
      status: s.status,
      performed_by: s.performed_by,
      reported_by: s.reported_by,
    });
    setShowForm(true);
  };

  const statusColors: Record<string, string> = {
    registered: "#6c757d",
    in_progress: "#ffc107",
    draft: "#17a2b8",
    final: "#28a745",
    delivered: "#007bff",
  };

  return (
    <div>
      <PageHeader
        title="Studies"
        actions={
          <>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              style={{
                padding: "8px 12px",
                fontSize: 14,
                border: "1px solid #ddd",
                borderRadius: 6,
              }}
            >
              <option value="">All Statuses</option>
              <option value="registered">Registered</option>
              <option value="in_progress">In Progress</option>
              <option value="draft">Draft</option>
              <option value="final">Final</option>
              <option value="delivered">Delivered</option>
            </select>
            <Button
              variant={showForm ? "secondary" : "primary"}
              onClick={() => {
                setEditing(null);
                setFormData({
                  patient: "",
                  service: "",
                  indication: "",
                  status: "registered",
                  performed_by: "",
                  reported_by: "",
                });
                setShowForm(!showForm);
              }}
            >
              {showForm ? "Cancel" : "Add Study"}
            </Button>
          </>
        }
      />

      {error && <ErrorAlert message={error} onDismiss={() => setError("")} />}

      {showForm && (
        <form
          onSubmit={handleSubmit}
          style={{
            background: "#f9f9f9",
            padding: 20,
            borderRadius: 8,
            marginBottom: 20,
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: 12,
          }}
        >
          <div>
            <label>Patient *</label>
            <select
              value={formData.patient}
              onChange={(e) => setFormData({ ...formData, patient: e.target.value })}
              required
              style={{ width: "100%", padding: 8 }}
            >
              <option value="">Select patient...</option>
              {patients.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.mrn} - {p.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label>Service *</label>
            <select
              value={formData.service}
              onChange={(e) => setFormData({ ...formData, service: e.target.value })}
              required
              style={{ width: "100%", padding: 8 }}
            >
              <option value="">Select service...</option>
              {services.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.modality.code} - {s.name}
                </option>
              ))}
            </select>
          </div>
          <div style={{ gridColumn: "1 / -1" }}>
            <label>Indication</label>
            <input
              type="text"
              value={formData.indication}
              onChange={(e) => setFormData({ ...formData, indication: e.target.value })}
              style={{ width: "100%", padding: 8 }}
            />
          </div>
          <div>
            <label>Status</label>
            <select
              value={formData.status}
              onChange={(e) => setFormData({ ...formData, status: e.target.value })}
              style={{ width: "100%", padding: 8 }}
            >
              <option value="registered">Registered</option>
              <option value="in_progress">In Progress</option>
              <option value="draft">Draft</option>
              <option value="final">Final</option>
              <option value="delivered">Delivered</option>
            </select>
          </div>
          <div>
            <label>Performed By</label>
            <input
              type="text"
              value={formData.performed_by}
              onChange={(e) => setFormData({ ...formData, performed_by: e.target.value })}
              style={{ width: "100%", padding: 8 }}
            />
          </div>
          <div>
            <label>Reported By</label>
            <input
              type="text"
              value={formData.reported_by}
              onChange={(e) => setFormData({ ...formData, reported_by: e.target.value })}
              style={{ width: "100%", padding: 8 }}
            />
          </div>
          <div style={{ gridColumn: "1 / -1" }}>
            <Button type="submit">
              {editing ? "Update" : "Create"} Study
            </Button>
          </div>
        </form>
      )}

      {loading ? (
        <div style={{ textAlign: "center", padding: 40, color: "#666" }}>Loading...</div>
      ) : studies.length === 0 ? (
        <div style={{ textAlign: "center", padding: 40, color: "#999", border: "1px solid #e0e0e0", borderRadius: 8 }}>
          No studies found.
        </div>
      ) : (
        <div style={{ border: "1px solid #e0e0e0", borderRadius: 8, overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ background: "#f5f5f5" }}>
                <th style={{ padding: 12, textAlign: "left", borderBottom: "2px solid #ddd", fontWeight: 600 }}>Accession</th>
                <th style={{ padding: 12, textAlign: "left", borderBottom: "2px solid #ddd", fontWeight: 600 }}>Patient</th>
                <th style={{ padding: 12, textAlign: "left", borderBottom: "2px solid #ddd", fontWeight: 600 }}>Service</th>
                <th style={{ padding: 12, textAlign: "left", borderBottom: "2px solid #ddd", fontWeight: 600 }}>Status</th>
                <th style={{ padding: 12, textAlign: "left", borderBottom: "2px solid #ddd", fontWeight: 600 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {studies.map((s) => (
                <tr key={s.id} style={{ borderBottom: "1px solid #eee" }}>
                  <td style={{ padding: 12 }}>{s.accession}</td>
                  <td style={{ padding: 12 }}>{s.patient_name}</td>
                  <td style={{ padding: 12 }}>{s.service_name}</td>
                  <td style={{ padding: 12 }}>
                    <span
                      style={{
                        padding: "4px 8px",
                        borderRadius: 4,
                        background: statusColors[s.status] || "#ccc",
                        color: "white",
                        fontSize: 12,
                        fontWeight: 500,
                      }}
                    >
                      {s.status}
                    </span>
                  </td>
                  <td style={{ padding: 12 }}>
                    <div style={{ display: "flex", gap: 8 }}>
                      <Button variant="secondary" onClick={() => handleEdit(s)} style={{ padding: "4px 12px", fontSize: 12 }}>
                        Edit
                      </Button>
                      {s.report && (
                        <Link
                          to={`/reports/${s.report.id}/edit`}
                          style={{
                            fontSize: 12,
                            padding: "4px 12px",
                            background: "#0B5ED7",
                            color: "white",
                            textDecoration: "none",
                            borderRadius: 6,
                            fontWeight: 500,
                          }}
                        >
                          {s.report.status === "final" ? "View Report" : "Edit Report"}
                        </Link>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
