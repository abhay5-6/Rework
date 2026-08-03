"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Network, Plus, ArrowRight } from "lucide-react";
import { toast } from "sonner";
import { isAuthenticated } from "@/lib/auth";
import { getOrganizations, createOrganization } from "@/lib/api/organizations";
import { useOrgStore } from "@/lib/store/orgStore";

export default function OrgsPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");
  const { organizations, setOrganizations, setActiveOrgId } = useOrgStore();

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/login");
      return;
    }
    loadOrgs();
  }, [router]);

  async function loadOrgs() {
    try {
      const data = await getOrganizations();
      setOrganizations(data);
    } catch (error) {
      console.error(error);
      toast.error("Failed to load organizations");
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateOrg() {
    if (!name.trim()) return;
    try {
      setCreating(true);
      await createOrganization(name);
      toast.success("Organization created");
      setName("");
      await loadOrgs();
    } catch (error) {
      console.error(error);
      toast.error("Failed to create organization");
    } finally {
      setCreating(false);
    }
  }

  function handleSelectOrg(orgId: number) {
    setActiveOrgId(orgId);
    router.push("/workspaces");
  }

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-73px)] flex items-center justify-center text-muted-foreground">
        Loading organizations...
      </div>
    );
  }

  return (
    <main className="min-h-[calc(100vh-73px)] bg-background text-foreground">
      <div className="mx-auto max-w-4xl px-4 py-12 md:px-6">
        <div className="mb-10 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-lg">
            <Network size={32} />
          </div>
          <h1 className="text-3xl font-bold tracking-tight">Your Organizations</h1>
          <p className="mt-2 text-muted-foreground">
            Select an organization to enter its workspace, or create a new one.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          {/* Create New Org */}
          <section className="flex flex-col justify-between rounded-xl border border-border bg-card p-6 shadow-sm">
            <div>
              <h2 className="text-xl font-semibold">Create Organization</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Set up a new space for your company or team.
              </p>
              <div className="mt-4 space-y-3">
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Organization name (e.g. Acme Corp)"
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
            </div>
            <button
              onClick={handleCreateOrg}
              disabled={creating || !name.trim()}
              className="mt-6 flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground transition hover:opacity-90 disabled:opacity-50"
            >
              <Plus size={18} />
              {creating ? "Creating..." : "Create"}
            </button>
          </section>

          {/* List Orgs */}
          <section className="flex flex-col gap-3">
            {organizations.length === 0 ? (
              <div className="flex h-full flex-col items-center justify-center rounded-xl border border-dashed border-border p-6 text-center text-muted-foreground">
                <Network size={24} className="mb-2 opacity-20" />
                <p className="text-sm">You don&apos;t belong to any organizations yet.</p>
              </div>
            ) : (
              organizations.map((org) => (
                <button
                  key={org.id}
                  onClick={() => handleSelectOrg(org.id)}
                  className="group flex items-center justify-between rounded-xl border border-border bg-card p-4 text-left shadow-sm transition hover:border-primary/50 hover:shadow-md"
                >
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                      <Network size={20} />
                    </div>
                    <div>
                      <h3 className="font-semibold">{org.name}</h3>
                      <p className="text-xs text-muted-foreground">
                        Joined {new Date(org.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <ArrowRight size={18} className="text-muted-foreground transition group-hover:text-primary group-hover:translate-x-1" />
                </button>
              ))
            )}
          </section>
        </div>
      </div>
    </main>
  );
}
