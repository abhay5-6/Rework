import api from "./client";

export interface SearchResult {
  messages: Array<{
    type: string;
    id: number;
    content: string;
    created_at: string;
    score: number;
  }>;
  memories: Array<{
    id: number;
    room_id: number;
    created_by: number;
    content: string;
    memory_type: string;
    created_at: string;
  }>;
}

export async function searchRoom(
  roomId: number,
  query: string
): Promise<SearchResult> {
  const response = await api.get(
    `/rooms/${roomId}/search`,
    {
      params: { query }
    }
  );
  return response.data;
}

export async function getRoomSummary(
  roomId: number,
  query: string
): Promise<{ summary: string | null }> {
  const response = await api.get(
    `/ai/summary/${roomId}`,
    {
      params: { query }
    }
  );
  return response.data;
}

export async function queryRoom(
  roomId: number,
  query: string
): Promise<{ answer: string }> {
  const response = await api.get(
    `/rooms/${roomId}/ai`,
    {
      params: { query }
    }
  );
  return response.data;
}
