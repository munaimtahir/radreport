import { E2E_API_URL, E2E_USER, E2E_PASS } from '../utils/env';

export interface AuthSession {
  access: string;
  refresh: string;
}

export interface BootstrapData {
  patientId: string;
  visitId: string;
  workItemId: string;
  templateCode: string;
}

export async function loginAPI(): Promise<AuthSession> {
  const response = await fetch(`${E2E_API_URL}/api/auth/token/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: E2E_USER, password: E2E_PASS }),
  });

  if (!response.ok) {
    throw new Error(`Login failed: ${await response.text()}`);
  }

  return response.json() as Promise<AuthSession>;
}

export async function bootstrapV2Report(session: AuthSession): Promise<BootstrapData> {
  // 1. Find a service mapped to V2 template
  const servicesResponse = await fetch(`${E2E_API_URL}/api/reporting/service-templates-v2/`, {
    headers: { Authorization: `Bearer ${session.access}` },
  });
  const serviceMappings = await servicesResponse.json();
  const mapping = serviceMappings.find((m: any) => m.is_active && m.is_default);

  if (!mapping) {
    throw new Error('No active V2 service mapping found. Did you run the seed command?');
  }

  const serviceId = mapping.service;
  const templateId = mapping.template;

  // Fetch template details to get the code
  const templateResponse = await fetch(`${E2E_API_URL}/api/reporting/templates-v2/${templateId}/`, {
    headers: { Authorization: `Bearer ${session.access}` },
  });
  const template = await templateResponse.json();
  const templateCode = template.code;

  // 2. Create a patient
  const patientResponse = await fetch(`${E2E_API_URL}/api/patients/`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${session.access}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      name: `E2E Test Patient ${Date.now()}`,
      gender: 'male',
      age: 30,
      phone: '1234567890',
    }),
  });
  const patient = await patientResponse.json();

  // 3. Create a service visit with that service
  const visitResponse = await fetch(`${E2E_API_URL}/api/workflow/visits/create_visit/`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${session.access}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      patient_id: patient.id,
      service_ids: [serviceId],
      subtotal: "1000",
      total_amount: "1000",
      amount_paid: "1000",
      payment_method: "cash"
    }),
  });
  const visit = await visitResponse.json();
  const workItem = visit.items[0];

  return {
    patientId: patient.id,
    visitId: visit.id,
    workItemId: workItem.id,
    templateCode: templateCode,
  };
}
