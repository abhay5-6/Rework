import { useState, useEffect } from "react";
import { X, Shield, ShieldAlert, User as UserIcon } from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api/client";
import { Workspace, WorkspaceMember } from "@/lib/store/workspaceStore";

export default function WorkspaceSettingsModal({
  workspace,
  onClose,
}: {
  workspace: Workspace;
  onClose: () => void;
}) {
  const [members, setMembers] = useState<WorkspaceMember[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMembers();
  }, [workspace.id]);

  async function fetchMembers() {
    try {
      setLoading(true);
      const res = await api.get(`/workspaces/${workspace.id}/members`);
      setMembers(res.data);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Failed to fetch members");
    } finally {
      setLoading(false);
    }
  }

  async function handleRoleChange(userId: number, newRole: string) {
    try {
      await api.patch(`/workspaces/${workspace.id}/members/${userId}`, { role: newRole });
      toast.success("Role updated successfully");
      fetchMembers();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Failed to update role");
    }
  }

  async function handleRemoveMember(userId: number) {
    if (!confirm("Are you sure you want to remove this member?")) return;
    try {
      await api.delete(`/workspaces/${workspace.id}/remove/${userId}`); // Wait, it's /members/{user_id} now in my new endpoint!
      toast.success("Member removed");
      fetchMembers();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Failed to remove member");
    }
  }

  // Fixing the endpoint above to match the new one I created
  async function handleRemoveMemberCorrected(userId: number) {
    if (!confirm("Are you sure you want to remove this member?")) return;
    try {
      await api.delete(`/workspaces/${workspace.id}/members/${userId}`);
      toast.success("Member removed");
      fetchMembers();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Failed to remove member");
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-xl rounded-lg border border-border bg-background shadow-xl">
        <div className="flex items-center justify-between border-b border-border p-4">
          <h2 className="text-lg font-semibold">Workspace Settings: {workspace.name}</h2>
          <button onClick={onClose} className="rounded p-1 hover:bg-muted text-muted-foreground transition">
            <X size={18} />
          </button>
        </div>
        
        <div className="p-4 max-h-[60vh] overflow-y-auto">
          <h3 className="mb-3 text-sm font-medium">Members</h3>
          {loading ? (
            <div className="text-sm text-muted-foreground">Loading...</div>
          ) : (
            <div className="space-y-3">
              {members.map((member) => (
                <div key={member.user_id} className="flex items-center justify-between rounded-md border border-border p-3">
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-primary">
                      <UserIcon size={16} />
                    </div>
                    <div>
                      <div className="text-sm font-medium">{member.username}</div>
                      <div className="text-xs text-muted-foreground flex items-center gap-1">
                        {member.role === 'owner' && <ShieldAlert size={12} className="text-destructive" />}
                        {member.role === 'admin' && <Shield size={12} className="text-primary" />}
                        {member.role}
                      </div>
                    </div>
                  </div>
                  
                  {workspace.role === "owner" || workspace.role === "admin" ? (
                    <div className="flex items-center gap-2">
                      <select
                        value={member.role}
                        onChange={(e) => handleRoleChange(member.user_id, e.target.value)}
                        disabled={member.role === "owner"}
                        className="rounded border border-border bg-background px-2 py-1 text-xs"
                      >
                        <option value="owner" disabled>Owner</option>
                        <option value="admin">Admin</option>
                        <option value="contributor">Contributor</option>
                        <option value="viewer">Viewer</option>
                      </select>
                      
                      {member.role !== "owner" && (
                        <button
                          onClick={() => handleRemoveMemberCorrected(member.user_id)}
                          className="rounded px-2 py-1 text-xs text-destructive hover:bg-destructive/10 transition"
                        >
                          Remove
                        </button>
                      )}
                    </div>
                  ) : (
                    <div className="text-xs text-muted-foreground uppercase">{member.role}</div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
