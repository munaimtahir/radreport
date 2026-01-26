import { apiGet, apiPost } from "./api";

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
