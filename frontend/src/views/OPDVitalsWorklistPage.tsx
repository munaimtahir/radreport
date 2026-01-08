import React, { useEffect, useState } from "react";
import { useAuth } from "../ui/auth";
import { apiGet, apiPost } from "../ui/api";
import PageHeader from "../ui/components/PageHeader";
import ErrorAlert from "../ui/components/ErrorAlert";
import SuccessAlert from "../ui/components/SuccessAlert";
import Button from "../ui/components/Button";

interface ServiceVisit {
  id: string;
  visit_id: string;
  patient_name: string;
  patient_reg_no: string;
  service_name: string;
  status: string;
  registered_at: string;
}

interface OPDVitals {
  id: string;
  service_visit_id: string;
  bp_systolic?: number;
  bp_diastolic?: number;
  pulse?: number;
  temperature?: number;
  respiratory_rate?: number;
  spo2?: number;
  weight?: number;
  height?: number;
  bmi?: number;
}

export default function OPDVitalsWorklistPage() {
  const { token } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const [success, setSuccess] = useState<string>("");
  const [visits, setVisits] = useState<ServiceVisit[]>([]);
  const [selectedVisit, setSelectedVisit] = useState<ServiceVisit | null>(null);
  const [vitals, setVitals] = useState<OPDVitals | null>(null);
  const [vitalsForm, setVitalsForm] = useState({
    bp_systolic: "",
    bp_diastolic: "",
    pulse: "",
    temperature: "",
    respiratory_rate: "",
    spo2: "",
    weight: "",
    height: "",
  });

  useEffect(() => {
    if (token) {
      loadVisits();
    }
  }, [token]);

  const loadVisits = async () => {
    if (!token) return;
    try {
      const data = await apiGet("/workflow/visits/?workflow=OPD&status=REGISTERED", token);
      setVisits(data.results || data || []);
    } catch (err: any) {
      setError(err.message || "Failed to load visits");
    }
  };

  const loadVitals = async (visitId: string) => {
    if (!token) return;
    try {
      const data = await apiGet(`/workflow/opd/vitals/?visit_id=${visitId}`, token);
      if (data && data.length > 0) {
        const v = data[0];
        setVitals(v);
        setVitalsForm({
          bp_systolic: v.bp_systolic?.toString() || "",
          bp_diastolic: v.bp_diastolic?.toString() || "",
          pulse: v.pulse?.toString() || "",
          temperature: v.temperature?.toString() || "",
          respiratory_rate: v.respiratory_rate?.toString() || "",
          spo2: v.spo2?.toString() || "",
          weight: v.weight?.toString() || "",
          height: v.height?.toString() || "",
        });
      } else {
        setVitals(null);
        setVitalsForm({
          bp_systolic: "",
          bp_diastolic: "",
          pulse: "",
          temperature: "",
          respiratory_rate: "",
          spo2: "",
          weight: "",
          height: "",
        });
      }
    } catch (err: any) {
      setVitals(null);
      setVitalsForm({
        bp_systolic: "",
        bp_diastolic: "",
        pulse: "",
        temperature: "",
        respiratory_rate: "",
        spo2: "",
        weight: "",
        height: "",
      });
    }
  };

  const handleSelectVisit = async (visit: ServiceVisit) => {
    setSelectedVisit(visit);
    await loadVitals(visit.id);
  };

  const calculateBMI = () => {
    const weight = parseFloat(vitalsForm.weight);
    const height = parseFloat(vitalsForm.height);
    if (weight && height && height > 0) {
      const heightInMeters = height / 100;
      return (weight / (heightInMeters * heightInMeters)).toFixed(1);
    }
    return "";
  };

  const saveVitals = async () => {
    if (!token || !selectedVisit) return;
    setLoading(true);
    setError("");
    try {
      const vitalsPayload: any = {
        visit_id: selectedVisit.id,
      };
      
      if (vitalsForm.bp_systolic) vitalsPayload.bp_systolic = parseInt(vitalsForm.bp_systolic);
      if (vitalsForm.bp_diastolic) vitalsPayload.bp_diastolic = parseInt(vitalsForm.bp_diastolic);
      if (vitalsForm.pulse) vitalsPayload.pulse = parseInt(vitalsForm.pulse);
      if (vitalsForm.temperature) vitalsPayload.temperature = parseFloat(vitalsForm.temperature);
      if (vitalsForm.respiratory_rate) vitalsPayload.respiratory_rate = parseInt(vitalsForm.respiratory_rate);
      if (vitalsForm.spo2) vitalsPayload.spo2 = parseInt(vitalsForm.spo2);
      if (vitalsForm.weight) vitalsPayload.weight = parseFloat(vitalsForm.weight);
      if (vitalsForm.height) vitalsPayload.height = parseFloat(vitalsForm.height);
      
      const bmi = calculateBMI();
      if (bmi) vitalsPayload.bmi = parseFloat(bmi);
      
      await apiPost("/workflow/opd/vitals/", token, vitalsPayload);
      setSuccess("Vitals saved successfully. Visit moved to Consultant Worklist.");
      setSelectedVisit(null);
      setVitals(null);
      await loadVisits();
    } catch (err: any) {
      setError(err.message || "Failed to save vitals");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto" }}>
      <PageHeader title="OPD Vitals Worklist" subtitle="Performance Desk" />
      
      {error && <ErrorAlert message={error} onDismiss={() => setError("")} />}
      {success && <SuccessAlert message={success} onDismiss={() => setSuccess("")} />}
      
      <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: 20 }}>
        {/* Visit List */}
        <div style={{ border: "1px solid #ddd", padding: 16, borderRadius: 8, maxHeight: "80vh", overflowY: "auto" }}>
          <h2>Pending Visits ({visits.length})</h2>
          {visits.length === 0 ? (
            <p>No visits pending</p>
          ) : (
            <div style={{ display: "grid", gap: 8 }}>
              {visits.map((visit) => (
                <div
                  key={visit.id}
                  onClick={() => handleSelectVisit(visit)}
                  style={{
                    padding: 12,
                    border: selectedVisit?.id === visit.id ? "2px solid #0B5ED7" : "1px solid #ddd",
                    borderRadius: 4,
                    cursor: "pointer",
                    backgroundColor: selectedVisit?.id === visit.id ? "#f0f7ff" : "white",
                  }}
                >
                  <div><strong>{visit.visit_id}</strong></div>
                  <div style={{ fontSize: 14, color: "#666" }}>
                    {visit.patient_name} ({visit.patient_reg_no})
                  </div>
                  <div style={{ fontSize: 12, color: "#999" }}>
                    {new Date(visit.registered_at).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        
        {/* Vitals Form */}
        {selectedVisit && (
          <div style={{ border: "1px solid #ddd", padding: 20, borderRadius: 8 }}>
            <h2>Vitals Entry - {selectedVisit.visit_id}</h2>
            <div style={{ marginBottom: 16, padding: 12, backgroundColor: "#f5f5f5", borderRadius: 4 }}>
              <div><strong>Patient:</strong> {selectedVisit.patient_name} ({selectedVisit.patient_reg_no})</div>
            </div>
            
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
              <div>
                <label>BP Systolic (mmHg):</label>
                <input
                  type="number"
                  value={vitalsForm.bp_systolic}
                  onChange={(e) => setVitalsForm({ ...vitalsForm, bp_systolic: e.target.value })}
                  style={{ width: "100%", padding: 8 }}
                />
              </div>
              <div>
                <label>BP Diastolic (mmHg):</label>
                <input
                  type="number"
                  value={vitalsForm.bp_diastolic}
                  onChange={(e) => setVitalsForm({ ...vitalsForm, bp_diastolic: e.target.value })}
                  style={{ width: "100%", padding: 8 }}
                />
              </div>
              <div>
                <label>Pulse (bpm):</label>
                <input
                  type="number"
                  value={vitalsForm.pulse}
                  onChange={(e) => setVitalsForm({ ...vitalsForm, pulse: e.target.value })}
                  style={{ width: "100%", padding: 8 }}
                />
              </div>
              <div>
                <label>Temperature (°C):</label>
                <input
                  type="number"
                  step="0.1"
                  value={vitalsForm.temperature}
                  onChange={(e) => setVitalsForm({ ...vitalsForm, temperature: e.target.value })}
                  style={{ width: "100%", padding: 8 }}
                />
              </div>
              <div>
                <label>Respiratory Rate (bpm):</label>
                <input
                  type="number"
                  value={vitalsForm.respiratory_rate}
                  onChange={(e) => setVitalsForm({ ...vitalsForm, respiratory_rate: e.target.value })}
                  style={{ width: "100%", padding: 8 }}
                />
              </div>
              <div>
                <label>SpO2 (%):</label>
                <input
                  type="number"
                  value={vitalsForm.spo2}
                  onChange={(e) => setVitalsForm({ ...vitalsForm, spo2: e.target.value })}
                  style={{ width: "100%", padding: 8 }}
                />
              </div>
              <div>
                <label>Weight (kg):</label>
                <input
                  type="number"
                  step="0.1"
                  value={vitalsForm.weight}
                  onChange={(e) => setVitalsForm({ ...vitalsForm, weight: e.target.value })}
                  style={{ width: "100%", padding: 8 }}
                />
              </div>
              <div>
                <label>Height (cm):</label>
                <input
                  type="number"
                  step="0.1"
                  value={vitalsForm.height}
                  onChange={(e) => setVitalsForm({ ...vitalsForm, height: e.target.value })}
                  style={{ width: "100%", padding: 8 }}
                />
              </div>
            </div>
            
            {vitalsForm.weight && vitalsForm.height && (
              <div style={{ marginBottom: 16, padding: 12, backgroundColor: "#e7f3ff", borderRadius: 4 }}>
                <strong>BMI:</strong> {calculateBMI()}
              </div>
            )}
            
            <Button onClick={saveVitals} disabled={loading}>
              Save Vitals
            </Button>
          </div>
        )}
        
        {!selectedVisit && (
          <div style={{ border: "1px solid #ddd", padding: 20, borderRadius: 8, textAlign: "center", color: "#999" }}>
            Select a visit from the list to enter vitals
          </div>
        )}
      </div>
    </div>
  );
}
