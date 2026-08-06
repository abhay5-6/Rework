"use client";

import { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { toast } from "sonner";
import axios from "axios";
import { Video, PhoneOff, CheckCircle2, Sparkles, X } from "lucide-react";

import WorkspaceSidebar from "./components/WorkspaceSidebar";
import WorkspaceHeader from "./components/WorkspaceHeader";
import WorkspaceRightSidebar from "./components/WorkspaceRightSidebar";
import ChatArea from "./components/ChatArea";
import AIAssistantPanel from "@/components/ai/AIAssistantPanel";
import LoadingSpinner from "@/components/LoadingSpinner";
import KanbanBoard from "@/components/tasks/KanbanBoard";
import VideoGrid from "@/components/video/VideoGrid";
import WorkspaceSettingsModal from "@/components/modals/WorkspaceSettingsModal";
import ChannelSettingsModal from "@/components/modals/ChannelSettingsModal";

import { useWebRTC } from "@/hooks/useWebRTC";
import { useWorkspaceSocket } from "@/hooks/useWorkspaceSocket";
import { isAuthenticated } from "@/lib/auth";
import { getMe } from "@/lib/api/auth";
import { getRoom, getWorkspaceMembers } from "@/lib/api/workspaces";
import { getWorkspaceChannels } from "@/lib/api/channels";
import { getCollaborators } from "@/lib/api/collaborators";
import { getMessages } from "@/lib/api/messages";

import { useAuthStore } from "@/lib/store/authStore";
import { useWorkspaceStore } from "@/lib/store/workspaceStore";
import { useSocketStore } from "@/lib/store/socketStore";
import { useQueueStore } from "@/lib/store/queueStore";

export default function RoomPage() {
  const params = useParams();
  const router = useRouter();
  const roomId = Number(params.id);

  // Stores
  const { user, setUser } = useAuthStore();
  const { workspace, setRoom, messages, setMessages, channels, setDesks, activeDeskId, setActiveDeskId } = useWorkspaceStore();
  const { socket, isConnected } = useSocketStore();
  const { queue } = useQueueStore();

  // Local state
  const [loading, setLoading] = useState(true);
  const [members, setMembers] = useState<{ user_id: number; username: string; role?: string }[]>([]);
  const [currentUserRole, setCurrentUserRole] = useState<string | null>(null);
  const [collaborators, setCollaborators] = useState<number[]>([]);

  const [aiEnabled, setAiEnabled] = useState(true);
  const [isTasksOpen, setIsTasksOpen] = useState(false);
  const [aiPanelOpen, setAiPanelOpen] = useState(false);
  const [parseWithAI, setParseWithAI] = useState(true);
  const [workspaceSettingsOpen, setWorkspaceSettingsOpen] = useState(false);
  const [channelSettingsDeskId, setChannelSettingsDeskId] = useState<number | null>(null);

  const socketRef = useRef<WebSocket | null>(null);

  // WebRTC
  const {
    localStream,
    remoteStreams,
    inCall,
    startCall,
    leaveCall,
    handleSignalingData,
  } = useWebRTC(roomId, user?.username || "", socketRef);

  // WebSocket
  const {
    connectionStatus,
    onlineUsers,
    typingUser,
    sendTypingEvent
  } = useWorkspaceSocket(roomId, handleSignalingData, socketRef);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/login");
    }

    const handleOpenWorkspaceSettings = () => setWorkspaceSettingsOpen(true);
    const handleOpenChannelSettings = (e: Event) => {
      const customEvent = e as CustomEvent<{ deskId: number }>;
      setChannelSettingsDeskId(customEvent.detail.deskId);
    };


    document.addEventListener('open-workspace-settings', handleOpenWorkspaceSettings);
    document.addEventListener('open-channel-settings', handleOpenChannelSettings);

    return () => {
      document.removeEventListener('open-workspace-settings', handleOpenWorkspaceSettings);
      document.removeEventListener('open-channel-settings', handleOpenChannelSettings);
    };
  }, [router]);

  useEffect(() => {
    async function loadMessages() {
      try {
        const data = await getMessages(roomId);
        setMessages(data);
      } catch (error) {
        if (axios.isAxiosError(error) && error.response?.status === 403) {
          toast.error("You do not have access to this workspace");
          router.push("/workspaces");
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

      getWorkspaceChannels(roomId)
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

  const hasFlushedRef = useRef(false);

  useEffect(() => {
    if (isConnected && socket && socket.readyState === WebSocket.OPEN && queue.length > 0) {
      if (hasFlushedRef.current) return;
      
      const pendingForThisRoom = queue.filter(q => q.workspace_id === roomId);
      for (const msg of pendingForThisRoom) {
        try {
          socket.send(
            JSON.stringify({
              type: "chat_message",
              message: msg.content,
              channel_id: msg.channel_id,
              temp_id: msg.temp_id,
              extra_data: msg.extra_data || {},
            })
          );
        } catch (error) {
          console.error("Failed to flush queued message", error);
        }
      }
      hasFlushedRef.current = true;
    } else if (!isConnected) {
      hasFlushedRef.current = false;
    }
  }, [isConnected, socket, queue, roomId]);

  useEffect(() => {
    async function loadMembers() {
      try {
        const data = await getWorkspaceMembers(roomId);
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

  if (loading || !workspace) {
    return (
      <div className="min-h-screen bg-background text-foreground flex items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-73px)] bg-background text-foreground">
      <div className="grid min-h-[calc(100vh-73px)] grid-cols-1 lg:grid-cols-[260px_minmax(0,1fr)_320px]">
        <WorkspaceSidebar
          workspace={workspace}
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
          <WorkspaceHeader
            workspace={workspace}
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
            messages={messages.filter(m => m.channel_id === activeDeskId || (!m.channel_id))}
            activeDeskId={activeDeskId}
            currentUsername={user?.username || null}
            typingUser={typingUser}
            sendTypingEvent={sendTypingEvent}
            aiEnabled={aiEnabled}
            parseWithAI={parseWithAI}
            setParseWithAI={setParseWithAI}
          />
        </main>

        <WorkspaceRightSidebar
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

      {workspaceSettingsOpen && workspace && (
        <WorkspaceSettingsModal
          workspace={workspace}
          onClose={() => setWorkspaceSettingsOpen(false)}
        />
      )}

      {channelSettingsDeskId && channels.find(c => c.id === channelSettingsDeskId) && (
        <ChannelSettingsModal
          channel={channels.find(c => c.id === channelSettingsDeskId)!}
          workspaceId={roomId}
          onClose={() => setChannelSettingsDeskId(null)}
        />
      )}
    </div>
  );
}
