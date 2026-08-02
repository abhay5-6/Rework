"use client";

import {
  useEffect,
  useState
} from "react";

import {
  Bell
} from "lucide-react";

import {
  toast
} from "sonner";

import {

  approveJoinRequest,

  getJoinRequests,

  rejectJoinRequest

} from "@/lib/api/notifications";

import {

  acceptCollaborationRequest,

  getCollaborationRequests,

  rejectCollaborationRequest

} from "@/lib/api/collaborators";


type JoinRequest = {

  request_id: number;

  room_id: number;

  room_name: string;

  user_id: number;

  username: string;
};


type CollaborationRequest = {

  request_id: number;

  sender_id: number;

  username: string;
};


export default function NotificationBell() {

  const [open, setOpen] =
    useState(false);

  const [

    roomRequests,

    setRoomRequests

  ] = useState<JoinRequest[]>([]);

  const [

    collaborationRequests,

    setCollaborationRequests

  ] = useState<
    CollaborationRequest[]
  >([]);


  async function fetchNotifications() {

    try {

      const roomData =
        await getJoinRequests();

      setRoomRequests(
        roomData
      );

      const collaborationData =
        await getCollaborationRequests();

      setCollaborationRequests(
        collaborationData
      );

    } catch (error) {

      console.error(error);
    }
  }


  useEffect(() => {

    queueMicrotask(() => {
      void fetchNotifications();
    });

  }, []);


  async function handleApproveRoom(
    requestId: number
  ) {

    try {

      await approveJoinRequest(
        requestId
      );

      setRoomRequests(
        (prev) =>
          prev.filter(
            (request) =>
              request.request_id !==
              requestId
          )
      );

      toast.success(
        "Request approved"
      );

    } catch (error) {

      console.error(error);

      toast.error(
        "Failed to approve request"
      );
    }
  }


  async function handleRejectRoom(
    requestId: number
  ) {

    try {

      await rejectJoinRequest(
        requestId
      );

      setRoomRequests(
        (prev) =>
          prev.filter(
            (request) =>
              request.request_id !==
              requestId
          )
      );

      toast.success(
        "Request rejected"
      );

    } catch (error) {

      console.error(error);

      toast.error(
        "Failed to reject request"
      );
    }
  }


  async function handleAcceptCollaboration(
    requestId: number
  ) {

    try {

      await acceptCollaborationRequest(
        requestId
      );

      setCollaborationRequests(
        (prev) =>
          prev.filter(
            (request) =>
              request.request_id !==
              requestId
          )
      );

      toast.success(
        "Collaboration accepted"
      );

    } catch (error) {

      console.error(error);

      toast.error(
        "Failed to accept collaboration"
      );
    }
  }


  async function handleRejectCollaboration(
    requestId: number
  ) {

    try {

      await rejectCollaborationRequest(
        requestId
      );

      setCollaborationRequests(
        (prev) =>
          prev.filter(
            (request) =>
              request.request_id !==
              requestId
          )
      );

      toast.success(
        "Collaboration rejected"
      );

    } catch (error) {

      console.error(error);

      toast.error(
        "Failed to reject collaboration"
      );
    }
  }


  const totalNotifications =

    roomRequests.length
    +
    collaborationRequests.length;


  return (

    <div className="relative">

      <button
        onClick={() =>
          setOpen(!open)
        }

        className="relative p-2 rounded-lg hover:bg-[rgba(88,101,242,0.16)] transition"
      >

        <Bell size={22} />

        {totalNotifications > 0 && (

          <span className="absolute -top-1 -right-1 bg-red-600 text-foreground text-xs font-bold min-w-[20px] h-5 px-1 flex items-center justify-center rounded-full">

            {totalNotifications}

          </span>
        )}

      </button>

      {open && (

        <div className="absolute right-0 mt-3 w-96 bg-background/80 backdrop-blur-xl border border-[rgba(88,101,242,0.35)] rounded-2xl shadow-2xl z-50 overflow-hidden">

          <div className="p-4 border-b border-border font-semibold text-lg">

            Notifications

          </div>

          {totalNotifications === 0 ? (

            <div className="p-6 text-muted-foreground text-center">

              No notifications

            </div>

          ) : (

            <div className="max-h-[500px] overflow-y-auto">

              {/* ROOM REQUESTS */}

              {roomRequests.length > 0 && (

                <div className="border-b border-border">

                  <div className="px-4 py-3 text-sm font-semibold text-muted-foreground uppercase">

                    Room Requests

                  </div>

                  {roomRequests.map(
                    (request) => (

                      <div
                        key={
                          request.request_id
                        }

                        className="p-4 border-t border-border"
                      >

                        <div className="mb-3 text-sm text-foreground leading-relaxed">

                          <span className="font-semibold text-foreground">

                            {
                              request.username
                            }

                          </span>{" "}

                          requested access to{" "}

                          <span className="font-semibold text-foreground">

                            {
                              request.room_name
                            }

                          </span>

                        </div>

                        <div className="flex gap-2">

                          <button
                            onClick={() =>
                              handleApproveRoom(
                                request.request_id
                              )
                            }

                            className="flex-1 bg-green-600 hover:bg-green-700 transition rounded-lg py-2 font-semibold"
                          >

                            Approve

                          </button>

                          <button
                            onClick={() =>
                              handleRejectRoom(
                                request.request_id
                              )
                            }

                            className="flex-1 bg-red-600 hover:bg-red-700 transition rounded-lg py-2 font-semibold"
                          >

                            Reject

                          </button>

                        </div>

                      </div>
                    )
                  )}

                </div>
              )}

              {/* COLLABORATION REQUESTS */}

              {collaborationRequests.length > 0 && (

                <div>

                  <div className="px-4 py-3 text-sm font-semibold text-muted-foreground uppercase">

                    Collaboration Requests

                  </div>

                  {collaborationRequests.map(
                    (request) => (

                      <div
                        key={
                          request.request_id
                        }

                        className="p-4 border-t border-border"
                      >

                        <div className="mb-3 text-sm text-foreground leading-relaxed">

                          <span className="font-semibold text-foreground">

                            {
                              request.username
                            }

                          </span>{" "}

                          wants to collaborate with you

                        </div>

                        <div className="flex gap-2">

                          <button
                            onClick={() =>
                              handleAcceptCollaboration(
                                request.request_id
                              )
                            }

                            className="flex-1 bg-green-600 hover:bg-green-700 transition rounded-lg py-2 font-semibold"
                          >

                            Accept

                          </button>

                          <button
                            onClick={() =>
                              handleRejectCollaboration(
                                request.request_id
                              )
                            }

                            className="flex-1 bg-red-600 hover:bg-red-700 transition rounded-lg py-2 font-semibold"
                          >

                            Reject

                          </button>

                        </div>

                      </div>
                    )
                  )}

                </div>
              )}

            </div>
          )}

        </div>
      )}

    </div>
  );
}
