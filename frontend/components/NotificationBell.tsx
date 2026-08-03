"use client";

import { useState } from "react";
import { Bell } from "lucide-react";
import { useNotifications } from "@/hooks/useNotifications";

export default function NotificationBell() {
  const [open, setOpen] = useState(false);
  const {
    workspaceRequests,
    collaborationRequests,
    totalNotifications,
    handleApproveWorkspace,
    handleRejectWorkspace,
    handleAcceptCollaboration,
    handleRejectCollaboration
  } = useNotifications();

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
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
              {/* WORKSPACE REQUESTS */}
              {workspaceRequests.length > 0 && (
                <div className="border-b border-border">
                  <div className="px-4 py-3 text-sm font-semibold text-muted-foreground uppercase">
                    Workspace Requests
                  </div>
                  {workspaceRequests.map((request) => (
                    <div
                      key={request.request_id}
                      className="p-4 border-t border-border"
                    >
                      <div className="mb-3 text-sm text-foreground leading-relaxed">
                        <span className="font-semibold text-foreground">
                          {request.username}
                        </span>{" "}
                        requested access to{" "}
                        <span className="font-semibold text-foreground">
                          {request.workspace_name}
                        </span>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleApproveWorkspace(request.request_id)}
                          className="flex-1 bg-green-600 hover:bg-green-700 transition rounded-lg py-2 font-semibold"
                        >
                          Approve
                        </button>
                        <button
                          onClick={() => handleRejectWorkspace(request.request_id)}
                          className="flex-1 bg-red-600 hover:bg-red-700 transition rounded-lg py-2 font-semibold"
                        >
                          Reject
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* COLLABORATION REQUESTS */}
              {collaborationRequests.length > 0 && (
                <div>
                  <div className="px-4 py-3 text-sm font-semibold text-muted-foreground uppercase">
                    Collaboration Requests
                  </div>
                  {collaborationRequests.map((request) => (
                    <div
                      key={request.request_id}
                      className="p-4 border-t border-border"
                    >
                      <div className="mb-3 text-sm text-foreground leading-relaxed">
                        <span className="font-semibold text-foreground">
                          {request.username}
                        </span>{" "}
                        wants to collaborate with you
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleAcceptCollaboration(request.request_id)}
                          className="flex-1 bg-green-600 hover:bg-green-700 transition rounded-lg py-2 font-semibold"
                        >
                          Accept
                        </button>
                        <button
                          onClick={() => handleRejectCollaboration(request.request_id)}
                          className="flex-1 bg-red-600 hover:bg-red-700 transition rounded-lg py-2 font-semibold"
                        >
                          Reject
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
