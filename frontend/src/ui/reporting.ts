import { apiGet, apiPost, API_BASE } from "./api";

export interface ReportParameterOption {
    id: string;
    label: string;
    value: string;
}

export interface ReportParameter {
    id: string; // Internal UUID
    parameter_id: string; // The UUID that should be used for value mapping as per spec
    name: string;
    type: "number" | "dropdown" | "checklist" | "boolean" | "short_text" | "long_text" | "heading" | "separator";
    unit: string | null;
    normal_value: string | null;
    is_required: boolean;
    options: ReportParameterOption[];
    section: string;
}

export interface ReportSchema {
    id: string;
    code: string;
    name: string;
    parameters: ReportParameter[];
}

export interface ReportValueEntry {
    parameter_id: string;
    value: any;
}

export interface ReportValuesResponse {
    status: "draft" | "submitted" | "verified";
    is_published?: boolean;
    values: ReportValueEntry[];
}

export async function getReportSchema(serviceVisitItemId: string, token: string | null): Promise<ReportSchema> {
    return apiGet(`/reporting/workitems/${serviceVisitItemId}/schema/`, token);
}

export async function getReportValues(serviceVisitItemId: string, token: string | null): Promise<ReportValuesResponse> {
    return apiGet(`/reporting/workitems/${serviceVisitItemId}/values/`, token);
}

export async function saveReport(serviceVisitItemId: string, valuesPayload: { values: ReportValueEntry[] }, token: string | null) {
    return apiPost(`/reporting/workitems/${serviceVisitItemId}/save/`, token, valuesPayload);
}

export async function submitReport(serviceVisitItemId: string, token: string | null) {
    return apiPost(`/reporting/workitems/${serviceVisitItemId}/submit/`, token, {});
}

export interface NarrativeResponse {
    status: string;
    narrative: {
        version: string;
        findings_text: string;
        impression_text: string;
        limitations_text: string;
    };
}

export async function generateNarrative(serviceVisitItemId: string, token: string | null): Promise<NarrativeResponse> {
    return apiPost(`/reporting/workitems/${serviceVisitItemId}/generate-narrative/`, token, {});
}

export async function getNarrative(serviceVisitItemId: string, token: string | null): Promise<NarrativeResponse> {
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

// Stage 4 Additions
export async function verifyReport(serviceVisitItemId: string, notes: string, token: string | null) {
    return apiPost(`/reporting/workitems/${serviceVisitItemId}/verify/`, token, { notes });
}

export async function returnReport(serviceVisitItemId: string, reason: string, token: string | null) {
    return apiPost(`/reporting/workitems/${serviceVisitItemId}/return-for-correction/`, token, { reason });
}

export async function publishReport(serviceVisitItemId: string, notes: string, token: string | null) {
    return apiPost(`/reporting/workitems/${serviceVisitItemId}/publish/`, token, { notes });
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
