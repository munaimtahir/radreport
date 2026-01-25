import { apiGet, apiPost } from "./api";

export interface ReportParameterOption {
    id: string;
    label: string;
    value: string;
}

export interface ReportParameter {
    parameter_id: string;
    name: string;
    slug: string;
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

export async function getReportSchema(workitemId: string, token: string | null): Promise<ReportSchema> {
    return apiGet(`/reporting/workitems/${workitemId}/schema/`, token);
}

export async function getReportValues(workitemId: string, token: string | null): Promise<ReportValuesResponse> {
    return apiGet(`/reporting/workitems/${workitemId}/values/`, token);
}

export async function saveReport(workitemId: string, valuesPayload: { values: ReportValueEntry[] }, token: string | null) {
    return apiPost(`/reporting/workitems/${workitemId}/save/`, token, valuesPayload);
}

export async function submitReport(workitemId: string, token: string | null) {
    return apiPost(`/reporting/workitems/${workitemId}/submit/`, token, {});
}
