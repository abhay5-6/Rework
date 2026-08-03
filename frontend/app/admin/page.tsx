"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ShieldAlert, Users, Network, Hash, Activity } from "lucide-react";
import { toast } from "sonner";
import { isAuthenticated } from "@/lib/auth";
import api from "@/lib/api/client";

interface AdminStats {
  users: number;
  organizations: number;
  workspaces: number;
}

export default function AdminDashboardPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<AdminStats | null>(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/login");
      return;
    }
    loadStats();
  }, [router]);

  async function loadStats() {
    try {
      const response = await api.get("/admin/stats");
      setStats(response.data);
    } catch (error: any) {
      console.error(error);
      toast.error(error.response?.data?.detail || "Not authorized to view admin dashboard");
      router.push("/workspaces");
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-73px)] flex items-center justify-center text-muted-foreground">
        Loading admin dashboard...
      </div>
    );
  }

  if (!stats) return null;

  return (
    <main className="min-h-[calc(100vh-73px)] bg-background text-foreground">
      <div className="mx-auto max-w-5xl px-4 py-12 md:px-6">
        <div className="mb-10 flex flex-col items-center justify-center text-center">
          <div className="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-3xl bg-red-600/10 text-red-600 shadow-sm border border-red-600/20">
            <ShieldAlert size={36} />
          </div>
          <h1 className="text-4xl font-bold tracking-tight">System Administration</h1>
          <p className="mt-3 text-lg text-muted-foreground max-w-xl mx-auto">
            Global overview of platform activity and settings.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-3 mb-10">
          <div className="rounded-2xl border border-border bg-card p-6 shadow-sm flex flex-col items-center justify-center text-center transition hover:border-primary/50 hover:shadow-md">
            <Users size={28} className="text-blue-500 mb-3" />
            <div className="text-3xl font-bold">{stats.users}</div>
            <div className="text-sm text-muted-foreground mt-1">Total Users</div>
          </div>
          
          <div className="rounded-2xl border border-border bg-card p-6 shadow-sm flex flex-col items-center justify-center text-center transition hover:border-primary/50 hover:shadow-md">
            <Network size={28} className="text-emerald-500 mb-3" />
            <div className="text-3xl font-bold">{stats.organizations}</div>
            <div className="text-sm text-muted-foreground mt-1">Organizations</div>
          </div>

          <div className="rounded-2xl border border-border bg-card p-6 shadow-sm flex flex-col items-center justify-center text-center transition hover:border-primary/50 hover:shadow-md">
            <Hash size={28} className="text-amber-500 mb-3" />
            <div className="text-3xl font-bold">{stats.workspaces}</div>
            <div className="text-sm text-muted-foreground mt-1">Workspaces</div>
          </div>
        </div>

        <section className="rounded-2xl border border-border bg-card p-8 shadow-sm">
          <h2 className="text-2xl font-semibold flex items-center gap-3 mb-6 border-b border-border pb-4">
            <Activity size={24} className="text-primary" />
            System Health
          </h2>
          <div className="text-center py-12 text-muted-foreground border-2 border-dashed border-border rounded-xl">
            <div className="mx-auto w-16 h-16 bg-green-500/10 text-green-500 rounded-full flex items-center justify-center mb-4">
              <Activity size={32} />
            </div>
            <p className="font-medium text-lg text-foreground">All systems operational</p>
            <p className="text-sm mt-1">No outstanding alerts or errors detected.</p>
          </div>
        </section>
      </div>
    </main>
  );
}
