import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../ui/auth";
import { login } from "../ui/api";
import { BrandHeader } from "../ui/components/brand";
import { theme } from "../theme";

export default function Login() {
  const { setToken } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

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
        fontFamily: theme.typography.fontFamily,
        backgroundColor: theme.colors.backgroundLight,
      }}
    >
      <div
        style={{
          maxWidth: 420,
          width: "100%",
          padding: 40,
          backgroundColor: theme.colors.background,
          borderRadius: theme.radius.md,
          boxShadow: theme.shadows.md,
        }}
      >
        <div style={{ marginBottom: 32 }}>
          <BrandHeader logoSize="lg" titleSize="md" layout="vertical" align="center" />
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
                border: `1px solid ${theme.colors.border}`,
                borderRadius: theme.radius.base,
                boxSizing: "border-box",
                fontFamily: theme.typography.fontFamily,
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
                border: `1px solid ${theme.colors.border}`,
                borderRadius: theme.radius.base,
                boxSizing: "border-box",
                fontFamily: theme.typography.fontFamily,
              }}
            />
          </div>
          {error && (
            <div
              style={{
                padding: "12px 16px",
                backgroundColor: "#fee",
                border: "1px solid #fcc",
                borderRadius: theme.radius.base,
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
              fontWeight: theme.typography.fontWeight.medium,
              backgroundColor: loading ? theme.colors.border : theme.colors.brandBlue,
              color: "white",
              border: "none",
              borderRadius: theme.radius.base,
              cursor: loading ? "not-allowed" : "pointer",
              transition: theme.transitions.base,
            }}
            onMouseEnter={(e) => {
              if (!loading) {
                (e.target as HTMLButtonElement).style.backgroundColor = theme.colors.brandBlueDark;
              }
            }}
            onMouseLeave={(e) => {
              if (!loading) {
                (e.target as HTMLButtonElement).style.backgroundColor = theme.colors.brandBlue;
              }
            }}
          >
            {loading ? "Logging in..." : "Login"}
          </button>
        </form>
        <p style={{ marginTop: 20, color: theme.colors.textSecondary, fontSize: 12, textAlign: "center" }}>
          Use your credentials to login
        </p>
      </div>
    </div>
  );
}
