import React, { useEffect, useState } from "react";
import { useAuth } from "../ui/auth";
import { apiGet } from "../ui/api";

export default function Studies() {
  const { token } = useAuth();
  const [data, setData] = useState<any>(null);
  const [err, setErr] = useState<string>("");

  useEffect(() => {
    if (!token) return;
    apiGet("/studies/", token).then(setData).catch(e => setErr(String(e)));
  }, [token]);

  return (
    <div>
      <h1>Studies</h1>
      {err && <pre>{err}</pre>}
      <pre style={{ background: "#f6f6f6", padding: 12, borderRadius: 8 }}>
        {JSON.stringify(data, null, 2)}
      </pre>
    </div>
  );
}
