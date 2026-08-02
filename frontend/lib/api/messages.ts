import api from "./client";

export async function getMessages(
  roomId: number
) {
  const response = await api.get(
    `/rooms/${roomId}/messages`
  );

  return response.data;
}