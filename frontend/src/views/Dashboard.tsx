import React, { useEffect, useState } from "react";
import { useAuth } from "../ui/auth";
import { apiGet } from "../ui/api";
import { Link, useNavigate } from "react-router-dom";
import PageHeader from "../ui/components/PageHeader";
import ErrorAlert from "../ui/components/ErrorAlert";

interface DashboardSummary {
  date: string;
  server_time: string;
  total_patients_today: number;
  total_services_today: number;
  reports_pending: number;
  reports_verified: number;
  critical_delays: number;
  threshold_hours: number;
}

interface DashboardFlow {
  date: string;
  server_time: string;
  registered_count: number;
  paid_count: number;
  performed_count: number;
  reported_count: number;
  verified_count: number;
}

interface WorklistItem {
  id: string;
  visit_id: string;
  patient_name: string;
  patient_mrn: string;
  service_name: string;
  department: string;
  status: string;
  status_display: string;
  created_at: string;
  last_updated: string;
  waiting_minutes: number;
  assigned_to: string | null;
  action_url: string;
}

interface WorklistResponse {
  scope: string;
  items?: WorklistItem[];
  grouped_by_department?: Record<string, WorklistItem[]>;
  total_items: number;
}

interface HealthStatus {
  status: "ok" | "degraded" | "down";
  server_time: string;
  version: string;
  checks: {
    db: "ok" | "fail";
    storage: "ok" | "unknown";
  };
  latency_ms: number;
}

