import React, { useEffect, useState } from "react";
import { useAuth } from "../ui/auth";
import { apiGet, apiPost, apiPatch, apiDelete } from "../ui/api";

interface Patient {
  id: string;
  mrn: string;
  name: string;
  age?: number;
  gender: string;
  phone: string;
  address: string;
  referrer: string;
  notes: string;
  created_at: string;
}

export default function Patients() {
  const { token } = useAuth();
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Patient | null>(null);
  const [formData, setFormData] = useState({
    mrn: "",
    name: "",
    age: "",
    gender: "",
    phone: "",
    address: "",
    referrer: "",
    notes: "",
  });
  const [search, setSearch] = useState("");

  const loadPatients = async () => {
    if (!token) return;
    try {
      setLoading(true);
      const data = await apiGet(`/patients/?search=${encodeURIComponent(search)}`, token);
      setPatients(data.results || data);
      setError("");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPatients();
  }, [token, search]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    try {
      const payload = {
        ...formData,
        age: formData.age ? parseInt(formData.age) : null,
      };
      if (editing) {
        await apiPatch(`/patients/${editing.id}/`, token, payload);
      } else {
        await apiPost("/patients/", token, payload);
      }
      setShowForm(false);
      setEditing(null);
      setFormData({
        mrn: "",
        name: "",
        age: "",
        gender: "",
        phone: "",
        address: "",
        referrer: "",
        notes: "",
      });
      loadPatients();
    } catch (e: any) {
      setError(e.message);
    }
  };

  const handleEdit = (p: Patient) => {
    setEditing(p);
    setFormData({
      mrn: p.mrn,
      name: p.name,
      age: p.age?.toString() || "",
      gender: p.gender,
      phone: p.phone,
      address: p.address,
      referrer: p.referrer,
      notes: p.notes,
    });
    setShowForm(true);
  };

  const handleDelete = async (id: string) => {
    if (!token || !confirm("Delete this patient?")) return;
    try {
      await apiDelete(`/patients/${id}/`, token);
      loadPatients();
    } catch (e: any) {
      setError(e.message);
    }
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <h1>Patients</h1>
        <div style={{ display: "flex", gap: 10 }}>
          <input
            type="text"
            placeholder="Search patients..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ padding: 8, fontSize: 14, width: 250 }}
          />
          <button
            onClick={() => {
              setEditing(null);
              setFormData({
                mrn: "",
                name: "",
                age: "",
                gender: "",
                phone: "",
                address: "",
                referrer: "",
                notes: "",
              });
              setShowForm(!showForm);
            }}
            style={{ padding: "8px 16px", fontSize: 14 }}
          >
            {showForm ? "Cancel" : "Add Patient"}
          </button>
        </div>
      </div>

      {error && <div style={{ color: "red", marginBottom: 10 }}>{error}</div>}

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
            <label>MRN *</label>
            <input
              type="text"
              value={formData.mrn}
              onChange={(e) => setFormData({ ...formData, mrn: e.target.value })}
              required
              style={{ width: "100%", padding: 8 }}
            />
          </div>
          <div>
            <label>Name *</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
              style={{ width: "100%", padding: 8 }}
            />
          </div>
          <div>
            <label>Age</label>
            <input
              type="number"
              value={formData.age}
              onChange={(e) => setFormData({ ...formData, age: e.target.value })}
              style={{ width: "100%", padding: 8 }}
            />
          </div>
          <div>
            <label>Gender</label>
            <select
              value={formData.gender}
              onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
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
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              style={{ width: "100%", padding: 8 }}
            />
          </div>
          <div>
            <label>Address</label>
            <input
              type="text"
              value={formData.address}
              onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              style={{ width: "100%", padding: 8 }}
            />
          </div>
          <div>
            <label>Referrer</label>
            <input
              type="text"
              value={formData.referrer}
              onChange={(e) => setFormData({ ...formData, referrer: e.target.value })}
              style={{ width: "100%", padding: 8 }}
            />
          </div>
          <div style={{ gridColumn: "1 / -1" }}>
            <label>Notes</label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              style={{ width: "100%", padding: 8, minHeight: 60 }}
            />
          </div>
          <div style={{ gridColumn: "1 / -1" }}>
            <button type="submit" style={{ padding: "10px 20px", fontSize: 14 }}>
              {editing ? "Update" : "Create"} Patient
            </button>
          </div>
        </form>
      )}

      {loading ? (
        <div>Loading...</div>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ background: "#f0f0f0" }}>
              <th style={{ padding: 10, textAlign: "left", border: "1px solid #ddd" }}>MRN</th>
              <th style={{ padding: 10, textAlign: "left", border: "1px solid #ddd" }}>Name</th>
              <th style={{ padding: 10, textAlign: "left", border: "1px solid #ddd" }}>Age</th>
              <th style={{ padding: 10, textAlign: "left", border: "1px solid #ddd" }}>Gender</th>
              <th style={{ padding: 10, textAlign: "left", border: "1px solid #ddd" }}>Phone</th>
              <th style={{ padding: 10, textAlign: "left", border: "1px solid #ddd" }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {patients.map((p) => (
              <tr key={p.id}>
                <td style={{ padding: 10, border: "1px solid #ddd" }}>{p.mrn}</td>
                <td style={{ padding: 10, border: "1px solid #ddd" }}>{p.name}</td>
                <td style={{ padding: 10, border: "1px solid #ddd" }}>{p.age || "-"}</td>
                <td style={{ padding: 10, border: "1px solid #ddd" }}>{p.gender || "-"}</td>
                <td style={{ padding: 10, border: "1px solid #ddd" }}>{p.phone || "-"}</td>
                <td style={{ padding: 10, border: "1px solid #ddd" }}>
                  <button onClick={() => handleEdit(p)} style={{ marginRight: 8, fontSize: 12 }}>
                    Edit
                  </button>
                  <button onClick={() => handleDelete(p.id)} style={{ fontSize: 12, color: "red" }}>
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {!loading && patients.length === 0 && <div style={{ marginTop: 20 }}>No patients found.</div>}
    </div>
  );
}
