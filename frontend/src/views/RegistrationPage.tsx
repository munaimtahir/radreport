import React, { useEffect, useMemo, useRef, useState } from "react";
import { useAuth } from "../ui/auth";
import { apiGet, apiPatch, apiPost } from "../ui/api";
import PageHeader from "../ui/components/PageHeader";
import ErrorAlert from "../ui/components/ErrorAlert";
import SuccessAlert from "../ui/components/SuccessAlert";
import Button from "../ui/components/Button";
import { theme } from "../theme";

// --- Types ---

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
  price: number | string;
  charges: number | string;
  category: string;
  usage_count?: number;
  modality: {
    code: string;
    name: string;
  };
  is_active: boolean;
}

interface Consultant {
  id: string;
  display_name: string;
}

interface ParsedNotes {
  fatherHusband: string;
  cnic: string;
  comments: string;
  extraNotes: string;
}

// --- Helpers ---

const LOCAL_USAGE_KEY = "rims:service-usage";

const parsePatientNotes = (notes?: string): ParsedNotes => {
  const parsed: ParsedNotes = {
    fatherHusband: "",
    cnic: "",
    comments: "",
    extraNotes: "",
  };

  if (!notes) return parsed;

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
  // Only preserve extra notes that aren't the structured internal ones
  const cleanExisting = (existingNotes || "")
    .split("\n")
    .filter((line) => !line.toLowerCase().startsWith("father/husband:")
      && !line.toLowerCase().startsWith("cnic:")
      && !line.toLowerCase().startsWith("comments:"))
    .join("\n")
    .trim();

  const tagged: string[] = [];
  if (fields.fatherHusband.trim()) tagged.push(`Father/Husband: ${fields.fatherHusband.trim()}`);
  if (fields.cnic.trim()) tagged.push(`CNIC: ${fields.cnic.trim()}`);
  if (fields.comments.trim()) tagged.push(`Comments: ${fields.comments.trim()}`);

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

// --- Styles ---

const styles = {
  container: {
    maxWidth: 1400,
    margin: "0 auto",
    padding: "0 20px 20px 20px",
    fontFamily: theme.fonts.body,
    color: "#334155",
  },
  topBar: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 20,
    paddingBottom: 10,
    borderBottom: "1px solid #e2e8f0",
  },
  title: {
    fontSize: 24,
    fontWeight: 600,
    color: "#1e293b",
    margin: 0,
  },
  globalSearch: {
    position: "relative" as "relative",
    width: 400,
  },
  searchInput: {
    width: "100%",
    padding: "10px 16px",
    borderRadius: 8,
    border: "1px solid #cbd5e1",
    fontSize: 14,
    outline: "none",
    boxShadow: "0 1px 2px rgba(0,0,0,0.05)",
    transition: "border-color 0.2s",
  },
  searchResults: {
    position: "absolute" as "absolute",
    top: "calc(100% + 4px)",
    left: 0,
    right: 0,
    background: "#fff",
    border: "1px solid #e2e8f0",
    borderRadius: 8,
    boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
    maxHeight: 300,
    overflowY: "auto" as "auto",
    zIndex: 50,
  },
  resultItem: {
    padding: "10px 16px",
    cursor: "pointer",
    borderBottom: "1px solid #f1f5f9",
    display: "flex",
    flexDirection: "column" as "column",
    gap: 2,
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr", // Equal split
    gap: 24,
    alignItems: "start",
  },
  card: {
    background: "#fff",
    border: "1px solid #e2e8f0",
    borderRadius: 12,
    padding: 24,
    boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
    height: "100%",
    display: "flex",
    flexDirection: "column" as "column",
  },
  cardHeader: {
    fontSize: 18,
    fontWeight: 600,
    marginBottom: 20,
    color: "#0f172a",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  sectionLabel: {
    fontSize: 12,
    textTransform: "uppercase" as "uppercase",
    letterSpacing: "0.05em",
    fontWeight: 600,
    color: "#64748b",
    marginBottom: 12,
    marginTop: 8,
    borderBottom: "1px solid #f1f5f9",
    paddingBottom: 4,
  },
  inputGroup: {
    marginBottom: 16,
  },
  label: {
    display: "block",
    marginBottom: 6,
    fontSize: 13,
    fontWeight: 500,
    color: "#475569",
  },
  input: {
    width: "100%",
    padding: "8px 12px",
    borderRadius: 6,
    border: "1px solid #cbd5e1",
    fontSize: 14,
    outline: "none",
    height: 38, // Consistent height
    transition: "border-color 0.2s",
  },
  row: {
    display: "flex",
    gap: 12,
  },
  serviceItem: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "8px 12px",
    background: "#f8fafc",
    borderRadius: 6,
    marginBottom: 8,
    border: "1px solid #e2e8f0",
  },
  billRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8,
    fontSize: 14,
  },
  totalRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: 16,
    paddingTop: 16,
    borderTop: "1px solid #e2e8f0",
    fontSize: 16,
    fontWeight: 600,
    color: "#0f172a",
  },
  dueRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: 12,
    padding: "12px",
    background: "#fff1f2",
    borderRadius: 6,
    color: "#be123c",
    fontWeight: 700,
    fontSize: 16,
  },
  disabledOverlay: {
    opacity: 0.5,
    pointerEvents: "none" as "none",
    filter: "grayscale(100%)",
  }
};

