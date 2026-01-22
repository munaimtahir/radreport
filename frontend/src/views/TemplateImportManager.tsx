import React, { useState } from "react";
import { useAuth } from "../ui/auth";
import { apiUpload } from "../ui/api";
import PageHeader from "../ui/components/PageHeader";
import Button from "../ui/components/Button";
import ErrorAlert from "../ui/components/ErrorAlert";
import SuccessAlert from "../ui/components/SuccessAlert";

interface ValidationResult {
    is_valid: boolean;
    errors: string[];
    preview?: any;
}

export default function TemplateImportManager() {
    const { token } = useAuth();
    const [file, setFile] = useState<File | null>(null);
    const [validation, setValidation] = useState<ValidationResult | null>(null);
    const [importMode, setImportMode] = useState<"create" | "update">("create");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
            setValidation(null);
            setError("");
            setSuccess("");
        }
    };

    const validate = async () => {
        if (!file || !token) return;
        setLoading(true);
        setError("");

        const formData = new FormData();
        formData.append("file", file);

        try {
            const res = await apiUpload("/template-packages/validate/", token, formData);
            setValidation(res);
            if (!res.is_valid) {
                setError("Validation failed.");
            }
        } catch (e: any) {
            setError(e.message || "Validation request failed");
        } finally {
            setLoading(false);
        }
    };

    const executeImport = async () => {
        if (!file || !token || !validation?.is_valid) return;
        setLoading(true);

        const formData = new FormData();
        formData.append("file", file);
        // Note: apiUpload logic handles Multipart. 
        // We append query param for mode since FormData + JSON body mix is complex

        try {
            const res = await apiUpload(`/template-packages/import/?mode=${importMode}`, token, formData);
            setSuccess(res.message);
            setValidation(null);
            setFile(null);
            // Reset file input value? Hard with react controlled state on file input
            const fileInput = document.getElementById("file-upload") as HTMLInputElement;
            if (fileInput) fileInput.value = "";

        } catch (e: any) {
            setError(e.message || "Import failed");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <PageHeader title="Template Import Manager" subtitle="Import sectioned templates (USG, etc.)" />
            
            {/* SUCCESS: This page uses the CORRECT system for USG templates! */}
            <div style={{ 
                padding: 16, 
                marginBottom: 20, 
                backgroundColor: '#d4edda', 
                border: '1px solid #28a745', 
                borderRadius: 8,
                maxWidth: 900
            }}>
                <strong>✅ This is the correct interface for USG templates!</strong>
                <br />
                Upload JSON templates with sections, NA support, and checklists.
                <br />
                <small>After import, link services using: <code style={{ background: '#f5f5f5', padding: '2px 6px', borderRadius: 3 }}>
                    python manage.py link_usg_services
                </code></small>
            </div>
            
            <div style={{ maxWidth: 900, background: "white", padding: 24, borderRadius: 8, boxShadow: "0 1px 3px rgba(0,0,0,0.1)" }}>
                {error && <ErrorAlert message={error} onDismiss={() => setError("")} />}
                {success && <SuccessAlert message={success} onDismiss={() => setSuccess("")} />}

                <div style={{ marginBottom: 24 }}>
                    <h3>1. Select Template Package</h3>
                    <input
                        id="file-upload"
                        type="file"
                        accept=".json"
                        onChange={handleFileChange}
                        disabled={loading}
                        style={{ padding: 10, border: "1px solid #ccc", borderRadius: 4, width: "100%" }}
                    />
                    {file && (
                        <div style={{ marginTop: 12 }}>
                            <Button onClick={validate} disabled={loading}>
                                {loading ? "Validating..." : "Validate Package"}
                            </Button>
                        </div>
                    )}
                </div>

                {validation && (
                    <div style={{ padding: 20, background: validation.is_valid ? "#f0fdf4" : "#fef2f2", borderRadius: 6, border: `1px solid ${validation.is_valid ? "#bbf7d0" : "#fecaca"}` }}>
                        <h3>2. Validation Result</h3>

                        {!validation.is_valid && (
                            <div>
                                <h4 style={{ color: "#dc2626" }}>Errors Found:</h4>
                                <ul style={{ color: "#b91c1c" }}>
                                    {validation.errors.map((e, i) => <li key={i}>{e}</li>)}
                                </ul>
                            </div>
                        )}

                        {validation.is_valid && (
                            <div>
                                <h4 style={{ color: "#16a34a" }}>✓ Package Valid</h4>
                                <div style={{ fontSize: 14, color: "#4b5563" }}>
                                    <strong>Name:</strong> {validation.preview.name} <br />
                                    <strong>Code:</strong> {validation.preview.code} <br />
                                    <strong>Sections:</strong> {validation.preview.sections?.length || 0}
                                </div>

                                <div style={{ marginTop: 24, padding: 16, background: "white", borderRadius: 6 }}>
                                    <h3>3. Import Options</h3>
                                    <div style={{ display: "flex", gap: 20, alignItems: "center", marginBottom: 16 }}>
                                        <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }}>
                                            <input
                                                type="radio"
                                                name="mode"
                                                value="create"
                                                checked={importMode === "create"}
                                                onChange={(e) => setImportMode("create")}
                                            />
                                            Create New (Fail if exists)
                                        </label>
                                        <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }}>
                                            <input
                                                type="radio"
                                                name="mode"
                                                value="update"
                                                checked={importMode === "update"}
                                                onChange={(e) => setImportMode("update")}
                                            />
                                            Update Existing (New Version)
                                        </label>
                                    </div>

                                    <Button onClick={executeImport} disabled={loading} variant="primary">
                                        {loading ? "Importing..." : `Import as ${importMode === "create" ? "New Template" : "Update"}`}
                                    </Button>
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
