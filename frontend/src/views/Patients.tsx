import React, { useEffect, useState } from "react";
import { useAuth } from "../ui/auth";
import { apiGet, apiPost, apiPatch, apiDelete } from "../ui/api";
import PageHeader from "../ui/components/PageHeader";
import ErrorAlert from "../ui/components/ErrorAlert";
import Button from "../ui/components/Button";

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
      <PageHeader
        title="Patients"
        actions={
          <>
            <input
              type="text"
              placeholder="Search patients..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{
                padding: "8px 12px",
                fontSize: 14,
                width: 250,
                border: "1px solid #ddd",
                borderRadius: 6,
              }}
            />
            <Button
              variant={showForm ? "secondary" : "primary"}
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
            >
              {showForm ? "Cancel" : "Add Patient"}
            </Button>
          </>
        }
      />

      {error && <ErrorAlert message={error} onDismiss={() => setError("")} />}

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
            <Button type="submit">
              {editing ? "Update" : "Create"} Patient
            </Button>
          </div>
        </form>
      )}

      {loading ? (
        <div style={{ textAlign: "center", padding: 40, color: "#666" }}>Loading...</div>
      ) : patients.length === 0 ? (
        <div style={{ textAlign: "center", padding: 40, color: "#999", border: "1px solid #e0e0e0", borderRadius: 8 }}>
          No patients found.
        </div>
      ) : (
        <div style={{ border: "1px solid #e0e0e0", borderRadius: 8, overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ background: "#f5f5f5" }}>
                <th style={{ padding: 12, textAlign: "left", borderBottom: "2px solid #ddd", fontWeight: 600 }}>MRN</th>
                <th style={{ padding: 12, textAlign: "left", borderBottom: "2px solid #ddd", fontWeight: 600 }}>Name</th>
                <th style={{ padding: 12, textAlign: "left", borderBottom: "2px solid #ddd", fontWeight: 600 }}>Age</th>
                <th style={{ padding: 12, textAlign: "left", borderBottom: "2px solid #ddd", fontWeight: 600 }}>Gender</th>
                <th style={{ padding: 12, textAlign: "left", borderBottom: "2px solid #ddd", fontWeight: 600 }}>Phone</th>
                <th style={{ padding: 12, textAlign: "left", borderBottom: "2px solid #ddd", fontWeight: 600 }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {patients.map((p) => (
                <tr key={p.id} style={{ borderBottom: "1px solid #eee" }}>
                  <td style={{ padding: 12 }}>{p.mrn}</td>
                  <td style={{ padding: 12 }}>{p.name}</td>
                  <td style={{ padding: 12 }}>{p.age || "-"}</td>
                  <td style={{ padding: 12 }}>{p.gender || "-"}</td>
                  <td style={{ padding: 12 }}>{p.phone || "-"}</td>
                  <td style={{ padding: 12 }}>
                    <div style={{ display: "flex", gap: 8 }}>
                      <Button variant="secondary" onClick={() => handleEdit(p)} style={{ padding: "4px 12px", fontSize: 12 }}>
                        Edit
                      </Button>
                      <Button variant="danger" onClick={() => handleDelete(p.id)} style={{ padding: "4px 12px", fontSize: 12 }}>
                        Delete
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
