import { create } from "zustand";
import { Channel } from "@/lib/api/channels";

export interface WorkspaceMember {
  user_id: number;
  username: string;
  role?: string;
}

export interface Message {
  id: number;
  content?: string;
  message?: string;
  sender_username?: string;
  username?: string;
  created_at: string;
  type?: string;
  extra_data?: Record<string, unknown>;
  channel_id?: number | null;
  parent_id?: number | null;
  edited_at?: string | null;
  is_pending?: boolean;
  temp_id?: string;
  retry_count?: number;
}

export interface Task {
  id: number;
  description: string;
  assignee_username: string | null;
  status: string;
}

export interface Memory {
  id: number;
  content: string;
  importance_score: number;
  domain: string;
  creator_username?: string;
}

export interface Workspace {
  owner_id: number;
  is_member: boolean;
  role: string | null;
  ai_enabled: boolean;
  can_create_private_channel?: boolean;
  id: number;
  name: string;
  description: string;
  is_private?: boolean;
}

interface RoomState {
  workspace: Workspace | null;
  setRoom: (workspace: Workspace | null) => void;
  messages: Message[];
  setMessages: (messages: Message[]) => void;
  addMessage: (message: Message) => void;
  tasks: Task[];
  setTasks: (tasks: Task[]) => void;
  memories: Memory[];
  setMemories: (memories: Memory[]) => void;
  isAiThinking: boolean;
  setIsAiThinking: (isAiThinking: boolean) => void;
  aiAnswer: string | null;
  setAiAnswer: (aiAnswer: string | null) => void;
  channels: Channel[];
  setDesks: (channels: Channel[]) => void;
  activeDeskId: number | null;
  setActiveDeskId: (id: number | null) => void;
  updateMessageStore: (id: number, content: string, editedAt: string | null) => void;
  moveMessageStore: (id: number, channelId: number) => void;
}

export const useWorkspaceStore = create<RoomState>((set) => ({
  workspace: null,
  setRoom: (workspace) => set({ workspace }),
  messages: [],
  setMessages: (messages) => set({ messages }),
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  tasks: [],
  setTasks: (tasks) => set({ tasks }),
  memories: [],
  setMemories: (memories) => set({ memories }),
  isAiThinking: false,
  setIsAiThinking: (isAiThinking) => set({ isAiThinking }),
  aiAnswer: null,
  setAiAnswer: (aiAnswer) => set({ aiAnswer }),
  channels: [],
  setDesks: (channels) => set({ channels }),
  activeDeskId: null,
  setActiveDeskId: (id) => set({ activeDeskId: id }),
  updateMessageStore: (id, content, editedAt) => set((state) => ({
    messages: state.messages.map(msg => 
      msg.id === id ? { ...msg, content, message: content, edited_at: editedAt } : msg
    )
  })),
  moveMessageStore: (id, channelId) => set((state) => ({
    messages: state.messages.map(msg => 
      msg.id === id ? { ...msg, channel_id: channelId } : msg
    )
  })),
}));
