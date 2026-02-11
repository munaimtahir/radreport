import React, { useEffect, useMemo, useRef, useState } from "react";
import PageHeader from "../../ui/components/PageHeader";
import Button from "../../ui/components/Button";
import ErrorAlert from "../../ui/components/ErrorAlert";
import SuccessAlert from "../../ui/components/SuccessAlert";
import Modal from "../../ui/components/Modal";
import { API_BASE, apiDelete, apiGet, apiPost, apiUpload } from "../../ui/api";
import { useAuth } from "../../ui/auth";
import { theme } from "../../theme";

type BackupItem = {
  id: string;
  date: string;
  status: string;
  trigger: string;
  created_by: string;
  uploaded: boolean;
  provider: string;
  backup_path: string;
  size: {
    db: number;
    media: number;
    infra: number;
  };
  can_delete: boolean;
  job_id?: string | null;
};

type BackupListResponse = {
  items: BackupItem[];
  cloud: {
    remote_name: string;
    remote_path: string;
    connected: boolean;
  };
  restore_in_progress: boolean;
  police_mode: boolean;
};

type BackupDetail = {
  id: string;
  status: string;
  trigger?: string;
  created_by?: string;
  backup_path?: string;
  db_path?: string;
  media_path?: string;
  infra_path?: string;
  logs_path?: string;
  meta: Record<string, any>;
  logs_tail: string[];
  checksums: Record<string, string>;
  can_delete: boolean;
  error_message?: string;
};

