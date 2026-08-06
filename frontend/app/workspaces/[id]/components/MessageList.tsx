import { useEffect, useState } from "react";
import { Hash, Sparkles, File as FileIcon, BookmarkPlus, MessageSquareReply, Pencil, MoveRight } from "lucide-react";
import { Message } from "@/lib/store/workspaceStore";
import { useWorkspaceStore } from "@/lib/store/workspaceStore";
import { downloadWorkspaceFile } from "@/lib/api/files";
import { toast } from "sonner";

function formatTime(timestamp?: string) {
  if (!timestamp) return "";
  return new Date(timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function formatDate(timestamp?: string) {
  if (!timestamp) return "";
  return new Date(timestamp).toLocaleDateString([], { month: "short", day: "numeric" });
}

function getInitials(name?: string) {
  return (name || "User").split(" ").map((part) => part[0]).join("").slice(0, 2).toUpperCase();
}

interface MessageListProps {
  messages: Message[];
  currentUsername: string | null;
  onSaveMemory: (message: Message) => void;
  messagesEndRef: React.RefObject<HTMLDivElement | null>;
  onReply?: (message: Message) => void;
  onEdit?: (message: Message) => void;
  roomId?: number;
}

interface SecureAttachmentProps {
  fileName: string;
  fileUrl: string;
  isImage: boolean;
  isVideo: boolean;
}

function SecureAttachment({
  fileName,
  fileUrl,
  isImage,
  isVideo,
}: SecureAttachmentProps) {
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [loadError, setLoadError] = useState(false);

  useEffect(() => {
    let active = true;
    let objectUrl: string | null = null;

    async function loadAttachment() {
      try {
        const blob = await downloadWorkspaceFile(fileUrl);
        objectUrl = URL.createObjectURL(blob);
        if (active) {
          setBlobUrl(objectUrl);
        }
      } catch {
        if (active) {
          setLoadError(true);
        }
      }
    }

    void loadAttachment();

    return () => {
      active = false;
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [fileUrl]);

  function downloadAttachment() {
    if (!blobUrl) {
      toast.error("File is still loading");
      return;
    }

    const link = document.createElement("a");
    link.href = blobUrl;
    link.download = fileName;
    link.click();
  }

  if (loadError) {
    return <p className="text-xs text-destructive">Attachment is unavailable or you no longer have access.</p>;
  }

  if (!blobUrl) {
    return <p className="text-xs text-muted-foreground">Loading attachment…</p>;
  }

  if (isImage) {
    return (
      <img
        src={blobUrl}
        alt={fileName}
        className="max-h-64 w-auto rounded-lg border border-border object-cover"
      />
    );
  }

  if (isVideo) {
    return (
      <video
        src={blobUrl}
        controls
        preload="metadata"
        className="max-h-72 w-full max-w-md rounded-lg border border-border bg-black/90 object-contain"
      />
    );
  }

  return (
    <button
      type="button"
      onClick={downloadAttachment}
      className="flex w-max max-w-full items-center gap-2 rounded-lg border border-border bg-background/80 px-3 py-2 text-foreground transition hover:bg-muted"
    >
      <FileIcon size={17} />
      <span className="truncate text-sm font-medium">{fileName}</span>
      <span className="text-xs text-muted-foreground">Download</span>
    </button>
  );
}

export default function MessageList({
  messages,
  currentUsername,
  onSaveMemory,
  messagesEndRef,
  onReply,
  onEdit,
  roomId,
}: MessageListProps) {
  const { channels } = useWorkspaceStore();

  async function handleMove(message: Message) {
    if (!roomId) return;
    const newChannelStr = prompt("Enter the name of the channel to move to:\n" + channels.map(c => c.name).join(", "));
    if (!newChannelStr) return;
    
    const targetChannel = channels.find(c => c.name.toLowerCase() === newChannelStr.toLowerCase());
    if (!targetChannel) {
      toast.error("Channel not found");
      return;
    }
    
    try {
      const { moveMessage } = await import("@/lib/api/messages");
      await moveMessage(roomId, message.id, targetChannel.id);
      toast.success(`Moved to ${targetChannel.name}`);
    } catch (error) {
      toast.error("Failed to move message");
    }
  }

  // To build threads easily, we can find the parent message and show a prefix if parent_id exists
  return (
    <section className="flex-1 overflow-y-auto px-3 py-4 md:px-5">
      {messages.length === 0 && (
        <div className="mx-auto mt-16 max-w-md text-center">
          <div className="mx-auto mb-4 h-12 w-12 rounded-lg border border-border bg-muted flex items-center justify-center">
            <Hash size={20} />
          </div>
          <h3 className="font-semibold">Start the channel</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Share notes, files, decisions, and questions. The memory layer
            will keep the useful parts findable.
          </p>
        </div>
      )}

      <div className="mx-auto flex max-w-4xl flex-col gap-1">
        {messages.map((msg, index) => {
          const username = msg.username || msg.sender_username;
          const mine = username === currentUsername || username === "You";
          const fromAI = username === "Rework AI";
          const previous = messages[index - 1];
          const prevUsername = previous ? (previous.username || previous.sender_username) : null;
          const grouped =
            prevUsername === username &&
            previous?.created_at &&
            msg.created_at &&
            !msg.parent_id &&
            formatDate(previous.created_at) === formatDate(msg.created_at);

          const content = msg.content || msg.message;

          const isVideo =
            Boolean(msg.extra_data?.file_type && typeof msg.extra_data.file_type === "string" && msg.extra_data.file_type.startsWith("video/")) ||
            Boolean(msg.extra_data?.file_name && typeof msg.extra_data.file_name === "string" && /\.(mp4|webm|ogg|mov|mkv)$/i.test(msg.extra_data.file_name));

          const isImage =
            Boolean(msg.extra_data?.file_type && typeof msg.extra_data.file_type === "string" && msg.extra_data.file_type.startsWith("image/")) ||
            Boolean(msg.extra_data?.file_name && typeof msg.extra_data.file_name === "string" && /\.(png|jpg|jpeg|gif|webp|svg)$/i.test(msg.extra_data.file_name));

          const isReply = !!msg.parent_id;

          return (
            <div
              id={`message-${msg.temp_id || msg.id}`}
              key={msg.temp_id ? `temp-${msg.temp_id}` : `${msg.id}-${index}`}
              className={`scroll-mt-24 flex gap-3 py-1 ${
                mine ? "justify-end" : "justify-start"
              } ${isReply ? "ml-8 opacity-90 border-l-2 border-border pl-2" : ""}`}
            >
              {!mine && (
                <div
                  className={`mt-1 h-9 w-9 shrink-0 rounded-lg flex items-center justify-center text-xs font-semibold ${
                    grouped
                      ? "opacity-0"
                      : fromAI
                        ? "bg-indigo-600 text-white"
                        : "bg-muted text-muted-foreground"
                  }`}
                >
                  {fromAI ? <Sparkles size={15} /> : getInitials(username)}
                </div>
              )}

              <div
                className={`group max-w-[82%] md:max-w-[68%] ${
                  mine ? "items-end" : "items-start"
                } flex flex-col`}
              >
                {!grouped && (
                  <div
                    className={`mb-1 flex items-center gap-2 px-1 text-xs text-muted-foreground ${
                      mine ? "justify-end" : "justify-start"
                    }`}
                  >
                    <span className="font-medium text-foreground">
                      {mine ? "You" : username || "User"}
                    </span>
                    <span>{formatTime(msg.created_at)}</span>
                  </div>
                )}

                <div
                  className={`relative rounded-lg px-4 py-2.5 text-sm leading-relaxed shadow-sm transition-all ${
                    msg.is_pending ? "opacity-60" : ""
                  } ${
                    fromAI
                      ? "bg-indigo-600/10 text-foreground border border-indigo-500/30"
                      : mine
                        ? "bg-emerald-600 text-white"
                        : "bg-muted text-foreground"
                  }`}
                >
                  <div className="whitespace-pre-wrap break-words">
                    {content}
                    {msg.edited_at && <span className="text-[10px] opacity-70 ml-2">(edited)</span>}
                  </div>

                  {msg.extra_data && typeof msg.extra_data.file_url === "string" && (
                    <div className="mt-3">
                      <SecureAttachment
                        fileUrl={msg.extra_data.file_url}
                        fileName={typeof msg.extra_data.file_name === "string" ? msg.extra_data.file_name : "file"}
                        isImage={isImage}
                        isVideo={isVideo}
                      />
                    </div>
                  )}

                  {!msg.is_pending && (
                    <div className={`absolute top-1/2 -translate-y-1/2 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity bg-background/95 shadow-sm border border-border rounded-md px-1 py-1 ${mine ? "right-full mr-2" : "left-full ml-2"}`}>
                      {onReply && (
                        <button onClick={() => onReply(msg)} className="p-1 hover:bg-muted rounded text-muted-foreground hover:text-foreground" title="Reply">
                          <MessageSquareReply size={14} />
                        </button>
                      )}
                      {mine && onEdit && (
                        <button onClick={() => onEdit(msg)} className="p-1 hover:bg-muted rounded text-muted-foreground hover:text-foreground" title="Edit">
                          <Pencil size={14} />
                        </button>
                      )}
                      <button onClick={() => handleMove(msg)} className="p-1 hover:bg-muted rounded text-muted-foreground hover:text-foreground" title="Move message">
                        <MoveRight size={14} />
                      </button>
                    </div>
                  )}
                </div>

                {!fromAI && content && !msg.is_pending && (
                  <button
                    type="button"
                    onClick={() => onSaveMemory(msg)}
                    className="mt-1 inline-flex items-center gap-1 self-start rounded-md px-2 py-1 text-xs text-muted-foreground opacity-0 transition hover:bg-muted hover:text-foreground focus-visible:opacity-100 group-hover:opacity-100"
                    title="Save message to workspace memory"
                  >
                    <BookmarkPlus size={13} />
                    Save to memory
                  </button>
                )}
                {msg.is_pending && (
                  <div className="mt-1 text-[10px] text-muted-foreground px-1 flex items-center gap-1">
                    {(msg.retry_count || 0) > 0 ? (
                      <span className="text-amber-500 flex items-center gap-1">
                        Retrying... ({msg.retry_count})
                      </span>
                    ) : (
                      <span>Sending...</span>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}

        <div ref={messagesEndRef} />
      </div>
    </section>
  );
}
