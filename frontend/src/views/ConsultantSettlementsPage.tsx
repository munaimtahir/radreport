import React, { useEffect, useState } from "react";
import { apiGet, apiPost } from "../ui/api";
import { useAuth } from "../ui/auth";
import PageHeader from "../ui/components/PageHeader";
import ErrorAlert from "../ui/components/ErrorAlert";
import SuccessAlert from "../ui/components/SuccessAlert";
import Button from "../ui/components/Button";
import { theme } from "../theme";

interface Consultant {
  id: string;
  display_name: string;
}

interface SettlementLinePreview {
  service_item_id: string;
  visit_id: string;
  patient_name: string;
  service_name: string;
  item_amount_snapshot: string;
  paid_amount_snapshot: string;
  consultant_share_snapshot: string;
  clinic_share_snapshot: string;
}

interface SettlementPreview {
  consultant: Consultant;
  date_from: string;
  date_to: string;
  consultant_percent: string;
  gross_collected: string;
  consultant_payable: string;
  clinic_share: string;
  lines: SettlementLinePreview[];
}

interface SettlementRecord {
  id: string;
  consultant_name: string;
  date_from: string;
  date_to: string;
  gross_collected: string;
  net_payable: string;
  clinic_share: string;
  status: string;
  created_at: string;
}

