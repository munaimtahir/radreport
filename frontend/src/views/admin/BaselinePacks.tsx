import React, { useEffect, useMemo, useState } from "react";
import { useAuth } from "../../ui/auth";
import { apiGet, API_BASE } from "../../ui/api";
import Button from "../../ui/components/Button";
import ErrorAlert from "../../ui/components/ErrorAlert";
import { theme } from "../../theme";

interface PackMeta {
  slug: string;
  profile_code: string;
  profile_name: string;
  modality: string;
  version: string;
}

interface SeedStep {
  file: string;
  status: number;
  data: Record<string, any>;
}

interface SeedResult {
  pack: string;
  dry_run: boolean;
  steps: SeedStep[];
  errors: any[];
  verification?: any;
}

const cardAccent = {
  usg_abdomen_v1: "linear-gradient(135deg, #0f766e, #115e59)",
  usg_kub_v1: "linear-gradient(135deg, #1f2937, #0f172a)",
  usg_pelvis_v1: "linear-gradient(135deg, #7c2d12, #9a3412)",
};

function SectionHeading({ label }: { label: string }) {
  return (
    <div style={{
      fontSize: 12,
      letterSpacing: "0.08em",
      textTransform: "uppercase",
      color: theme.colors.textTertiary,
      fontWeight: theme.typography.fontWeight.semibold
    }}>
      {label}
    </div>
  );
}

export default function BaselinePacks() {
  const { token } = useAuth();
  const [packs, setPacks] = useState<PackMeta[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeResult, setActiveResult] = useState<SeedResult | null>(null);
  const [busySlug, setBusySlug] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      if (!token) return;
      try {
        const data = await apiGet("/admin/baseline-packs/", token);
        setPacks(Array.isArray(data) ? data : []);
      } catch (e: any) {
        setError(e.message || "Failed to load baseline packs");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [token]);

  const heroText = useMemo(() => {
    return "Boot a clean database with narrative-ready USG templates in minutes.";
  }, []);

  const downloadZip = async (slug: string) => {
    if (!token) return;
    const resp = await fetch(`${API_BASE}/admin/baseline-packs/${slug}/download/`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    if (!resp.ok) throw new Error(await resp.text());
    const blob = await resp.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${slug}.zip`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  };

  const seedPack = async (slug: string, dryRun: boolean) => {
    if (!token) return;
    setBusySlug(slug);
    setError(null);
    try {
      const resp = await fetch(`${API_BASE}/admin/baseline-packs/${slug}/seed/?dry_run=${dryRun}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await resp.json();
      setActiveResult(data as SeedResult);
      if (!resp.ok) {
        throw new Error(data.detail || "Seed failed");
      }
    } catch (e: any) {
      setError(e.message || "Seed failed");
    } finally {
      setBusySlug(null);
    }
  };

  const renderSteps = (result: SeedResult) => {
    if (!result) return null;
    return (
      <div style={{
        marginTop: 16,
        padding: 16,
        border: `1px solid ${theme.colors.border}`,
        borderRadius: theme.radius.lg,
        backgroundColor: "#0b1224",
        color: "#e2e8f0"
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
          <div style={{ fontWeight: 700 }}>Seed {result.pack} ({result.dry_run ? "Dry Run" : "Applied"})</div>
          <div style={{ color: result.errors.length ? theme.colors.danger : theme.colors.success }}>
            {result.errors.length ? "Errors" : "Ready"}
          </div>
        </div>
        {result.steps.map((step) => (
          <div key={step.file} style={{ display: "flex", alignItems: "center", gap: 10, padding: "6px 0", borderBottom: `1px solid ${theme.colors.borderLight}` }}>
            <span style={{ width: 110, fontFamily: "monospace" }}>{step.file}</span>
            <span style={{ fontSize: 13, color: step.status >= 400 ? theme.colors.danger : theme.colors.success }}>
              {step.status}
            </span>
            <span style={{ fontSize: 13, color: "#cbd5e1" }}>
              {Object.keys(step.data || {}).join(", ") || ""}
            </span>
          </div>
        ))}
        {result.verification && (
          <div style={{ marginTop: 10, paddingTop: 10, borderTop: `1px solid ${theme.colors.borderLight}` }}>
            <div style={{ fontWeight: 600 }}>Verification: {result.verification.status?.toUpperCase()}</div>
            <ul style={{ margin: "6px 0 0", paddingLeft: 18 }}>
              {(result.verification.checks || []).map((c: any) => (
                <li key={c.name} style={{ color: c.status === "pass" ? theme.colors.success : theme.colors.danger }}>
                  {c.name}: {c.status}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  if (loading) return <div style={{ padding: 20 }}>Loading baseline packs…</div>;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <div style={{
        padding: 24,
        borderRadius: theme.radius.xl,
        background: "radial-gradient(circle at 20% 20%, #1e293b, #0b1224)",
        color: "#e2e8f0",
        border: `1px solid ${theme.colors.border}`,
      }}>
        <div style={{ fontSize: 13, letterSpacing: "0.12em", textTransform: "uppercase", color: "#94a3b8" }}>Catalog & Templates</div>
        <h1 style={{ margin: "6px 0", fontSize: 28 }}>Baseline Packs</h1>
        <p style={{ maxWidth: 620, margin: "6px 0 0", color: "#cbd5e1" }}>{heroText}</p>
      </div>

      {error && <ErrorAlert message={error} />}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 16 }}>
        {packs.map((p) => (
          <div
            key={p.slug}
            style={{
              borderRadius: theme.radius.xl,
              overflow: "hidden",
              border: `1px solid ${theme.colors.border}`,
              boxShadow: "0 18px 45px rgba(0,0,0,0.12)",
              background: "white",
            }}
          >
            <div style={{
              padding: 16,
              background: cardAccent[p.slug as keyof typeof cardAccent] || "linear-gradient(135deg, #0f172a, #111827)",
              color: "#f8fafc",
            }}>
              <div style={{ fontSize: 13, letterSpacing: "0.1em", textTransform: "uppercase", opacity: 0.8 }}>{p.modality}</div>
              <div style={{ fontSize: 20, fontWeight: 700, marginTop: 4 }}>{p.profile_name}</div>
              <div style={{ fontSize: 12, opacity: 0.85 }}>{p.profile_code} · {p.version}</div>
            </div>
            <div style={{ padding: 16, display: "flex", flexDirection: "column", gap: 10 }}>
              <SectionHeading label="Actions" />
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                <Button variant="secondary" onClick={() => downloadZip(p.slug)}>
                  Download ZIP
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => seedPack(p.slug, true)}
                  disabled={busySlug === p.slug}
                  style={{ borderColor: theme.colors.info, color: theme.colors.info }}
                >
                  Preview seed
                </Button>
                <Button
                  variant="primary"
                  onClick={() => seedPack(p.slug, false)}
                  disabled={busySlug === p.slug}
                >
                  Apply seed
                </Button>
              </div>
              <SectionHeading label="Notes" />
              <ul style={{ margin: 0, paddingLeft: 18, color: theme.colors.textSecondary, fontSize: 13 }}>
                <li>Import order enforced: profiles → parameters → services → linkage.</li>
                <li>Dry-run validates row-level errors before apply.</li>
                <li>Apply triggers automatic linkage + narrative smoke test.</li>
              </ul>
            </div>
          </div>
        ))}
      </div>

      {activeResult && renderSteps(activeResult)}
    </div>
  );
}

