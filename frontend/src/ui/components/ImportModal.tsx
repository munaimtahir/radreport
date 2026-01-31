import React, { useState, useCallback } from "react";
import { useAuth } from "../auth";
import { apiUpload } from "../api";
import { theme } from "../../theme";
import Button from "./Button";
import Modal from "./Modal";

type ImportState = "idle" | "validating" | "validation_complete" | "importing" | "success" | "error";

interface ImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImportSuccess: () => void;
  importUrl: string;
  title: string;
}

interface DryRunResult {
  created: number;
  updated: number;
  errors: { row: number; error: string }[];
  preview: any[];
}

export default function ImportModal({ isOpen, onClose, onImportSuccess, importUrl, title }: ImportModalProps) {
  const { token } = useAuth();
  const [file, setFile] = useState<File | null>(null);
  const [state, setState] = useState<ImportState>("idle");
  const [dryRunResult, setDryRunResult] = useState<DryRunResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const reset = () => {
    setFile(null);
    setState("idle");
    setDryRunResult(null);
    setErrorMessage(null);
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFile(e.target.files[0]);
      setState("idle");
      setDryRunResult(null);
    }
  };

  const handleDryRun = useCallback(async () => {
    if (!file || !token) return;
    setState("validating");
    setErrorMessage(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const result = await apiUpload(`${importUrl}?dry_run=true`, token, formData);
      setDryRunResult(result);
      setState("validation_complete");
      if (result.errors && result.errors.length > 0) {
        setErrorMessage("Validation failed. Please fix the errors in your CSV and try again.");
      }
    } catch (e: any) {
      setState("error");
      setErrorMessage(e.message || "Validation failed");
    }
  }, [file, token, importUrl]);

  const handleApplyImport = useCallback(async () => {
    if (!file || !token) return;
    setState("importing");
    setErrorMessage(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      await apiUpload(`${importUrl}?dry_run=false`, token, formData);
      setState("success");
      onImportSuccess();
    } catch (e: any) {
      setState("error");
      setErrorMessage(e.message || "Import failed");
    }
  }, [file, token, importUrl, onImportSuccess]);

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title={title}>
      {state === "success" ? (
        <div>
          <p>Import successful!</p>
          <Button onClick={handleClose}>Close</Button>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {errorMessage && <div style={{ color: theme.colors.danger, fontWeight: theme.typography.fontWeight.medium }}>{errorMessage}</div>}
          <input type="file" accept=".csv" onChange={handleFileChange} />
          
          {file && (
            <Button onClick={handleDryRun} disabled={state === "validating"}>
              {state === "validating" ? "Validating..." : "Validate (Dry Run)"}
            </Button>
          )}

          {dryRunResult && state === "validation_complete" && (
            <div>
              <h3 style={{ fontSize: 16, marginBottom: 8 }}>Validation Result</h3>
              <p>To be Created: {dryRunResult.created}</p>
              <p>To be Updated: {dryRunResult.updated}</p>
              <p>Errors: {dryRunResult.errors?.length || 0}</p>
              
              {dryRunResult.errors && dryRunResult.errors.length > 0 && (
                <div style={{ maxHeight: 200, overflowY: "auto", border: `1px solid ${theme.colors.border}`, borderRadius: theme.radius.base, padding: 8 }}>
                  <table style={{ width: "100%", fontSize: 12 }}>
                    <thead>
                      <tr>
                        <th style={{ textAlign: "left" }}>Row</th>
                        <th style={{ textAlign: "left" }}>Error</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dryRunResult.errors.map((err, i) => (
                        <tr key={i}>
                          <td>{err.row}</td>
                          <td>{err.error}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {dryRunResult.errors?.length === 0 && (
                <Button onClick={handleApplyImport} disabled={state === "importing"} variant="primary" style={{ marginTop: 16 }}>
                  {state === "importing" ? "Importing..." : "Apply Import"}
                </Button>
              )}
            </div>
          )}
        </div>
      )}
    </Modal>
  );
}
