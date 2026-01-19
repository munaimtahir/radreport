import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { apiGet, apiPost, apiPatch, apiDelete } from "../ui/api";
import { useAuth } from "../ui/auth";
import PageHeader from "../ui/components/PageHeader";
import ErrorAlert from "../ui/components/ErrorAlert";
import Button from "../ui/components/Button";
import { theme } from "../theme";

interface Consultant {
    id: string;
    display_name: string;
    mobile_number: string;
    email: string;
    degrees: string;
    designation: string;
    is_active: boolean;
}

interface BillingRule {
    id: string;
    consultant: string;
    rule_type: string;
    consultant_percent: string;
    active_from: string | null;
    service: string | null; // Service ID
    service_name: string | null;
}

export default function ConsultantsPage() {
    const { token } = useAuth();
    const navigate = useNavigate();
    const [consultants, setConsultants] = useState<Consultant[]>([]);
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const [editingId, setEditingId] = useState<string | null>(null);

    // Form State
    const [formData, setFormData] = useState<Partial<Consultant>>({
        display_name: "",
        mobile_number: "",
        email: "",
        degrees: "",
        designation: "",
        is_active: true,
    });

    // Billing Rules State (for the editing consultant)
    const [rules, setRules] = useState<BillingRule[]>([]);
    const [newRuleData, setNewRuleData] = useState({
        consultant_percent: "",
        active_from: "",
        service_id: "", // Optional service ID
    });

    useEffect(() => {
        if (token) loadConsultants();
    }, [token]);

    const loadConsultants = async () => {
        try {
            setLoading(true);
            const data = await apiGet("/consultants/", token);
            setConsultants(data.results || data);
        } catch (err: any) {
            setError(err.message || "Failed to load consultants");
        } finally {
            setLoading(false);
        }
    };

    const loadRules = async (consultantId: string) => {
        try {
            const data = await apiGet(`/consultants/${consultantId}/rules/`, token);
            setRules(data.results || data);
        } catch (err: any) {
            console.error("Failed to load rules", err);
        }
    };

    const handleEdit = (c: Consultant) => {
        setEditingId(c.id);
        setFormData({
            display_name: c.display_name,
            mobile_number: c.mobile_number,
            email: c.email,
            degrees: c.degrees,
            designation: c.designation,
            is_active: c.is_active,
        });
        setRules([]); // Clear prev rules
        loadRules(c.id);
    };

    const handleCancelEdit = () => {
        setEditingId(null);
        setFormData({ display_name: "", mobile_number: "", email: "", degrees: "", designation: "", is_active: true });
        setRules([]);
    };

    const handleSave = async () => {
        if (!formData.display_name) {
            setError("Name is required");
            return;
        }
        try {
            setLoading(true);
            if (editingId && editingId !== "new") {
                await apiPatch(`/consultants/${editingId}/`, token, formData);
            } else {
                await apiPost("/consultants/", token, formData);
            }
            setEditingId(null);
            setFormData({ display_name: "", mobile_number: "", email: "", degrees: "", designation: "", is_active: true });
            loadConsultants();
        } catch (err: any) {
            setError(err.message || "Failed to save consultant");
        } finally {
            setLoading(false);
        }
    };

    const handleAddRule = async () => {
        if (!editingId || editingId === "new") return;
        if (!newRuleData.consultant_percent) {
            alert("Percentage is required");
            return;
        }
        try {
            const payload: any = {
                consultant_percent: newRuleData.consultant_percent,
                active_from: newRuleData.active_from || null,
                rule_type: "PERCENT_SPLIT"
            };
            if (newRuleData.service_id) {
                payload.service_id = newRuleData.service_id;
            }

            await apiPost(`/consultants/${editingId}/rules/`, token, payload);
            setNewRuleData({ consultant_percent: "", active_from: "", service_id: "" });
            loadRules(editingId);
        } catch (err: any) {
            alert(err.message || "Failed to add rule");
        }
    };

    const handleDeleteRule = async (ruleId: string) => {
        if (!editingId) return;
        if (!confirm("Are you sure?")) return;
        try {
            await apiDelete(`/consultant-billing-rules/${ruleId}/`, token);
            loadRules(editingId);
        } catch (err: any) {
            alert("Failed to delete rule: " + err.message);
        }
    };

    return (
        <div style={{ maxWidth: 800 }}>
            <PageHeader title="Consultants" />
            {error && <ErrorAlert message={error} onDismiss={() => setError("")} />}

            {editingId ? (
                <div style={{ border: `1px solid ${theme.colors.border}`, padding: 20, borderRadius: 8, background: "white" }}>
                    <h3>{editingId === "new" ? "Add New Consultant" : "Edit Consultant"}</h3>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
                        <div>
                            <label style={{ display: "block", fontSize: 12 }}>Name</label>
                            <input
                                style={{ width: "100%", padding: 8 }}
                                value={formData.display_name}
                                onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                            />
                        </div>
                        <div>
                            <label style={{ display: "block", fontSize: 12 }}>Designation</label>
                            <input
                                style={{ width: "100%", padding: 8 }}
                                value={formData.designation}
                                onChange={(e) => setFormData({ ...formData, designation: e.target.value })}
                            />
                        </div>
                        <div>
                            <label style={{ display: "block", fontSize: 12 }}>Degrees</label>
                            <input
                                style={{ width: "100%", padding: 8 }}
                                value={formData.degrees}
                                onChange={(e) => setFormData({ ...formData, degrees: e.target.value })}
                            />
                        </div>
                        <div>
                            <label style={{ display: "block", fontSize: 12 }}>Mobile</label>
                            <input
                                style={{ width: "100%", padding: 8 }}
                                value={formData.mobile_number}
                                onChange={(e) => setFormData({ ...formData, mobile_number: e.target.value })}
                            />
                        </div>
                        <div>
                            <label style={{ display: "block", fontSize: 12 }}>Email</label>
                            <input
                                style={{ width: "100%", padding: 8 }}
                                value={formData.email}
                                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                            />
                        </div>
                        <div>
                            <label style={{ display: "block", fontSize: 12 }}>Status</label>
                            <select
                                style={{ width: "100%", padding: 8 }}
                                value={formData.is_active ? "true" : "false"}
                                onChange={(e) => setFormData({ ...formData, is_active: e.target.value === "true" })}
                            >
                                <option value="true">Active</option>
                                <option value="false">Inactive</option>
                            </select>
                        </div>
                    </div>
                    <div style={{ display: "flex", gap: 8, marginBottom: 20 }}>
                        <Button onClick={handleSave} disabled={loading}>Save</Button>
                        <Button variant="secondary" onClick={handleCancelEdit}>Cancel</Button>
                    </div>

                    {editingId !== "new" && (
                        <>
                            <hr style={{ border: "none", borderTop: `1px solid ${theme.colors.border}`, margin: "20px 0" }} />

                            <h4>Percentage Share Rules</h4>
                            <p style={{ fontSize: 13, color: theme.colors.textSecondary }}>
                                Set the global percentage share, or specific shares for services.
                            </p>

                            {/* Add Rule Form */}
                            <div style={{ display: "flex", gap: 8, alignItems: "flex-end", marginBottom: 12, background: theme.colors.backgroundGray, padding: 10, borderRadius: 6 }}>
                                <div style={{ flex: 1 }}>
                                    <label style={{ fontSize: 11 }}>Service Override (Optional)</label>
                                    <input
                                        placeholder="Enter Service ID (UUID) or leave blank for Global"
                                        value={newRuleData.service_id}
                                        onChange={(e) => setNewRuleData({ ...newRuleData, service_id: e.target.value })}
                                        style={{ width: "100%", padding: 6, fontSize: 13 }}
                                    />
                                </div>
                                <div style={{ width: 100 }}>
                                    <label style={{ fontSize: 11 }}>Percent %</label>
                                    <input
                                        type="number"
                                        value={newRuleData.consultant_percent}
                                        onChange={(e) => setNewRuleData({ ...newRuleData, consultant_percent: e.target.value })}
                                        style={{ width: "100%", padding: 6, fontSize: 13 }}
                                    />
                                </div>
                                <div style={{ width: 140 }}>
                                    <label style={{ fontSize: 11 }}>Active From</label>
                                    <input
                                        type="date"
                                        value={newRuleData.active_from}
                                        onChange={(e) => setNewRuleData({ ...newRuleData, active_from: e.target.value })}
                                        style={{ width: "100%", padding: 6, fontSize: 13 }}
                                    />
                                </div>
                                <Button size="sm" onClick={handleAddRule}>Add Rule</Button>
                            </div>

                            {/* Rules List */}
                            <table style={{ width: "100%", fontSize: 14 }}>
                                <thead>
                                    <tr style={{ textAlign: "left", color: theme.colors.textSecondary }}>
                                        <th>Service</th>
                                        <th>Percent</th>
                                        <th>Active From</th>
                                        <th>Action</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {rules.map(rule => (
                                        <tr key={rule.id} style={{ borderBottom: "1px solid #eee" }}>
                                            <td style={{ padding: 6 }}>
                                                {rule.service_name || <span style={{ fontWeight: "bold" }}>Global Default</span>}
                                            </td>
                                            <td style={{ padding: 6 }}>{rule.consultant_percent}%</td>
                                            <td style={{ padding: 6 }}>{rule.active_from || "Always"}</td>
                                            <td style={{ padding: 6 }}>
                                                <button
                                                    onClick={() => handleDeleteRule(rule.id)}
                                                    style={{ color: theme.colors.danger, border: "none", background: "none", cursor: "pointer" }}
                                                >
                                                    Remove
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </>
                    )}

                </div>
            ) : (
                <>
                    <div style={{ marginBottom: 16 }}>
                        <Button onClick={() => {
                            setEditingId("new");
                            setFormData({ display_name: "New Consultant", mobile_number: "", email: "", degrees: "", designation: "", is_active: true });
                        }}>
                            Add Consultant
                        </Button>
                    </div>

                    <div style={{ display: "grid", gap: 12 }}>
                        {consultants.map((c) => (
                            <div
                                key={c.id}
                                style={{
                                    border: `1px solid ${theme.colors.border}`,
                                    padding: 16,
                                    borderRadius: 8,
                                    background: "white",
                                    display: "flex",
                                    justifyContent: "space-between",
                                    alignItems: "center",
                                }}
                            >
                                <div>
                                    <div style={{ fontWeight: "bold" }}>{c.display_name}</div>
                                    <div style={{ fontSize: 12, color: theme.colors.textSecondary }}>
                                        {c.designation} {c.degrees ? `• ${c.degrees}` : ""}
                                    </div>
                                    <div style={{ fontSize: 12, color: theme.colors.textTertiary }}>
                                        {c.mobile_number} {c.email ? `• ${c.email}` : ""}
                                    </div>
                                </div>
                                <div>
                                    <Button variant="secondary" size="sm" onClick={() => handleEdit(c)}>Edit & Settings</Button>
                                </div>
                            </div>
                        ))}
                    </div>
                </>
            )}
        </div>
    );
}
