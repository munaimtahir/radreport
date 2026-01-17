import React, { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
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

export default function UsgPatientLookupPage() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [patientForm, setPatientForm] = useState({
    name: "",
    age: "",
    gender: "",
    phone: "",
    address: "",
  });

  const canSearch = query.trim().length >= 2;

  useEffect(() => {
    if (!token || !canSearch) {
      setResults([]);
      return;
    }
    const timer = window.setTimeout(async () => {
      setLoading(true);
      setError("");
      try {
        const data = await apiGet(`/patients/?search=${encodeURIComponent(query.trim())}`, token);
        setResults(data.results || data || []);
      } catch (err: any) {
        setError(err.message || "Failed to search patients");
      } finally {
        setLoading(false);
      }
    }, 300);
    return () => window.clearTimeout(timer);
  }, [token, query, canSearch]);

  const hasResults = results.length > 0;

  const resetForm = () => {
    setPatientForm({
      name: "",
      age: "",
      gender: "",
      phone: "",
      address: "",
    });
  };

  const handleCreatePatient = async () => {
    if (!token) return;
    if (!patientForm.name.trim()) {
      setError("Patient name is required.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const payload: any = {
        name: patientForm.name.trim(),
        gender: patientForm.gender || "",
        phone: patientForm.phone.trim(),
        address: patientForm.address.trim(),
      };
      if (patientForm.age.trim()) {
        payload.age = parseInt(patientForm.age, 10);
      }
      const patient = await apiPost("/patients/", token, payload);
      setSuccess(`Patient ${patient.mrn} created successfully.`);
      resetForm();
      setShowCreate(false);
      navigate(`/usg/patients/${patient.id}`);
    } catch (err: any) {
      setError(err.message || "Failed to create patient");
    } finally {
      setLoading(false);
    }
  };

  const summary = useMemo(() => {
    if (!canSearch) return "Search by MRN, name, or phone";
    if (loading) return "Searching patients...";
    if (hasResults) return `${results.length} patient${results.length === 1 ? "" : "s"} found`;
    return "No matching patients yet";
  }, [canSearch, loading, hasResults, results.length]);

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>
      <PageHeader title="Patient Lookup" subtitle="USG reporting workspace" />

      {error && <ErrorAlert message={error} onDismiss={() => setError("")} />}
      {success && <SuccessAlert message={success} onDismiss={() => setSuccess("")} />}

      <div style={{
        border: `1px solid ${theme.colors.border}`,
        borderRadius: theme.radius.md,
        padding: 20,
        marginBottom: 24,
        backgroundColor: theme.colors.background,
        boxShadow: theme.shadows.sm,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
          <div style={{ flex: 1, minWidth: 240 }}>
            <label style={{ display: "block", fontSize: 13, marginBottom: 6, color: theme.colors.textSecondary }}>
              Search by MRN, Name, or Phone
            </label>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Type MRN, patient name, or phone"
              style={{
                width: "100%",
                padding: "10px 12px",
                borderRadius: theme.radius.base,
                border: `1px solid ${theme.colors.border}`,
                fontSize: 14,
              }}
            />
            <div style={{ marginTop: 6, fontSize: 12, color: theme.colors.textTertiary }}>
              {summary}
            </div>
          </div>
          <Button variant="secondary" onClick={() => setShowCreate((prev) => !prev)}>
            {showCreate ? "Close New Patient" : "Create New Patient"}
          </Button>
        </div>

        {showCreate && (
          <div style={{
            marginTop: 20,
            padding: 16,
            borderRadius: theme.radius.base,
            border: `1px solid ${theme.colors.borderLight}`,
            backgroundColor: theme.colors.backgroundGray,
          }}>
            <h3 style={{ marginTop: 0, marginBottom: 12 }}>New Patient Registration</h3>
            <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))" }}>
              <div>
                <label style={{ display: "block", marginBottom: 6 }}>Patient Name *</label>
                <input
                  value={patientForm.name}
                  onChange={(event) => setPatientForm({ ...patientForm, name: event.target.value })}
                  style={{ width: "100%", padding: 8, borderRadius: 6, border: `1px solid ${theme.colors.border}` }}
                />
              </div>
              <div>
                <label style={{ display: "block", marginBottom: 6 }}>Age</label>
                <input
                  value={patientForm.age}
                  onChange={(event) => setPatientForm({ ...patientForm, age: event.target.value })}
                  style={{ width: "100%", padding: 8, borderRadius: 6, border: `1px solid ${theme.colors.border}` }}
                />
              </div>
              <div>
                <label style={{ display: "block", marginBottom: 6 }}>Gender</label>
                <select
                  value={patientForm.gender}
                  onChange={(event) => setPatientForm({ ...patientForm, gender: event.target.value })}
                  style={{ width: "100%", padding: 8, borderRadius: 6, border: `1px solid ${theme.colors.border}` }}
                >
                  <option value="">Select</option>
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </select>
              </div>
              <div>
                <label style={{ display: "block", marginBottom: 6 }}>Phone</label>
                <input
                  value={patientForm.phone}
                  onChange={(event) => setPatientForm({ ...patientForm, phone: event.target.value })}
                  style={{ width: "100%", padding: 8, borderRadius: 6, border: `1px solid ${theme.colors.border}` }}
                />
              </div>
            </div>
            <div style={{ marginTop: 12 }}>
              <label style={{ display: "block", marginBottom: 6 }}>Address</label>
              <input
                value={patientForm.address}
                onChange={(event) => setPatientForm({ ...patientForm, address: event.target.value })}
                style={{ width: "100%", padding: 8, borderRadius: 6, border: `1px solid ${theme.colors.border}` }}
              />
            </div>
            <div style={{ display: "flex", gap: 12, marginTop: 16 }}>
              <Button onClick={handleCreatePatient} disabled={loading}>
                {loading ? "Saving..." : "Save Patient"}
              </Button>
              <Button
                variant="secondary"
                onClick={() => {
                  resetForm();
                  setShowCreate(false);
                }}
              >
                Cancel
              </Button>
            </div>
          </div>
        )}
      </div>

      <div style={{
        border: `1px solid ${theme.colors.border}`,
        borderRadius: theme.radius.md,
        backgroundColor: theme.colors.background,
      }}>
        <div style={{ padding: "12px 16px", borderBottom: `1px solid ${theme.colors.border}` }}>
          <strong>Search Results</strong>
        </div>
        <div style={{ padding: 16 }}>
          {!hasResults && !loading && (
            <div style={{ color: theme.colors.textTertiary }}>
              Start typing to find an existing patient or create a new record.
            </div>
          )}
          {hasResults && (
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ textAlign: "left", fontSize: 12, color: theme.colors.textSecondary }}>
                  <th style={{ paddingBottom: 8 }}>MRN</th>
                  <th style={{ paddingBottom: 8 }}>Patient</th>
                  <th style={{ paddingBottom: 8 }}>Age/Sex</th>
                  <th style={{ paddingBottom: 8 }}>Phone</th>
                  <th style={{ paddingBottom: 8 }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {results.map((patient) => (
                  <tr key={patient.id} style={{ borderTop: `1px solid ${theme.colors.borderLight}` }}>
                    <td style={{ padding: "10px 4px" }}>{patient.mrn || "-"}</td>
                    <td style={{ padding: "10px 4px" }}>{patient.name}</td>
                    <td style={{ padding: "10px 4px" }}>
                      {patient.age ? `${patient.age}y` : "-"} {patient.gender || ""}
                    </td>
                    <td style={{ padding: "10px 4px" }}>{patient.phone || "-"}</td>
                    <td style={{ padding: "10px 4px" }}>
                      <Button variant="secondary" onClick={() => navigate(`/usg/patients/${patient.id}`)}>
                        Open Patient
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
