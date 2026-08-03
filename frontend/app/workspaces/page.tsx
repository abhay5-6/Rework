"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import {
  ArrowRight,
  Hash,
  Lock,
  MessageCircle,
  Plus,
  Search,
  ShieldCheck,
  Sparkles,
  Users,
} from "lucide-react";
import { toast } from "sonner";

import { createRoom, deleteRoom, getRooms, joinRoom, leaveRoom } from "@/lib/api/workspaces";
import { getOrganizations } from "@/lib/api/organizations";
import { isAuthenticated } from "@/lib/auth";
import { useOrgStore } from "@/lib/store/orgStore";

type Workspace = {
  id: number;
  name: string;
  description?: string;
  is_private: boolean;
  is_member: boolean;
  is_owner: boolean;
  has_pending_request: boolean;
};

function getErrorMessage(error: unknown, fallback: string) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;

    if (typeof detail === "string") {
      return detail;
    }
  }

  return fallback;
}

export default function RoomsPage() {
  const router = useRouter();
  const { activeOrgId, setActiveOrgId, setOrganizations } = useOrgStore();
  const [workspaces, setRooms] = useState<Workspace[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [isPrivate, setIsPrivate] = useState(false);
  const [search, setSearch] = useState("");

  const filteredRooms = useMemo(() => {
    const term = search.trim().toLowerCase();

    if (!term) {
      return workspaces;
    }

    return workspaces.filter((workspace) =>
      [workspace.name, workspace.description || ""].some((value) =>
        value.toLowerCase().includes(term)
      )
    );
  }, [workspaces, search]);

  const joinedRooms = workspaces.filter((workspace) => workspace.is_member).length;
  const privateRooms = workspaces.filter((workspace) => workspace.is_private).length;

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/login");
      return;
    }

    async function initRooms() {
      setLoading(true);
      try {
        let currentOrgId = activeOrgId;
        if (!currentOrgId) {
          const orgs = await getOrganizations();
          if (orgs.length > 0) {
            setOrganizations(orgs);
            currentOrgId = orgs[0].id;
            setActiveOrgId(currentOrgId);
          }
        }
        if (currentOrgId) {
          const data = await getRooms(currentOrgId);
          setRooms(data);
        } else {
          setRooms([]);
        }
      } catch (error) {
        console.error(error);
        toast.error("Failed to load workspaces");
      } finally {
        setLoading(false);
      }
    }

    initRooms();
  }, [router, activeOrgId, setActiveOrgId, setOrganizations]);

  async function handleCreateRoom() {
    if (!name.trim()) {
      return;
    }

    let targetOrgId = activeOrgId;
    if (!targetOrgId) {
      try {
        const orgs = await getOrganizations();
        if (orgs.length > 0) {
          targetOrgId = orgs[0].id;
          setActiveOrgId(targetOrgId);
          setOrganizations(orgs);
        }
      } catch (e) {
        console.error(e);
      }
    }

    if (!targetOrgId) {
      toast.error("Please create an organization first");
      router.push("/orgs");
      return;
    }

    try {
      setCreating(true);
      await createRoom(name, description, isPrivate, targetOrgId);
      toast.success("Workspace created");
      setName("");
      setDescription("");
      setIsPrivate(false);
      const data = await getRooms(targetOrgId);
      setRooms(data);
    } catch (error) {
      console.error(error);
      toast.error("Failed to create workspace");
    } finally {
      setCreating(false);
    }
  }

  async function loadRooms(orgId?: number) {
    const targetId = orgId || activeOrgId;
    if (!targetId) return;
    try {
      const data = await getRooms(targetId);
      setRooms(data);
    } catch (error) {
      console.error(error);
      toast.error("Failed to load workspaces");
    }
  }

  async function handleJoinRoom(roomId: number) {
    try {
      const response = await joinRoom(roomId);

      if (response.message === "Join request sent") {
        toast.success("Access request sent");
        await loadRooms();
        return;
      }

      if (response.message === "Joined workspace successfully") {
        toast.success("Joined workspace");
        await loadRooms();
        router.push(`/workspaces/${roomId}`);
      }
    } catch (error) {
      console.error(error);
      toast.error(getErrorMessage(error, "Failed to join workspace"));
    }
  }

  async function handleLeaveRoom(roomId: number) {
    try {
      await leaveRoom(roomId);
      toast.success("Left workspace");
      await loadRooms();
    } catch (error) {
      console.error(error);
      toast.error("Failed to leave workspace");
    }
  }

  async function handleDeleteRoom(roomId: number) {
    try {
      await deleteRoom(roomId);
      toast.success("Workspace deleted");
      await loadRooms();
    } catch (error) {
      console.error(error);
      toast.error("Failed to delete workspace");
    }
  }

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-73px)] flex items-center justify-center text-muted-foreground">
        Loading workspaces...
      </div>
    );
  }

  return (
    <main className="min-h-[calc(100vh-73px)] bg-background text-foreground">
      <div className="mx-auto grid max-w-7xl gap-6 px-4 py-6 md:px-6 lg:grid-cols-[320px_minmax(0,1fr)]">
        <aside className="space-y-4 lg:sticky lg:top-24 lg:self-start">
          <section className="rounded-lg border border-border bg-muted/30 p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-primary text-primary-foreground flex items-center justify-center">
                <Plus size={18} />
              </div>
              <div>
                <h1 className="font-semibold">New workspace</h1>
                <p className="text-xs text-muted-foreground">
                  Create a shared place for channels, chat, tasks, and memory.
                </p>
              </div>
            </div>

            <div className="mt-4 space-y-3">
              <input
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="Workspace name"
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
              />
              <textarea
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                placeholder="What should people use this for?"
                className="min-h-24 w-full resize-none rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
              />

              <label className="flex items-center justify-between rounded-lg border border-border bg-background p-3">
                <span>
                  <span className="block text-sm font-medium">Private</span>
                  <span className="block text-xs text-muted-foreground">
                    Require approval before joining.
                  </span>
                </span>
                <input
                  type="checkbox"
                  checked={isPrivate}
                  onChange={(event) => setIsPrivate(event.target.checked)}
                  className="h-4 w-4 accent-foreground"
                />
              </label>

              <button
                onClick={handleCreateRoom}
                disabled={creating || !name.trim()}
                className="w-full rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground transition hover:opacity-90 disabled:opacity-50"
              >
                {creating ? "Creating..." : "Create workspace"}
              </button>
            </div>
          </section>

          <section className="grid grid-cols-3 gap-2">
            <div className="rounded-lg border border-border bg-card p-3">
              <div className="text-xl font-semibold">{workspaces.length}</div>
              <div className="text-xs text-muted-foreground">Total</div>
            </div>
            <div className="rounded-lg border border-border bg-card p-3">
              <div className="text-xl font-semibold">{joinedRooms}</div>
              <div className="text-xs text-muted-foreground">Joined</div>
            </div>
            <div className="rounded-lg border border-border bg-card p-3">
              <div className="text-xl font-semibold">{privateRooms}</div>
              <div className="text-xs text-muted-foreground">Private</div>
            </div>
          </section>
        </aside>

        <section className="min-w-0 space-y-5">
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <h2 className="text-3xl font-bold tracking-tight">Workspaces</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Pick a workspace, then work inside channels with chat, AI memory,
                files, calls, and task boards.
              </p>
            </div>

            <div className="flex w-full items-center gap-2 rounded-lg border border-border bg-card px-3 py-2 text-sm md:w-72">
              <Search size={16} className="text-muted-foreground" />
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search workspaces"
                className="min-w-0 flex-1 bg-transparent outline-none"
              />
            </div>
          </div>

          <div className="grid gap-3">
            {filteredRooms.map((workspace) => (
              <article
                key={workspace.id}
                className="rounded-lg border border-border bg-card p-4 transition hover:border-foreground/30"
              >
                <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <div className="h-9 w-9 rounded-lg bg-muted flex items-center justify-center">
                        {workspace.is_private ? <Lock size={16} /> : <Hash size={16} />}
                      </div>
                      <div className="min-w-0">
                        <h3 className="truncate font-semibold">{workspace.name}</h3>
                        <p className="line-clamp-1 text-sm text-muted-foreground">
                          {workspace.description || "No description provided yet."}
                        </p>
                      </div>
                    </div>

                    <div className="mt-3 flex flex-wrap gap-2 text-xs">
                      <span className="rounded-md bg-muted px-2 py-1 text-muted-foreground">
                        {workspace.is_private ? "Private" : "Public"}
                      </span>
                      {workspace.is_member && (
                        <span className="rounded-md bg-emerald-500/10 px-2 py-1 text-emerald-600">
                          Joined
                        </span>
                      )}
                      {workspace.is_owner && (
                        <span className="inline-flex items-center gap-1 rounded-md bg-muted px-2 py-1 text-muted-foreground">
                          <ShieldCheck size={12} />
                          Owner
                        </span>
                      )}
                      <span className="inline-flex items-center gap-1 rounded-md bg-muted px-2 py-1 text-muted-foreground">
                        <MessageCircle size={12} />
                        Chat
                      </span>
                      <span className="inline-flex items-center gap-1 rounded-md bg-muted px-2 py-1 text-muted-foreground">
                        <Sparkles size={12} />
                        Memory
                      </span>
                      <span className="inline-flex items-center gap-1 rounded-md bg-muted px-2 py-1 text-muted-foreground">
                        <Users size={12} />
                        Team
                      </span>
                    </div>
                  </div>

                  <div className="flex shrink-0 flex-wrap gap-2">
                    {workspace.is_member ? (
                      <>
                        <button
                          onClick={() => router.push(`/workspaces/${workspace.id}`)}
                          className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition hover:opacity-90"
                        >
                          Open
                          <ArrowRight size={16} />
                        </button>
                        {!workspace.is_owner && (
                          <button
                            onClick={() => handleLeaveRoom(workspace.id)}
                            className="rounded-lg border border-border px-4 py-2 text-sm font-semibold transition hover:bg-muted"
                          >
                            Leave
                          </button>
                        )}
                        {workspace.is_owner && (
                          <button
                            onClick={() => handleDeleteRoom(workspace.id)}
                            className="rounded-lg bg-red-500/10 px-4 py-2 text-sm font-semibold text-red-500 transition hover:bg-red-500/20"
                          >
                            Delete
                          </button>
                        )}
                      </>
                    ) : workspace.has_pending_request ? (
                      <button
                        disabled
                        className="rounded-lg bg-muted px-4 py-2 text-sm font-semibold text-muted-foreground"
                      >
                        Request pending
                      </button>
                    ) : (
                      <button
                        onClick={() => handleJoinRoom(workspace.id)}
                        className="rounded-lg bg-secondary px-4 py-2 text-sm font-semibold text-secondary-foreground transition hover:bg-secondary/80"
                      >
                        {workspace.is_private ? "Request access" : "Join"}
                      </button>
                    )}
                  </div>
                </div>
              </article>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
