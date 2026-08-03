"use client";

import { ChevronRight, ChevronLeft, Sparkles } from "lucide-react";
import StaleMemoryAlerts from "./StaleMemoryAlerts";
import WorkspaceMemoryList from "./WorkspaceMemoryList";
import AISearchTab from "./AISearchTab";

interface AIAssistantPanelProps {
  roomId: number;
  isOpen: boolean;
  onToggle: () => void;
}

export default function AIAssistantPanel({
  roomId,
  isOpen,
  onToggle,
}: AIAssistantPanelProps) {
  return (
    <>
      <button
        onClick={onToggle}
        className="fixed right-4 top-1/2 -translate-y-1/2 z-40 bg-primary text-primary-foreground p-2 rounded-full hover:scale-110 transition shadow-lg lg:hidden"
      >
        {isOpen ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
      </button>

      <div
        className={`fixed right-0 top-0 h-screen w-full sm:w-96 bg-background/95 backdrop-blur-xl border-l border-border transform transition-transform duration-300 z-30 overflow-hidden flex flex-col ${
          isOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        <StaleMemoryAlerts roomId={roomId} />

        <div className="p-6 border-b border-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles size={20} className="text-blue-400" />
            <h2 className="text-xl font-bold text-foreground">AI Assistant</h2>
          </div>
          <button
            onClick={onToggle}
            className="text-muted-foreground hover:text-foreground transition"
          >
            <ChevronRight size={20} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          <WorkspaceMemoryList roomId={roomId} />
          <AISearchTab roomId={roomId} />
        </div>
      </div>

      {isOpen && (
        <div
          onClick={onToggle}
          className="fixed inset-0 bg-background/20 z-20 lg:hidden"
        />
      )}
    </>
  );
}
