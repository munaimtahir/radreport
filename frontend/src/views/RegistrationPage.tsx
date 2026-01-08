import React, { useEffect, useState } from "react";
import { useAuth } from "../ui/auth";
import { apiGet, apiPost } from "../ui/api";
import PageHeader from "../ui/components/PageHeader";
import ErrorAlert from "../ui/components/ErrorAlert";
import SuccessAlert from "../ui/components/SuccessAlert";
import Button from "../ui/components/Button";

interface Patient {
  id: string;
  patient_reg_no?: string;
  mrn: string;
  name: string;
  age?: number;
  date_of_birth?: string;
  gender: string;
  phone: string;
  address: string;
}

interface Service {
  id: string;
  code: string;
  name: string;
  price: number;
  charges: number;
  category: string;
  modality: {
    code: string;
    name: string;
  };
  is_active: boolean;
}

export default function RegistrationPage() {
  const { token } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const [success, setSuccess] = useState<string>("");
  
  // Patient state
  const [patientSearch, setPatientSearch] = useState("");
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [patientResults, setPatientResults] = useState<Patient[]>([]);
  const [showPatientForm, setShowPatientForm] = useState(false);
  const [patientForm, setPatientForm] = useState({
    name: "",
    age: "",
    date_of_birth: "",
    gender: "",
    phone: "",
    address: "",
  });
  
  // Service registration state
  const [services, setServices] = useState<Service[]>([]);
  const [selectedServices, setSelectedServices] = useState<Service[]>([]);
  const [servicePrice, setServicePrice] = useState("");
  const [discount, setDiscount] = useState("");
  const [amountPaid, setAmountPaid] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("cash");
  
  useEffect(() => {
    if (token) {
      loadServices();
    }
  }, [token]);
  
  const loadServices = async () => {
    if (!token) return;
    try {
      // Use unified catalog API
      const data = await apiGet("/services/", token);
      setServices(data.results || data || []);
    } catch (err: any) {
      setError(err.message || "Failed to load services");
    }
  };
  
  const toggleServiceSelection = (service: Service) => {
    setSelectedServices(prev => {
      const exists = prev.find(s => s.id === service.id);
      if (exists) {
        return prev.filter(s => s.id !== service.id);
      } else {
        const updated = [...prev, service];
        // Recalculate price from selected services
        const totalPrice = updated.reduce((sum, s) => sum + (s.price || s.charges || 0), 0);
        setServicePrice(totalPrice.toString());
        return updated;
      }
    });
  };
  
  const searchPatients = async () => {
    if (!token || !patientSearch.trim()) return;
    try {
      const data = await apiGet(`/patients/?search=${encodeURIComponent(patientSearch)}`, token);
      setPatientResults(data.results || data || []);
    } catch (err: any) {
      setError(err.message || "Failed to search patients");
    }
  };
  
  const createPatient = async () => {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const patientData: any = {
        name: patientForm.name,
        gender: patientForm.gender,
        phone: patientForm.phone,
        address: patientForm.address,
      };
      if (patientForm.age) patientData.age = parseInt(patientForm.age);
      if (patientForm.date_of_birth) patientData.date_of_birth = patientForm.date_of_birth;
      
      const patient = await apiPost("/patients/", token, patientData);
      setSelectedPatient(patient);
      setShowPatientForm(false);
      setPatientForm({ name: "", age: "", date_of_birth: "", gender: "", phone: "", address: "" });
      setSuccess("Patient created successfully");
    } catch (err: any) {
      setError(err.message || "Failed to create patient");
    } finally {
      setLoading(false);
    }
  };
  
  const updatePatient = async () => {
    if (!token || !selectedPatient) return;
    setLoading(true);
    setError("");
    try {
      const patientData: any = {
        name: patientForm.name || selectedPatient.name,
        gender: patientForm.gender || selectedPatient.gender,
        phone: patientForm.phone || selectedPatient.phone,
        address: patientForm.address || selectedPatient.address,
      };
      if (patientForm.age) patientData.age = parseInt(patientForm.age);
      if (patientForm.date_of_birth) patientData.date_of_birth = patientForm.date_of_birth;
      
      const updated = await apiPost(`/patients/${selectedPatient.id}/`, token, patientData);
      setSelectedPatient(updated);
      setSuccess("Patient updated successfully");
    } catch (err: any) {
      setError(err.message || "Failed to update patient");
    } finally {
      setLoading(false);
    }
  };
  
  const calculateTotals = () => {
    // Calculate subtotal from selected services
    const subtotal = selectedServices.reduce((sum, s) => sum + (s.price || s.charges || 0), 0);
    const total = parseFloat(servicePrice) || subtotal;
    const disc = parseFloat(discount) || 0;
    const net = total - disc;
    const paid = parseFloat(amountPaid) || net;
    const balance = net - paid;
    return { subtotal, total, discount: disc, net, paid, balance };
  };
  
  const saveVisit = async (printReceipt: boolean = false) => {
    if (!token || !selectedPatient || selectedServices.length === 0) {
      setError("Please select a patient and at least one service");
      return;
    }
    
    setLoading(true);
    setError("");
    try {
      const totals = calculateTotals();
      const visitData = {
        patient_id: selectedPatient.id,
        service_ids: selectedServices.map(s => s.id), // Multiple services
        subtotal: totals.subtotal,
        total_amount: totals.total,
        discount: totals.discount,
        net_amount: totals.net,
        amount_paid: totals.paid,
        payment_method: paymentMethod,
      };
      
      const visit = await apiPost("/workflow/visits/create_visit/", token, visitData);
      setSuccess(`Service visit created: ${visit.visit_id}`);
      
      // Reset form
      setSelectedServices([]);
      setServicePrice("");
      setDiscount("");
      setAmountPaid("");
      
      if (printReceipt) {
        // Fetch receipt PDF with auth token and open in new window
        const API_BASE = (import.meta as any).env.VITE_API_BASE || ((import.meta as any).env.PROD ? "/api" : "http://localhost:8000/api");
        const receiptUrl = `${API_BASE}/pdf/${visit.id}/receipt/`;
        
        fetch(receiptUrl, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })
          .then((res) => {
            if (!res.ok) throw new Error("Failed to fetch receipt PDF");
            return res.blob();
          })
          .then((blob) => {
            const url = window.URL.createObjectURL(blob);
            const win = window.open(url, "_blank");
            if (win) {
              // Clean up blob URL after a delay
              setTimeout(() => window.URL.revokeObjectURL(url), 100);
            }
          })
          .catch((err) => {
            console.error("Failed to load receipt:", err);
            setError("Failed to load receipt. Please try again.");
          });
      }
    } catch (err: any) {
      setError(err.message || "Failed to create service visit");
    } finally {
      setLoading(false);
    }
  };
  
  const totals = calculateTotals();
  
  return (
    <div style={{ maxWidth: 1200, margin: "0 auto" }}>
      <PageHeader title="Registration Desk" />
      
      {error && <ErrorAlert message={error} onDismiss={() => setError("")} />}
      {success && <SuccessAlert message={success} onDismiss={() => setSuccess("")} />}
      
      {/* Patient Search and Form Section */}
      <div style={{ border: "1px solid #ddd", padding: 20, marginBottom: 20, borderRadius: 8 }}>
        <h2>Patient Information</h2>
        
        {!selectedPatient ? (
          <>
            <div style={{ marginBottom: 16 }}>
              <input
                type="text"
                placeholder="Search by name, mobile, or Patient Reg No"
                value={patientSearch}
                onChange={(e) => setPatientSearch(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && searchPatients()}
                style={{ width: "100%", padding: 8, fontSize: 14 }}
              />
              <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                <Button onClick={searchPatients}>Search</Button>
                <Button variant="secondary" onClick={() => setShowPatientForm(true)}>
                  New Patient
                </Button>
              </div>
            </div>
            
            {patientResults.length > 0 && (
              <div style={{ border: "1px solid #eee", borderRadius: 4, maxHeight: 200, overflowY: "auto" }}>
                {patientResults.map((p) => (
                  <div
                    key={p.id}
                    onClick={() => {
                      setSelectedPatient(p);
                      setPatientForm({
                        name: p.name,
                        age: p.age?.toString() || "",
                        date_of_birth: p.date_of_birth || "",
                        gender: p.gender || "",
                        phone: p.phone || "",
                        address: p.address || "",
                      });
                      setPatientResults([]);
                    }}
                    style={{ padding: 12, borderBottom: "1px solid #eee", cursor: "pointer" }}
                  >
                    <strong>{p.name}</strong> - {p.patient_reg_no || p.mrn} - {p.phone}
                  </div>
                ))}
              </div>
            )}
            
            {showPatientForm && (
              <div style={{ marginTop: 16, border: "1px solid #ddd", padding: 16, borderRadius: 4 }}>
                <h3>New Patient</h3>
                <div style={{ display: "grid", gap: 12 }}>
                  <input
                    placeholder="Name *"
                    value={patientForm.name}
                    onChange={(e) => setPatientForm({ ...patientForm, name: e.target.value })}
                    required
                  />
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                    <input
                      type="number"
                      placeholder="Age"
                      value={patientForm.age}
                      onChange={(e) => setPatientForm({ ...patientForm, age: e.target.value })}
                    />
                    <input
                      type="date"
                      placeholder="Date of Birth"
                      value={patientForm.date_of_birth}
                      onChange={(e) => setPatientForm({ ...patientForm, date_of_birth: e.target.value })}
                    />
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                    <select
                      value={patientForm.gender}
                      onChange={(e) => setPatientForm({ ...patientForm, gender: e.target.value })}
                    >
                      <option value="">Gender</option>
                      <option value="Male">Male</option>
                      <option value="Female">Female</option>
                      <option value="Other">Other</option>
                    </select>
                    <input
                      placeholder="Phone"
                      value={patientForm.phone}
                      onChange={(e) => setPatientForm({ ...patientForm, phone: e.target.value })}
                    />
                  </div>
                  <textarea
                    placeholder="Address"
                    value={patientForm.address}
                    onChange={(e) => setPatientForm({ ...patientForm, address: e.target.value })}
                    rows={2}
                  />
                </div>
                <div style={{ marginTop: 16, display: "flex", gap: 8 }}>
                  <Button onClick={createPatient} disabled={loading || !patientForm.name}>
                    Create Patient
                  </Button>
                  <Button variant="secondary" onClick={() => setShowPatientForm(false)}>
                    Cancel
                  </Button>
                </div>
              </div>
            )}
          </>
        ) : (
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <strong>Selected Patient:</strong> {selectedPatient.name} - {selectedPatient.patient_reg_no || selectedPatient.mrn}
                <br />
                <small>Phone: {selectedPatient.phone} | Age: {selectedPatient.age || "N/A"} | Gender: {selectedPatient.gender || "N/A"}</small>
              </div>
              <button onClick={() => {
                setSelectedPatient(null);
                setPatientForm({ name: "", age: "", date_of_birth: "", gender: "", phone: "", address: "" });
              }}>
                Change Patient
              </button>
            </div>
            
            {showPatientForm && (
              <div style={{ marginTop: 16, border: "1px solid #ddd", padding: 16, borderRadius: 4 }}>
                <h3>Update Patient</h3>
                <div style={{ display: "grid", gap: 12 }}>
                  <input
                    placeholder="Name"
                    value={patientForm.name}
                    onChange={(e) => setPatientForm({ ...patientForm, name: e.target.value })}
                  />
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                    <input
                      type="number"
                      placeholder="Age"
                      value={patientForm.age}
                      onChange={(e) => setPatientForm({ ...patientForm, age: e.target.value })}
                    />
                    <input
                      type="date"
                      placeholder="Date of Birth"
                      value={patientForm.date_of_birth}
                      onChange={(e) => setPatientForm({ ...patientForm, date_of_birth: e.target.value })}
                    />
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                    <select
                      value={patientForm.gender}
                      onChange={(e) => setPatientForm({ ...patientForm, gender: e.target.value })}
                    >
                      <option value="">Gender</option>
                      <option value="Male">Male</option>
                      <option value="Female">Female</option>
                      <option value="Other">Other</option>
                    </select>
                    <input
                      placeholder="Phone"
                      value={patientForm.phone}
                      onChange={(e) => setPatientForm({ ...patientForm, phone: e.target.value })}
                    />
                  </div>
                  <textarea
                    placeholder="Address"
                    value={patientForm.address}
                    onChange={(e) => setPatientForm({ ...patientForm, address: e.target.value })}
                    rows={2}
                  />
                </div>
                <div style={{ marginTop: 16, display: "flex", gap: 8 }}>
                  <Button onClick={updatePatient} disabled={loading}>
                    Update Patient
                  </Button>
                  <Button variant="secondary" onClick={() => setShowPatientForm(false)}>
                    Cancel
                  </Button>
                </div>
              </div>
            )}
            {!showPatientForm && (
              <Button variant="secondary" onClick={() => setShowPatientForm(true)} style={{ marginTop: 8 }}>
                Edit Patient
              </Button>
            )}
          </div>
        )}
      </div>
      
      {/* Service Registration Form */}
      {selectedPatient && (
        <div style={{ border: "1px solid #ddd", padding: 20, borderRadius: 8 }}>
          <h2>Service Registration</h2>
          
          <div style={{ marginBottom: 16 }}>
            <label>Select Services (multiple allowed):</label>
            <div style={{ border: "1px solid #ddd", borderRadius: 4, maxHeight: 200, overflowY: "auto", padding: 8 }}>
              {services.filter(s => s.is_active).map(s => {
                const isSelected = selectedServices.find(sel => sel.id === s.id);
                return (
                  <div
                    key={s.id}
                    onClick={() => toggleServiceSelection(s)}
                    style={{
                      padding: 8,
                      marginBottom: 4,
                      border: isSelected ? "2px solid #007bff" : "1px solid #eee",
                      borderRadius: 4,
                      cursor: "pointer",
                      backgroundColor: isSelected ? "#e7f3ff" : "white",
                    }}
                  >
                    <strong>{s.name}</strong> ({s.code || s.modality?.code || ""}) - Rs. {s.price || s.charges || 0}
                    {isSelected && <span style={{ float: "right", color: "#007bff" }}>✓</span>}
                  </div>
                );
              })}
            </div>
            {selectedServices.length > 0 && (
              <div style={{ marginTop: 8, padding: 8, backgroundColor: "#f0f0f0", borderRadius: 4 }}>
                <strong>Selected ({selectedServices.length}):</strong> {selectedServices.map(s => s.name).join(", ")}
              </div>
            )}
          </div>
          
          {selectedServices.length > 0 && (
            <>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
                  <div>
                  <label>Subtotal (from services):</label>
                  <input
                    type="number"
                    value={servicePrice}
                    readOnly
                    style={{ width: "100%", padding: 8, backgroundColor: "#f5f5f5" }}
                  />
                  <small>Auto-calculated from selected services</small>
                </div>
                <div>
                  <label>Discount:</label>
                  <input
                    type="number"
                    value={discount}
                    onChange={(e) => {
                      setDiscount(e.target.value);
                      const price = parseFloat(servicePrice) || 0;
                      const disc = parseFloat(e.target.value) || 0;
                      setAmountPaid((price - disc).toString());
                    }}
                    style={{ width: "100%", padding: 8 }}
                  />
                </div>
              </div>
              
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
                <div>
                  <label>Net Amount:</label>
                  <input
                    type="number"
                    value={totals.net.toFixed(2)}
                    readOnly
                    style={{ width: "100%", padding: 8, backgroundColor: "#f5f5f5" }}
                  />
                </div>
                <div>
                  <label>Amount Paid:</label>
                  <input
                    type="number"
                    value={amountPaid}
                    onChange={(e) => setAmountPaid(e.target.value)}
                    style={{ width: "100%", padding: 8 }}
                  />
                </div>
              </div>
              
              <div style={{ marginBottom: 16 }}>
                <label>Payment Method:</label>
                <select
                  value={paymentMethod}
                  onChange={(e) => setPaymentMethod(e.target.value)}
                  style={{ width: "100%", padding: 8 }}
                >
                  <option value="cash">Cash</option>
                  <option value="card">Card</option>
                  <option value="online">Online</option>
                  <option value="insurance">Insurance</option>
                  <option value="other">Other</option>
                </select>
              </div>
              
              <div style={{ border: "1px solid #ddd", padding: 16, borderRadius: 4, marginBottom: 16 }}>
                <h3>Summary</h3>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                  <div>Total Amount:</div>
                  <div><strong>Rs. {totals.total.toFixed(2)}</strong></div>
                  <div>Discount:</div>
                  <div><strong>Rs. {totals.discount.toFixed(2)}</strong></div>
                  <div>Net Amount:</div>
                  <div><strong>Rs. {totals.net.toFixed(2)}</strong></div>
                  <div>Amount Paid:</div>
                  <div><strong>Rs. {totals.paid.toFixed(2)}</strong></div>
                  <div>Balance:</div>
                  <div><strong>Rs. {totals.balance.toFixed(2)}</strong></div>
                </div>
              </div>
              
              <div style={{ display: "flex", gap: 8 }}>
                <Button onClick={() => saveVisit(false)} disabled={loading}>
                  Save
                </Button>
                <Button onClick={() => saveVisit(true)} disabled={loading}>
                  Save & Print Receipt
                </Button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
