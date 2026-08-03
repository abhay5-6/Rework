import { useEffect, useRef, useState, useCallback } from "react";
import { useSocketStore } from "@/lib/store/socketStore";
import { useQueueStore } from "@/lib/store/queueStore";
import { useRoomStore } from "@/lib/store/roomStore";
import { createChatSocket } from "@/lib/websocket/chat";

/**
 * Custom hook to manage the WebSocket connection for a specific room.
 * Handles reconnection logic, ping/pong for keep-alive, WebRTC signaling delegation,
 * and dispatching incoming chat/task events.
 * 
 * @param roomId - The ID of the room to connect to.
 * @param handleSignalingData - Callback function to process WebRTC signaling messages.
 * @param socketRef - Mutable ref to store the active WebSocket instance.
 * @returns Object containing connectionStatus, onlineUsers, typingUser, and a sendTypingEvent function.
 */
export function useRoomSocket(
  roomId: number,
  handleSignalingData: (msg: any) => void,
  socketRef: React.MutableRefObject<WebSocket | null>
) {
  const { socket, isConnected, setSocket, setIsConnected } = useSocketStore();
  const { removeMessage } = useQueueStore();
  const { addMessage: addRoomMessage } = useRoomStore();
  const [onlineUsers, setOnlineUsers] = useState<string[]>([]);
  const [typingUser, setTypingUser] = useState("");
  const [connectionStatus, setConnectionStatus] = useState("Connecting...");
  
  const reconnectAttemptsRef = useRef(0);
  const handleSignalingDataRef = useRef(handleSignalingData);

  useEffect(() => {
    handleSignalingDataRef.current = handleSignalingData;
  }, [handleSignalingData]);

  useEffect(() => {
    if (!roomId) return;
    let reconnectTimeout: NodeJS.Timeout;
    let isMounted = true;
    const maxReconnects = 5;
    let pingInterval: NodeJS.Timeout;

    function cleanupSocket() {
      clearInterval(pingInterval);
      if (!socketRef.current) return;
      socketRef.current.onopen = null;
      socketRef.current.onclose = null;
      socketRef.current.onerror = null;
      socketRef.current.onmessage = null;
      socketRef.current.close();
      socketRef.current = null;
      setSocket(null);
      setIsConnected(false);
    }

    function connectSocket() {
      if (!isMounted) return;
      const token = localStorage.getItem("token") || sessionStorage.getItem("token");
      if (!token) {
        console.warn(`[useRoomSocket] Connection aborted: Unauthorized access to room ${roomId}`);
        setConnectionStatus("Unauthorized");
        return;
      }
      if (socketRef.current && (socketRef.current.readyState === WebSocket.OPEN || socketRef.current.readyState === WebSocket.CONNECTING)) {
        return;
      }

      cleanupSocket();
      setConnectionStatus("Connecting...");

      const ws = createChatSocket(roomId);
      socketRef.current = ws;
      setSocket(ws);

      ws.onopen = () => {
        console.info(`[useRoomSocket] Connected to room ${roomId}`);
        reconnectAttemptsRef.current = 0;
        setConnectionStatus("Connected");
        setIsConnected(true);
        pingInterval = setInterval(() => {
          if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: "ping" }));
          }
        }, 20000);
      };

      ws.onclose = (event) => {
        cleanupSocket();
        if (!isMounted) return;
        
        console.warn(`[useRoomSocket] Disconnected from room ${roomId}. Code: ${event.code}`);
        if (event.code === 1008) {
          setConnectionStatus("Unauthorized");
          return;
        }
        if (reconnectAttemptsRef.current >= maxReconnects) {
          console.error(`[useRoomSocket] Max reconnect attempts reached for room ${roomId}`);
          setConnectionStatus("Connection Failed");
          return;
        }
        reconnectAttemptsRef.current++;
        setConnectionStatus("Disconnected");
        
        // Exponential backoff
        const backoffTime = Math.min(3000 * Math.pow(1.5, reconnectAttemptsRef.current - 1), 10000);
        console.info(`[useRoomSocket] Attempting reconnect ${reconnectAttemptsRef.current}/${maxReconnects} in ${backoffTime}ms`);
        reconnectTimeout = setTimeout(connectSocket, backoffTime);
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);

          if (payload.type.startsWith("webrtc") || payload.type === "join_call" || payload.type === "leave_call") {
            handleSignalingDataRef.current(payload);
          } else if (payload.type === "task_created" || payload.type === "task_updated") {
            window.dispatchEvent(new CustomEvent("task_update", { detail: payload }));
          } else if (payload.type === "chat_message") {
            addRoomMessage(payload.data);
            if (payload.data.temp_id) {
              removeMessage(payload.data.temp_id);
            }
          } else if (payload.type === "online_users") {
            setOnlineUsers(payload.data.users);
          } else if (payload.type === "typing") {
            setTypingUser(payload.data.username);
            setTimeout(() => setTypingUser(""), 1500);
          }
        } catch (error) {
          console.error(`[useRoomSocket] Failed to parse incoming message in room ${roomId}:`, error);
        }
      };
    }

    connectSocket();

    return () => {
      isMounted = false;
      clearTimeout(reconnectTimeout);
      clearInterval(pingInterval);
      cleanupSocket();
    };
  }, [roomId, setSocket, setIsConnected, addRoomMessage, removeMessage]);

  const sendTypingEvent = useCallback(() => {
    const ws = socketRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    ws.send(JSON.stringify({ type: "typing" }));
  }, []);

  return {
    connectionStatus,
    onlineUsers,
    typingUser,
    sendTypingEvent
  };
}
