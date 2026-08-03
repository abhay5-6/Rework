
import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen bg-transparent text-foreground flex items-center justify-center px-6">
      <div className="max-w-2xl w-full flex flex-col items-center gap-8 text-center">

        <div className="space-y-4">
          <h1 className="text-5xl font-bold tracking-tight">
            Rework
          </h1>

          <p className="text-muted-foreground text-lg">
            AI-powered realtime collaboration platform.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 w-full sm:w-auto">

          <Link
            href="/login"
            className="px-6 py-3 rounded-xl bg-primary text-primary-foreground font-semibold hover:opacity-90 transition"
          >
            Login
          </Link>

          <Link
            href="/workspaces"
            className="px-6 py-3 rounded-xl border border-border hover:bg-muted transition"
          >
            Workspaces
          </Link>

        </div>

        <div className="pt-10 text-sm text-muted-foreground">
          FastAPI • Next.js • PostgreSQL • WebSockets
        </div>
      </div>
    </main>
  );
}
