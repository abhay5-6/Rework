"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { toast } from "sonner";
import axios from "axios";
import { Video, PhoneOff, CheckCircle2, Sparkles, X } from "lucide-react";

import RoomSidebar from "./components/RoomSidebar";
import RoomHeader from "./components/RoomHeader";
import RoomRightSidebar from "./components/RoomRightSidebar";
import ChatArea from "./components/ChatArea";
import AIAssistantPanel from "@/components/ai/AIAssistantPanel";
import LoadingSpinner from "@/components/LoadingSpinner";
import KanbanBoard from "@/components/tasks/KanbanBoard";
import VideoGrid from "@/components/video/VideoGrid";

import { useWebRTC } from "@/hooks/useWebRTC";
import { isAuthenticated } from "@/lib/auth";
import { getMe } from "@/lib/api/auth";
import { getRoom, getRoomMembers } from "@/lib/api/rooms";
import { getRoomDesks } from "@/lib/api/desks";
import { getCollaborators } from "@/lib/api/collaborators";
import { getMessages } from "@/lib/api/messages";
import { createChatSocket } from "@/lib/websocket/chat";

import { useAuthStore } from "@/lib/store/authStore";
import { useRoomStore } from "@/lib/store/roomStore";
import { useSocketStore } from "@/lib/store/socketStore";
import { useQueueStore } from "@/lib/store/queueStore";

