import api from "./client";

export async function getMessages(
  roomId: number
) {
  const response = await api.get(
    `/workspaces/${roomId}/messages`
  );

  return response.data;
}