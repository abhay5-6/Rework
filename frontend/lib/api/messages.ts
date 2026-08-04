import api from "./client";

export async function getMessages(
  roomId: number
) {
  const response = await api.get(
    `/workspaces/${roomId}/messages`
  );

  return response.data;
}

export async function updateMessage(
  roomId: number,
  messageId: number,
  content: string
) {
  const response = await api.put(
    `/workspaces/${roomId}/messages/${messageId}`,
    { content }
  );
  return response.data;
}

export async function moveMessage(
  roomId: number,
  messageId: number,
  channelId: number
) {
  const response = await api.patch(
    `/workspaces/${roomId}/messages/${messageId}/move`,
    { channel_id: channelId }
  );
  return response.data;
}