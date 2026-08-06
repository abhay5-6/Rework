export function createChatSocket(roomId: number, ticket?: string): WebSocket {
  const wsUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";
  const url = ticket
    ? `${wsUrl}/ws/${roomId}?ticket=${ticket}`
    : `${wsUrl}/ws/${roomId}`;
  return new WebSocket(url);
}