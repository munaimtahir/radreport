import React, { useEffect, useState } from "react";
import { useAuth } from "../ui/auth";
import { apiGet, apiPatch, apiUpload } from "../ui/api";
import PageHeader from "../ui/components/PageHeader";
import ErrorAlert from "../ui/components/ErrorAlert";
import SuccessAlert from "../ui/components/SuccessAlert";
import Button from "../ui/components/Button";
import { theme } from "../theme";

type PrintingConfig = {
  org_name: string;
  address?: string;
  phone?: string;
  disclaimer_text?: string;
  signatories_json: { name: string; designation: string }[];
  report_logo_url?: string;

  receipt_header_text: string;
  receipt_footer_text?: string;
  receipt_logo_url?: string;
  receipt_banner_url?: string;

  updated_at?: string;
};

type SeqInfo = {
  next_receipt?: string;
};

export default function PrintingSettings() {
  const { token } = useAuth();
  const [config, setConfig] = useState<PrintingConfig>({
    org_name: "Organization",
    address: "",
    phone: "",
    disclaimer_text: "This report is electronically verified.",
    signatories_json: [],
    receipt_header_text: "Consultant Place Clinic",
    receipt_footer_text:
      "Adjacent Excel Labs, Near Arman Pan Shop Faisalabad Road Jaranwala\nFor information/Appointment: Tel: 041 4313 777 | WhatsApp: 03279640897",
  });
  const [tab, setTab] = useState<"reports" | "receipts" | "sequences">("reports");
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [seqInfo, setSeqInfo] = useState<SeqInfo>({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!token) return;
    loadConfig();
    loadSeq();
  }, [token]);

  async function loadConfig() {
    try {
      const data = await apiGet("/printing/config/", token);
      setConfig({
        ...config,
        ...data,
      });
    } catch (e: any) {
      setError(e.message || "Failed to load printing settings");
    }
  }

  async function loadSeq() {
    try {
      const data = await apiGet("/printing/sequence/next?type=receipt&dry_run=1", token);
      setSeqInfo({ next_receipt: data.next });
    } catch {
      // ignore
    }
  }

  async function saveConfig(partial: Partial<PrintingConfig>) {
    if (!token) return;
    setLoading(true);
    setStatus("");
    setError("");
    try {
      const payload = { ...config, ...partial };
      await apiPatch("/printing/config/", token, payload);
      setStatus("Saved");
      setConfig(payload as PrintingConfig);
    } catch (e: any) {
      setError(e.message || "Failed to save settings");
    } finally {
      setLoading(false);
    }
  }

  async function upload(kind: "report_logo" | "receipt_logo" | "receipt_banner", file?: File | null) {
    if (!token || !file) return;
    setLoading(true);
    setStatus("");
    setError("");
    try {
      const form = new FormData();
      form.append(kind, file);
      await apiUpload(`/printing/config/upload-${kind}/`, token, form);
      await loadConfig();
      setStatus("Uploaded");
    } catch (e: any) {
      setError(e.message || "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  const tabBtn = (key: typeof tab, label: string) => (
    <button
      onClick={() => setTab(key)}
      style={{
        padding: "10px 14px",
        border: "none",
        borderBottom: tab === key ? `3px solid ${theme.colors.brandBlue}` : "3px solid transparent",
        background: "transparent",
        cursor: "pointer",
        fontWeight: tab === key ? 700 : 500,
      }}
    >
      {label}
    </button>
  );

  return (
    <div style={{ maxWidth: 1000, margin: "0 auto" }}>
      <PageHeader title="Printing Settings" subtitle="Configure report and receipt branding & numbering." />
      {error && <ErrorAlert message={error} onDismiss={() => setError("")} />}
      {status && <SuccessAlert message={status} onDismiss={() => setStatus("")} />}

      <div style={{ display: "flex", gap: 12, marginBottom: 16 }}>
        {tabBtn("reports", "Reports")}
        {tabBtn("receipts", "Receipts")}
        {tabBtn("sequences", "Sequences")}
      </div>

      {tab === "reports" && (
        <section style={panelStyle}>
          <h3>Report Branding</h3>
          <TwoCol>
            <LabeledInput
              label="Organization Name"
              value={config.org_name}
              onChange={(v) => setConfig({ ...config, org_name: v })}
            />
            <LabeledInput label="Phone" value={config.phone || ""} onChange={(v) => setConfig({ ...config, phone: v })} />
            <LabeledInput
              label="Address"
              multiline
              value={config.address || ""}
              onChange={(v) => setConfig({ ...config, address: v })}
            />
            <LabeledInput
              label="Disclaimer"
              multiline
              value={config.disclaimer_text || ""}
              onChange={(v) => setConfig({ ...config, disclaimer_text: v })}
            />
            <LabeledInput
              label="Signatories (name - designation per line)"
              multiline
              value={
                config.signatories_json?.map((s) => `${s.name} - ${s.designation}`).join("\n") || ""
              }
              onChange={(v) =>
                setConfig({
                  ...config,
                  signatories_json: v
                    .split("\n")
                    .filter(Boolean)
                    .map((line) => {
                      const [name, ...rest] = line.split("-");
                      return { name: name.trim(), designation: rest.join("-").trim() || "" };
                    }),
                })
              }
            />
          </TwoCol>
          <UploadBlock
            title="Report Logo"
            currentUrl={config.report_logo_url}
            onUpload={(file) => upload("report_logo", file)}
          />
          <Button onClick={() => saveConfig(config)} disabled={loading}>
            Save Report Settings
          </Button>
        </section>
      )}

      {tab === "receipts" && (
        <section style={panelStyle}>
          <h3>Receipt Branding</h3>
          <TwoCol>
            <LabeledInput
              label="Header Text"
              value={config.receipt_header_text}
              onChange={(v) => setConfig({ ...config, receipt_header_text: v })}
            />
            <LabeledInput
              label="Footer Text"
              multiline
              value={config.receipt_footer_text || ""}
              onChange={(v) => setConfig({ ...config, receipt_footer_text: v })}
            />
          </TwoCol>
          <UploadBlock
            title="Receipt Logo"
            currentUrl={config.receipt_logo_url}
            onUpload={(file) => upload("receipt_logo", file)}
          />
          <UploadBlock
            title="Receipt Banner"
            currentUrl={config.receipt_banner_url}
            onUpload={(file) => upload("receipt_banner", file)}
          />
          <Button onClick={() => saveConfig(config)} disabled={loading}>
            Save Receipt Settings
          </Button>
        </section>
      )}

      {tab === "sequences" && (
        <section style={panelStyle}>
          <h3>Sequences</h3>
          <div style={{ marginBottom: 8, color: theme.colors.textSecondary }}>
            Next receipt number preview: {seqInfo.next_receipt || "N/A"}
          </div>
          <Button onClick={loadSeq} disabled={loading}>
            Refresh Preview
          </Button>
        </section>
      )}
    </div>
  );
}

function LabeledInput({
  label,
  value,
  onChange,
  multiline = false,
}: {
  label: string;
  value: string;
  multiline?: boolean;
  onChange: (v: string) => void;
}) {
  return (
    <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      <span style={{ fontSize: 13, fontWeight: 600, color: "#444" }}>{label}</span>
      {multiline ? (
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          style={inputStyle}
          rows={3}
        />
      ) : (
        <input value={value} onChange={(e) => onChange(e.target.value)} style={inputStyle} />
      )}
    </label>
  );
}

const inputStyle: React.CSSProperties = {
  padding: "10px 12px",
  borderRadius: 8,
  border: "1px solid #ddd",
  fontSize: 14,
  fontFamily: "inherit",
};

const panelStyle: React.CSSProperties = {
  background: "white",
  border: "1px solid #e5e7eb",
  borderRadius: 12,
  padding: 16,
  marginBottom: 16,
  boxShadow: "0 1px 2px rgba(0,0,0,0.04)",
};

function TwoCol({ children }: { children: React.ReactNode }) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
        gap: 12,
        marginBottom: 12,
      }}
    >
      {children}
    </div>
  );
}

function UploadBlock({
  title,
  currentUrl,
  onUpload,
}: {
  title: string;
  currentUrl?: string;
  onUpload: (file?: File | null) => void;
}) {
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ fontWeight: 600, marginBottom: 6 }}>{title}</div>
      {currentUrl && (
        <div style={{ marginBottom: 8 }}>
          <img src={currentUrl} alt={title} style={{ maxHeight: 140, border: "1px solid #eee", padding: 6 }} />
        </div>
      )}
      <input
        type="file"
        accept="image/*"
        onChange={(e) => onUpload(e.target.files?.[0])}
        style={{ marginBottom: 6 }}
      />
    </div>
  );
}