export default function Dashboard() {
  const { token, user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");
  
  // Layer 1: Summary
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  
  // Layer 2: Worklist
  const [worklist, setWorklist] = useState<WorklistResponse | null>(null);
  
  // Layer 3: Flow
  const [flow, setFlow] = useState<DashboardFlow | null>(null);
  
  // Layer 4: Health
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [healthLastChecked, setHealthLastChecked] = useState<Date | null>(null);
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  const isAdmin = user?.is_superuser || (user?.groups || []).some((g: string) => g.toLowerCase() === "admin");

  // Load dashboard data
  useEffect(() => {
    if (!token) return;
    loadDashboardData();
  }, [token]);

  // Health polling (every 60s)
  useEffect(() => {
    if (!token) return;
    loadHealth();
    const interval = setInterval(loadHealth, 60000);
    return () => clearInterval(interval);
  }, [token]);

  // Network status monitoring
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);
    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  const loadDashboardData = async () => {
    if (!token) return;
    setLoading(true);
    setError("");
    try {
      const [summaryData, worklistData, flowData] = await Promise.all([
        apiGet("/dashboard/summary/", token).catch(() => null),
        apiGet(`/dashboard/worklist/?scope=${isAdmin ? "department" : "my"}`, token).catch(() => null),
        apiGet("/dashboard/flow/", token).catch(() => null),
      ]);
      
      if (summaryData) setSummary(summaryData);
      if (worklistData) setWorklist(worklistData);
      if (flowData) setFlow(flowData);
    } catch (err: any) {
      setError(err.message || "Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  };

  const loadHealth = async () => {
    if (!token) return;
    try {
      const healthData = await apiGet("/health/", token);
      setHealth(healthData);
      setHealthLastChecked(new Date());
    } catch (err) {
      setHealth({
        status: "down",
        server_time: new Date().toISOString(),
        version: "unknown",
        checks: { db: "fail", storage: "unknown" },
        latency_ms: 0,
      });
      setHealthLastChecked(new Date());
    }
  };

  const handleKPIClick = (type: string) => {
    // Navigate to filtered list based on KPI type
    switch (type) {
      case "patients":
        navigate("/registration");
        break;
      case "services":
        navigate("/registration");
        break;
      case "pending":
        navigate("/worklists/verification?status=PENDING_VERIFICATION");
        break;
      case "verified":
        navigate("/reports?status=PUBLISHED");
        break;
      case "delays":
        navigate("/worklists/verification?status=PENDING_VERIFICATION");
        break;
    }
  };

  const handleWorklistItemClick = (item: WorklistItem) => {
    if (item.action_url) {
      navigate(item.action_url);
    }
  };

  const formatWaitingTime = (minutes: number) => {
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      IN_PROGRESS: "#ffc107",
      PENDING_VERIFICATION: "#0B5ED7",
      RETURNED_FOR_CORRECTION: "#dc3545",
      FINALIZED: "#28a745",
      PUBLISHED: "#28a745",
    };
    return colors[status] || "#666";
  };

  if (loading && !summary) {
    return (
      <div>
        <PageHeader title="Dashboard" />
        <div style={{ textAlign: "center", padding: 40, color: "#666" }}>Loading...</div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 1400, margin: "0 auto" }}>
      <PageHeader title="Dashboard" />
      
      {error && <ErrorAlert message={error} onDismiss={() => setError("")} />}

      {/* Layer 1: Global Status Strip (KPI Tiles) */}
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16, color: "#333" }}>
          Today's Overview
        </h2>
        <div style={{ 
          display: "grid", 
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", 
          gap: 16 
        }}>
          {[
            { key: "patients", label: "Total Patients Today", value: summary?.total_patients_today || 0, color: "#0B5ED7" },
            { key: "services", label: "Total Services Today", value: summary?.total_services_today || 0, color: "#17a2b8" },
            { key: "pending", label: "Reports Pending", value: summary?.reports_pending || 0, color: "#ffc107" },
            { key: "verified", label: "Reports Verified", value: summary?.reports_verified || 0, color: "#28a745" },
            { key: "delays", label: "Critical Delays", value: summary?.critical_delays || 0, color: "#dc3545" },
          ].map((tile) => (
            <div
              key={tile.key}
              onClick={() => handleKPIClick(tile.key)}
              style={{
                border: "1px solid #e0e0e0",
                borderRadius: 8,
                padding: 20,
                background: "white",
                boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
                cursor: "pointer",
                transition: "all 0.2s",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.boxShadow = "0 4px 8px rgba(0,0,0,0.15)";
                e.currentTarget.style.transform = "translateY(-2px)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.boxShadow = "0 1px 3px rgba(0,0,0,0.1)";
                e.currentTarget.style.transform = "translateY(0)";
              }}
            >
              <h3 style={{ margin: "0 0 10px 0", color: "#666", fontSize: 13, fontWeight: 500 }}>
                {tile.label}
              </h3>
              <div style={{ fontSize: 32, fontWeight: "bold", color: tile.color, marginBottom: 8 }}>
                {tile.value}
              </div>
              <div style={{ fontSize: 11, color: "#999" }}>Click to view →</div>
            </div>
          ))}
        </div>
      </div>

      {/* Layer 2: Work In Progress */}
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16, color: "#333" }}>
          {isAdmin ? "Department Worklists" : "My Worklist"}
        </h2>
        {worklist?.grouped_by_department ? (
          // Admin: Grouped by department
          Object.entries(worklist.grouped_by_department).map(([dept, items]) => (
            <div key={dept} style={{ marginBottom: 20 }}>
              <h3 style={{ fontSize: 14, fontWeight: 600, color: "#666", marginBottom: 8 }}>
                {dept} ({items.length} items)
              </h3>
              <div style={{ 
                border: "1px solid #e0e0e0", 
                borderRadius: 8, 
                background: "white",
                overflow: "hidden"
              }}>
                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                  <thead>
                    <tr style={{ background: "#f8f9fa", borderBottom: "1px solid #e0e0e0" }}>
                      <th style={{ padding: "12px", textAlign: "left", fontSize: 12, fontWeight: 600, color: "#666" }}>Patient</th>
                      <th style={{ padding: "12px", textAlign: "left", fontSize: 12, fontWeight: 600, color: "#666" }}>Service</th>
                      <th style={{ padding: "12px", textAlign: "left", fontSize: 12, fontWeight: 600, color: "#666" }}>Status</th>
                      <th style={{ padding: "12px", textAlign: "left", fontSize: 12, fontWeight: 600, color: "#666" }}>Waiting</th>
                      <th style={{ padding: "12px", textAlign: "left", fontSize: 12, fontWeight: 600, color: "#666" }}>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.slice(0, 10).map((item) => (
                      <tr
                        key={item.id}
                        onClick={() => handleWorklistItemClick(item)}
                        style={{ 
                          borderBottom: "1px solid #f0f0f0",
                          cursor: "pointer",
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.background = "#f8f9fa";
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.background = "white";
                        }}
                      >
                        <td style={{ padding: "12px", fontSize: 13 }}>
                          <div style={{ fontWeight: 500 }}>{item.patient_name}</div>
                          <div style={{ fontSize: 11, color: "#999" }}>{item.patient_mrn}</div>
                        </td>
                        <td style={{ padding: "12px", fontSize: 13 }}>{item.service_name}</td>
                        <td style={{ padding: "12px" }}>
                          <span style={{
                            padding: "4px 8px",
                            borderRadius: 4,
                            fontSize: 11,
                            fontWeight: 500,
                            background: getStatusColor(item.status) + "20",
                            color: getStatusColor(item.status),
                          }}>
                            {item.status_display}
                          </span>
                        </td>
                        <td style={{ padding: "12px", fontSize: 13, color: "#666" }}>
                          {formatWaitingTime(item.waiting_minutes)}
                        </td>
                        <td style={{ padding: "12px", fontSize: 12, color: "#0B5ED7" }}>
                          Open →
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))
        ) : worklist?.items && worklist.items.length > 0 ? (
          // Non-admin: My worklist
          <div style={{ 
            border: "1px solid #e0e0e0", 
            borderRadius: 8, 
            background: "white",
            overflow: "hidden"
          }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ background: "#f8f9fa", borderBottom: "1px solid #e0e0e0" }}>
                  <th style={{ padding: "12px", textAlign: "left", fontSize: 12, fontWeight: 600, color: "#666" }}>Patient</th>
                  <th style={{ padding: "12px", textAlign: "left", fontSize: 12, fontWeight: 600, color: "#666" }}>Service</th>
                  <th style={{ padding: "12px", textAlign: "left", fontSize: 12, fontWeight: 600, color: "#666" }}>Status</th>
                  <th style={{ padding: "12px", textAlign: "left", fontSize: 12, fontWeight: 600, color: "#666" }}>Waiting</th>
                  <th style={{ padding: "12px", textAlign: "left", fontSize: 12, fontWeight: 600, color: "#666" }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {worklist.items.slice(0, 20).map((item) => (
                  <tr
                    key={item.id}
                    onClick={() => handleWorklistItemClick(item)}
                    style={{ 
                      borderBottom: "1px solid #f0f0f0",
                      cursor: "pointer",
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = "#f8f9fa";
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = "white";
                    }}
                  >
                    <td style={{ padding: "12px", fontSize: 13 }}>
                      <div style={{ fontWeight: 500 }}>{item.patient_name}</div>
                      <div style={{ fontSize: 11, color: "#999" }}>{item.patient_mrn}</div>
                    </td>
                    <td style={{ padding: "12px", fontSize: 13 }}>{item.service_name}</td>
                    <td style={{ padding: "12px" }}>
                      <span style={{
                        padding: "4px 8px",
                        borderRadius: 4,
                        fontSize: 11,
                        fontWeight: 500,
                        background: getStatusColor(item.status) + "20",
                        color: getStatusColor(item.status),
                      }}>
                        {item.status_display}
                      </span>
                    </td>
                    <td style={{ padding: "12px", fontSize: 13, color: "#666" }}>
                      {formatWaitingTime(item.waiting_minutes)}
                    </td>
                    <td style={{ padding: "12px", fontSize: 12, color: "#0B5ED7" }}>
                      Open →
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ 
            border: "1px solid #e0e0e0", 
            borderRadius: 8, 
            padding: 40, 
            background: "white",
            textAlign: "center",
            color: "#999"
          }}>
            No work items found
          </div>
        )}
      </div>

      {/* Layer 3: Today's Flow */}
      {flow && (
        <div style={{ marginBottom: 24 }}>
          <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16, color: "#333" }}>
            Today's Flow
          </h2>
          <div style={{ 
            display: "grid", 
            gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", 
            gap: 16 
          }}>
            {[
              { label: "Registered", value: flow.registered_count, color: "#0B5ED7" },
              { label: "Paid", value: flow.paid_count, color: "#17a2b8" },
              { label: "Performed", value: flow.performed_count, color: "#ffc107" },
              { label: "Reported", value: flow.reported_count, color: "#fd7e14" },
              { label: "Verified", value: flow.verified_count, color: "#28a745" },
            ].map((step, idx, arr) => (
              <div key={step.label} style={{ position: "relative" }}>
                <div style={{
                  border: "1px solid #e0e0e0",
                  borderRadius: 8,
                  padding: 16,
                  background: "white",
                  textAlign: "center",
                }}>
                  <div style={{ fontSize: 24, fontWeight: "bold", color: step.color, marginBottom: 4 }}>
                    {step.value}
                  </div>
                  <div style={{ fontSize: 12, color: "#666", fontWeight: 500 }}>
                    {step.label}
                  </div>
                </div>
                {idx < arr.length - 1 && (
                  <div style={{
                    position: "absolute",
                    top: "50%",
                    right: -8,
                    transform: "translateY(-50%)",
                    fontSize: 20,
                    color: "#ccc",
                  }}>
                    →
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Layer 4: Alerts & System Health */}
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16, color: "#333" }}>
          Alerts & System Health
        </h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: 16 }}>
          {/* Alerts Card */}
          <div style={{ 
            border: "1px solid #e0e0e0", 
            borderRadius: 8, 
            padding: 20, 
            background: "white" 
          }}>
            <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12, color: "#333" }}>Alerts</h3>
            <div style={{ fontSize: 13, color: "#666" }}>
              {summary?.critical_delays && summary.critical_delays > 0 ? (
                <div style={{ padding: "8px 12px", background: "#fff3cd", borderRadius: 4, marginBottom: 8 }}>
                  ⚠️ {summary.critical_delays} items pending &gt; {summary.threshold_hours}h
                </div>
              ) : (
                <div style={{ color: "#999" }}>No active alerts</div>
              )}
            </div>
          </div>

          {/* System Health Card */}
          <div style={{ 
            border: "1px solid #e0e0e0", 
            borderRadius: 8, 
            padding: 20, 
            background: "white" 
          }}>
            <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12, color: "#333" }}>System Health</h3>
            {health ? (
              <div style={{ fontSize: 13 }}>
                <div style={{ marginBottom: 8 }}>
                  <span style={{ color: "#666" }}>Backend API: </span>
                  <span style={{ 
                    color: health.status === "ok" ? "#28a745" : health.status === "degraded" ? "#ffc107" : "#dc3545",
                    fontWeight: 500
                  }}>
                    {health.status.toUpperCase()}
                  </span>
                  {health.latency_ms > 0 && (
                    <span style={{ color: "#999", marginLeft: 8 }}>
                      ({health.latency_ms}ms)
                    </span>
                  )}
                </div>
                <div style={{ marginBottom: 8 }}>
                  <span style={{ color: "#666" }}>Database: </span>
                  <span style={{ 
                    color: health.checks.db === "ok" ? "#28a745" : "#dc3545",
                    fontWeight: 500
                  }}>
                    {health.checks.db.toUpperCase()}
                  </span>
                </div>
                <div style={{ marginBottom: 8 }}>
                  <span style={{ color: "#666" }}>Network: </span>
                  <span style={{ 
                    color: isOnline ? "#28a745" : "#dc3545",
                    fontWeight: 500
                  }}>
                    {isOnline ? "ONLINE" : "OFFLINE"}
                  </span>
                </div>
                {health.version && health.version !== "unknown" && (
                  <div style={{ marginBottom: 8, fontSize: 11, color: "#999" }}>
                    Version: {health.version.substring(0, 8)}
                  </div>
                )}
                {healthLastChecked && (
                  <div style={{ fontSize: 11, color: "#999" }}>
                    Last checked: {healthLastChecked.toLocaleTimeString()}
                  </div>
                )}
              </div>
            ) : (
              <div style={{ color: "#999", fontSize: 13 }}>Loading health status...</div>
            )}
          </div>
        </div>
      </div>

      {/* Layer 5: Shortcuts */}
      <div>
        <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16, color: "#333" }}>
          Quick Actions
        </h2>
        <div style={{ 
          display: "grid", 
          gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", 
          gap: 12 
        }}>
          {[
            { label: "New Registration", path: "/registration", icon: "➕" },
            { label: "Search Patient", path: "/registration", icon: "🔍" },
            { label: "USG Worklist", path: "/worklists/usg", icon: "📋" },
            { label: "Verification", path: "/worklists/verification", icon: "✓" },
            ...(isAdmin ? [{ label: "Templates", path: "/templates", icon: "📄" }] : []),
          ].slice(0, 5).map((action) => (
            <Link
              key={action.path}
              to={action.path}
              style={{
                border: "1px solid #e0e0e0",
                borderRadius: 8,
                padding: 16,
                background: "white",
                textDecoration: "none",
                textAlign: "center",
                transition: "all 0.2s",
                display: "block",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.boxShadow = "0 2px 4px rgba(0,0,0,0.1)";
                e.currentTarget.style.borderColor = "#0B5ED7";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.boxShadow = "none";
                e.currentTarget.style.borderColor = "#e0e0e0";
              }}
            >
              <div style={{ fontSize: 24, marginBottom: 8 }}>{action.icon}</div>
              <div style={{ fontSize: 13, color: "#333", fontWeight: 500 }}>
                {action.label}
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
