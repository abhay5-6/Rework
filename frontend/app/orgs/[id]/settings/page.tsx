"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Settings, Shield, Globe, Lock, ArrowLeft } from "lucide-react";
import { toast } from "sonner";
import { AxiosError } from "axios";
import { isAuthenticated } from "@/lib/auth";

import { getOrganization, updateOrganization, Organization } from "@/lib/api/organizations";
import { useOrgStore } from "@/lib/store/orgStore";

export default function OrgSettingsPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const orgId = parseInt(params.id, 10);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [org, setOrg] = useState<Organization | null>(null);

  // Form states
  const [name, setName] = useState("");
  const [allowPrivateChannels, setAllowPrivateChannels] = useState(false);
  const [allowPublicWorkspaces, setAllowPublicWorkspaces] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/login");
      return;
    }
    loadOrg();
  }, [router, orgId]);

  async function loadOrg() {
    try {
      const data = await getOrganization(orgId);
      setOrg(data);
      setName(data.name);
      setAllowPrivateChannels(data.allow_private_channels);
      setAllowPublicWorkspaces(data.allow_public_workspaces);
    } catch (error) {
      console.error(error);
      toast.error("Failed to load organization");
      router.push("/orgs");
    } finally {
      setLoading(false);
    }
  }

  async function handleSave() {
    if (!name.trim() || !org) return;
    try {
      setSaving(true);
      await updateOrganization(orgId, {
        name,
        allow_private_channels: allowPrivateChannels,
        allow_public_workspaces: allowPublicWorkspaces
      });
      toast.success("Settings saved successfully");
      loadOrg();
    } catch (error: unknown) {
      console.error(error);
      if (error instanceof AxiosError && error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error("Failed to save settings");
      }
    } finally {

      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-73px)] flex items-center justify-center text-muted-foreground">
        Loading settings...
      </div>
    );
  }

  if (!org) return null;

  return (
    <main className="min-h-[calc(100vh-73px)] bg-background text-foreground">
      <div className="mx-auto max-w-3xl px-4 py-12 md:px-6">
        <button
          onClick={() => router.push("/workspaces")}
          className="mb-8 flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition"
        >
          <ArrowLeft size={16} />
          Back to Workspaces
        </button>

        <div className="mb-10 flex items-center gap-4">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-lg">
            <Settings size={32} />
          </div>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Organization Settings</h1>
            <p className="mt-1 text-muted-foreground">
              Manage {org.name}&apos;s preferences and permissions.
            </p>
          </div>
        </div>

        <div className="space-y-6">
          <section className="rounded-xl border border-border bg-card p-6 shadow-sm">
            <h2 className="text-xl font-semibold flex items-center gap-2 mb-4">
              <Shield size={20} className="text-primary" />
              General
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-1.5">
                  Organization Name
                </label>
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
            </div>
          </section>

          <section className="rounded-xl border border-border bg-card p-6 shadow-sm">
            <h2 className="text-xl font-semibold flex items-center gap-2 mb-4">
              <Lock size={20} className="text-primary" />
              Security & Permissions
            </h2>
            <div className="space-y-6">
              <div className="flex items-start justify-between">
                <div>
                  <label className="text-base font-medium text-foreground block mb-0.5">
                    Allow Private Channels
                  </label>
                  <p className="text-sm text-muted-foreground max-w-[80%]">
                    If enabled, members can create private channels. If disabled, only Organization Administrators can create private channels.
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer mt-1">
                  <input 
                    type="checkbox" 
                    className="sr-only peer"
                    checked={allowPrivateChannels}
                    onChange={(e) => setAllowPrivateChannels(e.target.checked)}
                  />
                  <div className="w-11 h-6 bg-muted peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                </label>
              </div>

              <div className="flex items-start justify-between">
                <div>
                  <label className="text-base font-medium text-foreground block mb-0.5">
                    Allow Public Workspaces
                  </label>
                  <p className="text-sm text-muted-foreground max-w-[80%]">
                    If enabled, workspaces can be made public to the internet. If disabled, all workspaces are restricted to organization members.
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer mt-1">
                  <input 
                    type="checkbox" 
                    className="sr-only peer"
                    checked={allowPublicWorkspaces}
                    onChange={(e) => setAllowPublicWorkspaces(e.target.checked)}
                  />
                  <div className="w-11 h-6 bg-muted peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                </label>
              </div>
            </div>
          </section>

          <div className="flex justify-end pt-4">
            <button
              onClick={handleSave}
              disabled={saving}
              className="rounded-lg bg-primary px-6 py-2.5 text-sm font-semibold text-primary-foreground shadow-md transition hover:bg-primary/90 disabled:opacity-50"
            >
              {saving ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}
