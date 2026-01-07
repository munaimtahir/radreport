import React, { useEffect, useState } from "react";
import { useAuth } from "../ui/auth";
import { apiGet, apiPost } from "../ui/api";

interface Patient {
  id: string;
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
  code?: string;
  name: string;
  category: string;
  modality: { code: string; name: string };
  charges: number;
  price: number;
  tat_value: number;
  tat_unit: string;
  is_active: boolean;
}

interface CartItem {
  service_id: string;
  service_name: string;
  service_code?: string;
  modality: string;
  charge: number;
  indication: string;
}

export default function FrontDeskIntake() {
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
  
  // Services state
  const [services, setServices] = useState<Service[]>([]);
  const [serviceSearch, setServiceSearch] = useState("");
  const [cart, setCart] = useState<CartItem[]>([]);
  
  // Billing state
  const [discountType, setDiscountType] = useState<"amount" | "percentage">("amount");
  const [discountValue, setDiscountValue] = useState("");
  const [paidAmount, setPaidAmount] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("");
  
  // Load services on mount
  useEffect(() => {
    if (token) {
      loadServices();
    }
  }, [token]);
  
  // Calculate billing totals
  const subtotal = cart.reduce((sum, item) => sum + item.charge, 0);
  const discountAmount = discountType === "amount" 
    ? parseFloat(discountValue) || 0 
    : subtotal * ((parseFloat(discountValue) || 0) / 100);
  const netTotal = subtotal - discountAmount;
  const paid = parseFloat(paidAmount) || netTotal;
  const due = netTotal - paid;
  
  // Update paid amount when net total changes
  useEffect(() => {
    if (!paidAmount || paidAmount === "0") {
      setPaidAmount(netTotal.toFixed(2));
    }
  }, [netTotal]);
  
  const loadServices = async () => {
    if (!token) return;
    try {
      const data = await apiGet("/services/?include_inactive=false", token);
      setServices(data.results || data || []);
      setError("");
    } catch (e: any) {
      console.error("Failed to load services:", e);
      setError(e.message || "Failed to load services");
      setServices([]);
    }
  };
  
  const searchPatients = async (query: string) => {
    if (!token || query.length < 2) {
      setPatientResults([]);
      return;
    }
    try {
      const data = await apiGet(`/patients/?search=${encodeURIComponent(query)}`, token);
      setPatientResults(data.results || data);
    } catch (e: any) {
      setError(e.message);
    }
  };
  
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (patientSearch) {
        searchPatients(patientSearch);
      } else {
        setPatientResults([]);
      }
    }, 300);
    return () => clearTimeout(timeoutId);
  }, [patientSearch]);
  
  const handleSelectPatient = (patient: Patient) => {
    setSelectedPatient(patient);
    setPatientSearch(`${patient.mrn} - ${patient.name}`);
    setPatientResults([]);
    setShowPatientForm(false);
  };
  
  const handleAddNewPatient = () => {
    setSelectedPatient(null);
    setPatientSearch("");
    setShowPatientForm(true);
  };
  
  const handleSavePatient = async () => {
    if (!token) return;
    
    if (!patientForm.name.trim()) {
      setError("Patient name is required");
      return;
    }
    
    setLoading(true);
    setError("");
    setSuccess("");
    
    try {
      const payload: any = {
        name: patientForm.name.trim(),
        gender: patientForm.gender || undefined,
        phone: patientForm.phone.trim() || undefined,
        address: patientForm.address.trim() || undefined,
      };
      
      if (patientForm.age) {
        payload.age = parseInt(patientForm.age);
      }
      if (patientForm.date_of_birth) {
        payload.date_of_birth = patientForm.date_of_birth;
      }
      
      const newPatient = await apiPost("/patients/", token, payload);
      
      // Select the newly created patient
      setSelectedPatient(newPatient);
      setPatientSearch(`${newPatient.mrn} - ${newPatient.name}`);
      setShowPatientForm(false);
      setPatientForm({ name: "", age: "", date_of_birth: "", gender: "", phone: "", address: "" });
      setSuccess(`Patient ${newPatient.mrn} created successfully!`);
      setTimeout(() => setSuccess(""), 3000);
    } catch (e: any) {
      setError(e.message || "Failed to create patient");
    } finally {
      setLoading(false);
    }
  };
  
  const handleAddToCart = (service: Service, e?: React.MouseEvent) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    try {
      if (!service || !service.id) {
        throw new Error("Invalid service selected");
      }
      
      const cartItem: CartItem = {
        service_id: service.id,
        service_name: service.name || "Unknown Service",
        service_code: service.code,
        modality: service.modality?.code || "N/A",
        charge: service.charges || service.price || 0,
        indication: "",
      };
      setCart([...cart, cartItem]);
      setServiceSearch("");
      setError(""); // Clear any previous errors
      setSuccess(`Service "${service.name || 'Unknown'}" added to cart`);
      setTimeout(() => setSuccess(""), 2000);
    } catch (err: any) {
      console.error("Error adding service to cart:", err);
      setError(err.message || "Failed to add service to cart");
      setTimeout(() => setError(""), 5000);
    }
  };
  
  const handleRemoveFromCart = (index: number) => {
    setCart(cart.filter((_, i) => i !== index));
  };
  
  const handleUpdateCartItem = (index: number, field: keyof CartItem, value: any) => {
    const updated = [...cart];
    updated[index] = { ...updated[index], [field]: value };
    setCart(updated);
  };
  
  const handleSubmit = async (printReceipt: boolean = false) => {
    if (!token) return;
    
    if (!selectedPatient && !showPatientForm) {
      setError("Please select or create a patient");
      return;
    }
    
    if (cart.length === 0) {
      setError("Please add at least one service");
      return;
    }
    
    setLoading(true);
    setError("");
    setSuccess("");
    
    try {
      const payload: any = {
        items: cart.map(item => ({
          service_id: item.service_id,
          indication: item.indication,
        })),
        discount_amount: discountType === "amount" ? discountAmount : 0,
        discount_percentage: discountType === "percentage" ? parseFloat(discountValue) : null,
        paid_amount: paid,
        payment_method: paymentMethod,
      };
      
      if (selectedPatient) {
        payload.patient_id = selectedPatient.id;
      } else {
        // New patient
        payload.name = patientForm.name;
        if (patientForm.age) payload.age = parseInt(patientForm.age);
        if (patientForm.date_of_birth) payload.date_of_birth = patientForm.date_of_birth;
        payload.gender = patientForm.gender;
        payload.phone = patientForm.phone;
        payload.address = patientForm.address;
      }
      
      const visit = await apiPost("/visits/unified-intake/", token, payload);
      
      setSuccess(`Visit ${visit.visit_number} created successfully!`);
      
      // Reset form
      setSelectedPatient(null);
      setPatientSearch("");
      setPatientForm({ name: "", age: "", date_of_birth: "", gender: "", phone: "", address: "" });
      setShowPatientForm(false);
      setCart([]);
      setDiscountValue("");
      setPaidAmount("");
      setPaymentMethod("");
      
      // Generate and print receipt if requested
      if (printReceipt && visit.id && token) {
        const API_BASE = (import.meta as any).env.VITE_API_BASE || "http://localhost:8000/api";
        
        // First generate receipt (creates receipt number and PDF if not exists)
        fetch(`${API_BASE}/visits/${visit.id}/generate-receipt/`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        })
          .then((res) => {
            if (!res.ok) throw new Error("Failed to generate receipt");
            return res.json();
          })
          .then((updatedVisit) => {
            // Then fetch the PDF
            const receiptUrl = `${API_BASE}/visits/${visit.id}/receipt/`;
            return fetch(receiptUrl, {
              headers: {
                Authorization: `Bearer ${token}`,
              },
            });
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
            console.error("Failed to generate/load receipt:", err);
            setError("Failed to generate receipt. Please try again.");
          });
      }
      
      setTimeout(() => setSuccess(""), 5000);
    } catch (e: any) {
      setError(e.message || "Failed to create visit");
    } finally {
      setLoading(false);
    }
  };
  
  const filteredServices = services.filter(
    (s) =>
      s.is_active &&
      (s.name.toLowerCase().includes(serviceSearch.toLowerCase()) ||
       s.code?.toLowerCase().includes(serviceSearch.toLowerCase()) ||
       s.modality.code.toLowerCase().includes(serviceSearch.toLowerCase()))
  );
  
  return (
    <div style={{ maxWidth: 1200, margin: "0 auto", padding: 20 }}>
      <h1>Front Desk Intake</h1>
      
      {error && (
        <div style={{ background: "#fee", color: "#c00", padding: 12, borderRadius: 4, marginBottom: 20 }}>
          {error}
        </div>
      )}
      
      {success && (
        <div style={{ background: "#efe", color: "#060", padding: 12, borderRadius: 4, marginBottom: 20 }}>
          {success}
        </div>
      )}
      
      {/* Patient Section */}
      <div style={{ background: "#f9f9f9", padding: 20, borderRadius: 8, marginBottom: 20 }}>
        <h2 style={{ marginTop: 0 }}>Patient Registration</h2>
        
        {!showPatientForm && (
          <div>
            <label style={{ display: "block", marginBottom: 8 }}>Search Patient (MRN, Name, Phone)</label>
            <div style={{ display: "flex", gap: 10, marginBottom: 10 }}>
              <input
                type="text"
                value={patientSearch}
                onChange={(e) => setPatientSearch(e.target.value)}
                placeholder="Search..."
                style={{ flex: 1, padding: 8 }}
              />
              <button onClick={handleAddNewPatient} style={{ padding: "8px 16px" }}>
                New Patient
              </button>
            </div>
            
            {patientResults.length > 0 && (
              <div style={{ border: "1px solid #ddd", borderRadius: 4, maxHeight: 200, overflowY: "auto" }}>
                {patientResults.map((p) => (
                  <div
                    key={p.id}
                    onClick={() => handleSelectPatient(p)}
                    style={{
                      padding: 10,
                      cursor: "pointer",
                      borderBottom: "1px solid #eee",
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = "#f0f0f0")}
                    onMouseLeave={(e) => (e.currentTarget.style.background = "white")}
                  >
                    <strong>{p.mrn}</strong> - {p.name} {p.phone && `(${p.phone})`}
                  </div>
                ))}
              </div>
            )}
            
            {selectedPatient && (
              <div style={{ marginTop: 15, padding: 10, background: "#e8f5e9", borderRadius: 4 }}>
                <strong>Selected:</strong> {selectedPatient.mrn} - {selectedPatient.name}
                {selectedPatient.phone && ` | Phone: ${selectedPatient.phone}`}
              </div>
            )}
          </div>
        )}
        
        {showPatientForm && (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <div>
              <label>Name *</label>
              <input
                type="text"
                value={patientForm.name}
                onChange={(e) => setPatientForm({ ...patientForm, name: e.target.value })}
                required
                style={{ width: "100%", padding: 8 }}
              />
            </div>
            <div>
              <label>Age</label>
              <input
                type="number"
                value={patientForm.age}
                onChange={(e) => setPatientForm({ ...patientForm, age: e.target.value })}
                style={{ width: "100%", padding: 8 }}
              />
            </div>
            <div>
              <label>Date of Birth</label>
              <input
                type="date"
                value={patientForm.date_of_birth}
                onChange={(e) => setPatientForm({ ...patientForm, date_of_birth: e.target.value })}
                style={{ width: "100%", padding: 8 }}
              />
            </div>
            <div>
              <label>Gender</label>
              <select
                value={patientForm.gender}
                onChange={(e) => setPatientForm({ ...patientForm, gender: e.target.value })}
                style={{ width: "100%", padding: 8 }}
              >
                <option value="">Select...</option>
                <option value="M">Male</option>
                <option value="F">Female</option>
                <option value="Other">Other</option>
              </select>
            </div>
            <div>
              <label>Phone</label>
              <input
                type="text"
                value={patientForm.phone}
                onChange={(e) => setPatientForm({ ...patientForm, phone: e.target.value })}
                style={{ width: "100%", padding: 8 }}
              />
            </div>
            <div>
              <label>Address</label>
              <input
                type="text"
                value={patientForm.address}
                onChange={(e) => setPatientForm({ ...patientForm, address: e.target.value })}
                style={{ width: "100%", padding: 8 }}
              />
            </div>
            <div style={{ gridColumn: "1 / -1", display: "flex", gap: 10 }}>
              <button
                onClick={handleSavePatient}
                disabled={loading || !patientForm.name.trim()}
                style={{
                  padding: "8px 16px",
                  background: loading || !patientForm.name.trim() ? "#ccc" : "#007bff",
                  color: "white",
                  border: "none",
                  borderRadius: 4,
                  cursor: loading || !patientForm.name.trim() ? "not-allowed" : "pointer",
                }}
              >
                {loading ? "Saving..." : "Save Patient"}
              </button>
              <button
                onClick={() => {
                  setShowPatientForm(false);
                  setPatientForm({ name: "", age: "", date_of_birth: "", gender: "", phone: "", address: "" });
                }}
                disabled={loading}
                style={{
                  padding: "8px 16px",
                  background: loading ? "#ccc" : "#6c757d",
                  color: "white",
                  border: "none",
                  borderRadius: 4,
                  cursor: loading ? "not-allowed" : "pointer",
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
      
      {/* Services & Billing Section */}
      <div style={{ background: "#f9f9f9", padding: 20, borderRadius: 8 }}>
        <h2 style={{ marginTop: 0 }}>Services & Billing</h2>
        
        {/* Service Selection */}
        <div style={{ marginBottom: 20 }}>
          <label style={{ display: "block", marginBottom: 8 }}>Add Service</label>
          <input
            type="text"
            value={serviceSearch}
            onChange={(e) => setServiceSearch(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                e.stopPropagation();
              }
            }}
            placeholder="Search services..."
            style={{ width: "100%", padding: 8 }}
            autoComplete="off"
          />
          {serviceSearch && filteredServices.length > 0 && (
            <div 
              style={{ border: "1px solid #ddd", borderRadius: 4, marginTop: 5, maxHeight: 200, overflowY: "auto" }}
              onClick={(e) => e.stopPropagation()}
            >
              {filteredServices.map((s) => (
                <div
                  key={s.id}
                  onClick={(e) => handleAddToCart(s, e)}
                  style={{
                    padding: 10,
                    cursor: "pointer",
                    borderBottom: "1px solid #eee",
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = "#f0f0f0")}
                  onMouseLeave={(e) => (e.currentTarget.style.background = "white")}
                >
                  <strong>{s.modality.code}</strong> - {s.name} | Rs. {s.charges || s.price}
                </div>
              ))}
            </div>
          )}
        </div>
        
        {/* Cart */}
        {cart.length > 0 && (
          <div style={{ marginBottom: 20 }}>
            <h3>Selected Services</h3>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ background: "#f0f0f0" }}>
                  <th style={{ padding: 10, textAlign: "left", border: "1px solid #ddd" }}>Service</th>
                  <th style={{ padding: 10, textAlign: "left", border: "1px solid #ddd" }}>Indication</th>
                  <th style={{ padding: 10, textAlign: "right", border: "1px solid #ddd" }}>Charge</th>
                  <th style={{ padding: 10, textAlign: "center", border: "1px solid #ddd" }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {cart.map((item, index) => (
                  <tr key={index}>
                    <td style={{ padding: 10, border: "1px solid #ddd" }}>
                      {item.modality} - {item.service_name}
                    </td>
                    <td style={{ padding: 10, border: "1px solid #ddd" }}>
                      <input
                        type="text"
                        value={item.indication}
                        onChange={(e) => handleUpdateCartItem(index, "indication", e.target.value)}
                        placeholder="Optional indication"
                        style={{ width: "100%", padding: 4 }}
                      />
                    </td>
                    <td style={{ padding: 10, textAlign: "right", border: "1px solid #ddd" }}>
                      Rs. {item.charge.toFixed(2)}
                    </td>
                    <td style={{ padding: 10, textAlign: "center", border: "1px solid #ddd" }}>
                      <button onClick={() => handleRemoveFromCart(index)} style={{ color: "red" }}>
                        Remove
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        
        {/* Billing */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
          <div>
            <h3>Billing Details</h3>
            <div style={{ marginBottom: 12 }}>
              <label style={{ display: "block", marginBottom: 4 }}>Discount Type</label>
              <select
                value={discountType}
                onChange={(e) => {
                  setDiscountType(e.target.value as "amount" | "percentage");
                  setDiscountValue("");
                }}
                style={{ width: "100%", padding: 8 }}
              >
                <option value="amount">Fixed Amount</option>
                <option value="percentage">Percentage</option>
              </select>
            </div>
            <div style={{ marginBottom: 12 }}>
              <label style={{ display: "block", marginBottom: 4 }}>
                Discount {discountType === "percentage" ? "(%)" : "(Rs.)"}
              </label>
              <input
                type="number"
                value={discountValue}
                onChange={(e) => setDiscountValue(e.target.value)}
                step={discountType === "percentage" ? "0.01" : "1"}
                style={{ width: "100%", padding: 8 }}
              />
            </div>
            <div style={{ marginBottom: 12 }}>
              <label style={{ display: "block", marginBottom: 4 }}>Payment Method</label>
              <select
                value={paymentMethod}
                onChange={(e) => setPaymentMethod(e.target.value)}
                style={{ width: "100%", padding: 8 }}
              >
                <option value="">Select...</option>
                <option value="cash">Cash</option>
                <option value="card">Card</option>
                <option value="online">Online</option>
                <option value="insurance">Insurance</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>
          
          <div>
            <h3>Billing Summary</h3>
            <div style={{ background: "white", padding: 15, borderRadius: 4 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                <span>Subtotal:</span>
                <strong>Rs. {subtotal.toFixed(2)}</strong>
              </div>
              {discountAmount > 0 && (
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8, color: "#060" }}>
                  <span>Discount:</span>
                  <strong>-Rs. {discountAmount.toFixed(2)}</strong>
                </div>
              )}
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8, fontSize: 16, fontWeight: "bold" }}>
                <span>Net Total:</span>
                <strong>Rs. {netTotal.toFixed(2)}</strong>
              </div>
              <hr style={{ margin: "12px 0" }} />
              <div style={{ marginBottom: 8 }}>
                <label style={{ display: "block", marginBottom: 4 }}>Paid Amount</label>
                <input
                  type="number"
                  value={paidAmount}
                  onChange={(e) => setPaidAmount(e.target.value)}
                  step="0.01"
                  style={{ width: "100%", padding: 8 }}
                />
              </div>
              {due > 0 && (
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8, color: "#c00" }}>
                  <span>Due Amount:</span>
                  <strong>Rs. {due.toFixed(2)}</strong>
                </div>
              )}
              {due < 0 && (
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8, color: "#060" }}>
                  <span>Change:</span>
                  <strong>Rs. {Math.abs(due).toFixed(2)}</strong>
                </div>
              )}
            </div>
          </div>
        </div>
        
        {/* Action Buttons */}
        <div style={{ marginTop: 20, display: "flex", gap: 10 }}>
          <button
            onClick={() => handleSubmit(false)}
            disabled={loading || cart.length === 0 || (!selectedPatient && !showPatientForm)}
            style={{
              padding: "12px 24px",
              fontSize: 16,
              background: loading ? "#ccc" : "#007bff",
              color: "white",
              border: "none",
              borderRadius: 4,
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            {loading ? "Saving..." : "Save"}
          </button>
          <button
            onClick={() => handleSubmit(true)}
            disabled={loading || cart.length === 0 || (!selectedPatient && !showPatientForm)}
            style={{
              padding: "12px 24px",
              fontSize: 16,
              background: loading ? "#ccc" : "#28a745",
              color: "white",
              border: "none",
              borderRadius: 4,
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            {loading ? "Saving..." : "Save & Print Receipt"}
          </button>
        </div>
      </div>
    </div>
  );
}
