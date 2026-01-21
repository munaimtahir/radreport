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
    consultant_percent: string | null;
    consultant_fixed_amount: string | null;
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
        consultant_fixed_amount: "",
        rule_type: "PERCENT_SPLIT",
        active_from: "",
        service_id: "", // Optional service ID
    });

    // Services for search
    const [services, setServices] = useState<any[]>([]);
    const [serviceSearch, setServiceSearch] = useState("");
    const [showServiceDropdown, setShowServiceDropdown] = useState(false);

    useEffect(() => {
        if (token) {
            loadConsultants();
            loadServices();
        }
    }, [token]);

    const loadServices = async () => {
        try {
            const data = await apiGet("/services/", token);
            setServices(data.results || data || []);
        } catch (err) {
            console.error("Failed to load services", err);
        }
    };

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

    const handleDeleteRule = async (ruleId: string) => {
        if (!confirm("Are you sure you want to delete this rule?")) return;
        try {
            await apiDelete(`/consultants/${editingId}/rules/${ruleId}/`, token);
            loadRules(editingId!);
        } catch (err: any) {
            alert(err.message || "Failed to delete rule");
        }
    };

    const handleAddRule = async () => {
        if (!editingId || editingId === "new") return;

        if (newRuleData.rule_type === "PERCENT_SPLIT" && !newRuleData.consultant_percent) {
            alert("Percentage is required");
            return;
        }
        if (newRuleData.rule_type === "FIXED_AMOUNT" && !newRuleData.consultant_fixed_amount) {
            alert("Fixed Amount is required");
            return;
        }

        try {
            const payload: any = {
                active_from: newRuleData.active_from || null,
                rule_type: newRuleData.rule_type
            };

            if (newRuleData.rule_type === "PERCENT_SPLIT") {
                payload.consultant_percent = newRuleData.consultant_percent;
            } else {
                payload.consultant_fixed_amount = newRuleData.consultant_fixed_amount;
            }

            if (newRuleData.service_id) {
                payload.service_id = newRuleData.service_id;
            }

            await apiPost(`/consultants/${editingId}/rules/`, token, payload);
            setNewRuleData({
                consultant_percent: "",
                consultant_fixed_amount: "",
                active_from: "",
                service_id: "",
                rule_type: "PERCENT_SPLIT"
            });
            setServiceSearch("");
            loadRules(editingId);
        } catch (err: any) {
            alert(err.message || "Failed to add rule");
        }
    };

    const filteredServices = services.filter(s => {
        if (!serviceSearch) return false;
        const q = serviceSearch.toLowerCase();
        return s.name.toLowerCase().includes(q) || (s.code && s.code.toLowerCase().includes(q));
    }).slice(0, 10);

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

                            <h4>Billing Rules</h4>
                            <p style={{ fontSize: 13, color: theme.colors.textSecondary }}>
                                Set the global rules or specific service overrides.
                            </p>

                            {/* Add Rule Form */}
                            <div style={{ background: theme.colors.backgroundGray, padding: 10, borderRadius: 6, marginBottom: 12 }}>
                                <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
                                    <div style={{ flex: 1, position: "relative" }}>
                                        <label style={{ fontSize: 11 }}>Service Override (Leave blank for Global)</label>
                                        <input
                                            placeholder="Search Service..."
                                            value={serviceSearch}
                                            onFocus={() => setShowServiceDropdown(true)}
                                            onBlur={() => setTimeout(() => setShowServiceDropdown(false), 200)}
                                            onChange={(e) => {
                                                setServiceSearch(e.target.value);
                                                if (newRuleData.service_id) {
                                                    setNewRuleData({ ...newRuleData, service_id: "" });
                                                }
                                            }}
                                            style={{ width: "100%", padding: 6, fontSize: 13 }}
                                        />
                                        {newRuleData.service_id && (
                                            <span style={{ fontSize: 10, color: "green", fontWeight: "bold" }}>Selected: {services.find(s => s.id === newRuleData.service_id)?.name || newRuleData.service_id}</span>
                                        )}
                                        {showServiceDropdown && serviceSearch && (
                                            <div style={{
                                                position: "absolute", top: "100%", left: 0, right: 0,
                                                background: "white", border: "1px solid #ccc", zIndex: 10,
                                                maxHeight: 200, overflowY: "auto"
                                            }}>
                                                {filteredServices.map(s => (
                                                    <div
                                                        key={s.id}
                                                        style={{ padding: 8, cursor: "pointer", borderBottom: "1px solid #eee" }}
                                                        onClick={() => {
                                                            setNewRuleData({ ...newRuleData, service_id: s.id });
                                                            setServiceSearch(s.name);
                                                            setShowServiceDropdown(false);
                                                        }}
                                                    >
                                                        {s.name} <small>({s.code})</small>
                                                    </div>
                                                ))}
                                                {filteredServices.length === 0 && <div style={{ padding: 8 }}>No results</div>}
                                            </div>
                                        )}
                                    </div>
                                    <div style={{ width: 140 }}>
                                        <label style={{ fontSize: 11 }}>Rule Type</label>
                                        <select
                                            value={newRuleData.rule_type}
                                            onChange={(e) => setNewRuleData({ ...newRuleData, rule_type: e.target.value })}
                                            style={{ width: "100%", padding: 6, fontSize: 13 }}
                                        >
                                            <option value="PERCENT_SPLIT">Percentage</option>
                                            <option value="FIXED_AMOUNT">Fixed Amount</option>
                                        </select>
                                    </div>
                                </div>
                                <div style={{ display: "flex", gap: 8, alignItems: "flex-end" }}>
                                    {newRuleData.rule_type === "PERCENT_SPLIT" ? (
                                        <div style={{ width: 120 }}>
                                            <label style={{ fontSize: 11 }}>Percent %</label>
                                            <input
                                                type="number"
                                                value={newRuleData.consultant_percent}
                                                onChange={(e) => setNewRuleData({ ...newRuleData, consultant_percent: e.target.value })}
                                                style={{ width: "100%", padding: 6, fontSize: 13 }}
                                            />
                                        </div>
                                    ) : (
                                        <div style={{ width: 120 }}>
                                            <label style={{ fontSize: 11 }}>Fixed Amount</label>
                                            <input
                                                type="number"
                                                value={newRuleData.consultant_fixed_amount}
                                                onChange={(e) => setNewRuleData({ ...newRuleData, consultant_fixed_amount: e.target.value })}
                                                style={{ width: "100%", padding: 6, fontSize: 13 }}
                                            />
                                        </div>
                                    )}

                                    <div style={{ width: 140 }}>
                                        <label style={{ fontSize: 11 }}>Active From</label>
                                        <input
                                            type="date"
                                            value={newRuleData.active_from}
                                            onChange={(e) => setNewRuleData({ ...newRuleData, active_from: e.target.value })}
                                            style={{ width: "100%", padding: 6, fontSize: 13 }}
                                        />
                                    </div>
                                    <Button onClick={handleAddRule}>Add Rule</Button>
                                </div>
                            </div>

                            {/* Rules List */}
                            <table style={{ width: "100%", fontSize: 14 }}>
                                <thead>
                                    <tr style={{ textAlign: "left", color: theme.colors.textSecondary }}>
                                        <th>Service</th>
                                        <th>Rule (Percent / Fixed)</th>
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
                                            <td style={{ padding: 6 }}>
                                                {rule.rule_type === "FIXED_AMOUNT"
                                                    ? `${rule.consultant_fixed_amount} PKR`
                                                    : `${rule.consultant_percent}%`
                                                }
                                            </td>
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
                                    <Button variant="secondary" onClick={() => handleEdit(c)}>Edit & Settings</Button>
                                </div>
                            </div>
                        ))}
                    </div>
                </>
            )}
        </div>
    );
}
