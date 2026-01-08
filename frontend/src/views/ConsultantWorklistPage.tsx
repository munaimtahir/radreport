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

interface OPDConsult {
  id: string;
  service_visit_id: string;
  diagnosis: string;
  notes: string;
  medicines_json: any[];
  investigations_json: any[];
  advice: string;
  followup: string;
}

export default function ConsultantWorklistPage() {
  const { token } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const [success, setSuccess] = useState<string>("");
  const [visits, setVisits] = useState<ServiceVisit[]>([]);
  const [selectedVisit, setSelectedVisit] = useState<ServiceVisit | null>(null);
  const [consult, setConsult] = useState<OPDConsult | null>(null);
  const [consultForm, setConsultForm] = useState({
    diagnosis: "",
    notes: "",
    advice: "",
    followup: "",
  });
  const [medicines, setMedicines] = useState<Array<{name: string; dosage: string; frequency: string; duration: string}>>([]);
  const [investigations, setInvestigations] = useState<string[]>([]);
  const [newMedicine, setNewMedicine] = useState({ name: "", dosage: "", frequency: "", duration: "" });
  const [newInvestigation, setNewInvestigation] = useState("");

  useEffect(() => {
    if (token) {
      loadVisits();
    }
  }, [token]);

  const loadVisits = async () => {
    if (!token) return;
    try {
      const data = await apiGet("/workflow/visits/?workflow=OPD&status=IN_PROGRESS", token);
      setVisits(data.results || data || []);
    } catch (err: any) {
      setError(err.message || "Failed to load visits");
    }
  };

  const loadConsult = async (visitId: string) => {
    if (!token) return;
    try {
      const data = await apiGet(`/workflow/opd/consult/?visit_id=${visitId}`, token);
      if (data && data.length > 0) {
        const c = data[0];
        setConsult(c);
        setConsultForm({
          diagnosis: c.diagnosis || "",
          notes: c.notes || "",
          advice: c.advice || "",
          followup: c.followup || "",
        });
        setMedicines(Array.isArray(c.medicines_json) ? c.medicines_json : []);
        setInvestigations(Array.isArray(c.investigations_json) ? c.investigations_json : []);
      } else {
        setConsult(null);
        setConsultForm({ diagnosis: "", notes: "", advice: "", followup: "" });
        setMedicines([]);
        setInvestigations([]);
      }
    } catch (err: any) {
      setConsult(null);
      setConsultForm({ diagnosis: "", notes: "", advice: "", followup: "" });
      setMedicines([]);
      setInvestigations([]);
    }
  };

  const handleSelectVisit = async (visit: ServiceVisit) => {
    setSelectedVisit(visit);
    await loadConsult(visit.id);
  };

  const addMedicine = () => {
    if (newMedicine.name.trim()) {
      setMedicines([...medicines, { ...newMedicine }]);
      setNewMedicine({ name: "", dosage: "", frequency: "", duration: "" });
    }
  };

  const removeMedicine = (index: number) => {
    setMedicines(medicines.filter((_, i) => i !== index));
  };

  const addInvestigation = () => {
    if (newInvestigation.trim()) {
      setInvestigations([...investigations, newInvestigation]);
      setNewInvestigation("");
    }
  };

  const removeInvestigation = (index: number) => {
    setInvestigations(investigations.filter((_, i) => i !== index));
  };

  const saveAndPrint = async () => {
    if (!token || !selectedVisit) return;
    setLoading(true);
    setError("");
    try {
      const consultPayload: any = {
        visit_id: selectedVisit.id,
        diagnosis: consultForm.diagnosis,
        notes: consultForm.notes,
        medicines_json: medicines,
        investigations_json: investigations,
        advice: consultForm.advice,
        followup: consultForm.followup,
      };
      
      const result = await apiPost(`/workflow/opd/consult/${selectedVisit.id}/save_and_print/`, token, consultPayload);
      setSuccess("Prescription saved and printed successfully!");
      
      // Open PDF in new window
      if (result.published_pdf_url) {
        window.open(result.published_pdf_url, "_blank");
      }
      
      setSelectedVisit(null);
      setConsult(null);
      await loadVisits();
    } catch (err: any) {
      setError(err.message || "Failed to save prescription");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 1400, margin: "0 auto" }}>
      <PageHeader title="Consultant Worklist" subtitle="Performance Desk" />
      
      {error && <ErrorAlert message={error} onDismiss={() => setError("")} />}
      {success && <SuccessAlert message={success} onDismiss={() => setSuccess("")} />}
      
      <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: 20 }}>
        {/* Visit List */}
        <div style={{ border: "1px solid #ddd", padding: 16, borderRadius: 8, maxHeight: "80vh", overflowY: "auto" }}>
          <h2>Pending Consultations ({visits.length})</h2>
          {visits.length === 0 ? (
            <p>No consultations pending</p>
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
        
        {/* Consultation Form */}
        {selectedVisit && (
          <div style={{ border: "1px solid #ddd", padding: 20, borderRadius: 8, maxHeight: "80vh", overflowY: "auto" }}>
            <h2>Consultation - {selectedVisit.visit_id}</h2>
            <div style={{ marginBottom: 16, padding: 12, backgroundColor: "#f5f5f5", borderRadius: 4 }}>
              <div><strong>Patient:</strong> {selectedVisit.patient_name} ({selectedVisit.patient_reg_no})</div>
            </div>
            
            <div style={{ marginBottom: 16 }}>
              <label><strong>Diagnosis:</strong></label>
              <textarea
                value={consultForm.diagnosis}
                onChange={(e) => setConsultForm({ ...consultForm, diagnosis: e.target.value })}
                rows={3}
                style={{ width: "100%", padding: 8 }}
                placeholder="Enter diagnosis..."
              />
            </div>
            
            <div style={{ marginBottom: 16 }}>
              <label><strong>Clinical Notes:</strong></label>
              <textarea
                value={consultForm.notes}
                onChange={(e) => setConsultForm({ ...consultForm, notes: e.target.value })}
                rows={4}
                style={{ width: "100%", padding: 8 }}
                placeholder="Enter clinical notes..."
              />
            </div>
            
            <div style={{ marginBottom: 16, border: "1px solid #ddd", padding: 16, borderRadius: 4 }}>
              <h3>Medicines</h3>
              {medicines.map((med, index) => (
                <div key={index} style={{ marginBottom: 8, padding: 8, backgroundColor: "#f9f9f9", borderRadius: 4, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div>
                    <strong>{med.name}</strong> - {med.dosage} - {med.frequency} - {med.duration}
                  </div>
                  <Button variant="danger" onClick={() => removeMedicine(index)} style={{ padding: "4px 8px", fontSize: 12 }}>
                    Remove
                  </Button>
                </div>
              ))}
              <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr 1fr auto", gap: 8, marginTop: 8 }}>
                <input
                  placeholder="Medicine name"
                  value={newMedicine.name}
                  onChange={(e) => setNewMedicine({ ...newMedicine, name: e.target.value })}
                  style={{ padding: 6 }}
                />
                <input
                  placeholder="Dosage"
                  value={newMedicine.dosage}
                  onChange={(e) => setNewMedicine({ ...newMedicine, dosage: e.target.value })}
                  style={{ padding: 6 }}
                />
                <input
                  placeholder="Frequency"
                  value={newMedicine.frequency}
                  onChange={(e) => setNewMedicine({ ...newMedicine, frequency: e.target.value })}
                  style={{ padding: 6 }}
                />
                <input
                  placeholder="Duration"
                  value={newMedicine.duration}
                  onChange={(e) => setNewMedicine({ ...newMedicine, duration: e.target.value })}
                  style={{ padding: 6 }}
                />
                <Button variant="success" onClick={addMedicine} style={{ padding: "6px 12px", fontSize: 12 }}>
                  Add
                </Button>
              </div>
            </div>
            
            <div style={{ marginBottom: 16, border: "1px solid #ddd", padding: 16, borderRadius: 4 }}>
              <h3>Investigations</h3>
              {investigations.map((inv, index) => (
                <div key={index} style={{ marginBottom: 8, padding: 8, backgroundColor: "#f9f9f9", borderRadius: 4, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div>{inv}</div>
                  <Button variant="danger" onClick={() => removeInvestigation(index)} style={{ padding: "4px 8px", fontSize: 12 }}>
                    Remove
                  </Button>
                </div>
              ))}
              <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                <input
                  placeholder="Investigation name"
                  value={newInvestigation}
                  onChange={(e) => setNewInvestigation(e.target.value)}
                  onKeyPress={(e) => e.key === "Enter" && addInvestigation()}
                  style={{ flex: 1, padding: 6 }}
                />
                <Button variant="success" onClick={addInvestigation} style={{ padding: "6px 12px", fontSize: 12 }}>
                  Add
                </Button>
              </div>
            </div>
            
            <div style={{ marginBottom: 16 }}>
              <label><strong>Advice:</strong></label>
              <textarea
                value={consultForm.advice}
                onChange={(e) => setConsultForm({ ...consultForm, advice: e.target.value })}
                rows={3}
                style={{ width: "100%", padding: 8 }}
                placeholder="Enter advice..."
              />
            </div>
            
            <div style={{ marginBottom: 16 }}>
              <label><strong>Follow-up:</strong></label>
              <input
                value={consultForm.followup}
                onChange={(e) => setConsultForm({ ...consultForm, followup: e.target.value })}
                style={{ width: "100%", padding: 8 }}
                placeholder="e.g., Review after 1 week"
              />
            </div>
            
            <Button onClick={saveAndPrint} disabled={loading || !consultForm.diagnosis.trim()}>
              Save & Print Prescription
            </Button>
          </div>
        )}
        
        {!selectedVisit && (
          <div style={{ border: "1px solid #ddd", padding: 20, borderRadius: 8, textAlign: "center", color: "#999" }}>
            Select a visit from the list to start consultation
          </div>
        )}
      </div>
    </div>
  );
}
