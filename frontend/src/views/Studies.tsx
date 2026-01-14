import React, { useEffect, useState } from "react";
import { useAuth } from "../ui/auth";
import { apiGet } from "../ui/api";
import PageHeader from "../ui/components/PageHeader";
import ErrorAlert from "../ui/components/ErrorAlert";

interface ServiceVisitItem {
  id: string;
  status: string;
  service_name_snapshot: string;
  service_name?: string;
  service_code?: string;
  department_snapshot: string;
  visit_id: string;
  patient_name: string;
  patient_mrn: string;
  created_at: string;
}

export default function Studies() {
  const { token } = useAuth();
  const [items, setItems] = useState<ServiceVisitItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<string>("");

  const loadData = async () => {
    if (!token) return;
    try {
      setLoading(true);
      const data = await apiGet(
        `/workflow/items/${statusFilter ? `?status=${statusFilter}` : ""}`,
        token
      );
      setItems(data.results || data || []);
      setError("");
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [token, statusFilter]);

  const statusColors: Record<string, string> = {
    REGISTERED: "#6c757d",
    IN_PROGRESS: "#ffc107",
    PENDING_VERIFICATION: "#17a2b8",
    RETURNED_FOR_CORRECTION: "#fd7e14",
    FINALIZED: "#28a745",
    PUBLISHED: "#007bff",
    CANCELLED: "#6f42c1",
  };

  return (
    <div>
      <PageHeader
        title="Workflow Items"
        actions={
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{
              padding: "8px 12px",
              fontSize: 14,
              border: "1px solid #ddd",
              borderRadius: 6,
            }}
          >
            <option value="">All Statuses</option>
            <option value="REGISTERED">Registered</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="PENDING_VERIFICATION">Pending Verification</option>
            <option value="RETURNED_FOR_CORRECTION">Returned for Correction</option>
            <option value="FINALIZED">Finalized</option>
            <option value="PUBLISHED">Published</option>
            <option value="CANCELLED">Cancelled</option>
          </select>
        }
      />

      {error && <ErrorAlert message={error} onDismiss={() => setError("")} />}

      {loading ? (
        <div>Loading...</div>
      ) : items.length === 0 ? (
        <div>No workflow items found.</div>
      ) : (
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ textAlign: "left", borderBottom: "2px solid #eee" }}>
                <th style={{ padding: 12 }}>Visit</th>
                <th style={{ padding: 12 }}>Patient</th>
                <th style={{ padding: 12 }}>Service</th>
                <th style={{ padding: 12 }}>Department</th>
                <th style={{ padding: 12 }}>Status</th>
                <th style={{ padding: 12 }}>Created</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id} style={{ borderBottom: "1px solid #eee" }}>
                  <td style={{ padding: 12 }}>{item.visit_id}</td>
                  <td style={{ padding: 12 }}>
                    {item.patient_name} ({item.patient_mrn})
                  </td>
                  <td style={{ padding: 12 }}>
                    {item.service_name_snapshot || item.service_name}
                    {item.service_code ? ` (${item.service_code})` : ""}
                  </td>
                  <td style={{ padding: 12 }}>{item.department_snapshot}</td>
                  <td style={{ padding: 12 }}>
                    <span
                      style={{
                        padding: "4px 8px",
                        borderRadius: 12,
                        background: statusColors[item.status] || "#6c757d",
                        color: "#fff",
                        fontSize: 12,
                      }}
                    >
                      {item.status.replace(/_/g, " ")}
                    </span>
                  </td>
                  <td style={{ padding: 12 }}>
                    {new Date(item.created_at).toLocaleString()}
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
