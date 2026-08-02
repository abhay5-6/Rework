"use client";

import { useEffect } from "react";
import { RotateCcw } from "lucide-react";


export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("route_error", error);
  }, [error]);

  return (
    <div className="min-h-[60vh] flex items-center justify-center px-6">
      <div className="w-full max-w-md rounded-lg border border-white/10 bg-primary/[0.04] p-6 shadow-2xl">
        <h2 className="text-xl font-semibold text-foreground">
          Something went wrong
        </h2>
        <p className="mt-2 text-sm leading-6 text-foreground/70">
          Rework hit a recoverable page error. Your session is still intact.
        </p>
        <button
          type="button"
          onClick={reset}
          className="mt-5 inline-flex items-center gap-2 rounded-md bg-cyan-400 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300"
        >
          <RotateCcw size={16} />
          Try again
        </button>
      </div>
    </div>
  );
}
