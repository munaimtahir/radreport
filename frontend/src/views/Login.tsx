import React, { useState } from "react";
import { useAuth } from "../ui/auth";

export default function Login() {
  const { setToken } = useAuth();
  const [tokenInput, setTokenInput] = useState("");

  return (
    <div style={{ maxWidth: 420, margin: "10vh auto", fontFamily: "system-ui" }}>
      <h1>Login</h1>
      <p style={{ color: "#555" }}>
        MVP placeholder: paste a JWT access token here (use backend docs later).
      </p>
      <input
        value={tokenInput}
        onChange={(e) => setTokenInput(e.target.value)}
        placeholder="Paste JWT token"
        style={{ width: "100%", padding: 10 }}
      />
      <button style={{ marginTop: 12 }} onClick={() => setToken(tokenInput || null)}>
        Save Token
      </button>
    </div>
  );
}
