import React, { useEffect, useState, useRef, useCallback } from "react";
import { useAuth } from "../ui/auth";
import { apiGet, apiPatch, apiPost } from "../ui/api";
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
  usage_count?: number;
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
  const [mostUsedServices, setMostUsedServices] = useState<Service[]>([]);
  const [selectedServices, setSelectedServices] = useState<Service[]>([]);
  const [serviceSearch, setServiceSearch] = useState("");
  const [serviceSearchResults, setServiceSearchResults] = useState<Service[]>([]);
  const [serviceSearchFocused, setServiceSearchFocused] = useState(false);
  const [selectedSearchIndex, setSelectedSearchIndex] = useState(-1);
  const [servicePrice, setServicePrice] = useState("");
  const [discount, setDiscount] = useState("");
  const [discountType, setDiscountType] = useState<"amount" | "percentage">("percentage");
  const [amountPaid, setAmountPaid] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("cash");
  
  // Refs for keyboard navigation
  const serviceSearchRef = useRef<HTMLInputElement>(null);
  const patientNameRef = useRef<HTMLInputElement>(null);
  const patientAgeRef = useRef<HTMLInputElement>(null);
  const patientDobRef = useRef<HTMLInputElement>(null);
  const patientGenderRef = useRef<HTMLSelectElement>(null);
  const patientPhoneRef = useRef<HTMLInputElement>(null);
  const patientAddressRef = useRef<HTMLTextAreaElement>(null);
  const discountRef = useRef<HTMLInputElement>(null);
  const amountPaidRef = useRef<HTMLInputElement>(null);
  
  // Debounce timer for service search
  const searchDebounceTimer = useRef<NodeJS.Timeout | null>(null);
  
  useEffect(() => {
    if (token) {
      loadServices();
      loadMostUsedServices();
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
  
  const loadMostUsedServices = async () => {
    if (!token) return;
    try {
      const data = await apiGet("/services/most-used/?limit=5", token);
      setMostUsedServices(data || []);
    } catch (err: any) {
      // Fallback: use local services if endpoint fails
      console.warn("Failed to load most-used services, using local fallback");
      const localServices = services.filter(s => s.is_active).slice(0, 5);
      setMostUsedServices(localServices);
    }
  };
  
  // Debounced service search
  useEffect(() => {
    if (searchDebounceTimer.current) {
      clearTimeout(searchDebounceTimer.current);
    }
    
    if (serviceSearch.trim().length >= 2) {
      searchDebounceTimer.current = setTimeout(() => {
        const filtered = services.filter(s => 
          s.is_active && (
            s.name.toLowerCase().includes(serviceSearch.toLowerCase()) ||
            s.code?.toLowerCase().includes(serviceSearch.toLowerCase()) ||
            s.modality?.code?.toLowerCase().includes(serviceSearch.toLowerCase())
          )
        ).slice(0, 10);
        setServiceSearchResults(filtered);
        setSelectedSearchIndex(-1);
      }, 300);
    } else {
      setServiceSearchResults([]);
      setSelectedSearchIndex(-1);
    }
    
    return () => {
      if (searchDebounceTimer.current) {
        clearTimeout(searchDebounceTimer.current);
      }
    };
  }, [serviceSearch, services]);
  
  // DOB ↔ Age linkage
  const calculateAgeFromDOB = (dob: string): string => {
    if (!dob) return "";
    const birthDate = new Date(dob);
    const today = new Date();
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
      age--;
    }
    return age.toString();
  };
  
  const calculateDOBFromAge = (age: string): string => {
    if (!age) return "";
    const ageNum = parseInt(age);
    if (isNaN(ageNum)) return "";
    const today = new Date();
    const birthYear = today.getFullYear() - ageNum;
    return `${birthYear}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
  };
  
  // Keyboard navigation: Enter behaves like Tab
  const handleEnterAsTab = (e: React.KeyboardEvent, nextRef?: React.RefObject<HTMLElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (nextRef?.current) {
        nextRef.current.focus();
      } else {
        // Find next focusable element
        const form = e.currentTarget.closest('form') || e.currentTarget.closest('div');
        if (form) {
          const focusableElements = form.querySelectorAll(
            'input, select, textarea, button:not([disabled])'
          );
          const currentIndex = Array.from(focusableElements).indexOf(e.currentTarget as HTMLElement);
          const nextElement = focusableElements[currentIndex + 1] as HTMLElement;
          if (nextElement) {
            nextElement.focus();
          }
        }
      }
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
      
      // Auto-focus service search after patient save (v2 feature)
      setTimeout(() => {
        serviceSearchRef.current?.focus();
      }, 100);
    } catch (err: any) {
      setError(err.message || "Failed to create patient");
    } finally {
      setLoading(false);
    }
  };
  
  const addService = (service: Service) => {
    setSelectedServices(prev => {
      const exists = prev.find(s => s.id === service.id);
      if (exists) {
        return prev.filter(s => s.id !== service.id);
      } else {
        const updated = [...prev, service];
        const totalPrice = updated.reduce((sum, s) => sum + (s.price || s.charges || 0), 0);
        setServicePrice(totalPrice.toString());
        return updated;
      }
    });
    setServiceSearch("");
    setServiceSearchResults([]);
    serviceSearchRef.current?.focus();
  };
  
  const removeService = (serviceId: string) => {
    setSelectedServices(prev => {
      const filtered = prev.filter(s => s.id !== serviceId);
      const totalPrice = filtered.reduce((sum, s) => sum + (s.price || s.charges || 0), 0);
      setServicePrice(totalPrice.toString());
      return filtered;
    });
  };
  
  // Handle service search keyboard navigation
  const handleServiceSearchKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedSearchIndex(prev => 
        prev < serviceSearchResults.length - 1 ? prev + 1 : prev
      );
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedSearchIndex(prev => prev > 0 ? prev - 1 : -1);
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (selectedSearchIndex >= 0 && serviceSearchResults[selectedSearchIndex]) {
        addService(serviceSearchResults[selectedSearchIndex]);
      } else if (serviceSearchResults.length > 0) {
        addService(serviceSearchResults[0]);
      }
    } else if (e.key === "Escape") {
      setServiceSearchResults([]);
      setSelectedSearchIndex(-1);
    } else {
      handleEnterAsTab(e, discountRef);
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
      
      const updated = await apiPatch(`/patients/${selectedPatient.id}/`, token, patientData);
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
    
    // Calculate discount (amount or percentage)
    let disc = 0;
    if (discountType === "percentage") {
      const discPercent = Math.min(Math.max(parseFloat(discount) || 0, 0), 100); // Clamp 0-100
      disc = total * (discPercent / 100);
    } else {
      disc = parseFloat(discount) || 0;
    }
    
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
        // Use correct endpoint pattern: /api/pdf/{id}/receipt/ (matches PDFViewSet action)
        const receiptUrl = `${API_BASE}/pdf/${visit.id}/receipt/`;
        
        fetch(receiptUrl, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })
          .then((res) => {
            if (!res.ok) {
              if (res.status === 401) {
                throw new Error("Authentication failed. Please log in again.");
              }
              throw new Error(`Failed to fetch receipt PDF: ${res.status} ${res.statusText}`);
            }
            // Verify content-type is PDF
            const contentType = res.headers.get("content-type");
            if (!contentType || !contentType.includes("application/pdf")) {
              console.warn("Expected PDF but got:", contentType);
            }
            return res.blob();
          })
          .then((blob) => {
            const url = window.URL.createObjectURL(blob);
            const win = window.open(url, "_blank");
            if (win) {
              // Wait for window to load before attempting print
              win.onload = () => {
                // Trigger print dialog
                win.print();
              };
              // Clean up blob URL after a delay (give time for print dialog)
              setTimeout(() => window.URL.revokeObjectURL(url), 60000); // 60 seconds to allow for print
            } else {
              // Popup blocked, try fallback
              const link = document.createElement("a");
              link.href = url;
              link.target = "_blank";
              link.download = `receipt_${visit.visit_id || visit.id}.pdf`;
              document.body.appendChild(link);
              link.click();
              document.body.removeChild(link);
              setTimeout(() => window.URL.revokeObjectURL(url), 60000);
            }
          })
          .catch((err) => {
            console.error("Failed to load receipt:", err);
            setError(`Failed to load receipt: ${err.message}`);
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
                    ref={patientNameRef}
                    placeholder="Name *"
                    value={patientForm.name}
                    onChange={(e) => setPatientForm({ ...patientForm, name: e.target.value })}
                    onKeyDown={(e) => handleEnterAsTab(e, patientAgeRef)}
                    required
                  />
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                    <input
                      ref={patientAgeRef}
                      type="number"
                      placeholder="Age"
                      value={patientForm.age}
                      onChange={(e) => {
                        const age = e.target.value;
                        setPatientForm({ ...patientForm, age });
                        // Auto-calculate DOB from age
                        if (age) {
                          const dob = calculateDOBFromAge(age);
                          setPatientForm(prev => ({ ...prev, age, date_of_birth: dob }));
                        }
                      }}
                      onKeyDown={(e) => handleEnterAsTab(e, patientDobRef)}
                    />
                    <input
                      ref={patientDobRef}
                      type="date"
                      placeholder="Date of Birth"
                      value={patientForm.date_of_birth}
                      onChange={(e) => {
                        const dob = e.target.value;
                        setPatientForm({ ...patientForm, date_of_birth: dob });
                        // Auto-calculate age from DOB
                        if (dob) {
                          const age = calculateAgeFromDOB(dob);
                          setPatientForm(prev => ({ ...prev, date_of_birth: dob, age }));
                        }
                      }}
                      onKeyDown={(e) => handleEnterAsTab(e, patientGenderRef)}
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
                    ref={patientNameRef}
                    placeholder="Name"
                    value={patientForm.name}
                    onChange={(e) => setPatientForm({ ...patientForm, name: e.target.value })}
                    onKeyDown={(e) => handleEnterAsTab(e, patientAgeRef)}
                  />
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                    <input
                      ref={patientAgeRef}
                      type="number"
                      placeholder="Age"
                      value={patientForm.age}
                      onChange={(e) => {
                        const age = e.target.value;
                        setPatientForm({ ...patientForm, age });
                        if (age) {
                          const dob = calculateDOBFromAge(age);
                          setPatientForm(prev => ({ ...prev, age, date_of_birth: dob }));
                        }
                      }}
                      onKeyDown={(e) => handleEnterAsTab(e, patientDobRef)}
                    />
                    <input
                      ref={patientDobRef}
                      type="date"
                      placeholder="Date of Birth"
                      value={patientForm.date_of_birth}
                      onChange={(e) => {
                        const dob = e.target.value;
                        setPatientForm({ ...patientForm, date_of_birth: dob });
                        if (dob) {
                          const age = calculateAgeFromDOB(dob);
                          setPatientForm(prev => ({ ...prev, date_of_birth: dob, age }));
                        }
                      }}
                      onKeyDown={(e) => handleEnterAsTab(e, patientGenderRef)}
                    />
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                    <select
                      ref={patientGenderRef}
                      value={patientForm.gender}
                      onChange={(e) => setPatientForm({ ...patientForm, gender: e.target.value })}
                      onKeyDown={(e) => handleEnterAsTab(e, patientPhoneRef)}
                    >
                      <option value="">Gender</option>
                      <option value="Male">Male</option>
                      <option value="Female">Female</option>
                      <option value="Other">Other</option>
                    </select>
                    <input
                      ref={patientPhoneRef}
                      placeholder="Phone"
                      value={patientForm.phone}
                      onChange={(e) => setPatientForm({ ...patientForm, phone: e.target.value })}
                      onKeyDown={(e) => handleEnterAsTab(e, patientAddressRef)}
                    />
                  </div>
                  <textarea
                    ref={patientAddressRef}
                    placeholder="Address"
                    value={patientForm.address}
                    onChange={(e) => setPatientForm({ ...patientForm, address: e.target.value })}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        handleEnterAsTab(e);
                      }
                    }}
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
            <label>Add Service</label>
            
            {/* Most-used services quick buttons */}
            {mostUsedServices.length > 0 && (
              <div style={{ marginBottom: 12 }}>
                <small style={{ display: "block", marginBottom: 6, color: "#666" }}>Most Used:</small>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                  {mostUsedServices.map(service => (
                    <button
                      key={service.id}
                      type="button"
                      onClick={() => addService(service)}
                      disabled={selectedServices.some(s => s.id === service.id)}
                      style={{
                        padding: "6px 12px",
                        fontSize: 12,
                        border: "1px solid #ddd",
                        borderRadius: 4,
                        backgroundColor: selectedServices.some(s => s.id === service.id) ? "#e7f3ff" : "white",
                        cursor: selectedServices.some(s => s.id === service.id) ? "not-allowed" : "pointer",
                      }}
                    >
                      {service.name} ({service.usage_count || 0})
                    </button>
                  ))}
                </div>
              </div>
            )}
            
            {/* Service search with dropdown */}
            <div style={{ position: "relative", marginBottom: 12 }}>
              <input
                ref={serviceSearchRef}
                type="text"
                placeholder="Search services..."
                value={serviceSearch}
                onChange={(e) => setServiceSearch(e.target.value)}
                onKeyDown={handleServiceSearchKeyDown}
                onFocus={() => setServiceSearchFocused(true)}
                onBlur={() => setTimeout(() => setServiceSearchFocused(false), 200)}
                style={{ width: "100%", padding: 8, fontSize: 14 }}
                autoComplete="off"
              />
              
              {/* Search results dropdown */}
              {serviceSearchFocused && serviceSearchResults.length > 0 && (
                <div
                  style={{
                    position: "absolute",
                    top: "100%",
                    left: 0,
                    right: 0,
                    border: "1px solid #ddd",
                    borderRadius: 4,
                    backgroundColor: "white",
                    maxHeight: 200,
                    overflowY: "auto",
                    zIndex: 1000,
                    marginTop: 4,
                  }}
                >
                  {serviceSearchResults.map((service, index) => (
                    <div
                      key={service.id}
                      onClick={() => addService(service)}
                      style={{
                        padding: 10,
                        cursor: "pointer",
                        backgroundColor: index === selectedSearchIndex ? "#e7f3ff" : "white",
                        borderBottom: "1px solid #eee",
                      }}
                      onMouseEnter={() => setSelectedSearchIndex(index)}
                    >
                      <strong>{service.name}</strong> ({service.code || service.modality?.code || ""}) - Rs. {service.price || service.charges || 0}
                    </div>
                  ))}
                </div>
              )}
            </div>
            
            {/* Selected services list */}
            {selectedServices.length > 0 && (
              <div style={{ marginTop: 12 }}>
                <strong>Selected Services ({selectedServices.length}):</strong>
                <div style={{ marginTop: 8, display: "flex", flexDirection: "column", gap: 6 }}>
                  {selectedServices.map(service => (
                    <div
                      key={service.id}
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        padding: 8,
                        backgroundColor: "#f0f0f0",
                        borderRadius: 4,
                      }}
                    >
                      <span>
                        <strong>{service.name}</strong> - Rs. {service.price || service.charges || 0}
                      </span>
                      <button
                        type="button"
                        onClick={() => removeService(service.id)}
                        style={{
                          padding: "4px 8px",
                          fontSize: 12,
                          backgroundColor: "#dc3545",
                          color: "white",
                          border: "none",
                          borderRadius: 4,
                          cursor: "pointer",
                        }}
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                </div>
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
                  <div style={{ display: "flex", gap: 8 }}>
                    <select
                      value={discountType}
                      onChange={(e) => setDiscountType(e.target.value as "amount" | "percentage")}
                      style={{ padding: 8, width: 100 }}
                    >
                      <option value="percentage">%</option>
                      <option value="amount">Rs.</option>
                    </select>
                    <input
                      ref={discountRef}
                      type="number"
                      value={discount}
                      onChange={(e) => {
                        let value = e.target.value;
                        // Clamp percentage to 0-100
                        if (discountType === "percentage") {
                          const num = parseFloat(value) || 0;
                          value = Math.min(Math.max(num, 0), 100).toString();
                        }
                        setDiscount(value);
                        const totals = calculateTotals();
                        setAmountPaid(totals.net.toString());
                      }}
                      onKeyDown={(e) => handleEnterAsTab(e, amountPaidRef)}
                      min={discountType === "percentage" ? 0 : undefined}
                      max={discountType === "percentage" ? 100 : undefined}
                      style={{ flex: 1, padding: 8 }}
                      placeholder={discountType === "percentage" ? "0-100" : "Amount"}
                    />
                  </div>
                  {discountType === "percentage" && discount && (
                    <small style={{ color: "#666" }}>
                      {parseFloat(discount) || 0}% = Rs. {calculateTotals().discount.toFixed(2)}
                    </small>
                  )}
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
                    ref={amountPaidRef}
                    type="number"
                    value={amountPaid}
                    onChange={(e) => setAmountPaid(e.target.value)}
                    onKeyDown={(e) => handleEnterAsTab(e)}
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
