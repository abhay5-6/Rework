import { useState, useEffect } from "react";
import { toast } from "sonner";
import {
  approveJoinRequest,
  getJoinRequests,
  rejectJoinRequest,
} from "@/lib/api/notifications";
import {
  acceptCollaborationRequest,
  getCollaborationRequests,
  rejectCollaborationRequest,
} from "@/lib/api/collaborators";

export type JoinRequest = {
  request_id: number;
  workspace_id: number;
  workspace_name: string;
  user_id: number;
  username: string;
};

export type CollaborationRequest = {
  request_id: number;
  sender_id: number;
  username: string;
};

export function useNotifications() {
  const [workspaceRequests, setWorkspaceRequests] = useState<JoinRequest[]>([]);
  const [collaborationRequests, setCollaborationRequests] = useState<CollaborationRequest[]>([]);
  const [loading, setLoading] = useState(true);

  async function fetchNotifications() {
    try {
      const workspaceData = await getJoinRequests();
      setWorkspaceRequests(workspaceData);

      const collaborationData = await getCollaborationRequests();
      setCollaborationRequests(collaborationData);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    queueMicrotask(() => {
      void fetchNotifications();
    });
  }, []);

  async function handleApproveWorkspace(requestId: number) {
    try {
      await approveJoinRequest(requestId);
      setWorkspaceRequests((prev) => prev.filter((r) => r.request_id !== requestId));
      toast.success("Request approved");
    } catch (error) {
      console.error(error);
      toast.error("Failed to approve request");
    }
  }

  async function handleRejectWorkspace(requestId: number) {
    try {
      await rejectJoinRequest(requestId);
      setWorkspaceRequests((prev) => prev.filter((r) => r.request_id !== requestId));
      toast.success("Request rejected");
    } catch (error) {
      console.error(error);
      toast.error("Failed to reject request");
    }
  }

  async function handleAcceptCollaboration(requestId: number) {
    try {
      await acceptCollaborationRequest(requestId);
      setCollaborationRequests((prev) => prev.filter((r) => r.request_id !== requestId));
      toast.success("Collaboration accepted");
    } catch (error) {
      console.error(error);
      toast.error("Failed to accept collaboration");
    }
  }

  async function handleRejectCollaboration(requestId: number) {
    try {
      await rejectCollaborationRequest(requestId);
      setCollaborationRequests((prev) => prev.filter((r) => r.request_id !== requestId));
      toast.success("Collaboration rejected");
    } catch (error) {
      console.error(error);
      toast.error("Failed to reject collaboration");
    }
  }

  const totalNotifications = workspaceRequests.length + collaborationRequests.length;

  return {
    workspaceRequests,
    collaborationRequests,
    totalNotifications,
    loading,
    handleApproveWorkspace,
    handleRejectWorkspace,
    handleAcceptCollaboration,
    handleRejectCollaboration,
    refreshNotifications: fetchNotifications
  };
}
