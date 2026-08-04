"use client";

import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { BrainCircuit, LayoutGrid, LogOut, Network, ChevronDown, Settings, ShieldAlert } from "lucide-react";
import { useAuth } from "@/components/AuthProvider";
import NotificationBell from "@/components/NotificationBell";
import { ThemeToggle } from "@/components/ThemeToggle";
import { useOrgStore, Organization, OrgMembership } from "@/lib/store/orgStore";
import { getOrganizations } from "@/lib/api/organizations";
import { useState, useRef, useEffect } from "react";

export default function Navbar() {
  const router = useRouter();
  const pathname = usePathname();
  const auth = useAuth();
  const { organizations, activeOrgId, setActiveOrgId, setOrganizations } = useOrgStore();
  const [showOrgDropdown, setShowOrgDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowOrgDropdown(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (auth.isAuthenticated) {
      getOrganizations().then((data) => {
        setOrganizations(data);
        if (data.length > 0 && !activeOrgId) {
          setActiveOrgId(data[0].id);
        }
      }).catch(console.error);
    }
  }, [auth.isAuthenticated, setOrganizations, activeOrgId, setActiveOrgId]);

  function handleLogout() {
    auth.logout();
    router.push("/login");
    router.refresh();
  }

  function isActive(path: string) {
    return pathname.startsWith(path);
  }

  return (
    <nav className="sticky top-0 z-50 w-full border-b border-border bg-background/80 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        {/* LEFT */}
        <div className="flex items-center gap-10">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="h-10 w-10 rounded-2xl bg-foreground text-background flex items-center justify-center font-bold shadow-lg group-hover:scale-105 transition">
              <BrainCircuit size={20} />
            </div>
            <div>
              <div className="text-xl font-semibold tracking-tight text-foreground">
                Rework
              </div>
              <div className="text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
                Cognitive Workspace
              </div>
            </div>
          </Link>

          {auth.isAuthenticated && (
            <div className="flex items-center gap-4">
              <Link
                href="/workspaces"
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm transition ${
                  isActive("/workspaces") && !isActive("/orgs")
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted"
                }`}
              >
                <LayoutGrid size={16} />
                Workspaces
              </Link>

              {auth.user?.is_system_admin && (
                <Link
                  href="/admin"
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm transition ${
                    isActive("/admin")
                      ? "bg-red-600 text-white shadow-sm"
                      : "text-muted-foreground hover:text-red-500 hover:bg-red-500/10 border border-transparent hover:border-red-500/20"
                  }`}
                >
                  <ShieldAlert size={16} />
                  Admin
                </Link>
              )}

              <div className="relative" ref={dropdownRef}>
                <button
                  onClick={() => setShowOrgDropdown(!showOrgDropdown)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm transition ${
                    isActive("/orgs")
                      ? "bg-primary text-primary-foreground shadow-sm"
                      : "text-muted-foreground hover:text-foreground hover:bg-muted border border-transparent hover:border-border"
                  }`}
                >
                  <Network size={16} />
                  <span className="max-w-[120px] truncate font-medium">
                    {organizations.find((o) => o.id === activeOrgId)?.name || "Select Org"}
                  </span>
                  <ChevronDown size={14} className="opacity-50" />
                </button>

                {showOrgDropdown && (
                  <div className="absolute left-0 mt-2 w-56 rounded-xl border border-border bg-background shadow-lg overflow-hidden py-1">
                    <div className="px-3 py-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      Organizations
                    </div>
                    {organizations.map((org) => (
                      <button
                        key={org.id}
                        onClick={() => {
                          setActiveOrgId(org.id);
                          setShowOrgDropdown(false);
                          if (pathname !== "/workspaces") router.push("/workspaces");
                        }}
                        className={`w-full flex items-center gap-2 px-4 py-2 text-sm text-left transition ${
                          activeOrgId === org.id
                            ? "bg-primary/10 text-primary font-medium"
                            : "text-foreground hover:bg-muted"
                        }`}
                      >
                        <Network size={14} className={activeOrgId === org.id ? "text-primary" : "text-muted-foreground"} />
                        <span className="truncate">{org.name}</span>
                      </button>
                    ))}
                    <div className="my-1 border-t border-border" />
                    <Link
                      href="/orgs"
                      onClick={() => setShowOrgDropdown(false)}
                      className="flex items-center gap-2 px-4 py-2 text-sm text-muted-foreground hover:bg-muted hover:text-foreground transition"
                    >
                      <Settings size={14} />
                      Manage Organizations
                    </Link>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* RIGHT */}
        <div className="flex items-center gap-4">
          <ThemeToggle />

          {auth.isAuthenticated ? (
            <>
              <div className="hidden md:flex items-center gap-2 px-3 py-2 rounded-xl border border-border bg-muted/50 text-xs text-muted-foreground">
                AI Memory Active
              </div>

              <NotificationBell />

              <button
                onClick={handleLogout}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-foreground text-background font-medium hover:opacity-90 transition"
              >
                <LogOut size={16} />
                Logout
              </button>
            </>
          ) : (
            <div className="flex items-center gap-3">
              <Link
                href="/login"
                className="px-4 py-2 rounded-xl text-muted-foreground hover:text-foreground hover:bg-muted transition"
              >
                Login
              </Link>

              <Link
                href="/register"
                className="px-5 py-2.5 rounded-xl bg-foreground text-background font-semibold hover:opacity-90 transition shadow-lg"
              >
                Register
              </Link>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}