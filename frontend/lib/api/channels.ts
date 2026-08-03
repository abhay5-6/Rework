import api from "./client";

export interface Channel {
  id: number;
  name: string;
  description: string | null;
  workspace_id: number;
  created_at: string;
}

export async function createDesk(name: string, roomId: number, description?: string): Promise<Channel> {
  const response = await api.post("/channels/", { name, description, workspace_id: roomId });
  return response.data;
}

export async function getRoomDesks(roomId: number): Promise<Channel[]> {
  const response = await api.get(`/channels/workspace/${roomId}`);
  return response.data;
}
