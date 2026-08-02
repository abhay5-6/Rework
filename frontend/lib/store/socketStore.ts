import { create } from "zustand";

interface SocketState {
  socket: WebSocket | null;
  isConnected: boolean;
  setSocket: (socket: WebSocket | null) => void;
  setIsConnected: (isConnected: boolean) => void;
}

export const useSocketStore = create<SocketState>((set) => ({
  socket: null,
  isConnected: false,
  setSocket: (socket) => set({ socket }),
  setIsConnected: (isConnected) => set({ isConnected }),
}));
