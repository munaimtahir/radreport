import { apiDelete, apiGet, apiPatch, apiPost, apiPut } from "../ui/api";

export type Permission = {
  id: number;
  name: string;
  codename: string;
  content_type: number;
  app_label?: string;
  model?: string;
};

export type Group = {
  id: number;
  name: string;
  permissions: number[];
};

export type User = {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  is_active: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  groups: number[];
  user_permissions: number[];
};

export type UserPayload = Omit<User, "id"> & { password?: string };

function buildQuery(params: Record<string, string | number | boolean | undefined>) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") return;
    search.set(key, String(value));
  });
  const q = search.toString();
  return q ? `?${q}` : "";
}

export async function listUsers(
  token: string | null,
  params: { search?: string } = {}
): Promise<User[]> {
  const query = buildQuery({ search: params.search });
  return apiGet(`/auth/users/${query}`, token);
}

export async function createUser(token: string | null, payload: UserPayload): Promise<User> {
  return apiPost("/auth/users/", token, payload);
}

export async function updateUser(token: string | null, id: number, payload: Partial<UserPayload>): Promise<User> {
  return apiPut(`/auth/users/${id}/`, token, payload);
}

export async function deleteUser(token: string | null, id: number) {
  return apiDelete(`/auth/users/${id}/`, token);
}

export async function resetUserPassword(token: string | null, id: number, password: string) {
  return apiPost(`/auth/users/${id}/reset-password/`, token, { password });
}

export async function listGroups(token: string | null): Promise<Group[]> {
  return apiGet("/auth/groups/", token);
}

export async function createGroup(token: string | null, payload: { name: string; permissions?: number[] }): Promise<Group> {
  return apiPost("/auth/groups/", token, payload);
}

export async function updateGroup(token: string | null, id: number, payload: Partial<Group>): Promise<Group> {
  return apiPatch(`/auth/groups/${id}/`, token, payload);
}

export async function deleteGroup(token: string | null, id: number) {
  return apiDelete(`/auth/groups/${id}/`, token);
}

export async function listPermissions(token: string | null): Promise<Permission[]> {
  return apiGet("/auth/permissions/", token);
}
