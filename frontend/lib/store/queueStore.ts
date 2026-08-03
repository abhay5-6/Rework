import { create } from "zustand";


/** Represents an offline message queued for WebSocket auto-flushing upon reconnection */
export interface QueuedMessage {
  temp_id: string;
  workspace_id: number;
  channel_id: number | null;
  content: string;
  extra_data?: Record<string, unknown>;
  created_at: string; // ISO string for sorting
  retry_count: number;
}

interface QueueState {
  queue: QueuedMessage[];
  addMessage: (msg: QueuedMessage) => void;
  removeMessage: (temp_id: string) => void;
  incrementRetry: (temp_id: string) => void;
  clearQueue: (workspace_id?: number) => void;
}

/**
 * Zustand store for persisting offline messages in localStorage.
 * Automatically flushes messages when WebSocket connection re-establishes.
 */
export const useQueueStore = create<QueueState>((set) => ({
  queue: [],
  addMessage: (msg) =>
    set((state) => ({ queue: [...state.queue, msg] })),
  removeMessage: (temp_id) =>
    set((state) => ({
      queue: state.queue.filter((m) => m.temp_id !== temp_id),
    })),
  incrementRetry: (temp_id) =>
    set((state) => ({
      queue: state.queue.map((m) =>
        m.temp_id === temp_id ? { ...m, retry_count: m.retry_count + 1 } : m
      ),
    })),
  clearQueue: (workspace_id) =>
    set((state) => ({
      queue: workspace_id
        ? state.queue.filter((m) => m.workspace_id !== workspace_id)
        : [],
    })),
}));
