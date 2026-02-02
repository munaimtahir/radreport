import { apiGet, apiPatch, apiPost, apiPut } from "../ui/api";

const TEMPLATE_V2_BASE = "/reporting/templates-v2/";
const SERVICE_TEMPLATE_V2_BASE = "/reporting/service-templates-v2/";

export async function listTemplatesV2(token: string | null) {
  return apiGet(TEMPLATE_V2_BASE, token);
}

export async function createTemplateV2(token: string | null, payload: Record<string, any>) {
  return apiPost(TEMPLATE_V2_BASE, token, payload);
}

export async function updateTemplateV2(token: string | null, id: string, payload: Record<string, any>) {
  return apiPut(`${TEMPLATE_V2_BASE}${id}/`, token, payload);
}

export async function activateTemplateV2(token: string | null, id: string, force?: boolean) {
  const path = force
    ? `${TEMPLATE_V2_BASE}${id}/activate/?force=1`
    : `${TEMPLATE_V2_BASE}${id}/activate/`;
  return apiPost(path, token, {});
}

export async function listServiceTemplatesV2(token: string | null) {
  return apiGet(SERVICE_TEMPLATE_V2_BASE, token);
}

export async function createServiceTemplateV2(token: string | null, payload: Record<string, any>) {
  return apiPost(SERVICE_TEMPLATE_V2_BASE, token, payload);
}

export async function updateServiceTemplateV2(
  token: string | null,
  id: string,
  payload: Record<string, any>
) {
  return apiPatch(`${SERVICE_TEMPLATE_V2_BASE}${id}/`, token, payload);
}

export async function setDefaultServiceTemplateV2(token: string | null, id: string) {
  return apiPost(`${SERVICE_TEMPLATE_V2_BASE}${id}/set-default/`, token, {});
}

export async function toggleServiceTemplateV2Active(
  token: string | null,
  id: string,
  isActive: boolean
) {
  return apiPatch(`${SERVICE_TEMPLATE_V2_BASE}${id}/`, token, { is_active: isActive });
}
