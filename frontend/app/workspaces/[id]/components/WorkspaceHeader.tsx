import Link from "next/link";
import { Network, Hash, Users, MessageCircle, Wifi, CheckCircle2, Sparkles, PhoneOff, Phone, Bot } from "lucide-react";
import { Workspace } from "@/lib/store/workspaceStore";
import { toggleRoomAI } from "@/lib/api/workspaces";
import { toast } from "sonner";
import axios from "axios";

export default function WorkspaceHeader({
  workspace,
  roomId,
  membersCount,
  messagesCount,
  connectionStatus,
  aiPanelOpen,
  setAiPanelOpen,
  isTasksOpen,
  setIsTasksOpen,
  currentUserRole,
  aiEnabled,
  setAiEnabled,
  inCall,
  startCall,
  leaveCall,
}: {
  workspace: Workspace;
  roomId: number;
  membersCount: number;
  messagesCount: number;
  connectionStatus: string;
  aiPanelOpen: boolean;
  setAiPanelOpen: (val: boolean) => void;
  isTasksOpen: boolean;
  setIsTasksOpen: (val: boolean) => void;
  currentUserRole: string | null;
  aiEnabled: boolean;
  setAiEnabled: (val: boolean) => void;
  inCall: boolean;
  startCall: () => void;
  leaveCall: () => void;
}) {
  async function handleAIToggle() {
    const previousValue = aiEnabled;

    try {
      const newValue = !aiEnabled;
      setAiEnabled(newValue);
      await toggleRoomAI(roomId, newValue);
      toast.success(newValue ? "Automatic memory enabled" : "Automatic memory paused");
    } catch (error: unknown) {
      setAiEnabled(previousValue);
      const detail = axios.isAxiosError(error) ? error.response?.data?.detail : null;
      toast.error(typeof detail === "string" ? detail : "Failed to toggle AI setting");
    }
  }

  return (
    <header className="sticky top-[73px] z-20 border-b border-border bg-background/95 backdrop-blur-xl">
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 md:px-5">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <Hash size={19} className="text-muted-foreground" />
            <h2 className="truncate text-lg font-semibold">
              {workspace.name}
            </h2>
          </div>
          <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <Users size={13} />
              {membersCount} members
            </span>
            <span className="flex items-center gap-1">
              <MessageCircle size={13} />
              {messagesCount} messages
            </span>
            <span className="flex items-center gap-1">
              <Wifi
                size={13}
                className={
                  connectionStatus === "Connected"
                    ? "text-emerald-500"
                    : "text-red-500"
                }
              />
              {connectionStatus}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2 overflow-x-auto">
          <Link
            href={`/workspaces/${roomId}/graph`}
            className="h-10 w-10 rounded-lg border border-border bg-background hover:bg-muted flex items-center justify-center transition"
            title="Memory graph"
          >
            <Network size={17} />
          </Link>

          <button
            onClick={() => {
              setAiPanelOpen(!aiPanelOpen);
              setIsTasksOpen(false);
            }}
            className={`h-10 w-10 rounded-lg border border-border flex items-center justify-center transition ${
              aiPanelOpen
                ? "bg-primary text-primary-foreground"
                : "bg-background hover:bg-muted"
            }`}
            title="Workspace memory assistant"
          >
            <Sparkles size={17} />
          </button>

          <button
            onClick={() => {
              setIsTasksOpen(!isTasksOpen);
              setAiPanelOpen(false);
            }}
            className={`h-10 w-10 rounded-lg border border-border flex items-center justify-center transition ${
              isTasksOpen
                ? "bg-primary text-primary-foreground"
                : "bg-background hover:bg-muted"
            }`}
            title="Tasks"
          >
            <CheckCircle2 size={17} />
          </button>

          {currentUserRole === "owner" && (
            <button
              onClick={handleAIToggle}
              className={`h-10 w-10 rounded-lg border border-border flex items-center justify-center transition ${
                aiEnabled
                  ? "bg-emerald-600 text-white"
                  : "bg-background text-muted-foreground hover:bg-muted"
              }`}
              title={aiEnabled ? "Pause automatic memory" : "Enable automatic memory"}
            >
              <Bot size={17} />
            </button>
          )}

          {inCall ? (
            <button
              onClick={leaveCall}
              className="h-10 w-10 rounded-lg border border-red-500/30 bg-red-500/10 text-red-500 hover:bg-red-500/20 flex items-center justify-center transition"
              title="Leave call"
            >
              <PhoneOff size={17} />
            </button>
          ) : (
            <button
              onClick={startCall}
              className="h-10 w-10 rounded-lg border border-border bg-background hover:bg-muted flex items-center justify-center transition"
              title="Join call"
            >
              <Phone size={17} />
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