function formatBytes(value: number) {
  if (!Number.isFinite(value) || value <= 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let v = value;
  let i = 0;
  while (v >= 1024 && i < units.length - 1) {
    v /= 1024;
    i += 1;
  }
  return `${v.toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

function isRunning(status: string) {
  return status === "RUNNING";
}

export default function BackupOpsPage() {
  const { token, user } = useAuth();
  const [data, setData] = useState<BackupListResponse | null>(null);
  const [selected, setSelected] = useState<BackupDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);
  const [showCloud, setShowCloud] = useState(false);
  const [showRestore, setShowRestore] = useState(false);
  const [restoreTarget, setRestoreTarget] = useState<BackupItem | null>(null);
  const [restorePhrase, setRestorePhrase] = useState("");
  const [restoreIdText, setRestoreIdText] = useState("");
  const [remoteName, setRemoteName] = useState("offsite");
  const [remotePath, setRemotePath] = useState("radreport-backups");
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const isSuperuser = user?.is_superuser || false;

  async function load() {
    if (!token) return;
    setLoading(true);
    try {
      const payload = (await apiGet("/backups/", token)) as BackupListResponse;
      setData(payload);
      setRemoteName(payload.cloud.remote_name || "offsite");
      setRemotePath(payload.cloud.remote_path || "radreport-backups");
    } catch (err: any) {
      setError(err?.message || "Failed to load backups");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const hasRunning = useMemo(() => (data?.items || []).some((x) => isRunning(x.status)) || !!data?.restore_in_progress, [data]);

  useEffect(() => {
    if (!hasRunning) return;
    const timer = window.setInterval(() => {
      load();
      if (selected?.id) {
        viewDetails(selected.id);
      }
    }, 2500);
    return () => window.clearInterval(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasRunning, selected?.id]);

  async function viewDetails(id: string) {
    if (!token) return;
    setError(null);
    try {
      const payload = (await apiGet(`/backups/${id}/`, token)) as BackupDetail;
      setSelected(payload);
    } catch (err: any) {
      setError(err?.message || "Failed to load backup detail");
    }
  }

  async function createBackupNow() {
    if (!token) return;
    setBusy(true);
    setError(null);
    setOk(null);
    try {
      await apiPost("/backups/", token, { force: false, deletable: true });
      setOk("Backup job started");
      await load();
    } catch (err: any) {
      setError(err?.message || "Failed to start backup");
    } finally {
      setBusy(false);
    }
  }

  async function exportBackup(id: string) {
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE}/backups/${id}/export/`, {
        method: "GET",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        const t = await res.text();
        throw new Error(t || `Export failed (${res.status})`);
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `backup-${id}.tar.gz`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      setOk("Backup export downloaded");
    } catch (err: any) {
      setError(err?.message || "Export failed");
    }
  }

  async function uploadCloud(id: string) {
    if (!token) return;
    setBusy(true);
    try {
      await apiPost(`/backups/${id}/upload/`, token, {});
      setOk("Cloud upload started");
      await load();
    } catch (err: any) {
      setError(err?.message || "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  async function deleteBackup(id: string) {
    if (!token) return;
    const okDelete = window.confirm("Delete this backup permanently?");
    if (!okDelete) return;
    setBusy(true);
    try {
      await apiDelete(`/backups/${id}/`, token);
      setOk("Backup deleted");
      if (selected?.id === id) setSelected(null);
      await load();
    } catch (err: any) {
      setError(err?.message || "Delete failed");
    } finally {
      setBusy(false);
    }
  }

  async function importBackup(file: File) {
    if (!token) return;
    setBusy(true);
    setError(null);
    const form = new FormData();
    form.append("file", file);
    try {
      await apiUpload("/backups/import/", token, form);
      setOk("Backup import completed");
      await load();
    } catch (err: any) {
      setError(err?.message || "Import failed");
    } finally {
      setBusy(false);
    }
  }

  async function testCloudConnection() {
    if (!token) return;
    setBusy(true);
    setError(null);
    try {
      await apiPost("/backups/cloud/test/", token, { remote_name: remoteName, remote_path: remotePath });
      setOk("Cloud connection OK");
      await load();
    } catch (err: any) {
      setError(err?.message || "Cloud test failed");
    } finally {
      setBusy(false);
    }
  }

  async function confirmRestore() {
    if (!token || !restoreTarget) return;
    if (restorePhrase !== "RESTORE NOW") {
      setError('Restore confirmation phrase must be "RESTORE NOW"');
      return;
    }
    if (restoreIdText !== restoreTarget.id) {
      setError("Restore backup id confirmation does not match");
      return;
    }

    setBusy(true);
    try {
      await apiPost(`/backups/${restoreTarget.id}/restore/`, token, {
        confirm_phrase: restorePhrase,
        dry_run: false,
        yes: true,
        allow_system_caddy_overwrite: false,
      });
      setOk("Restore started");
      setShowRestore(false);
      setRestorePhrase("");
      setRestoreIdText("");
      setRestoreTarget(null);
      await load();
    } catch (err: any) {
      setError(err?.message || "Restore failed to start");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <PageHeader title="Backups" subtitle="Create, review, import/export, cloud sync, and restore backups" />

      {error && <ErrorAlert message={error} />}
      {ok && <SuccessAlert message={ok} />}

      <div
        style={{
          border: `1px solid ${theme.colors.border}`,
          borderRadius: theme.radius.lg,
          background: "#fff",
          padding: 16,
          display: "flex",
          justifyContent: "space-between",
          gap: 12,
          flexWrap: "wrap",
          alignItems: "center",
        }}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          <strong>Cloud Sync</strong>
          <span style={{ fontSize: 13, color: data?.cloud.connected ? theme.colors.success : theme.colors.warning }}>
            {data?.cloud.connected ? "Connected" : "Not connected"}
          </span>
          {data?.restore_in_progress && <span style={{ color: theme.colors.danger, fontSize: 13 }}>Restore in progress. New operations are blocked.</span>}
        </div>

        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <Button onClick={createBackupNow} disabled={busy || hasRunning}>
            Create Backup Now
          </Button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".zip,.tar,.gz,.tgz,.tar.gz"
            style={{ display: "none" }}
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) importBackup(f);
              if (fileInputRef.current) fileInputRef.current.value = "";
            }}
          />
          <Button variant="secondary" onClick={() => fileInputRef.current?.click()} disabled={busy || hasRunning}>
            Import Backup
          </Button>
          <Button variant="secondary" onClick={() => setShowCloud(true)}>
            Cloud Settings
          </Button>
        </div>
      </div>

      <div style={{ border: `1px solid ${theme.colors.border}`, borderRadius: theme.radius.lg, background: "#fff", overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 1100 }}>
          <thead>
            <tr style={{ background: theme.colors.backgroundGray }}>
              {[
                "Date/Time",
                "Trigger",
                "Status",
                "Size (DB/Media/Infra)",
                "Stored Locally",
                "Uploaded",
                "Actions",
              ].map((h) => (
                <th key={h} style={{ textAlign: "left", padding: 12, fontSize: 13, color: theme.colors.textSecondary }}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {(data?.items || []).map((item) => (
              <tr key={item.id} style={{ borderTop: `1px solid ${theme.colors.borderLight}` }}>
                <td style={{ padding: 12, fontSize: 13 }}>{item.date || item.id}</td>
                <td style={{ padding: 12, fontSize: 13 }}>{item.trigger === "cron" ? "Auto" : "Manual"}</td>
                <td style={{ padding: 12, fontSize: 13 }}>
                  <span
                    style={{
                      padding: "4px 8px",
                      borderRadius: 999,
                      background:
                        item.status === "SUCCESS" ? "#e6f7ee" : item.status === "FAILED" ? "#ffecec" : "#fff7e6",
                      color:
                        item.status === "SUCCESS" ? "#117a35" : item.status === "FAILED" ? "#b42318" : "#b54708",
                    }}
                  >
                    {item.status}
                  </span>
                </td>
                <td style={{ padding: 12, fontSize: 13 }}>
                  {formatBytes(item.size.db)} / {formatBytes(item.size.media)} / {formatBytes(item.size.infra)}
                </td>
                <td style={{ padding: 12, fontSize: 13 }}>Yes</td>
                <td style={{ padding: 12, fontSize: 13 }}>{item.uploaded ? `Yes ${item.provider ? `(${item.provider})` : ""}` : "No"}</td>
                <td style={{ padding: 12, fontSize: 13, display: "flex", gap: 6, flexWrap: "wrap" }}>
                  <Button variant="secondary" onClick={() => viewDetails(item.id)} disabled={busy}>
                    View
                  </Button>
                  <Button variant="secondary" onClick={() => exportBackup(item.id)} disabled={busy}>
                    Export
                  </Button>
                  <Button variant="secondary" onClick={() => uploadCloud(item.id)} disabled={busy || hasRunning}>
                    Upload
                  </Button>
                  {item.can_delete && (
                    <Button variant="danger" onClick={() => deleteBackup(item.id)} disabled={busy || hasRunning}>
                      Delete
                    </Button>
                  )}
                  {isSuperuser && (
                    <Button
                      variant="warning"
                      onClick={() => {
                        setRestoreTarget(item);
                        setShowRestore(true);
                      }}
                      disabled={busy || hasRunning}
                    >
                      Restore
                    </Button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {loading && <div style={{ padding: 12, fontSize: 13, color: theme.colors.textSecondary }}>Loading...</div>}
      </div>

      <Modal isOpen={!!selected} onClose={() => setSelected(null)} title="Backup Details">
        {selected && (
          <div style={{ display: "flex", flexDirection: "column", gap: 12, fontSize: 13 }}>
            <div>
              <strong>Created by:</strong> {selected.created_by || selected.meta?.created_by || "-"}
            </div>
            <div>
              <strong>Trigger:</strong> {selected.trigger || selected.meta?.trigger || "-"}
            </div>
            <div>
              <strong>Commit:</strong> {selected.meta?.git_commit || "-"}
            </div>
            <div>
              <strong>Artifacts:</strong>
              <div>DB: {selected.db_path || "-"}</div>
              <div>Media: {selected.media_path || "-"}</div>
              <div>Infra: {selected.infra_path || "-"}</div>
            </div>
            <div>
              <strong>Checksums:</strong>
              <pre style={{ maxHeight: 150, overflow: "auto", background: theme.colors.backgroundGray, padding: 10 }}>
                {Object.entries(selected.checksums)
                  .map(([k, v]) => `${k}: ${v}`)
                  .join("\n") || "No checksums"}
              </pre>
            </div>
            <div>
              <strong>Logs (tail):</strong>
              <pre style={{ maxHeight: 220, overflow: "auto", background: theme.colors.backgroundGray, padding: 10 }}>
                {selected.logs_tail?.join("\n") || "No logs"}
              </pre>
            </div>
          </div>
        )}
      </Modal>

      <Modal isOpen={showCloud} onClose={() => setShowCloud(false)} title="Cloud Settings">
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <label>
            <div style={{ fontSize: 13, marginBottom: 4 }}>Remote name</div>
            <input
              value={remoteName}
              onChange={(e) => setRemoteName(e.target.value)}
              style={{ width: "100%", padding: 8, borderRadius: 8, border: `1px solid ${theme.colors.border}` }}
            />
          </label>
          <label>
            <div style={{ fontSize: 13, marginBottom: 4 }}>Remote path</div>
            <input
              value={remotePath}
              onChange={(e) => setRemotePath(e.target.value)}
              style={{ width: "100%", padding: 8, borderRadius: 8, border: `1px solid ${theme.colors.border}` }}
            />
          </label>
          <div style={{ fontSize: 12, color: theme.colors.textSecondary }}>
            Configure rclone on server with: <code>rclone config</code>. Keep secrets in server-side rclone config only.
          </div>
          <div style={{ display: "flex", justifyContent: "flex-end", gap: 8 }}>
            <Button variant="secondary" onClick={() => setShowCloud(false)}>
              Close
            </Button>
            <Button onClick={testCloudConnection} disabled={busy}>
              Test Connection
            </Button>
          </div>
        </div>
      </Modal>

      <Modal isOpen={showRestore} onClose={() => setShowRestore(false)} title="Restore Backup">
        <div style={{ display: "flex", flexDirection: "column", gap: 12, fontSize: 13 }}>
          <div style={{ color: theme.colors.danger, fontWeight: 600 }}>
            Destructive action: this restores database/media/infra from selected backup.
          </div>
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            <li>Active users should be informed.</li>
            <li>Take a fresh backup before restore.</li>
            <li>Restore is superuser-only and audited.</li>
          </ul>
          <label>
            <div>Type confirmation phrase</div>
            <input
              value={restorePhrase}
              onChange={(e) => setRestorePhrase(e.target.value)}
              placeholder="RESTORE NOW"
              style={{ width: "100%", padding: 8, borderRadius: 8, border: `1px solid ${theme.colors.border}` }}
            />
          </label>
          <label>
            <div>Type backup id again</div>
            <input
              value={restoreIdText}
              onChange={(e) => setRestoreIdText(e.target.value)}
              placeholder={restoreTarget?.id || ""}
              style={{ width: "100%", padding: 8, borderRadius: 8, border: `1px solid ${theme.colors.border}` }}
            />
          </label>
          <div style={{ display: "flex", justifyContent: "flex-end", gap: 8 }}>
            <Button variant="secondary" onClick={() => setShowRestore(false)}>
              Cancel
            </Button>
            <Button variant="danger" onClick={confirmRestore} disabled={busy}>
              Start Restore
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
