import api from "./client";

export interface Organization {
  id: number;
  name: string;
  created_by: number;
  created_at: string;
}

export interface OrgMember {
  user_id: number;
  role: string;
  created_at: string;
  username: string;
}

export async function createOrganization(name: string): Promise<Organization> {
  const response = await api.post("/orgs/", { name });
  return response.data;
}

export async function getOrganizations(): Promise<Organization[]> {
  const response = await api.get("/orgs/");
  return response.data;
}

export async function getOrganization(orgId: number): Promise<Organization> {
  const response = await api.get(`/orgs/${orgId}`);
  return response.data;
}

export async function getOrgMembers(orgId: number): Promise<OrgMember[]> {
  const response = await api.get(`/orgs/${orgId}/members`);
  return response.data;
}
