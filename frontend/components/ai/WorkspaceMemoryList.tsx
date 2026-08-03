import { useState, useEffect } from "react";
import { Loader, Clock3, Pencil, Trash2, Check, X } from "lucide-react";
import {
  getRoomMemories,
  pruneMemory,
  reinforceMemory,
  updateWorkspaceMemory,
} from "@/lib/api/memories";
import type { WorkspaceMemory } from "@/lib/api/memories";

export default function WorkspaceMemoryList({ roomId }: { roomId: number }) {
  const [memories, setMemories] = useState<WorkspaceMemory[]>([]);
  const [memoryLoading, setMemoryLoading] = useState(false);
  const [memoryActionId, setMemoryActionId] = useState<number | null>(null);
  const [editingMemoryId, setEditingMemoryId] = useState<number | null>(null);
  const [editingContent, setEditingContent] = useState("");

  useEffect(() => {
    let mounted = true;
    async function loadMemories() {
      try {
        setMemoryLoading(true);
        const data = await getRoomMemories(roomId);
        if (mounted) setMemories(data);
      } catch (error) {
        console.error("Failed to load workspace memories", error);
      } finally {
        if (mounted) setMemoryLoading(false);
      }
    }
    loadMemories();
    return () => { mounted = false; };
  }, [roomId]);

  async function handleReinforceMemory(memoryId: number) {
    try {
      setMemoryActionId(memoryId);
      await reinforceMemory(roomId, memoryId);
      setMemories((current) =>
        current.map((memory) =>
          memory.id === memoryId
            ? { ...memory, last_reinforced_at: new Date().toISOString() }
            : memory
        )
      );
    } catch (error) {
      console.error("Failed to reinforce workspace memory", error);
    } finally {
      setMemoryActionId(null);
    }
  }

  async function handleForgetMemory(memoryId: number) {
    try {
      setMemoryActionId(memoryId);
      await pruneMemory(roomId, memoryId);
      setMemories((current) => current.filter((memory) => memory.id !== memoryId));
    } catch (error) {
      console.error("Failed to forget workspace memory", error);
    } finally {
      setMemoryActionId(null);
    }
  }

  function startEditingMemory(memory: WorkspaceMemory) {
    setEditingMemoryId(memory.id);
    setEditingContent(memory.content);
  }

  function cancelEditingMemory() {
    setEditingMemoryId(null);
    setEditingContent("");
  }

  async function handleUpdateMemory(memoryId: number) {
    if (!editingContent.trim()) return;
    try {
      setMemoryActionId(memoryId);
      const updated = await updateWorkspaceMemory(roomId, memoryId, {
        content: editingContent.trim(),
      });
      setMemories((current) =>
        current.map((memory) => memory.id === memoryId ? updated : memory)
      );
      cancelEditingMemory();
    } catch (error) {
      console.error("Failed to update workspace memory", error);
    } finally {
      setMemoryActionId(null);
    }
  }

  return (
    <section className="space-y-3 border-b border-border pb-5">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-foreground">Workspace memory</h3>
          <p className="mt-1 text-xs text-muted-foreground">
            Review what Rework remembers and why it exists.
          </p>
        </div>
        <span className="text-xs text-muted-foreground">{memories.length} recent</span>
      </div>

      {memoryLoading ? (
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Loader size={13} className="animate-spin" />
          Loading workspace memory
        </div>
      ) : memories.length === 0 ? (
        <p className="rounded-lg border border-dashed border-border p-3 text-xs text-muted-foreground">
          Save a useful message to start the workspace memory.
        </p>
      ) : (
        <div className="space-y-2">
          {memories.slice(0, 5).map((memory) => (
            <div key={memory.id} className="rounded-lg border border-border bg-muted/40 p-3">
              {editingMemoryId === memory.id ? (
                <textarea
                  value={editingContent}
                  onChange={(event) => setEditingContent(event.target.value)}
                  className="min-h-24 w-full resize-y rounded-md border border-border bg-background p-2 text-sm leading-relaxed text-foreground outline-none focus:ring-2 focus:ring-primary"
                  aria-label="Edit workspace memory"
                />
              ) : (
                <p className="line-clamp-3 text-sm leading-relaxed text-foreground">
                  {memory.content}
                </p>
              )}
              <div className="mt-2 flex flex-wrap items-center gap-x-2 gap-y-1 text-[11px] text-muted-foreground">
                <span>{memory.memory_type}</span>
                <span aria-hidden="true">•</span>
                {memory.source_type === "message" && memory.source_id ? (
                  <a href={`/workspaces/${roomId}#message-${memory.source_id}`} className="text-primary hover:underline">
                    Message #{memory.source_id}
                  </a>
                ) : (
                  <span>Manual note</span>
                )}
                <span aria-hidden="true">•</span>
                <span>By {memory.creator_username || `member #${memory.created_by}`}</span>
              </div>
              <div className="mt-3 flex items-center justify-between gap-2">
                <span className="inline-flex items-center gap-1 text-[11px] text-muted-foreground">
                  <Clock3 size={12} />
                  {Math.round(memory.confidence_score * 100)}% confidence
                </span>
                <div className="flex items-center gap-1">
                  {editingMemoryId === memory.id ? (
                    <>
                      <button type="button" onClick={cancelEditingMemory} className="inline-flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground transition hover:bg-background hover:text-foreground">
                        <X size={13} />
                      </button>
                      <button type="button" onClick={() => handleUpdateMemory(memory.id)} disabled={memoryActionId === memory.id} className="inline-flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground transition hover:bg-background hover:text-emerald-600 disabled:opacity-50">
                        <Check size={13} />
                      </button>
                    </>
                  ) : (
                    <>
                      <button type="button" onClick={() => startEditingMemory(memory)} className="inline-flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground transition hover:bg-background hover:text-foreground">
                        <Pencil size={13} />
                      </button>
                      <button type="button" onClick={() => handleForgetMemory(memory.id)} disabled={memoryActionId === memory.id} className="inline-flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground transition hover:bg-background hover:text-red-500 disabled:opacity-50">
                        <Trash2 size={13} />
                      </button>
                      <button type="button" onClick={() => handleReinforceMemory(memory.id)} disabled={memoryActionId === memory.id} className="inline-flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground transition hover:bg-background hover:text-emerald-600 disabled:opacity-50">
                        <Check size={13} />
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
