import api from "./client";

export interface Channel {
  id: number;
  name: string;
  description: string | null;
  workspace_id: number;
  is_private: boolean;
  created_at: string;
}

export async function createChannel(name: string, workspace_id: number, is_private: boolean = false, description?: string): Promise<Channel> {
  const response = await api.post("/channels/", { name, description, workspace_id, is_private });
  return response.data;
}

export async function getWorkspaceChannels(workspace_id: number): Promise<Channel[]> {
  const response = await api.get(`/channels/workspace/${workspace_id}`);
  return response.data;
}
