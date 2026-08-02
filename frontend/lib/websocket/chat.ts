export function createChatSocket(
  roomId: number
) {

  // Try sessionStorage first (more secure), then localStorage (fallback)
  let token =
    sessionStorage.getItem(
      "token"
    );
  
  if (!token) {
    token = localStorage.getItem(
      "token"
    );
  }

  if (!token) {

    throw new Error(
      "No auth token found"
    );
  }

  // Note: Token is in URL query params which gets logged.
  // For production, implement token-in-header authentication
  // by using WebSocket subprotocols or a pre-auth session token.
  return new WebSocket(

    `${process.env
      .NEXT_PUBLIC_WS_URL}/ws/${roomId}?token=${token}`
  );
}