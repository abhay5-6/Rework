import { useState, useEffect, useCallback } from "react";
import { X, UserPlus, Trash2 } from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api/client";
import { AxiosError } from "axios";
import { Channel } from "@/lib/api/channels";


interface ChannelMember {
  user_id: number;
  username: string;
  email: string;
  role: string;
}

interface WorkspaceMemberItem {
  user_id: number;
  username: string;
  role?: string;
}

export default function ChannelSettingsModal({
  channel,
  workspaceId,
  onClose,
}: {
  channel: { id: number; name: string; is_private: boolean };
  workspaceId: number;
  onClose: () => void;
}) {
  const [members, setMembers] = useState<ChannelMember[]>([]);
  const [workspaceMembers, setWorkspaceMembers] = useState<WorkspaceMemberItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedUserToAdd, setSelectedUserToAdd] = useState("");

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [membersRes, wsMembersRes] = await Promise.all([
        api.get(`/channels/${channel.id}/members`),
        api.get(`/workspaces/${workspaceId}/members`)
      ]);
      setMembers(membersRes.data);
      setWorkspaceMembers(wsMembersRes.data);
    } catch {
      toast.error("Failed to load channel data");
    } finally {
      setLoading(false);
    }
  }, [channel.id, workspaceId]);

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchData();
    }, 0);
    return () => clearTimeout(timer);
  }, [fetchData]);


  async function handleAddMember(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedUserToAdd) return;
    
    try {
      await api.post(`/channels/${channel.id}/members`, { user_id: parseInt(selectedUserToAdd) });
      toast.success("Member added to private channel");
      setSelectedUserToAdd("");
      fetchData();
    } catch (err: unknown) {
      if (err instanceof AxiosError && err.response?.data?.detail) {
        toast.error(err.response.data.detail);
      } else {
        toast.error("Failed to add member");
      }
    }
  }

  async function handleRemoveMember(userId: number) {
    if (!confirm("Are you sure you want to remove this member from the channel?")) return;
    try {
      await api.delete(`/channels/${channel.id}/members/${userId}`);
      toast.success("Member removed");
      fetchData();
    } catch (err: unknown) {
      if (err instanceof AxiosError && err.response?.data?.detail) {
        toast.error(err.response.data.detail);
      } else {
        toast.error("Failed to remove member");
      }
    }
  }

  // Filter workspace members that are not already in the channel
  const availableMembersToAdd = workspaceMembers.filter(
    wm => !members.some(cm => cm.user_id === wm.user_id)
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-xl rounded-lg border border-border bg-background shadow-xl">
        <div className="flex items-center justify-between border-b border-border p-4">
          <div>
            <h2 className="text-lg font-semibold">Channel Settings: #{channel.name}</h2>
            <p className="text-xs text-muted-foreground">Private Channel Members</p>
          </div>
          <button onClick={onClose} className="rounded p-1 hover:bg-muted text-muted-foreground transition">
            <X size={18} />
          </button>
        </div>
        
        <div className="p-4">
          <form onSubmit={handleAddMember} className="mb-6 flex gap-2">
            <select
              value={selectedUserToAdd}
              onChange={(e) => setSelectedUserToAdd(e.target.value)}
              className="flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm"
              disabled={loading || availableMembersToAdd.length === 0}
            >
              <option value="">Select a workspace member to add...</option>
              {availableMembersToAdd.map(m => (
                <option key={m.user_id} value={m.user_id}>{m.username}</option>
              ))}
            </select>
            <button
              type="submit"
              disabled={!selectedUserToAdd || loading}
              className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"
            >
              <UserPlus size={16} />
              Add
            </button>
          </form>

          <h3 className="mb-3 text-sm font-medium">Current Members</h3>
          {loading ? (
            <div className="text-sm text-muted-foreground">Loading...</div>
          ) : (
            <div className="space-y-2 max-h-[40vh] overflow-y-auto">
              {members.map((member) => (
                <div key={member.user_id} className="flex items-center justify-between rounded-md border border-border p-3">
                  <div>
                    <div className="text-sm font-medium">{member.username}</div>
                    <div className="text-xs text-muted-foreground uppercase">{member.role}</div>
                  </div>
                  
                  <button
                    onClick={() => handleRemoveMember(member.user_id)}
                    className="rounded p-2 text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition"
                    title="Remove from channel"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
              {members.length === 0 && (
                <div className="text-sm text-muted-foreground py-4 text-center">No members found.</div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
