import {
  AtSign,
  Shield,
  X,
  Users,
} from "lucide-react";
import axios from "axios";
import { promoteMember, demoteMember, removeMember } from "@/lib/api/rooms";
import { sendCollaborationRequest } from "@/lib/api/collaborators";
import { toast } from "sonner";
import { RoomMember } from "@/lib/store/roomStore";

export default function RoomRightSidebar({
  roomId,
  members,
  onlineUsers,
  currentUserRole,
  currentUsername,
  collaborators,
  setMembers,
}: {
  roomId: number;
  members: RoomMember[];
  onlineUsers: string[];
  currentUserRole: string | null;
  currentUsername: string | null;
  collaborators: number[];
  setMembers: (m: RoomMember[]) => void;
}) {
  function getErrorMessage(error: unknown, fallback: string) {
    if (axios.isAxiosError(error) && typeof error.response?.data?.detail === "string") {
      return error.response.data.detail;
    }
    return fallback;
  }

  async function handlePromote(userId: number) {
    try {
      await promoteMember(roomId, userId);
      toast.success("Member promoted");
      // Need a way to fetch members again, pass a callback or just optimistic update?
      // For now we will rely on setMembers being passed down.
    } catch (error) {
      toast.error(getErrorMessage(error, "Promotion failed"));
    }
  }

  async function handleDemote(userId: number) {
    try {
      await demoteMember(roomId, userId);
      toast.success("Member demoted");
    } catch (error) {
      toast.error(getErrorMessage(error, "Demotion failed"));
    }
  }

  async function handleRemove(userId: number) {
    try {
      await removeMember(roomId, userId);
      toast.success("Member removed");
    } catch (error) {
      toast.error(getErrorMessage(error, "Removal failed"));
    }
  }

  async function handleCollaborate(userId: number) {
    try {
      await sendCollaborationRequest(userId);
      toast.success("Collaboration request sent");
    } catch (error) {
      toast.error(getErrorMessage(error, "Failed to send request"));
    }
  }

  return (
    <aside className="hidden w-80 flex-col border-l border-border bg-background lg:flex">
      <div className="flex h-[57px] items-center border-b border-border px-4">
        <h3 className="font-semibold flex items-center gap-2">
          <Users size={16} />
          Members — {members.length}
        </h3>
      </div>
      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-4">
          {members.map((member) => {
            const isOnline = onlineUsers.includes(member.username);
            const isMe = member.username === currentUsername;
            const canManage = currentUserRole === "owner" && !isMe;
            const isCollab = collaborators.includes(member.user_id);

            return (
              <div key={member.user_id} className="group relative flex flex-col gap-2 rounded-lg border border-border bg-muted/30 p-3 transition hover:bg-muted">
                <div className="flex items-center gap-3">
                  <div className="relative">
                    <div className="h-10 w-10 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-semibold">
                      {(member.username || "U")[0].toUpperCase()}
                    </div>
                    <span
                      className={`absolute bottom-0 right-0 h-3 w-3 rounded-full border-2 border-background ${
                        isOnline ? "bg-emerald-500" : "bg-gray-400"
                      }`}
                    />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium truncate">{member.username}</span>
                      {isMe && (
                        <span className="rounded-md bg-muted px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground">
                          YOU
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-muted-foreground flex items-center gap-1 capitalize">
                      {member.role === "owner" ? (
                        <Shield size={10} className="text-indigo-400" />
                      ) : (
                        <AtSign size={10} />
                      )}
                      {member.role}
                    </div>
                  </div>
                </div>

                {canManage && (
                  <div className="mt-1 flex gap-2 border-t border-border pt-2 opacity-0 transition-opacity group-hover:opacity-100">
                    {member.role !== "owner" ? (
                      <button
                        onClick={() => handlePromote(member.user_id)}
                        className="flex-1 rounded border border-border bg-background px-2 py-1 text-xs hover:bg-muted"
                      >
                        Promote
                      </button>
                    ) : (
                      <button
                        onClick={() => handleDemote(member.user_id)}
                        className="flex-1 rounded border border-border bg-background px-2 py-1 text-xs hover:bg-muted"
                      >
                        Demote
                      </button>
                    )}
                    <button
                      onClick={() => handleRemove(member.user_id)}
                      className="flex items-center justify-center rounded border border-red-500/20 bg-red-500/10 px-2 py-1 text-red-500 hover:bg-red-500/20"
                      title="Remove from room"
                    >
                      <X size={14} />
                    </button>
                  </div>
                )}
                {!isMe && !isCollab && (
                  <div className="mt-1 opacity-0 transition-opacity group-hover:opacity-100">
                    <button
                      onClick={() => handleCollaborate(member.user_id)}
                      className="w-full rounded border border-border bg-background px-2 py-1.5 text-xs font-medium hover:bg-muted"
                    >
                      Send Collab Request
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </aside>
  );
}
