import React, { useEffect, useState } from "react";
import { useAuth } from "../ui/auth";
import { apiGet, apiPost } from "../ui/api";
import PageHeader from "../ui/components/PageHeader";
import ErrorAlert from "../ui/components/ErrorAlert";
import SuccessAlert from "../ui/components/SuccessAlert";
import Button from "../ui/components/Button";

interface ReceiptSettings {
  header_text: string;
  footer_text?: string;
  logo_image?: string;
  header_image?: string;
  logo_image_url?: string;
  header_image_url?: string;
  updated_at?: string;
}

export default function ReceiptSettings() {
  const { token } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const [success, setSuccess] = useState<string>("");
  const [settings, setSettings] = useState<ReceiptSettings>({
    header_text: "Consultants Clinic Place",
    footer_text: "",
  });
  const [logoPreview, setLogoPreview] = useState<string>("");
  const [headerPreview, setHeaderPreview] = useState<string>("");

  useEffect(() => {
    if (token) {
      loadSettings();
    }
  }, [token]);

  const loadSettings = async () => {
    if (!token) return;
    try {
      const data = await apiGet("/receipt-settings/", token);
      setSettings(data);
      if (data.logo_image_url) {
        setLogoPreview(data.logo_image_url);
      }
      if (data.header_image_url) {
        setHeaderPreview(data.header_image_url);
      }
    } catch (e: any) {
      setError(e.message);
    }
  };

  const handleUpdateHeaderText = async () => {
    if (!token) return;
    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const API_BASE = (import.meta as any).env.VITE_API_BASE || "http://localhost:8000/api";
      const response = await fetch(`${API_BASE}/receipt-settings/1/`, {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          header_text: settings.header_text,
          footer_text: settings.footer_text,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to update receipt text");
      }

      setSuccess("Receipt text updated successfully!");
      setTimeout(() => setSuccess(""), 3000);
    } catch (e: any) {
      setError(e.message || "Failed to update receipt text");
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateFooterText = async () => {
    if (!token) return;
    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const API_BASE = (import.meta as any).env.VITE_API_BASE || "http://localhost:8000/api";

  const handleUploadLogo = async (event: React.ChangeEvent<HTMLInputElement>) => {
    if (!token || !event.target.files?.[0]) return;
    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const API_BASE = (import.meta as any).env.VITE_API_BASE || "http://localhost:8000/api";
      const formData = new FormData();
      formData.append("logo_image", event.target.files[0]);

      const response = await fetch(`${API_BASE}/receipt-settings/logo/`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Failed to upload logo");
      }

      const data = await response.json();
      setSettings(data);
      if (data.logo_image_url) {
        setLogoPreview(data.logo_image_url);
      }
      setSuccess("Logo uploaded successfully!");
      setTimeout(() => setSuccess(""), 3000);
    } catch (e: any) {
      setError(e.message || "Failed to upload logo");
    } finally {
      setLoading(false);
    }
  };

  const handleUploadHeaderImage = async (event: React.ChangeEvent<HTMLInputElement>) => {
    if (!token || !event.target.files?.[0]) return;
    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const API_BASE = (import.meta as any).env.VITE_API_BASE || "http://localhost:8000/api";
      const formData = new FormData();
      formData.append("header_image", event.target.files[0]);

      const response = await fetch(`${API_BASE}/receipt-settings/header-image/`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Failed to upload header image");
      }

      const data = await response.json();
      setSettings(data);
      if (data.header_image_url) {
        setHeaderPreview(data.header_image_url);
      }
      setSuccess("Header image uploaded successfully!");
      setTimeout(() => setSuccess(""), 3000);
    } catch (e: any) {
      setError(e.message || "Failed to upload header image");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 800, margin: "0 auto" }}>
      <PageHeader title="Receipt Branding Settings" />

      {error && <ErrorAlert message={error} onDismiss={() => setError("")} />}
      {success && <SuccessAlert message={success} onDismiss={() => setSuccess("")} />}

      <div style={{ background: "#f9f9f9", padding: 20, borderRadius: 8, marginBottom: 20 }}>
        <h2 style={{ marginTop: 0 }}>Header & Footer Text</h2>
        <div style={{ marginBottom: 15 }}>
          <label style={{ display: "block", marginBottom: 8 }}>Header Text</label>
          <input
            type="text"
            value={settings.header_text}
            onChange={(e) => setSettings({ ...settings, header_text: e.target.value })}
            style={{ width: "100%", padding: 8 }}
            placeholder="Consultants Clinic Place"
          />
        </div>
        <div style={{ marginBottom: 15 }}>
          <label style={{ display: "block", marginBottom: 8 }}>Footer Text</label>
          <textarea
            value={settings.footer_text || ""}
            onChange={(e) => setSettings({ ...settings, footer_text: e.target.value })}
            style={{ width: "100%", padding: 8, minHeight: 100 }}
            placeholder="Footer text displayed at bottom of receipt"
          />
        </div>
        <Button onClick={handleUpdateHeaderText} disabled={loading}>
          {loading ? "Saving..." : "Save Receipt Text"}
        </Button>
      </div>

      <div style={{ background: "#f9f9f9", padding: 20, borderRadius: 8, marginBottom: 20 }}>
        <h2 style={{ marginTop: 0 }}>Logo Image</h2>
        {logoPreview && (
          <div style={{ marginBottom: 15 }}>
            <p>Current Logo:</p>
            <img
              src={logoPreview}
              alt="Logo preview"
              style={{ maxWidth: 200, maxHeight: 200, border: "1px solid #ddd", padding: 10 }}
            />
          </div>
        )}
        <div>
          <label style={{ display: "block", marginBottom: 8 }}>Upload Logo</label>
          <input
            type="file"
            accept="image/*"
            onChange={handleUploadLogo}
            disabled={loading}
            style={{ marginBottom: 10 }}
          />
          <p style={{ fontSize: 12, color: "#666" }}>
            Recommended: Square image, max 200x200px
          </p>
        </div>
      </div>

      <div style={{ background: "#f9f9f9", padding: 20, borderRadius: 8 }}>
        <h2 style={{ marginTop: 0 }}>Header Image (Banner)</h2>
        {headerPreview && (
          <div style={{ marginBottom: 15 }}>
            <p>Current Header Image:</p>
            <img
              src={headerPreview}
              alt="Header preview"
              style={{ maxWidth: "100%", maxHeight: 300, border: "1px solid #ddd", padding: 10 }}
            />
          </div>
        )}
        <div>
          <label style={{ display: "block", marginBottom: 8 }}>Upload Header Image</label>
          <input
            type="file"
            accept="image/*"
            onChange={handleUploadHeaderImage}
            disabled={loading}
            style={{ marginBottom: 10 }}
          />
          <p style={{ fontSize: 12, color: "#666" }}>
            Recommended: Wide banner image, 1200x200px or similar aspect ratio
          </p>
        </div>
      </div>
    </div>
  );
}
