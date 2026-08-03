import { useRef, useEffect, useState } from "react";
import { toast } from "sonner";
import { createWorkspaceMemory } from "@/lib/api/memories";
import { uploadRoomFile } from "@/lib/api/files";
import { Message } from "@/lib/store/workspaceStore";
import { useSocketStore } from "@/lib/store/socketStore";
import { useQueueStore } from "@/lib/store/queueStore";
import MessageList from "./MessageList";
import MessageInput from "./MessageInput";

const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getErrorMessage(error: unknown, fallback: string) {
  const err = error as { response?: { data?: { detail?: string } } };
  if (err.response?.data?.detail && typeof err.response.data.detail === "string") {
    return err.response.data.detail;
  }
  return fallback;
}

export default function ChatArea({
  roomId,
  messages,
  activeDeskId,
  currentUsername,
  typingUser,
  sendTypingEvent,
  aiEnabled,
  parseWithAI,
  setParseWithAI,
}: {
  roomId: number;
  messages: Message[];
  activeDeskId: number | null;
  currentUsername: string | null;
  typingUser: string;
  sendTypingEvent: () => void;
  aiEnabled: boolean;
  parseWithAI: boolean;
  setParseWithAI: (val: boolean) => void;
}) {
  const [input, setInput] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { socket } = useSocketStore();
  const { queue, addMessage } = useQueueStore();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const deskQueue = queue.filter(q => q.workspace_id === roomId && q.channel_id === activeDeskId);
  const combinedMessages: Message[] = [
    ...messages,
    ...deskQueue.map(q => ({
      id: 0,
      content: q.content,
      sender_username: currentUsername || "You",
      created_at: q.created_at,
      extra_data: q.extra_data,
      channel_id: q.channel_id || null,
      is_pending: true,
      temp_id: q.temp_id,
      retry_count: q.retry_count
    }))
  ].sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [combinedMessages]);

  async function handleSaveMemory(message: Message) {
    const content = (message.content || message.message || "").trim();
    if (!content || !message.id) return;
    try {
      await createWorkspaceMemory(roomId, {
        content,
        source_type: "message",
        source_id: message.id,
        memory_type: "decision",
        importance_score: 3,
      });
      toast.success("Saved to workspace memory");
    } catch (error) {
      toast.error(getErrorMessage(error, "Could not save this message"));
    }
  }

  function sendMessage() {
    if (!input.trim() && !selectedFile) {
      return;
    }

    const temp_id = Date.now().toString();
    const queuedMessage = {
      temp_id,
      workspace_id: roomId,
      channel_id: activeDeskId,
      content: input,
      extra_data: {},
      created_at: new Date().toISOString(),
      retry_count: 0
    };

    if (!socket || socket.readyState !== WebSocket.OPEN) {
      // Offline mode: queue for reconnection
      addMessage(queuedMessage);
      setInput("");
      setSelectedFile(null);
      toast.info("Offline: Message queued for reconnection");
      return;
    }

    async function executeSend() {
      try {
        let extraData = {};
        if (selectedFile) {
          const uploadResult = await uploadRoomFile(
            roomId,
            selectedFile,
            (progressEvent) => {
              const percentCompleted = Math.round(
                (progressEvent.loaded * 100) / (progressEvent.total || 1)
              );
              setUploadProgress(percentCompleted);
            }
          );
          extraData = {
            file_url: uploadResult.file_url,
            file_name: uploadResult.file_name,
            file_type: uploadResult.file_type,
            ai_parse: parseWithAI && aiEnabled,
          };
        }

        if (socket && socket.readyState === WebSocket.OPEN) {
          socket.send(
            JSON.stringify({
              type: "chat_message",
              message: input,
              channel_id: activeDeskId,
              temp_id: temp_id,
              extra_data: extraData,
            })
          );
        }
        setInput("");
        setSelectedFile(null);
        setUploadProgress(0);
      } catch {
        toast.error("Failed to send message");
      }
    }
    executeSend();
  }

  return (
    <>
      <MessageList
        messages={combinedMessages}
        currentUsername={currentUsername}
        onSaveMemory={handleSaveMemory}
        messagesEndRef={messagesEndRef}
        apiUrl={apiUrl}
      />
      <MessageInput
        input={input}
        setInput={setInput}
        selectedFile={selectedFile}
        setSelectedFile={setSelectedFile}
        uploadProgress={uploadProgress}
        setUploadProgress={setUploadProgress}
        fileInputRef={fileInputRef}
        typingUser={typingUser}
        sendTypingEvent={sendTypingEvent}
        aiEnabled={aiEnabled}
        parseWithAI={parseWithAI}
        setParseWithAI={setParseWithAI}
        sendMessage={sendMessage}
      />
    </>
  );
}
