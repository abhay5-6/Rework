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
  room_id: number;
  room_name: string;
  user_id: number;
  username: string;
};

export type CollaborationRequest = {
  request_id: number;
  sender_id: number;
  username: string;
};

export function useNotifications() {
  const [roomRequests, setRoomRequests] = useState<JoinRequest[]>([]);
  const [collaborationRequests, setCollaborationRequests] = useState<CollaborationRequest[]>([]);
  const [loading, setLoading] = useState(true);

  async function fetchNotifications() {
    try {
      const roomData = await getJoinRequests();
      setRoomRequests(roomData);

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

  async function handleApproveRoom(requestId: number) {
    try {
      await approveJoinRequest(requestId);
      setRoomRequests((prev) => prev.filter((r) => r.request_id !== requestId));
      toast.success("Request approved");
    } catch (error) {
      console.error(error);
      toast.error("Failed to approve request");
    }
  }

  async function handleRejectRoom(requestId: number) {
    try {
      await rejectJoinRequest(requestId);
      setRoomRequests((prev) => prev.filter((r) => r.request_id !== requestId));
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

  const totalNotifications = roomRequests.length + collaborationRequests.length;

  return {
    roomRequests,
    collaborationRequests,
    totalNotifications,
    loading,
    handleApproveRoom,
    handleRejectRoom,
    handleAcceptCollaboration,
    handleRejectCollaboration,
    refreshNotifications: fetchNotifications
  };
}
