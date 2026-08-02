"use client";

import { useEffect } from "react";
import { RotateCcw } from "lucide-react";
import "./globals.css";


export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("global_error", error);
  }, [error]);

  return (
    <html lang="en">
      <body className="min-h-screen bg-[#0b0f1a] text-foreground">
        <main className="min-h-screen flex items-center justify-center px-6">
          <div className="w-full max-w-md rounded-lg border border-white/10 bg-primary/[0.04] p-6 shadow-2xl">
            <h2 className="text-xl font-semibold">
              Rework needs a quick refresh
            </h2>
            <p className="mt-2 text-sm leading-6 text-foreground/70">
              The app shell hit an unexpected error, but the page can recover.
            </p>
            <button
              type="button"
              onClick={reset}
              className="mt-5 inline-flex items-center gap-2 rounded-md bg-cyan-400 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300"
            >
              <RotateCcw size={16} />
              Reload
            </button>
          </div>
        </main>
      </body>
    </html>
  );
}
