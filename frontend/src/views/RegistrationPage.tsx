import React, { useEffect, useState } from "react";
import { useAuth } from "../ui/auth";
import { apiGet, apiPost } from "../ui/api";

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

interface ServiceCatalog {
  id: string;
  code: string;
  name: string;
  default_price: number;
  turnaround_time: number;
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
  const [services, setServices] = useState<ServiceCatalog[]>([]);
  const [selectedService, setSelectedService] = useState<ServiceCatalog | null>(null);
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
      const data = await apiGet("/workflow/service-catalog/", token);
      setServices(data.results || data || []);
    } catch (err: any) {
      setError(err.message || "Failed to load services");
    }
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
    const total = parseFloat(servicePrice) || 0;
    const disc = parseFloat(discount) || 0;
    const net = total - disc;
    const paid = parseFloat(amountPaid) || net;
    const balance = net - paid;
    return { total, discount: disc, net, paid, balance };
  };
  
  const saveVisit = async (printReceipt: boolean = false) => {
    if (!token || !selectedPatient || !selectedService) {
      setError("Please select a patient and service");
      return;
    }
    
    setLoading(true);
    setError("");
    try {
      const totals = calculateTotals();
      const visitData = {
        patient_id: selectedPatient.id,
        service_id: selectedService.id,
        total_amount: totals.total,
        discount: totals.discount,
        net_amount: totals.net,
        balance_amount: totals.balance,
        amount_paid: totals.paid,
        payment_method: paymentMethod,
      };
      
      const visit = await apiPost("/workflow/visits/create_visit/", token, visitData);
      setSuccess(`Service visit created: ${visit.visit_id}`);
      
      // Reset form
      setSelectedService(null);
      setServicePrice("");
      setDiscount("");
      setAmountPaid("");
      
      if (printReceipt) {
        // Open receipt PDF in new window
        window.open(`/api/pdf/receipt/${visit.id}/`, "_blank");
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
      <h1>Registration Desk</h1>
      
      {error && <div style={{ color: "red", marginBottom: 16 }}>{error}</div>}
      {success && <div style={{ color: "green", marginBottom: 16 }}>{success}</div>}
      
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
              <button onClick={searchPatients} style={{ marginTop: 8, padding: "8px 16px" }}>
                Search
              </button>
              <button onClick={() => setShowPatientForm(true)} style={{ marginTop: 8, marginLeft: 8, padding: "8px 16px" }}>
                New Patient
              </button>
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
                <div style={{ marginTop: 16 }}>
                  <button onClick={createPatient} disabled={loading || !patientForm.name}>
                    Create Patient
                  </button>
                  <button onClick={() => setShowPatientForm(false)} style={{ marginLeft: 8 }}>
                    Cancel
                  </button>
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
                <div style={{ marginTop: 16 }}>
                  <button onClick={updatePatient} disabled={loading}>
                    Update Patient
                  </button>
                  <button onClick={() => setShowPatientForm(false)} style={{ marginLeft: 8 }}>
                    Cancel
                  </button>
                </div>
              </div>
            )}
            {!showPatientForm && (
              <button onClick={() => setShowPatientForm(true)} style={{ marginTop: 8 }}>
                Edit Patient
              </button>
            )}
          </div>
        )}
      </div>
      
      {/* Service Registration Form */}
      {selectedPatient && (
        <div style={{ border: "1px solid #ddd", padding: 20, borderRadius: 8 }}>
          <h2>Service Registration</h2>
          
          <div style={{ marginBottom: 16 }}>
            <label>Select Service:</label>
            <select
              value={selectedService?.id || ""}
              onChange={(e) => {
                const service = services.find(s => s.id === e.target.value);
                setSelectedService(service || null);
                if (service) {
                  setServicePrice(service.default_price.toString());
                  setAmountPaid(service.default_price.toString());
                }
              }}
              style={{ width: "100%", padding: 8, fontSize: 14 }}
            >
              <option value="">-- Select Service --</option>
              {services.filter(s => s.is_active).map(s => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.code}) - Rs. {s.default_price}
                </option>
              ))}
            </select>
          </div>
          
          {selectedService && (
            <>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
                <div>
                  <label>Service Price:</label>
                  <input
                    type="number"
                    value={servicePrice}
                    onChange={(e) => {
                      setServicePrice(e.target.value);
                      const price = parseFloat(e.target.value) || 0;
                      const disc = parseFloat(discount) || 0;
                      setAmountPaid((price - disc).toString());
                    }}
                    style={{ width: "100%", padding: 8 }}
                  />
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
              
              <div>
                <button
                  onClick={() => saveVisit(false)}
                  disabled={loading}
                  style={{ padding: "12px 24px", fontSize: 16, marginRight: 8 }}
                >
                  Save
                </button>
                <button
                  onClick={() => saveVisit(true)}
                  disabled={loading}
                  style={{ padding: "12px 24px", fontSize: 16 }}
                >
                  Save & Print Receipt
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
