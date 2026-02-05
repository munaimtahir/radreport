import { apiGet, apiPost, API_BASE } from "./api";

export interface ReportSchemaV2 {
    id: string;
    code?: string;
    name: string;
    schema_version: "v2";
    json_schema: Record<string, any>;
    ui_schema?: Record<string, any> | null;
}

export interface ReportValuesResponse {
    status: "draft" | "submitted" | "verified";
    is_published?: boolean;
    values_json?: Record<string, any>;
    narrative_json?: Record<string, any>;
    schema_version?: string;
    last_saved_at?: string;
    last_published_at?: string;
}

export async function getReportSchema(
    serviceVisitItemId: string,
    token: string | null
): Promise<ReportSchemaV2> {
    return apiGet(`/reporting/workitems/${serviceVisitItemId}/schema/`, token);
}

export async function getReportValues(serviceVisitItemId: string, token: string | null): Promise<ReportValuesResponse> {
    return apiGet(`/reporting/workitems/${serviceVisitItemId}/values/`, token);
}

export async function saveReport(
    serviceVisitItemId: string,
    valuesPayload: { schema_version: "v2"; values_json: Record<string, any> },
    token: string | null
) {
    return apiPost(`/reporting/workitems/${serviceVisitItemId}/save/`, token, valuesPayload);
}

export async function submitReport(serviceVisitItemId: string, token: string | null) {
    return apiPost(`/reporting/workitems/${serviceVisitItemId}/submit/`, token, {});
}

export interface NarrativeResponseV2 {
    schema_version: "v2";
    status: string;
    narrative_json: Record<string, any>;
}

export async function generateNarrative(serviceVisitItemId: string, token: string | null): Promise<NarrativeResponseV2> {
    return apiPost(`/reporting/workitems/${serviceVisitItemId}/generate-narrative/`, token, {});
}

export async function getNarrative(serviceVisitItemId: string, token: string | null): Promise<NarrativeResponseV2> {
    return apiGet(`/reporting/workitems/${serviceVisitItemId}/narrative/`, token);
}

export async function fetchReportPdf(serviceVisitItemId: string, token: string | null): Promise<Blob> {
    const response = await fetch(`${API_BASE}/reporting/workitems/${serviceVisitItemId}/report-pdf/`, {
        method: "GET",
        headers: {
            "Authorization": `Bearer ${token}`
        }
    });
    if (!response.ok) {
        throw new Error("Failed to fetch PDF");
    }
    return response.blob();
}

export async function verifyReport(serviceVisitItemId: string, notes: string, token: string | null) {
    return apiPost(`/reporting/workitems/${serviceVisitItemId}/verify/`, token, { notes });
}

export async function returnReport(serviceVisitItemId: string, reason: string, token: string | null) {
    return apiPost(`/reporting/workitems/${serviceVisitItemId}/return-for-correction/`, token, { reason });
}

export async function publishReport(serviceVisitItemId: string, notes: string, token: string | null) {
    return apiPost(`/reporting/workitems/${serviceVisitItemId}/publish/`, token, { notes, confirm: "PUBLISH" });
}

export async function checkIntegrity(serviceVisitItemId: string, version: number, token: string | null) {
    return apiGet(`/reporting/workitems/${serviceVisitItemId}/published-integrity/?version=${version}`, token);
}

export async function getPublishHistory(serviceVisitItemId: string, token: string | null) {
    return apiGet(`/reporting/workitems/${serviceVisitItemId}/publish-history/`, token);
}

export async function fetchPublishedPdf(serviceVisitItemId: string, version: number, token: string | null): Promise<Blob> {
    const response = await fetch(`${API_BASE}/reporting/workitems/${serviceVisitItemId}/published-pdf/?version=${version}`, {
        method: "GET",
        headers: {
            "Authorization": `Bearer ${token}`
        }
    });
    if (!response.ok) {
        throw new Error("Failed to fetch PDF");
    }
    return response.blob();
}
