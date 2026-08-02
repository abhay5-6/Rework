import { create } from "zustand";
import { Desk } from "@/lib/api/desks";

export interface RoomMember {
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
  desk_id?: number | null;
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

export interface Room {
  id: number;
  name: string;
  description: string;
  ai_enabled?: boolean;
  is_private?: boolean;
}

interface RoomState {
  room: Room | null;
  setRoom: (room: Room | null) => void;
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
  desks: Desk[];
  setDesks: (desks: Desk[]) => void;
  activeDeskId: number | null;
  setActiveDeskId: (id: number | null) => void;
}

export const useRoomStore = create<RoomState>((set) => ({
  room: null,
  setRoom: (room) => set({ room }),
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
  desks: [],
  setDesks: (desks) => set({ desks }),
  activeDeskId: null,
  setActiveDeskId: (id) => set({ activeDeskId: id }),
}));
