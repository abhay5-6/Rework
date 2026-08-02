import api from "./client";

export interface Desk {
  id: number;
  name: string;
  description: string | null;
  room_id: number;
  created_at: string;
}

export async function createDesk(name: string, roomId: number, description?: string): Promise<Desk> {
  const response = await api.post("/desks/", { name, description, room_id: roomId });
  return response.data;
}

export async function getRoomDesks(roomId: number): Promise<Desk[]> {
  const response = await api.get(`/desks/room/${roomId}`);
  return response.data;
}