export default function ConsultantSettlementsPage() {
  const { token } = useAuth();
  const [consultants, setConsultants] = useState<Consultant[]>([]);
  const [selectedConsultantId, setSelectedConsultantId] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [preview, setPreview] = useState<SettlementPreview | null>(null);
  const [settlements, setSettlements] = useState<SettlementRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    if (!token) return;
    loadConsultants();
    loadSettlements();
  }, [token]);

  const loadConsultants = async () => {
    if (!token) return;
    try {
      const data = await apiGet("/consultants/", token);
      setConsultants(data.results || data || []);
    } catch (err: any) {
      setError(err.message || "Failed to load consultants");
    }
  };

  const loadSettlements = async () => {
    if (!token) return;
    try {
      const data = await apiGet("/consultant-settlements/", token);
      setSettlements(data.results || data || []);
    } catch (err: any) {
      setError(err.message || "Failed to load settlements");
    }
  };

  const handlePreview = async () => {
    if (!token) return;
    if (!selectedConsultantId || !dateFrom || !dateTo) {
      setError("Select a consultant and date range before previewing.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const data = await apiGet(
        `/consultant-settlements/preview/?consultant_id=${selectedConsultantId}&date_from=${dateFrom}&date_to=${dateTo}`,
        token
      );
      setPreview(data);
    } catch (err: any) {
      setError(err.message || "Failed to preview settlement");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateDraft = async () => {
    if (!token) return;
    if (!selectedConsultantId || !dateFrom || !dateTo) {
      setError("Select a consultant and date range before creating a draft.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const data = await apiPost("/consultant-settlements/", token, {
        consultant_id: selectedConsultantId,
        date_from: dateFrom,
        date_to: dateTo,
      });
      setSuccess("Settlement draft created.");
      setPreview(null);
      await loadSettlements();
      return data;
    } catch (err: any) {
      setError(err.message || "Failed to create draft settlement");
    } finally {
      setLoading(false);
    }
  };

  const handleFinalize = async (settlementId: string) => {
    if (!token) return;
    if (!window.confirm("Finalize this settlement? This action cannot be undone.")) return;
    setLoading(true);
    setError("");
    try {
      await apiPost(`/consultant-settlements/${settlementId}/finalize/`, token, {});
      setSuccess("Settlement finalized.");
      await loadSettlements();
    } catch (err: any) {
      setError(err.message || "Failed to finalize settlement");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto" }}>
      <PageHeader title="Consultant Settlements" />

      {error && <ErrorAlert message={error} onDismiss={() => setError("")} />}
      {success && <SuccessAlert message={success} onDismiss={() => setSuccess("")} />}

      <div style={{ border: `1px solid ${theme.colors.border}`, padding: 20, borderRadius: 8, marginBottom: 24 }}>
        <h2>Settlement Preview</h2>
        <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
          <div>
            <label style={{ display: "block", marginBottom: 6 }}>Consultant</label>
            <select
              value={selectedConsultantId}
              onChange={(e) => setSelectedConsultantId(e.target.value)}
              style={{ width: "100%", padding: 8 }}
            >
              <option value="">Select consultant</option>
              {consultants.map((consultant) => (
                <option key={consultant.id} value={consultant.id}>
                  {consultant.display_name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label style={{ display: "block", marginBottom: 6 }}>Date From</label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              style={{ width: "100%", padding: 8 }}
            />
          </div>
          <div>
            <label style={{ display: "block", marginBottom: 6 }}>Date To</label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              style={{ width: "100%", padding: 8 }}
            />
          </div>
        </div>
        <div style={{ marginTop: 16, display: "flex", gap: 8, flexWrap: "wrap" }}>
          <Button onClick={handlePreview} disabled={loading}>Preview</Button>
          <Button variant="secondary" onClick={handleCreateDraft} disabled={loading}>Create Draft</Button>
        </div>
      </div>

      {preview && (
        <div style={{ border: `1px solid ${theme.colors.border}`, padding: 20, borderRadius: 8, marginBottom: 24 }}>
          <h3>Preview Totals</h3>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 16 }}>
            <div>Consultant Split (%):</div>
            <div><strong>{preview.consultant_percent}%</strong></div>
            <div>Gross Collected:</div>
            <div><strong>Rs. {preview.gross_collected}</strong></div>
            <div>Consultant Payable:</div>
            <div><strong>Rs. {preview.consultant_payable}</strong></div>
            <div>Clinic Share:</div>
            <div><strong>Rs. {preview.clinic_share}</strong></div>
          </div>
          <h4>Line Preview</h4>
          {preview.lines.length === 0 ? (
            <div style={{ color: theme.colors.textTertiary }}>No consultant-assigned items found.</div>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ textAlign: "left", borderBottom: `1px solid ${theme.colors.border}` }}>
                    <th style={{ padding: 8 }}>Visit</th>
                    <th style={{ padding: 8 }}>Patient</th>
                    <th style={{ padding: 8 }}>Service</th>
                    <th style={{ padding: 8 }}>Item Amount</th>
                    <th style={{ padding: 8 }}>Paid Amount</th>
                    <th style={{ padding: 8 }}>Consultant Share</th>
                    <th style={{ padding: 8 }}>Clinic Share</th>
                  </tr>
                </thead>
                <tbody>
                  {preview.lines.map((line) => (
                    <tr key={line.service_item_id} style={{ borderBottom: `1px solid ${theme.colors.border}` }}>
                      <td style={{ padding: 8 }}>{line.visit_id}</td>
                      <td style={{ padding: 8 }}>{line.patient_name}</td>
                      <td style={{ padding: 8 }}>{line.service_name}</td>
                      <td style={{ padding: 8 }}>Rs. {line.item_amount_snapshot}</td>
                      <td style={{ padding: 8 }}>Rs. {line.paid_amount_snapshot}</td>
                      <td style={{ padding: 8 }}>Rs. {line.consultant_share_snapshot}</td>
                      <td style={{ padding: 8 }}>Rs. {line.clinic_share_snapshot}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      <div style={{ border: `1px solid ${theme.colors.border}`, padding: 20, borderRadius: 8 }}>
        <h3>Settlement History</h3>
        {settlements.length === 0 ? (
          <div style={{ color: theme.colors.textTertiary }}>No settlements created yet.</div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ textAlign: "left", borderBottom: `1px solid ${theme.colors.border}` }}>
                  <th style={{ padding: 8 }}>Consultant</th>
                  <th style={{ padding: 8 }}>Date Range</th>
                  <th style={{ padding: 8 }}>Gross</th>
                  <th style={{ padding: 8 }}>Consultant Payable</th>
                  <th style={{ padding: 8 }}>Clinic Share</th>
                  <th style={{ padding: 8 }}>Status</th>
                  <th style={{ padding: 8 }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {settlements.map((settlement) => (
                  <tr key={settlement.id} style={{ borderBottom: `1px solid ${theme.colors.border}` }}>
                    <td style={{ padding: 8 }}>{settlement.consultant_name}</td>
                    <td style={{ padding: 8 }}>{settlement.date_from} → {settlement.date_to}</td>
                    <td style={{ padding: 8 }}>Rs. {settlement.gross_collected}</td>
                    <td style={{ padding: 8 }}>Rs. {settlement.net_payable}</td>
                    <td style={{ padding: 8 }}>Rs. {settlement.clinic_share}</td>
                    <td style={{ padding: 8 }}>{settlement.status}</td>
                    <td style={{ padding: 8 }}>
                      {settlement.status === "DRAFT" ? (
                        <Button variant="secondary" onClick={() => handleFinalize(settlement.id)} disabled={loading}>
                          Finalize
                        </Button>
                      ) : (
                        <span style={{ color: theme.colors.textTertiary }}>—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