// --- Main Component ---

export default function RegistrationPage() {
  const { token } = useAuth();

  // -- Data State --
  const [services, setServices] = useState<Service[]>([]);
  const [consultants, setConsultants] = useState<Consultant[]>([]);

  // -- UI State --
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const [success, setSuccess] = useState<string>("");
  const [patientLocked, setPatientLocked] = useState(false); // True = Patient Saved/Selected

  // -- Patient Search State --
  const [searchQuery, setSearchQuery] = useState("");
  const [patientResults, setPatientResults] = useState<Patient[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [activeResultIndex, setActiveResultIndex] = useState(-1);

  // -- Patient Form State --
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [patientForm, setPatientForm] = useState({
    name: "",
    gender: "",
    date_of_birth: "",
    ageYears: "",
    ageMonths: "",
    ageDays: "",
    phone: "",
    email: "", // Placeholder if needed
    address: "",
    fatherHusband: "",
    cnic: "",
    comments: "",
  });

  // -- Service & Billing State --
  const [selectedServices, setSelectedServices] = useState<Service[]>([]);
  const [serviceSearch, setServiceSearch] = useState("");
  const [activeServiceIndex, setActiveServiceIndex] = useState(-1);
  const [bookedConsultantId, setBookedConsultantId] = useState("");
  const [referringConsultant, setReferringConsultant] = useState("");

  // Billing
  const [discountPercent, setDiscountPercent] = useState("");
  const [discountAmount, setDiscountAmount] = useState("");
  const [paidAmount, setPaidAmount] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("cash");

  const serviceSearchRef = useRef<HTMLInputElement>(null);
  const globalSearchRef = useRef<HTMLInputElement>(null);

  // -- Effects --

  useEffect(() => {
    if (token) {
      loadServices();
      loadConsultants();
    }
  }, [token]);

  // Global Search Debounce
  useEffect(() => {
    if (!token || !searchQuery.trim()) {
      setPatientResults([]);
      return;
    }
    const timer = setTimeout(() => {
      performPatientSearch(searchQuery);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery, token]);

  // Auto-calculate Paid Amount Default
  const subtotal = useMemo(() => {
    return selectedServices.reduce((sum, s) => {
      const price = typeof s.price === 'number' ? s.price : parseFloat(s.price as any) || 0;
      return sum + price;
    }, 0);
  }, [selectedServices]);

  const netPayable = useMemo(() => {
    const disc = parseFloat(discountAmount) || 0;
    return Math.max(0, subtotal - disc);
  }, [subtotal, discountAmount]);

  useEffect(() => {
    if (subtotal > 0 && !paidAmount) {
      setPaidAmount(netPayable.toFixed(2));
    }
    // Also update paidAmount if netPayable changes (e.g. discount applied) 
    // AND paidAmount matches OLD netPayable? 
    // For now, let's just default it if not set, or user can override. 
    // Requirement says: "Default Behavior: Paid Amount = Net Payable (auto-filled)"
    // If we want it strictly auto-filled unless edited:
    setPaidAmount(netPayable.toFixed(2));
  }, [netPayable, subtotal]);

  // -- Loaders --

  const loadServices = async () => {
    try {
      const data = await apiGet("/services/", token);
      setServices(data.results || data || []);
    } catch (err) {
      console.error(err);
    }
  };

  const loadConsultants = async () => {
    try {
      const data = await apiGet("/consultants/", token);
      setConsultants(data.results || data || []);
    } catch (err) {
      console.error(err);
    }
  };

  const performPatientSearch = async (query: string) => {
    setIsSearching(true);
    try {
      const data = await apiGet(`/patients/?search=${encodeURIComponent(query)}`, token);
      setPatientResults(data.results || data || []);
      setActiveResultIndex(data.results?.length ? 0 : -1);
    } catch (err) {
      console.error(err);
    } finally {
      setIsSearching(false);
    }
  };

  // -- Handlers --

  const handleSelectPatient = (patient: Patient) => {
    const parsedNotes = parsePatientNotes(patient.notes);
    const derivedAge = patient.date_of_birth ? calculateAgeFromDob(patient.date_of_birth) : null;

    setSelectedPatient(patient);
    setPatientForm({
      name: patient.name || "",
      gender: patient.gender || "",
      date_of_birth: patient.date_of_birth || "",
      ageYears: derivedAge?.years || (patient.age ? String(patient.age) : ""),
      ageMonths: derivedAge?.months || "",
      ageDays: derivedAge?.days || "",
      phone: patient.phone || "",
      email: "",
      address: patient.address || "",
      fatherHusband: parsedNotes.fatherHusband,
      cnic: parsedNotes.cnic,
      comments: parsedNotes.comments,
    });

    setSearchQuery("");
    setPatientResults([]);
    // Switch to edit mode immediately if selected from search
    setPatientLocked(true);
  };

  const handlePatientReset = () => {
    setSelectedPatient(null);
    setPatientLocked(false);
    setPatientForm({
      name: "",
      gender: "",
      date_of_birth: "",
      ageYears: "",
      ageMonths: "",
      ageDays: "",
      phone: "",
      email: "",
      address: "",
      fatherHusband: "",
      cnic: "",
      comments: "",
    });
    // Reset billing
    setSelectedServices([]);
    setDiscountAmount("");
    setDiscountPercent("");
    setPaidAmount("");
  };

  const handleSavePatient = async () => {
    if (!token) return;
    if (!patientForm.name.trim() || !patientForm.phone.trim() || !patientForm.gender) {
      setError("Name, Mobile, and Gender are required.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      // Build payload
      const payload: any = {
        name: patientForm.name.trim(),
        gender: patientForm.gender,
        phone: patientForm.phone.trim(),
        address: patientForm.address.trim(),
      };

      if (patientForm.date_of_birth) payload.date_of_birth = patientForm.date_of_birth;
      if (patientForm.ageYears) payload.age = parseInt(patientForm.ageYears, 10);

      const notesPayload = buildNotes(selectedPatient?.notes, {
        fatherHusband: patientForm.fatherHusband,
        cnic: patientForm.cnic,
        comments: patientForm.comments,
        extraNotes: "",
      });
      if (notesPayload) payload.notes = notesPayload;

      let patient: Patient;
      if (selectedPatient) {
        patient = await apiPatch(`/patients/${selectedPatient.id}/`, token, payload);
      } else {
        patient = await apiPost("/patients/", token, payload);
      }

      setSelectedPatient(patient);
      setPatientLocked(true);
      setSuccess("Patient saved. Proceed to add services.");

      // Focus on service search
      setTimeout(() => serviceSearchRef.current?.focus(), 100);

    } catch (err: any) {
      setError(err.message || "Failed to save patient.");
    } finally {
      setLoading(false);
    }
  };

  // -- Service Search --

  const filteredServices = useMemo(() => {
    const q = serviceSearch.trim().toLowerCase();
    if (!q) return [];
    return services.filter(s =>
      s.is_active && (
        s.name.toLowerCase().includes(q) ||
        s.code?.toLowerCase().includes(q)
      )
    ).slice(0, 10);
  }, [serviceSearch, services]);

  const handleAddService = (service: Service) => {
    if (selectedServices.find(s => s.id === service.id)) return;
    setSelectedServices([...selectedServices, service]);
    updateLocalUsage(service.id);
    setServiceSearch("");
    setActiveServiceIndex(-1);
    // Keep focus
    serviceSearchRef.current?.focus();
  };

  // -- Billing Logic --

  const handleDiscountPercentChange = (val: string) => {
    setDiscountPercent(val);
    const pct = parseFloat(val);
    if (!isNaN(pct)) {
      const amt = (subtotal * pct) / 100;
      setDiscountAmount(amt.toFixed(2));
    } else {
      setDiscountAmount("");
    }
  };

  const handleDiscountAmountChange = (val: string) => {
    setDiscountAmount(val);
    const amt = parseFloat(val);
    if (!isNaN(amt) && subtotal > 0) {
      const pct = (amt / subtotal) * 100;
      setDiscountPercent(pct.toFixed(2));
    } else if (subtotal === 0) {
      setDiscountPercent("0");
    } else {
      setDiscountPercent("");
    }
  };

  const dueAmount = netPayable - (parseFloat(paidAmount) || 0);

  const handleSaveVisit = async (printReceipt = false) => {
    if (!token || !selectedPatient || selectedServices.length === 0) {
      setError("Please ensure patient is saved and services are added.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const visitData = {
        patient_id: selectedPatient.id,
        service_ids: selectedServices.map(s => s.id),
        booked_consultant_id: bookedConsultantId || null,
        referring_consultant: referringConsultant,
        subtotal: subtotal,
        total_amount: subtotal, // This seems redundant in API but requested
        discount: parseFloat(discountAmount) || 0,
        // We can send percentage if we want backend to store it, but amount is source of truth here
        discount_percentage: parseFloat(discountPercent) || 0,
        net_amount: netPayable,
        amount_paid: parseFloat(paidAmount) || 0,
        payment_method: paymentMethod
      };

      const visit = await apiPost("/workflow/visits/create_visit/", token, visitData);
      setSuccess(`Visit created: ${visit.visit_id}`);

      // Reset Billing only (Keep patient if they want to do another? No, usually reset all)
      // Requirement says "Registration switches to edit/view mode". 
      // After save, we probably want a fresh start.
      handlePatientReset();

      if (printReceipt) {
        printReceiptPdf(visit.id, visit.visit_id);
      }

    } catch (err: any) {
      setError(err.message || "Failed to create visit.");
    } finally {
      setLoading(false);
    }
  };

  const printReceiptPdf = (visitId: string, visitCode: string) => {
    // Re-use existing print logic or simplified version
    const API_BASE = (import.meta as any).env.VITE_API_BASE
      || ((import.meta as any).env.PROD ? "/api" : "http://localhost:8000/api");
    const url = `${API_BASE}/pdf/${visitId}/receipt/`;

    // Open in new window for simplicity
    const win = window.open(url, "_blank");
    if (win) {
      win.onload = () => win.print();
    }
  };

  // -- Render Helpers --

  const handleGlobalKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveResultIndex(prev => Math.min(prev + 1, patientResults.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveResultIndex(prev => Math.max(prev - 1, 0));
    } else if (e.key === 'Enter' && activeResultIndex >= 0) {
      e.preventDefault();
      const p = patientResults[activeResultIndex];
      if (p) handleSelectPatient(p);
    }
  };

  const handleServiceKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveServiceIndex(prev => Math.min(prev + 1, filteredServices.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveServiceIndex(prev => Math.max(prev - 1, 0));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (activeServiceIndex >= 0 && filteredServices[activeServiceIndex]) {
        handleAddService(filteredServices[activeServiceIndex]);
      } else if (filteredServices.length > 0) {
        handleAddService(filteredServices[0]);
      }
    }
  };

  return (
    <div style={styles.container}>
      <PageHeader title="New Registration" />

      {error && <ErrorAlert message={error} onDismiss={() => setError("")} />}
      {success && <SuccessAlert message={success} onDismiss={() => setSuccess("")} />}

      {/* Top Bar: Global Search */}
      <div style={styles.topBar}>
        <div /> {/* Spacer */}
        <div style={styles.globalSearch}>
          <input
            ref={globalSearchRef}
            type="text"
            placeholder="Search patient by name, mobile, or Reg #"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={handleGlobalKeyDown}
            style={styles.searchInput}
          />
          {patientResults.length > 0 && (
            <div style={styles.searchResults}>
              {patientResults.map((p, idx) => (
                <div
                  key={p.id}
                  style={{
                    ...styles.resultItem,
                    background: idx === activeResultIndex ? "#f1f5f9" : "transparent"
                  }}
                  onClick={() => handleSelectPatient(p)}
                  onMouseEnter={() => setActiveResultIndex(idx)}
                >
                  <span style={{ fontWeight: 600, color: "#334155" }}>{p.name}</span>
                  <span style={{ fontSize: 12, color: "#64748b" }}>{p.mobile || p.phone} | {p.mrn}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div style={styles.grid}>
        {/* Left Column: Patient Registration */}
        <div style={styles.card}>
          <div style={styles.cardHeader}>
            <span>Patient Details</span>
            {patientLocked && (
              <Button
                onClick={() => setPatientLocked(false)}
                variant="secondary"
                style={{ fontSize: 12, padding: "4px 8px" }}
              >
                Edit
              </Button>
            )}
          </div>

          <div style={{ flex: 1, pointerEvents: patientLocked ? "none" : "auto", opacity: patientLocked ? 0.8 : 1 }}>
            {/* Block 1: Identity */}
            <div style={styles.sectionLabel}>Identity</div>
            <div style={styles.row}>
              <div style={{ flex: 2 }}>
                <label style={styles.label}>Full Name *</label>
                <input
                  style={styles.input}
                  value={patientForm.name}
                  onChange={e => setPatientForm({ ...patientForm, name: e.target.value })}
                  placeholder="e.g. John Doe"
                />
              </div>
              <div style={{ flex: 1 }}>
                <label style={styles.label}>Gender *</label>
                <select
                  style={styles.input}
                  value={patientForm.gender}
                  onChange={e => setPatientForm({ ...patientForm, gender: e.target.value })}
                >
                  <option value="">Select</option>
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </select>
              </div>
            </div>

            <div style={{ ...styles.row, marginTop: 12 }}>
              <div style={{ flex: 1 }}>
                <label style={styles.label}>Date of Birth</label>
                <input
                  type="date"
                  style={styles.input}
                  value={patientForm.date_of_birth}
                  onChange={e => {
                    const val = e.target.value;
                    const age = calculateAgeFromDob(val);
                    setPatientForm({
                      ...patientForm,
                      date_of_birth: val,
                      ageYears: age.years,
                      ageMonths: age.months,
                      ageDays: age.days
                    });
                  }}
                />
              </div>
              <div style={{ flex: 1.5 }}>
                <label style={styles.label}>Age (Y / M / D)</label>
                <div style={{ display: "flex", gap: 4 }}>
                  <input
                    type="number"
                    placeholder="Y"
                    style={{ ...styles.input, textAlign: "center" }}
                    value={patientForm.ageYears}
                    onChange={e => setPatientForm({ ...patientForm, ageYears: e.target.value })}
                  />
                  <input
                    type="number"
                    placeholder="M"
                    style={{ ...styles.input, textAlign: "center" }}
                    value={patientForm.ageMonths}
                    onChange={e => setPatientForm({ ...patientForm, ageMonths: e.target.value })}
                  />
                  <input
                    type="number"
                    placeholder="D"
                    style={{ ...styles.input, textAlign: "center" }}
                    value={patientForm.ageDays}
                    onChange={e => setPatientForm({ ...patientForm, ageDays: e.target.value })}
                  />
                </div>
              </div>
            </div>

            {/* Block 2: Contact */}
            <div style={{ ...styles.sectionLabel, marginTop: 24 }}>Contact</div>
            <div style={styles.row}>
              <div style={{ flex: 1 }}>
                <label style={styles.label}>Mobile Number *</label>
                <input
                  style={styles.input}
                  value={patientForm.phone}
                  onChange={e => setPatientForm({ ...patientForm, phone: e.target.value })}
                  placeholder="0300-1234567"
                />
              </div>
              <div style={{ flex: 1 }}>
                <label style={styles.label}>Email (Optional)</label>
                <input
                  style={styles.input}
                  value={patientForm.email}
                  onChange={e => setPatientForm({ ...patientForm, email: e.target.value })}
                />
              </div>
            </div>
            <div style={{ marginTop: 12 }}>
              <label style={styles.label}>Address</label>
              <textarea
                style={{ ...styles.input, height: 60, resize: "none" }}
                value={patientForm.address}
                onChange={e => setPatientForm({ ...patientForm, address: e.target.value })}
              />
            </div>

            {/* Block 3: Additional */}
            <div style={{ ...styles.sectionLabel, marginTop: 24 }}>Additional Info</div>
            <div style={styles.row}>
              <div style={{ flex: 1 }}>
                <label style={styles.label}>Father/Husband Name</label>
                <input
                  style={styles.input}
                  value={patientForm.fatherHusband}
                  onChange={e => setPatientForm({ ...patientForm, fatherHusband: e.target.value })}
                />
              </div>
              <div style={{ flex: 1 }}>
                <label style={styles.label}>CNIC / National ID</label>
                <input
                  style={styles.input}
                  value={patientForm.cnic}
                  onChange={e => setPatientForm({ ...patientForm, cnic: e.target.value })}
                />
              </div>
            </div>
          </div>

          {/* Action Bar */}
          <div style={{ marginTop: 24, paddingTop: 16, borderTop: "1px solid #e2e8f0", display: "flex", justifyContent: "flex-end", gap: 12 }}>
            <Button variant="secondary" onClick={handlePatientReset}>Clear</Button>
            {!patientLocked && (
              <Button onClick={handleSavePatient} disabled={loading}>
                {loading ? "Saving..." : "Save Patient & Continue"}
              </Button>
            )}
          </div>
        </div>

        {/* Right Column: Service & Billing */}
        <div style={{ ...styles.card, ...(!patientLocked ? styles.disabledOverlay : {}) }}>
          <div style={styles.cardHeader}>Services & Billing</div>

          {/* Search */}
          <div style={{ position: "relative", marginBottom: 20 }}>
            <label style={styles.label}>Add Service / Test</label>
            <input
              ref={serviceSearchRef}
              style={styles.input}
              placeholder="Type test name or code (e.g. CBC, Lipid)..."
              value={serviceSearch}
              onChange={e => setServiceSearch(e.target.value)}
              onKeyDown={handleServiceKeyDown}
              disabled={!patientLocked}
            />
            {serviceSearch && filteredServices.length > 0 && (
              <div style={styles.searchResults}>
                {filteredServices.map((s, idx) => (
                  <div
                    key={s.id}
                    style={{
                      ...styles.resultItem,
                      background: idx === activeServiceIndex ? "#f1f5f9" : "transparent"
                    }}
                    onClick={() => handleAddService(s)}
                    onMouseEnter={() => setActiveServiceIndex(idx)}
                  >
                    <span style={{ fontWeight: 600 }}>{s.name}</span>
                    <span style={{ fontSize: 12, color: "#64748b" }}>{s.code} | {s.price} PKR</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Service List */}
          <div style={{ flex: 1, overflowY: "auto", marginBottom: 20, maxHeight: 300 }}>
            {selectedServices.map((s, idx) => (
              <div key={idx} style={styles.serviceItem}>
                <div>
                  <div style={{ fontWeight: 600, fontSize: 14 }}>{s.name}</div>
                  <div style={{ fontSize: 12, color: "#64748b" }}>{s.code}</div>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <span style={{ fontWeight: 600 }}>{s.price}</span>
                  <button
                    onClick={() => setSelectedServices(prev => prev.filter((_, i) => i !== idx))}
                    style={{ border: "none", background: "none", color: "#ef4444", cursor: "pointer" }}
                  >
                    ✕
                  </button>
                </div>
              </div>
            ))}
            {selectedServices.length === 0 && (
              <div style={{ textAlign: "center", color: "#94a3b8", padding: 20, fontStyle: "italic" }}>
                No services added yet.
              </div>
            )}
          </div>

          {/* Consultant Info */}
          <div style={styles.row}>
            <div style={{ flex: 1 }}>
              <label style={styles.label}>Consultant</label>
              <select
                style={styles.input}
                value={bookedConsultantId}
                onChange={e => setBookedConsultantId(e.target.value)}
              >
                <option value="">None / Walk-in</option>
                {consultants.map(c => <option key={c.id} value={c.id}>{c.display_name}</option>)}
              </select>
            </div>
            <div style={{ flex: 1 }}>
              <label style={styles.label}>Referring Dr.</label>
              <input
                style={styles.input}
                placeholder="External doctor name"
                value={referringConsultant}
                onChange={e => setReferringConsultant(e.target.value)}
              />
            </div>
          </div>

          {/* Billing Summary */}
          <div style={{ marginTop: 24, padding: 16, background: "#f8fafc", borderRadius: 8 }}>
            <div style={styles.billRow}>
              <span>Subtotal</span>
              <span style={{ fontWeight: 600 }}>{subtotal.toFixed(2)}</span>
            </div>
            <div style={styles.billRow}>
              <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                Discount
                <div style={{ display: "flex", gap: 4 }}>
                  <input
                    placeholder="%"
                    style={{ ...styles.input, width: 50, height: 28, padding: 4 }}
                    value={discountPercent}
                    onChange={e => handleDiscountPercentChange(e.target.value)}
                  />
                  <input
                    placeholder="PKR"
                    style={{ ...styles.input, width: 70, height: 28, padding: 4 }}
                    value={discountAmount}
                    onChange={e => handleDiscountAmountChange(e.target.value)}
                  />
                </div>
              </span>
              <span style={{ color: "#ef4444" }}>-{parseFloat(discountAmount || "0").toFixed(2)}</span>
            </div>

            <div style={styles.totalRow}>
              <span>Net Payable</span>
              <span>{netPayable.toFixed(2)}</span>
            </div>

            <div style={{ ...styles.billRow, marginTop: 12 }}>
              <span style={{ alignSelf: "center" }}>Amount Paid</span>
              <input
                style={{ ...styles.input, width: 120, textAlign: "right", fontWeight: 600 }}
                value={paidAmount}
                onChange={e => setPaidAmount(e.target.value)}
              />
            </div>

            {dueAmount > 0 && (
              <div style={styles.dueRow}>
                <span>DUE AMOUNT</span>
                <span>{dueAmount.toFixed(2)}</span>
              </div>
            )}
          </div>

          <div style={{ marginTop: 20, display: "flex", gap: 12 }}>
            <Button
              onClick={() => handleSaveVisit(true)}
              disabled={loading || selectedServices.length === 0}
              style={{ flex: 1 }}
            >
              Save & Print Receipt
            </Button>
            <Button
              onClick={() => handleSaveVisit(false)}
              disabled={loading || selectedServices.length === 0}
              variant="secondary"
            >
              Save Only
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
