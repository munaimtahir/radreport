import React, { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import Button from "../ui/components/Button";
import ErrorAlert from "../ui/components/ErrorAlert";
import RadiologyMasterPrintLayout, { RadiologyMasterPayload } from "../components/reporting/RadiologyMasterPrintLayout";
import { useAuth } from "../ui/auth";
import { fetchReportPdf, getReportPrintPayload } from "../ui/reporting";

export default function RadiologyReportPrintPage() {
  const { service_visit_item_id: id } = useParams<{ service_visit_item_id: string }>();
  const { token } = useAuth();
  const navigate = useNavigate();

  const [payload, setPayload] = useState<RadiologyMasterPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id || !token) return;
    setLoading(true);
    setError(null);
    getReportPrintPayload(id, token)
      .then((data) => setPayload(data))
      .catch((e: any) => setError(e?.message || "Failed to load print preview"))
      .finally(() => setLoading(false));
  }, [id, token]);

  async function downloadServerPdf() {
    if (!id || !token) return;
    try {
      const blob = await fetchReportPdf(id, token);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `report-${id}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      setError(e?.message || "Failed to download server PDF");
    }
  }

  if (loading) {
    return <div style={{ padding: 24 }}>Loading print layout...</div>;
  }

  if (!payload) {
    return (
      <div style={{ padding: 24 }}>
        {error ? <ErrorAlert message={error} /> : null}
        <Button variant="secondary" onClick={() => navigate(-1)}>
          Back
        </Button>
      </div>
    );
  }

  return (
    <div>
      {error ? <div style={{ maxWidth: 960, margin: "10px auto 0" }}><ErrorAlert message={error} /></div> : null}
      <RadiologyMasterPrintLayout
        payload={payload}
        actions={
          <>
            <Button variant="secondary" onClick={() => navigate(-1)}>
              Back
            </Button>
            <Button variant="secondary" onClick={downloadServerPdf}>
              Download Server PDF
            </Button>
            <Button onClick={() => window.print()}>Print / Save PDF</Button>
          </>
        }
      />
    </div>
  );
}
