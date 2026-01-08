import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../ui/auth";
import { login, apiGet } from "../ui/api";

export default function Login() {
  const { setToken } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [logoUrl, setLogoUrl] = useState<string | null>(null);

  useEffect(() => {
    // Try to fetch logo (without auth token for login page)
    // This will likely fail, but we handle it gracefully
    // Logo will be available after login
    apiGet("/receipt-settings/", null)
      .then((data: any) => {
        if (data?.logo_image_url) {
          setLogoUrl(data.logo_image_url);
        }
      })
      .catch(() => {
        // Logo not available without auth, continue without it
        // It will be fetched after successful login
      });
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const token = await login(username, password);
      setToken(token);
      navigate("/");
    } catch (err: any) {
      setError(err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "system-ui",
        backgroundColor: "#f5f5f5",
      }}
    >
      <div
        style={{
          maxWidth: 420,
          width: "100%",
          padding: 40,
          backgroundColor: "white",
          borderRadius: 8,
          boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
        }}
      >
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          {logoUrl && (
            <img
              src={logoUrl}
              alt="Logo"
              style={{ width: 64, height: 64, objectFit: "contain", marginBottom: 16 }}
            />
          )}
          <h1 style={{ margin: 0, fontSize: 24, fontWeight: 600, color: "#333" }}>
            Consultant Place Clinics
          </h1>
        </div>
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Username"
              required
              style={{
                width: "100%",
                padding: 12,
                fontSize: 14,
                border: "1px solid #ddd",
                borderRadius: 6,
                boxSizing: "border-box",
              }}
            />
          </div>
          <div>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
              required
              style={{
                width: "100%",
                padding: 12,
                fontSize: 14,
                border: "1px solid #ddd",
                borderRadius: 6,
                boxSizing: "border-box",
              }}
            />
          </div>
          {error && (
            <div
              style={{
                padding: "12px 16px",
                backgroundColor: "#fee",
                border: "1px solid #fcc",
                borderRadius: 6,
                color: "#c33",
                fontSize: 14,
              }}
            >
              {error}
            </div>
          )}
          <button
            type="submit"
            disabled={loading}
            style={{
              padding: 12,
              fontSize: 16,
              fontWeight: 500,
              backgroundColor: loading ? "#ccc" : "#0B5ED7",
              color: "white",
              border: "none",
              borderRadius: 6,
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            {loading ? "Logging in..." : "Login"}
          </button>
        </form>
        <p style={{ marginTop: 20, color: "#666", fontSize: 12, textAlign: "center" }}>
          Use your Django superuser credentials to login.
        </p>
      </div>
    </div>
  );
}
