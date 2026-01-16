import React, { useEffect, useMemo, useRef, useState } from "react";
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
  notes?: string;
}

interface Service {
  id: string;
  code: string;
  name: string;
  price: number;
  charges: number;
  category: string;
  usage_count?: number;
  modality: {
    code: string;
    name: string;
  };
  is_active: boolean;
}

interface ParsedNotes {
  fatherHusband: string;
  cnic: string;
  comments: string;
  extraNotes: string;
}

const LOCAL_USAGE_KEY = "rims:service-usage";

const parsePatientNotes = (notes?: string): ParsedNotes => {
  const parsed: ParsedNotes = {
    fatherHusband: "",
    cnic: "",
    comments: "",
    extraNotes: "",
  };

  if (!notes) {
    return parsed;
  }

  const lines = notes.split("\n").map((line) => line.trim()).filter(Boolean);
  const remaining: string[] = [];

  lines.forEach((line) => {
    if (line.toLowerCase().startsWith("father/husband:")) {
      parsed.fatherHusband = line.replace(/father\/husband:/i, "").trim();
    } else if (line.toLowerCase().startsWith("cnic:")) {
      parsed.cnic = line.replace(/cnic:/i, "").trim();
    } else if (line.toLowerCase().startsWith("comments:")) {
      parsed.comments = line.replace(/comments:/i, "").trim();
    } else {
      remaining.push(line);
    }
  });

  if (!parsed.comments && remaining.length > 0) {
    parsed.comments = remaining.join("\n");
  }
  parsed.extraNotes = remaining.join("\n");

  return parsed;
};

const buildNotes = (existingNotes: string | undefined, fields: ParsedNotes): string => {
  const cleanExisting = (existingNotes || "")
    .split("\n")
    .filter((line) => !line.toLowerCase().startsWith("father/husband:")
      && !line.toLowerCase().startsWith("cnic:")
      && !line.toLowerCase().startsWith("comments:"))
    .join("\n")
    .trim();

  const tagged: string[] = [];
  if (fields.fatherHusband.trim()) {
    tagged.push(`Father/Husband: ${fields.fatherHusband.trim()}`);
  }
  if (fields.cnic.trim()) {
    tagged.push(`CNIC: ${fields.cnic.trim()}`);
  }
  if (fields.comments.trim()) {
    tagged.push(`Comments: ${fields.comments.trim()}`);
  }

  return [cleanExisting, tagged.join("\n")].filter(Boolean).join("\n");
};

const calculateAgeFromDob = (dateString: string) => {
  if (!dateString) return { years: "", months: "", days: "" };
  const dob = new Date(dateString);
  if (Number.isNaN(dob.getTime())) return { years: "", months: "", days: "" };
  const today = new Date();
  let years = today.getFullYear() - dob.getFullYear();
  let months = today.getMonth() - dob.getMonth();
  let days = today.getDate() - dob.getDate();

  if (days < 0) {
    months -= 1;
    const previousMonth = new Date(today.getFullYear(), today.getMonth(), 0);
    days += previousMonth.getDate();
  }
  if (months < 0) {
    years -= 1;
    months += 12;
  }

  return {
    years: years >= 0 ? String(years) : "",
    months: months >= 0 ? String(months) : "",
    days: days >= 0 ? String(days) : "",
  };
};

const calculateDobFromAge = (years: string, months: string, days: string) => {
  const y = parseInt(years || "0", 10) || 0;
  const m = parseInt(months || "0", 10) || 0;
  const d = parseInt(days || "0", 10) || 0;
  if (y === 0 && m === 0 && d === 0) return "";
  const today = new Date();
  const estimated = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  estimated.setFullYear(estimated.getFullYear() - y);
  estimated.setMonth(estimated.getMonth() - m);
  estimated.setDate(estimated.getDate() - d);
  return estimated.toISOString().slice(0, 10);
};

const getLocalUsageMap = () => {
  try {
    const stored = localStorage.getItem(LOCAL_USAGE_KEY);
    if (!stored) return {} as Record<string, number>;
    return JSON.parse(stored) as Record<string, number>;
  } catch {
    return {} as Record<string, number>;
  }
};

const updateLocalUsage = (serviceId: string) => {
  const usage = getLocalUsageMap();
  usage[serviceId] = (usage[serviceId] || 0) + 1;
  localStorage.setItem(LOCAL_USAGE_KEY, JSON.stringify(usage));
};

