import { RefObject } from "react";
import { Paperclip, SendHorizonal, X, Video as VideoIcon, File as FileIcon } from "lucide-react";

interface MessageInputProps {
  input: string;
  setInput: (val: string) => void;
  selectedFile: File | null;
  setSelectedFile: (file: File | null) => void;
  uploadProgress: number;
  setUploadProgress: (val: number) => void;
  fileInputRef: RefObject<HTMLInputElement>;
  typingUser: string;
  sendTypingEvent: () => void;
  aiEnabled: boolean;
  parseWithAI: boolean;
  setParseWithAI: (val: boolean) => void;
  sendMessage: () => void;
}

export default function MessageInput({
  input,
  setInput,
  selectedFile,
  setSelectedFile,
  uploadProgress,
  setUploadProgress,
  fileInputRef,
  typingUser,
  sendTypingEvent,
  aiEnabled,
  parseWithAI,
  setParseWithAI,
  sendMessage,
}: MessageInputProps) {
  return (
    <footer className="border-t border-border bg-background px-3 py-3 md:px-5">
      <div className="mx-auto max-w-4xl">
        {typingUser && (
          <div className="mb-2 px-2 text-xs font-medium text-muted-foreground flex items-center gap-1">
            <span className="flex gap-0.5">
              <span className="animate-bounce inline-block">.</span>
              <span className="animate-bounce inline-block delay-75">.</span>
              <span className="animate-bounce inline-block delay-150">.</span>
            </span>
            {typingUser} is typing
          </div>
        )}

        {selectedFile && (
          <div className="mb-3 flex items-center justify-between rounded-lg border border-border bg-muted/50 p-3">
            <div className="flex items-center gap-3 overflow-hidden">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded bg-background shadow-sm">
                {selectedFile.type.startsWith("video/") || /\.(mp4|webm|ogg|mov|mkv)$/i.test(selectedFile.name) ? (
                  <VideoIcon size={18} className="text-indigo-500" />
                ) : (
                  <FileIcon size={18} className="text-muted-foreground" />
                )}
              </div>
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-foreground">
                  {selectedFile.name}
                </p>
                <p className="text-xs text-muted-foreground">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {uploadProgress > 0 && uploadProgress < 100 && (
                <div className="text-xs font-medium text-primary">
                  {uploadProgress}%
                </div>
              )}
              <button
                onClick={() => {
                  setSelectedFile(null);
                  setUploadProgress(0);
                  if (fileInputRef.current) fileInputRef.current.value = "";
                }}
                className="rounded-md p-1.5 text-muted-foreground hover:bg-background hover:text-foreground transition"
              >
                <X size={16} />
              </button>
            </div>
          </div>
        )}

        {aiEnabled && selectedFile && (
          <div className="mb-3 flex items-center gap-2 px-1">
            <input
              type="checkbox"
              id="parseWithAI"
              checked={parseWithAI}
              onChange={(e) => setParseWithAI(e.target.checked)}
              className="rounded border-border bg-background text-primary"
            />
            <label htmlFor="parseWithAI" className="text-xs text-muted-foreground">
              Extract contents into room memory
            </label>
          </div>
        )}

        <div className="relative flex items-end gap-2 rounded-xl border border-border bg-background p-2 shadow-sm focus-within:border-primary focus-within:ring-1 focus-within:ring-primary/50 transition-all">
          <input
            type="file"
            ref={fileInputRef}
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) setSelectedFile(file);
            }}
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground transition"
            title="Attach file"
          >
            <Paperclip size={18} />
          </button>
          <textarea
            value={input}
            onChange={(e) => {
              setInput(e.target.value);
              sendTypingEvent();
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
              }
            }}
            placeholder="Message..."
            className="max-h-32 min-h-[36px] w-full resize-none bg-transparent py-2 text-sm focus:outline-none"
            rows={1}
          />
          <button
            onClick={sendMessage}
            disabled={(!input.trim() && !selectedFile)}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition"
          >
            <SendHorizonal size={18} />
          </button>
        </div>
      </div>
    </footer>
  );
}