export default function RoomPage() {
  const params = useParams();
  const router = useRouter();
  const roomId = Number(params.id);

  // Stores
  const { user, setUser } = useAuthStore();
  const { room, setRoom, messages, setMessages, addMessage, setDesks, activeDeskId, setActiveDeskId } = useRoomStore();
  const { socket, isConnected, setSocket, setIsConnected } = useSocketStore();
  const { queue, removeMessage, incrementRetry } = useQueueStore();

  // Local state
  const [loading, setLoading] = useState(true);
  const [members, setMembers] = useState<{ user_id: number; username: string; role?: string }[]>([]);
  const [onlineUsers, setOnlineUsers] = useState<string[]>([]);
  const [currentUserRole, setCurrentUserRole] = useState<string | null>(null);
  const [collaborators, setCollaborators] = useState<number[]>([]);

  const [aiEnabled, setAiEnabled] = useState(true);
  const [isTasksOpen, setIsTasksOpen] = useState(false);
  const [aiPanelOpen, setAiPanelOpen] = useState(false);
  const [parseWithAI, setParseWithAI] = useState(true);
  const [typingUser, setTypingUser] = useState("");
  const [connectionStatus, setConnectionStatus] = useState("Connecting...");

  const socketRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);

  const {
    localStream,
    remoteStreams,
    inCall,
    startCall,
    leaveCall,
    handleSignalingData,
  } = useWebRTC(roomId, user?.username || "", socketRef);

  const handleSignalingDataRef = useRef(handleSignalingData);

  useEffect(() => {
    handleSignalingDataRef.current = handleSignalingData;
  }, [handleSignalingData]);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/login");
    }
  }, [router]);

  useEffect(() => {
    async function loadMessages() {
      try {
        const data = await getMessages(roomId);
        setMessages(data);
      } catch (error) {
        if (axios.isAxiosError(error) && error.response?.status === 403) {
          toast.error("You do not have access to this room");
          router.push("/rooms");
          return;
        }
        toast.error("Failed to load messages");
      } finally {
        setLoading(false);
      }
    }

    if (roomId) {
      loadMessages();
      getRoom(roomId)
        .then((roomData) => {
          setRoom(roomData);
          setAiEnabled(roomData.ai_enabled ?? true);
        })
        .catch(console.error);

      getRoomDesks(roomId)
        .then((data) => {
          setDesks(data);
          if (data.length > 0 && !activeDeskId) {
            setActiveDeskId(data[0].id);
          }
        })
        .catch(console.error);
    }
  }, [roomId, router, setMessages, setRoom, setDesks, activeDeskId, setActiveDeskId]);

  useEffect(() => {
    async function loadCurrentUser() {
      try {
        const u = await getMe();
        setUser(u);
      } catch (error) {
        console.error(error);
      }
    }
    loadCurrentUser();
  }, [setUser]);

  useEffect(() => {
    async function loadCollaborators() {
      try {
        const data = await getCollaborators();
        setCollaborators(data.map((u: { id: number }) => u.id));
      } catch (error) {
        console.error(error);
      }
    }
    loadCollaborators();
  }, []);

  useEffect(() => {
    if (isConnected && socket && socket.readyState === WebSocket.OPEN && queue.length > 0) {
      const pendingForThisRoom = queue.filter(q => q.room_id === roomId);
      for (const msg of pendingForThisRoom) {
        try {
          socket.send(
            JSON.stringify({
              type: "chat_message",
              message: msg.content,
              desk_id: msg.desk_id,
              temp_id: msg.temp_id,
              extra_data: msg.extra_data || {},
            })
          );
          incrementRetry(msg.temp_id);
        } catch (error) {
          console.error("Failed to flush queued message", error);
        }
      }
    }
  }, [isConnected, socket, queue, roomId, incrementRetry]);

  useEffect(() => {
    async function loadMembers() {
      try {
        const data = await getRoomMembers(roomId);
        setMembers(data);
        const me = data.find((m: { username: string; role: string }) => m.username === user?.username);
        if (me) {
          setCurrentUserRole(me.role);
        }
      } catch (error) {
        console.error(error);
      }
    }
    if (roomId && user?.username) {
      loadMembers();
    }
  }, [roomId, user?.username]);

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
        if (event.code === 1008) {
          setConnectionStatus("Unauthorized");
          return;
        }
        if (reconnectAttemptsRef.current >= maxReconnects) {
          setConnectionStatus("Connection Failed");
          return;
        }
        reconnectAttemptsRef.current++;
        setConnectionStatus("Disconnected");
        reconnectTimeout = setTimeout(connectSocket, 3000);
      };

      ws.onmessage = (event) => {
        const payload = JSON.parse(event.data);

        if (payload.type.startsWith("webrtc") || payload.type === "join_call" || payload.type === "leave_call") {
          handleSignalingDataRef.current(payload);
        } else if (payload.type === "task_created" || payload.type === "task_updated") {
          window.dispatchEvent(new CustomEvent("task_update", { detail: payload }));
        } else if (payload.type === "chat_message") {
          addMessage(payload.data);
          if (payload.data.temp_id) {
            removeMessage(payload.data.temp_id);
          }
        }

        if (payload.type === "online_users") {
          setOnlineUsers(payload.data.users);
        }

        if (payload.type === "typing") {
          setTypingUser(payload.data.username);
          setTimeout(() => setTypingUser(""), 1500);
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
  }, [roomId]);

  function sendTypingEvent() {
    const ws = socketRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    ws.send(JSON.stringify({ type: "typing" }));
  }

  if (loading || !room) {
    return (
      <div className="min-h-screen bg-background text-foreground flex items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-73px)] bg-background text-foreground">
      <div className="grid min-h-[calc(100vh-73px)] grid-cols-1 lg:grid-cols-[260px_minmax(0,1fr)_320px]">
        <RoomSidebar
          room={room}
          members={members}
          aiEnabled={aiEnabled}
          onTasksOpen={() => {
            setIsTasksOpen(true);
            setAiPanelOpen(false);
          }}
          onAiPanelOpen={() => {
            setAiPanelOpen(true);
            setIsTasksOpen(false);
          }}
        />

        <main className="flex min-h-[calc(100vh-73px)] min-w-0 flex-col">
          <RoomHeader
            room={room}
            roomId={roomId}
            membersCount={members.length}
            messagesCount={messages.length}
            connectionStatus={connectionStatus}
            aiPanelOpen={aiPanelOpen}
            setAiPanelOpen={setAiPanelOpen}
            isTasksOpen={isTasksOpen}
            setIsTasksOpen={setIsTasksOpen}
            currentUserRole={currentUserRole}
            aiEnabled={aiEnabled}
            setAiEnabled={setAiEnabled}
            inCall={inCall}
            startCall={startCall}
            leaveCall={leaveCall}
          />

          {inCall && (
            <div className="border-b border-border bg-muted/30 p-4">
              <VideoGrid
                localStream={localStream}
                remoteStreams={remoteStreams}
                onLeaveCall={leaveCall}
                currentUser={user?.username || "You"}
              />
            </div>
          )}

          <ChatArea
            roomId={roomId}
            messages={messages.filter(m => m.desk_id === activeDeskId || (!m.desk_id))}
            activeDeskId={activeDeskId}
            currentUsername={user?.username || null}
            typingUser={typingUser}
            sendTypingEvent={sendTypingEvent}
            aiEnabled={aiEnabled}
            parseWithAI={parseWithAI}
            setParseWithAI={setParseWithAI}
          />
        </main>

        <RoomRightSidebar
          roomId={roomId}
          members={members}
          onlineUsers={onlineUsers}
          currentUserRole={currentUserRole}
          currentUsername={user?.username || null}
          collaborators={collaborators}
          setMembers={setMembers}
        />
      </div>

      <div className="fixed bottom-20 right-4 z-30 flex flex-col gap-2 xl:hidden">
        <button
          onClick={() => {
            setAiPanelOpen(true);
            setIsTasksOpen(false);
          }}
          className="h-11 w-11 rounded-lg border border-border bg-background shadow-lg flex items-center justify-center"
          title="Automatic memory"
        >
          <Sparkles size={18} />
        </button>
        <button
          onClick={() => {
            setIsTasksOpen(true);
            setAiPanelOpen(false);
          }}
          className="h-11 w-11 rounded-lg border border-border bg-background shadow-lg flex items-center justify-center"
          title="Tasks"
        >
          <CheckCircle2 size={18} />
        </button>
        <button
          onClick={inCall ? leaveCall : startCall}
          className="h-11 w-11 rounded-lg border border-border bg-background shadow-lg flex items-center justify-center"
          title={inCall ? "Leave call" : "Join call"}
        >
          {inCall ? <PhoneOff size={18} /> : <Video size={18} />}
        </button>
      </div>

      <AIAssistantPanel
        roomId={roomId}
        isOpen={aiPanelOpen}
        onToggle={() => setAiPanelOpen(false)}
      />

      <div
        className={`fixed inset-y-0 right-0 z-40 flex w-[95vw] max-w-6xl flex-col border-l border-border bg-background/95 backdrop-blur-xl transition-transform duration-300 ease-in-out ${
          isTasksOpen ? "translate-x-0 shadow-2xl" : "translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between border-b border-border px-5 py-4">
          <div>
            <h2 className="font-semibold">Task board</h2>
            <p className="text-xs text-muted-foreground">
              Shared channel work, ready to drag and organize.
            </p>
          </div>
          <button
            onClick={() => setIsTasksOpen(false)}
            className="h-9 w-9 rounded-md border border-border bg-background hover:bg-muted flex items-center justify-center"
            title="Close task board"
          >
            <X size={18} />
          </button>
        </div>

        <div className="min-h-0 flex-1 overflow-hidden">
          <KanbanBoard roomId={roomId} currentUsername={user?.username || ""} />
        </div>
      </div>
    </div>
  );
}