const getLocalMostUsed = (services: Service[]) => {
  const usage = getLocalUsageMap();
  return [...services]
    .filter((service) => service.is_active)
    .sort((a, b) => (usage[b.id] || 0) - (usage[a.id] || 0))
    .slice(0, 5);
};

export default function RegistrationPage() {
  const { token } = useAuth();
  const pageRef = useRef<HTMLDivElement>(null);
  const serviceSearchRef = useRef<HTMLInputElement>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const [success, setSuccess] = useState<string>("");

  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [patientResults, setPatientResults] = useState<Patient[]>([]);
  const [activePatientIndex, setActivePatientIndex] = useState(-1);
  const [patientLocked, setPatientLocked] = useState(false);
  const [patientForm, setPatientForm] = useState({
    phone: "",
    name: "",
    fatherHusband: "",
    date_of_birth: "",
    ageYears: "",
    ageMonths: "",
    ageDays: "",
    gender: "",
    cnic: "",
    address: "",
    comments: "",
  });

  const [services, setServices] = useState<Service[]>([]);
  const [mostUsedServices, setMostUsedServices] = useState<Service[]>([]);
  const [selectedServices, setSelectedServices] = useState<Service[]>([]);
  const [serviceSearch, setServiceSearch] = useState("");
  const [activeServiceIndex, setActiveServiceIndex] = useState(-1);
  const [discountPercentage, setDiscountPercentage] = useState("");
  const [amountPaid, setAmountPaid] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("cash");

  useEffect(() => {
    if (token) {
      loadServices();
    }
  }, [token]);

  useEffect(() => {
    if (!token) return;
    if (!patientForm.phone.trim()) {
      setPatientResults([]);
      setActivePatientIndex(-1);
      return;
    }
    const timer = window.setTimeout(() => {
      searchPatients(patientForm.phone.trim());
    }, 300);

    return () => window.clearTimeout(timer);
  }, [patientForm.phone, token]);

  useEffect(() => {
    if (selectedPatient) {
      setPatientLocked(true);
      setTimeout(() => serviceSearchRef.current?.focus(), 0);
    }
  }, [selectedPatient]);

  const loadServices = async () => {
    if (!token) return;
    try {
      const data = await apiGet("/services/", token);
      const serviceList = data.results || data || [];
      setServices(serviceList);
      await loadMostUsedServices(serviceList);
    } catch (err: any) {
      setError(err.message || "Failed to load services");
    }
  };

  const loadMostUsedServices = async (serviceList: Service[]) => {
    if (!token) return;
    try {
      const data = await apiGet("/services/most-used/", token);
      if (Array.isArray(data) && data.length > 0) {
        setMostUsedServices(data);
        return;
      }
    } catch (err) {
      // Fall back to local usage when endpoint is unavailable
    }
    setMostUsedServices(getLocalMostUsed(serviceList));
  };

  const searchPatients = async (query: string) => {
    if (!token || !query.trim()) return;
    try {
      const data = await apiGet(`/patients/?search=${encodeURIComponent(query)}`, token);
      const results = data.results || data || [];
      setPatientResults(results);
      setActivePatientIndex(results.length > 0 ? 0 : -1);
    } catch (err: any) {
      setError(err.message || "Failed to search patients");
    }
  };

  const focusNextElement = (current: HTMLElement) => {
    if (!pageRef.current) return;
    const focusable = Array.from(
      pageRef.current.querySelectorAll<HTMLElement>(
        "input, select, textarea, button, [tabindex]:not([tabindex='-1'])"
      )
    ).filter((el) => !el.hasAttribute("disabled") && el.tabIndex !== -1);
    const currentIndex = focusable.indexOf(current);
    if (currentIndex >= 0 && currentIndex < focusable.length - 1) {
      focusable[currentIndex + 1]?.focus();
    }
  };

  const handleEnterAsTab = (event: React.KeyboardEvent<HTMLElement>) => {
    if (event.key !== "Enter") return;
    event.preventDefault();
    focusNextElement(event.currentTarget as HTMLElement);
  };

  const handleSelectPatient = (patient: Patient) => {
    const parsedNotes = parsePatientNotes(patient.notes);
    const derivedAge = patient.date_of_birth ? calculateAgeFromDob(patient.date_of_birth) : null;
    setSelectedPatient(patient);
    setPatientForm({
      phone: patient.phone || "",
      name: patient.name || "",
      fatherHusband: parsedNotes.fatherHusband,
      date_of_birth: patient.date_of_birth || "",
      ageYears: derivedAge?.years || (patient.age ? String(patient.age) : ""),
      ageMonths: derivedAge?.months || "",
      ageDays: derivedAge?.days || "",
      gender: patient.gender || "",
      cnic: parsedNotes.cnic,
      address: patient.address || "",
      comments: parsedNotes.comments || "",
    });
    setPatientResults([]);
  };

  const buildPatientPayload = (existingNotes?: string) => {
    const payload: any = {
      name: patientForm.name.trim(),
      gender: patientForm.gender,
      phone: patientForm.phone.trim(),
      address: patientForm.address.trim(),
    };
    if (patientForm.date_of_birth) {
      payload.date_of_birth = patientForm.date_of_birth;
    }
    if (patientForm.ageYears) {
      payload.age = parseInt(patientForm.ageYears, 10);
    }
    const notesPayload = buildNotes(existingNotes, {
      fatherHusband: patientForm.fatherHusband,
      cnic: patientForm.cnic,
      comments: patientForm.comments,
      extraNotes: "",
    });
    if (notesPayload) {
      payload.notes = notesPayload;
    }
    return payload;
  };

  const savePatient = async () => {
    if (!token) return;
    if (!patientForm.phone.trim() || !patientForm.name.trim() || !patientForm.gender) {
      setError("Mobile number, patient name, and gender are required.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const payload = buildPatientPayload(selectedPatient?.notes);
      const patient = selectedPatient
        ? await apiPatch(`/patients/${selectedPatient.id}/`, token, payload)
        : await apiPost("/patients/", token, payload);
      setSelectedPatient(patient);
      setPatientLocked(true);
      setSuccess(selectedPatient ? "Patient updated successfully" : "Patient created successfully");
      setTimeout(() => serviceSearchRef.current?.focus(), 0);
    } catch (err: any) {
      setError(err.message || "Failed to save patient");
    } finally {
      setLoading(false);
    }
  };

  const resetPatient = () => {
    setSelectedPatient(null);
    setPatientLocked(false);
    setPatientForm({
      phone: "",
      name: "",
      fatherHusband: "",
      date_of_birth: "",
      ageYears: "",
      ageMonths: "",
      ageDays: "",
      gender: "",
      cnic: "",
      address: "",
      comments: "",
    });
  };

  const estimatedDob =
    patientForm.date_of_birth
      ? ""
      : calculateDobFromAge(patientForm.ageYears, patientForm.ageMonths, patientForm.ageDays);

  const filteredServices = useMemo(() => {
    const query = serviceSearch.trim().toLowerCase();
    if (!query) return [] as Service[];
    return services.filter((service) => {
      const matchName = service.name.toLowerCase().includes(query);
      const matchCode = service.code?.toLowerCase().includes(query);
      return matchName || matchCode;
    }).slice(0, 8);
  }, [serviceSearch, services]);

  const addServiceToCart = (service: Service) => {
    if (!service || !service.id) return;
    setSelectedServices((prev) => {
      if (prev.find((item) => item.id === service.id)) return prev;
      return [...prev, service];
    });
    updateLocalUsage(service.id);
    setServiceSearch("");
    setActiveServiceIndex(-1);
    setTimeout(() => serviceSearchRef.current?.focus(), 0);
    setMostUsedServices(getLocalMostUsed(services));
  };

  const removeServiceFromCart = (serviceId: string) => {
    setSelectedServices((prev) => prev.filter((item) => item.id !== serviceId));
  };

  const handleServiceSearchKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveServiceIndex((prev) => Math.min(prev + 1, filteredServices.length - 1));
      return;
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveServiceIndex((prev) => Math.max(prev - 1, 0));
      return;
    }
    if (event.key === "Enter") {
      event.preventDefault();
      if (filteredServices.length > 0) {
        const targetIndex = activeServiceIndex >= 0 ? activeServiceIndex : 0;
        const targetService = filteredServices[targetIndex];
        if (targetService) {
          addServiceToCart(targetService);
          return;
        }
      }
      focusNextElement(event.currentTarget);
    }
  };

  const handlePatientSearchKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActivePatientIndex((prev) => Math.min(prev + 1, patientResults.length - 1));
      return;
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      setActivePatientIndex((prev) => Math.max(prev - 1, 0));
      return;
    }
    if (event.key === "Enter") {
      event.preventDefault();
      if (patientResults.length > 0) {
        const targetIndex = activePatientIndex >= 0 ? activePatientIndex : 0;
        const targetPatient = patientResults[targetIndex];
        if (targetPatient) {
          handleSelectPatient(targetPatient);
          return;
        }
      }
      focusNextElement(event.currentTarget);
    }
  };

  const handleDobChange = (value: string) => {
    const age = calculateAgeFromDob(value);
    setPatientForm((prev) => ({
      ...prev,
      date_of_birth: value,
      ageYears: age.years,
      ageMonths: age.months,
      ageDays: age.days,
    }));
  };

  const handleAgeChange = (field: "ageYears" | "ageMonths" | "ageDays", value: string) => {
    setPatientForm((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const subtotal = selectedServices.reduce((sum, service) => sum + (service.price || service.charges || 0), 0);
  const discountPercentValue = Math.min(Math.max(parseFloat(discountPercentage) || 0, 0), 100);
  const discountAmount = (subtotal * discountPercentValue) / 100;
  const totalAmount = subtotal;
  const netAmount = totalAmount - discountAmount;
  const paidAmount = parseFloat(amountPaid) || netAmount;
  const balanceAmount = netAmount - paidAmount;

  useEffect(() => {
    if (selectedServices.length === 0) {
      setAmountPaid("");
      return;
    }
    if (!amountPaid) {
      setAmountPaid(netAmount.toFixed(2));
    }
  }, [selectedServices.length, netAmount, amountPaid]);

  const saveVisit = async (printReceipt: boolean = false) => {
    if (!token || !selectedPatient || selectedServices.length === 0) {
      setError("Please select a patient and at least one service");
      return;
    }

    setLoading(true);
    setError("");
    try {
      const visitData = {
        patient_id: selectedPatient.id,
        service_ids: selectedServices.map((service) => service.id),
        subtotal,
        total_amount: totalAmount,
        discount: discountAmount,
        discount_percentage: discountPercentValue,
        net_amount: netAmount,
        amount_paid: paidAmount,
        payment_method: paymentMethod,
      };

      const visit = await apiPost("/workflow/visits/create_visit/", token, visitData);
      setSuccess(`Service visit created: ${visit.visit_id}`);

      setSelectedServices([]);
      setDiscountPercentage("");
      setAmountPaid("");

      if (printReceipt) {
        const API_BASE = (import.meta as any).env.VITE_API_BASE
          || ((import.meta as any).env.PROD ? "/api" : "http://localhost:8000/api");
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
              win.onload = () => {
                win.print();
              };
              setTimeout(() => window.URL.revokeObjectURL(url), 60000);
            } else {
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

  return (
    <div ref={pageRef} style={{ maxWidth: 1200, margin: "0 auto" }}>
      <PageHeader title="Registration Desk" />

      {error && <ErrorAlert message={error} onDismiss={() => setError("")} />}
      {success && <SuccessAlert message={success} onDismiss={() => setSuccess("")} />}

      <div style={{ border: "1px solid #ddd", padding: 20, marginBottom: 20, borderRadius: 8 }}>
        <h2>Patient Information</h2>
        <div style={{ display: "grid", gap: 12 }}>
          <div style={{ position: "relative" }}>
            <label style={{ display: "block", marginBottom: 6 }}>Mobile Number *</label>
            <input
              type="text"
              placeholder="Search by mobile number"
              value={patientForm.phone}
              onChange={(e) => {
                setPatientForm({ ...patientForm, phone: e.target.value });
                setPatientLocked(false);
              }}
              onKeyDown={handlePatientSearchKeyDown}
              disabled={patientLocked}
              style={{ width: "100%", padding: 8, fontSize: 14 }}
            />
            {patientResults.length > 0 && !patientLocked && (
              <div style={{
                position: "absolute",
                top: "100%",
                left: 0,
                right: 0,
                background: "#fff",
                border: "1px solid #eee",
                borderRadius: 4,
                maxHeight: 200,
                overflowY: "auto",
                zIndex: 10,
              }}>
                {patientResults.map((patient, index) => (
                  <div
                    key={patient.id}
                    onClick={() => handleSelectPatient(patient)}
                    style={{
                      padding: 10,
                      cursor: "pointer",
                      backgroundColor: activePatientIndex === index ? "#eef5ff" : "transparent",
                    }}
                  >
                    <strong>{patient.name}</strong> - {patient.patient_reg_no || patient.mrn} - {patient.phone}
                  </div>
                ))}
              </div>
            )}
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <div>
              <label style={{ display: "block", marginBottom: 6 }}>Patient Name *</label>
              <input
                type="text"
                value={patientForm.name}
                onChange={(e) => setPatientForm({ ...patientForm, name: e.target.value })}
                onKeyDown={handleEnterAsTab}
                disabled={patientLocked}
                style={{ width: "100%", padding: 8 }}
              />
            </div>
            <div>
              <label style={{ display: "block", marginBottom: 6 }}>Father/Husband Name</label>
              <input
                type="text"
                value={patientForm.fatherHusband}
                onChange={(e) => setPatientForm({ ...patientForm, fatherHusband: e.target.value })}
                onKeyDown={handleEnterAsTab}
                disabled={patientLocked}
                style={{ width: "100%", padding: 8 }}
              />
            </div>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <div>
              <label style={{ display: "block", marginBottom: 6 }}>Date of Birth</label>
              <input
                type="date"
                value={patientForm.date_of_birth}
                onChange={(e) => handleDobChange(e.target.value)}
                onKeyDown={handleEnterAsTab}
                disabled={patientLocked}
                style={{ width: "100%", padding: 8 }}
              />
            </div>
            <div>
              <label style={{ display: "block", marginBottom: 6 }}>Age (Years / Months / Days)</label>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
                <input
                  type="number"
                  placeholder="Years"
                  value={patientForm.ageYears}
                  onChange={(e) => handleAgeChange("ageYears", e.target.value)}
                  onKeyDown={handleEnterAsTab}
                  disabled={patientLocked}
                />
                <input
                  type="number"
                  placeholder="Months"
                  value={patientForm.ageMonths}
                  onChange={(e) => handleAgeChange("ageMonths", e.target.value)}
                  onKeyDown={handleEnterAsTab}
                  disabled={patientLocked}
                />
                <input
                  type="number"
                  placeholder="Days"
                  value={patientForm.ageDays}
                  onChange={(e) => handleAgeChange("ageDays", e.target.value)}
                  onKeyDown={handleEnterAsTab}
                  disabled={patientLocked}
                />
              </div>
              {estimatedDob && (
                <small style={{ color: "#666" }}>Estimated DOB: {estimatedDob}</small>
              )}
            </div>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <div>
              <label style={{ display: "block", marginBottom: 6 }}>Gender *</label>
              <select
                value={patientForm.gender}
                onChange={(e) => setPatientForm({ ...patientForm, gender: e.target.value })}
                onKeyDown={handleEnterAsTab}
                disabled={patientLocked}
                style={{ width: "100%", padding: 8 }}
              >
                <option value="">Select Gender</option>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
              </select>
            </div>
            <div>
              <label style={{ display: "block", marginBottom: 6 }}>CNIC</label>
              <input
                type="text"
                value={patientForm.cnic}
                onChange={(e) => setPatientForm({ ...patientForm, cnic: e.target.value })}
                onKeyDown={handleEnterAsTab}
                disabled={patientLocked}
                style={{ width: "100%", padding: 8 }}
              />
            </div>
          </div>
          <div>
            <label style={{ display: "block", marginBottom: 6 }}>Address</label>
            <input
              type="text"
              value={patientForm.address}
              onChange={(e) => setPatientForm({ ...patientForm, address: e.target.value })}
              onKeyDown={handleEnterAsTab}
              disabled={patientLocked}
              style={{ width: "100%", padding: 8 }}
            />
          </div>
          <div>
            <label style={{ display: "block", marginBottom: 6 }}>Comments</label>
            <textarea
              value={patientForm.comments}
              onChange={(e) => setPatientForm({ ...patientForm, comments: e.target.value })}
              onKeyDown={handleEnterAsTab}
              disabled={patientLocked}
              rows={2}
              style={{ width: "100%", padding: 8 }}
            />
          </div>
        </div>
        <div style={{ marginTop: 16, display: "flex", gap: 8, flexWrap: "wrap" }}>
          <Button onClick={savePatient} disabled={loading || patientLocked}>
            Save Patient Registration
          </Button>
          {patientLocked && (
            <Button variant="secondary" onClick={() => setPatientLocked(false)}>
              Edit Patient
            </Button>
          )}
          <Button variant="secondary" onClick={resetPatient}>
            Change Patient
          </Button>
        </div>
      </div>

      {selectedPatient && (
        <div style={{ border: "1px solid #ddd", padding: 20, borderRadius: 8 }}>
          <h2>Service Registration</h2>

          <div style={{ marginBottom: 16, position: "relative" }}>
            <label style={{ display: "block", marginBottom: 6 }}>Service Search</label>
            <input
              ref={serviceSearchRef}
              type="text"
              value={serviceSearch}
              onChange={(e) => {
                setServiceSearch(e.target.value);
                setActiveServiceIndex(0);
              }}
              onKeyDown={handleServiceSearchKeyDown}
              placeholder="Search service by name or code"
              style={{ width: "100%", padding: 8 }}
            />
            {serviceSearch && filteredServices.length > 0 && (
              <div style={{
                position: "absolute",
                top: "100%",
                left: 0,
                right: 0,
                background: "#fff",
                border: "1px solid #eee",
                borderRadius: 4,
                maxHeight: 220,
                overflowY: "auto",
                zIndex: 10,
              }}>
                {filteredServices.map((service, index) => (
                  <div
                    key={service.id}
                    onClick={() => addServiceToCart(service)}
                    style={{
                      padding: 10,
                      cursor: "pointer",
                      backgroundColor: activeServiceIndex === index ? "#eef5ff" : "transparent",
                    }}
                  >
                    <strong>{service.name}</strong> ({service.code || service.modality?.code || ""}) - Rs. {service.price || service.charges || 0}
                  </div>
                ))}
              </div>
            )}
          </div>

          {mostUsedServices.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <h3 style={{ marginBottom: 8 }}>Most Used Services</h3>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                {mostUsedServices.map((service) => (
                  <Button
                    key={service.id}
                    variant="secondary"
                    onClick={() => addServiceToCart(service)}
                  >
                    {service.name}
                  </Button>
                ))}
              </div>
            </div>
          )}

          <div style={{ marginBottom: 16 }}>
            <h3>Selected Services</h3>
            {selectedServices.length === 0 ? (
              <div style={{ color: "#666" }}>No services added yet.</div>
            ) : (
              <div style={{ border: "1px solid #eee", borderRadius: 4 }}>
                {selectedServices.map((service) => (
                  <div
                    key={service.id}
                    style={{ display: "flex", justifyContent: "space-between", padding: 10, borderBottom: "1px solid #eee" }}
                  >
                    <div>
                      <strong>{service.name}</strong> ({service.code || service.modality?.code || ""})
                      <div style={{ fontSize: 12, color: "#666" }}>Rs. {service.price || service.charges || 0}</div>
                    </div>
                    <button
                      onClick={() => removeServiceFromCart(service.id)}
                      style={{ background: "transparent", border: "none", color: "#d00", cursor: "pointer" }}
                    >
                      Remove
                    </button>
                  </div>
                ))}
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
                    value={subtotal.toFixed(2)}
                    readOnly
                    style={{ width: "100%", padding: 8, backgroundColor: "#f5f5f5" }}
                  />
                  <small>Auto-calculated from selected services</small>
                </div>
                <div>
                  <label>Discount (%)</label>
                  <input
                    type="number"
                    value={discountPercentage}
                    min={0}
                    max={100}
                    onChange={(e) => {
                      const value = Math.min(Math.max(parseFloat(e.target.value) || 0, 0), 100);
                      setDiscountPercentage(e.target.value === "" ? "" : value.toString());
                      if (!amountPaid) {
                        setAmountPaid((subtotal - (subtotal * value) / 100).toFixed(2));
                      }
                    }}
                    onKeyDown={handleEnterAsTab}
                    style={{ width: "100%", padding: 8 }}
                  />
                </div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
                <div>
                  <label>Net Amount:</label>
                  <input
                    type="number"
                    value={netAmount.toFixed(2)}
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
                    onKeyDown={handleEnterAsTab}
                    style={{ width: "100%", padding: 8 }}
                  />
                </div>
              </div>

              <div style={{ marginBottom: 16 }}>
                <label>Payment Method:</label>
                <select
                  value={paymentMethod}
                  onChange={(e) => setPaymentMethod(e.target.value)}
                  onKeyDown={handleEnterAsTab}
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
                  <div><strong>Rs. {totalAmount.toFixed(2)}</strong></div>
                  <div>Discount ({discountPercentValue.toFixed(2)}%):</div>
                  <div><strong>Rs. {discountAmount.toFixed(2)}</strong></div>
                  <div>Net Amount:</div>
                  <div><strong>Rs. {netAmount.toFixed(2)}</strong></div>
                  <div>Amount Paid:</div>
                  <div><strong>Rs. {paidAmount.toFixed(2)}</strong></div>
                  <div>Balance:</div>
                  <div><strong>Rs. {balanceAmount.toFixed(2)}</strong></div>
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
