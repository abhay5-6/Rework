import { useState } from "react";
import Link from "next/link";
import { Network, Lock, Hash, Search, Bot, Plus, X, CheckCircle2, Sparkles, PanelRightOpen } from "lucide-react";
import { useRoomStore, Room } from "@/lib/store/roomStore";
import { createDesk } from "@/lib/api/desks";
import { toast } from "sonner";

const defaultTools = [
  { id: "decisions", label: "decisions", icon: CheckCircle2 },
  { id: "memory", label: "memory", icon: Sparkles },
  { id: "tasks", label: "tasks", icon: PanelRightOpen },
];

export default function RoomSidebar({
  room,
  members,
  aiEnabled,
  onTasksOpen,
  onAiPanelOpen,
}: {
  room: Room;
  members: { user_id: number; username: string; role?: string }[];
  aiEnabled: boolean;
  onTasksOpen: () => void;
  onAiPanelOpen: () => void;
}) {
  const { desks, setDesks, activeDeskId, setActiveDeskId } = useRoomStore();
  const [isCreatingChannel, setIsCreatingChannel] = useState(false);
  const [newChannelName, setNewChannelName] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleCreateChannel(e: React.FormEvent) {
    e.preventDefault();
    if (!newChannelName.trim()) return;

    try {
      setLoading(true);
      const createdDesk = await createDesk(newChannelName.trim(), room.id);
      setDesks([...desks, createdDesk]);
      setActiveDeskId(createdDesk.id);
      setNewChannelName("");
      setIsCreatingChannel(false);
      toast.success(`Channel #${createdDesk.name} created`);
    } catch (error) {
      console.error(error);
      toast.error("Failed to create channel");
    } finally {
      setLoading(false);
    }
  }

  return (
    <aside className="hidden lg:flex border-r border-border bg-muted/30 flex-col">
      <div className="p-4 border-b border-border">
        <Link
          href="/rooms"
          className="text-xs text-muted-foreground hover:text-foreground"
        >
          Back to rooms
        </Link>

        <div className="mt-4 flex items-center gap-3">
          <div className="h-11 w-11 rounded-lg bg-primary text-primary-foreground flex items-center justify-center">
            <Network size={20} />
          </div>
          <div className="min-w-0">
            <h1 className="font-semibold truncate">{room.name}</h1>
            <div className="text-xs text-muted-foreground flex items-center gap-1.5">
              {room.is_private ? <Lock size={12} /> : <Hash size={12} />}
              {room.is_private ? "Private workspace" : "Public workspace"}
            </div>
          </div>
        </div>
      </div>

      <div className="p-3 border-b border-border">
        <div className="flex items-center gap-2 rounded-lg border border-border bg-background px-3 py-2 text-sm text-muted-foreground">
          <Search size={15} />
          Search workspace
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-3">
        <div className="flex items-center justify-between px-2 pb-2 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
          <span>Channels</span>
          <button
            onClick={() => setIsCreatingChannel(!isCreatingChannel)}
            className="rounded p-0.5 hover:bg-background hover:text-foreground transition"
            title="Create Channel"
          >
            {isCreatingChannel ? <X size={14} /> : <Plus size={14} />}
          </button>
        </div>

        {isCreatingChannel && (
          <form onSubmit={handleCreateChannel} className="mb-2 px-1">
            <div className="flex items-center gap-1 rounded-md border border-border bg-background p-1">
              <Hash size={14} className="text-muted-foreground ml-1" />
              <input
                type="text"
                value={newChannelName}
                onChange={(e) => setNewChannelName(e.target.value)}
                placeholder="channel-name"
                className="w-full bg-transparent text-xs outline-none"
                autoFocus
                disabled={loading}
              />
              <button
                type="submit"
                disabled={loading || !newChannelName.trim()}
                className="rounded bg-primary px-2 py-0.5 text-[10px] font-semibold text-primary-foreground disabled:opacity-50"
              >
                Add
              </button>
            </div>
          </form>
        )}

        <div className="space-y-1">
          {desks.map((desk) => {
            const active = desk.id === activeDeskId;

            return (
              <button
                key={desk.id}
                onClick={() => setActiveDeskId(desk.id)}
                className={`w-full flex items-center gap-2 rounded-md px-3 py-2 text-sm transition ${
                  active
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-background hover:text-foreground"
                }`}
              >
                <Hash size={16} />
                {desk.name}
              </button>
            );
          })}
        </div>

        <div className="mt-6 px-2 pb-2 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
          Tools
        </div>
        <div className="space-y-1">
          {defaultTools.map((tool) => {
            const Icon = tool.icon;
            return (
              <button
                key={tool.id}
                onClick={() => {
                  if (tool.id === "tasks") onTasksOpen();
                  if (tool.id === "memory") onAiPanelOpen();
                }}
                className={`w-full flex items-center gap-2 rounded-md px-3 py-2 text-sm transition text-muted-foreground hover:bg-background hover:text-foreground`}
              >
                <Icon size={16} />
                {tool.label}
              </button>
            );
          })}
        </div>

        <div className="mt-6 px-2 pb-2 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
          Direct collaborators
        </div>
        <div className="space-y-1">
          {members.slice(0, 6).map((member) => (
            <div
              key={member.user_id}
              className="flex items-center gap-2 rounded-md px-3 py-2 text-sm text-muted-foreground"
            >
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              <span className="truncate">{member.username}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="p-3 border-t border-border">
        <div className="rounded-lg bg-background border border-border p-3">
          <div className="flex items-center gap-2 text-sm font-medium">
            <Bot size={16} />
            Automatic memory
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            {aiEnabled
              ? "Rework is indexing useful room context."
              : "Memory capture is paused for this room."}
          </p>
        </div>
      </div>
    </aside>
  );
}
