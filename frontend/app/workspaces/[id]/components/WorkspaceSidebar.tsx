import { useState } from "react";
import Link from "next/link";
import { Network, Lock, Hash, Search, Bot, Plus, X, CheckCircle2, Sparkles, PanelRightOpen, Shield } from "lucide-react";
import { useWorkspaceStore, Workspace } from "@/lib/store/workspaceStore";
import { createChannel } from "@/lib/api/channels";
import { toast } from "sonner";

const defaultTools = [
  { id: "decisions", label: "decisions", icon: CheckCircle2 },
  { id: "memory", label: "memory", icon: Sparkles },
  { id: "tasks", label: "tasks", icon: PanelRightOpen },
];

export default function WorkspaceSidebar({
  workspace,
  members,
  aiEnabled,
  onTasksOpen,
  onAiPanelOpen,
}: {
  workspace: Workspace;
  members: { user_id: number; username: string; role?: string }[];
  aiEnabled: boolean;
  onTasksOpen: () => void;
  onAiPanelOpen: () => void;
}) {
  const { channels, setDesks, activeDeskId, setActiveDeskId } = useWorkspaceStore();
  const [isCreatingChannel, setIsCreatingChannel] = useState(false);
  const [newChannelName, setNewChannelName] = useState("");
  const [isPrivateChannel, setIsPrivateChannel] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleCreateChannel(e: React.FormEvent) {
    e.preventDefault();
    if (!newChannelName.trim()) return;

    try {
      setLoading(true);
      const createdChannel = await createChannel(newChannelName.trim(), workspace.id, isPrivateChannel);
      setDesks([...channels, createdChannel]);
      setActiveDeskId(createdChannel.id);
      setNewChannelName("");
      setIsPrivateChannel(false);
      setIsCreatingChannel(false);
      toast.success(`Channel #${createdChannel.name} created`);
    } catch (error: any) {
      console.error(error);
      toast.error(error.response?.data?.detail || "Failed to create channel");
    } finally {
      setLoading(false);
    }
  }

  return (
    <aside className="hidden lg:flex border-r border-border bg-muted/30 flex-col">
      <div className="p-4 border-b border-border">
        <Link
          href="/workspaces"
          className="text-xs text-muted-foreground hover:text-foreground"
        >
          Back to workspaces
        </Link>

        <div className="mt-4 flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="h-11 w-11 rounded-lg bg-primary text-primary-foreground flex items-center justify-center">
              <Network size={20} />
            </div>
            <div className="min-w-0">
              <h1 className="font-semibold truncate">{workspace.name}</h1>
              <div className="text-xs text-muted-foreground flex items-center gap-1.5">
                {workspace.is_private ? <Lock size={12} /> : <Hash size={12} />}
                {workspace.is_private ? "Private workspace" : "Public workspace"}
              </div>
            </div>
          </div>
          
          {(workspace.role === "owner" || workspace.role === "admin") && (
            <button 
              onClick={() => document.dispatchEvent(new CustomEvent('open-workspace-settings'))}
              className="text-muted-foreground hover:text-foreground p-1 transition"
              title="Workspace Settings"
            >
              <Shield size={14} />
            </button>
          )}
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
            <div className="flex flex-col gap-2 rounded-md border border-border bg-background p-2">
              <div className="flex items-center gap-1 border-b border-border pb-1">
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
              </div>
              <div className="flex items-center justify-between">
                <label 
                  className={`flex items-center gap-1.5 text-[10px] ${workspace.can_create_private_channel ? 'text-muted-foreground cursor-pointer' : 'text-muted-foreground/50 cursor-not-allowed'}`}
                  title={!workspace.can_create_private_channel ? "Organization restricts private channels to administrators only." : undefined}
                >
                  <input
                    type="checkbox"
                    checked={isPrivateChannel}
                    onChange={(e) => workspace.can_create_private_channel && setIsPrivateChannel(e.target.checked)}
                    disabled={!workspace.can_create_private_channel}
                    className="rounded border-border bg-background text-primary focus:ring-primary disabled:opacity-50"
                  />
                  <Lock size={10} />
                  Private Channel
                </label>
                <button
                  type="submit"
                  disabled={loading || !newChannelName.trim()}
                  className="rounded bg-primary px-3 py-1 text-[10px] font-semibold text-primary-foreground disabled:opacity-50"
                >
                  Create
                </button>
              </div>
            </div>
          </form>
        )}

        <div className="space-y-1">
          {channels.map((channel) => {
            const active = channel.id === activeDeskId;

            return (
              <div key={channel.id} className="group relative flex items-center">
                <button
                  onClick={() => setActiveDeskId(channel.id)}
                  className={`flex-1 flex items-center gap-2 rounded-md px-3 py-2 text-sm transition pr-8 ${
                    active
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:bg-background hover:text-foreground"
                  }`}
                >
                  {channel.is_private ? <Lock size={14} /> : <Hash size={16} />}
                  <span className="truncate">{channel.name}</span>
                </button>
                {channel.is_private && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      document.dispatchEvent(new CustomEvent('open-channel-settings', { detail: { deskId: channel.id } }));
                    }}
                    className={`absolute right-2 p-1 rounded-md opacity-0 group-hover:opacity-100 transition ${
                      active ? 'text-primary-foreground hover:bg-black/20' : 'text-muted-foreground hover:bg-muted'
                    }`}
                    title="Channel Settings"
                  >
                    <Shield size={14} />
                  </button>
                )}
              </div>
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
              ? "Rework is indexing useful workspace context."
              : "Memory capture is paused for this workspace."}
          </p>
        </div>
      </div>
    </aside>
  );
}
