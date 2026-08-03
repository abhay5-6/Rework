"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import axios from "axios";
import { LockKeyhole, Mail, UserRound } from "lucide-react";
import { toast } from "sonner";

import { useAuth } from "@/components/AuthProvider";
import {
  getAuthProviders,
  getProviderAuthUrl,
  register,
  type AuthProviders,
} from "@/lib/api/auth";

function GoogleMark() {
  return (
    <span className="text-sm font-bold" aria-hidden="true">
      G
    </span>
  );
}

function GitHubMark() {
  return (
    <span className="text-xs font-bold" aria-hidden="true">
      GH
    </span>
  );
}

export default function RegisterPage() {
  const router = useRouter();
  const auth = useAuth();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [providers, setProviders] = useState<AuthProviders>({
    google: false,
    github: false,
  });

  useEffect(() => {
    if (auth.isAuthenticated) {
      router.push("/workspaces");
    }
  }, [auth.isAuthenticated, router]);

  useEffect(() => {
    getAuthProviders().then(setProviders).catch(() => undefined);
  }, []);

  async function handleRegister(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);

    try {
      await register(username, email, password);
      toast.success("Account created");
      router.push("/login");
    } catch (error: unknown) {
      console.error(error);
      let message = "Registration failed";
      const detail = axios.isAxiosError(error)
        ? error.response?.data?.detail
        : undefined;

      if (typeof detail === "string") {
        message = detail;
      } else if (Array.isArray(detail) && typeof detail[0]?.msg === "string") {
        message = detail[0].msg;
      }

      toast.error(message);
    } finally {
      setLoading(false);
    }
  }

  function handleProvider(provider: "google" | "github") {
    if (!providers[provider]) {
      toast.info(`${provider === "google" ? "Google" : "GitHub"} sign-in is not configured yet.`);
      return;
    }

    window.location.assign(getProviderAuthUrl(provider));
  }

  return (
    <main className="min-h-[calc(100vh-73px)] bg-background text-foreground">
      <div className="mx-auto grid min-h-[calc(100vh-73px)] max-w-6xl items-center gap-8 px-4 py-8 md:px-6 lg:grid-cols-[1fr_440px]">
        <section className="hidden lg:block">
          <div className="max-w-xl">
            <h1 className="text-5xl font-bold tracking-tight">
              Start with a real workspace identity.
            </h1>
            <p className="mt-5 text-lg text-muted-foreground">
              Rework will feel best when accounts map to verified providers.
              For now, create a password account with the email you plan to use
              for Google or GitHub later.
            </p>
          </div>
        </section>

        <form
          onSubmit={handleRegister}
          className="rounded-lg border border-border bg-card p-6 shadow-sm"
        >
          <div>
            <h2 className="text-2xl font-semibold tracking-tight">
              Create your account
            </h2>
            <p className="mt-1 text-sm text-muted-foreground">
              This creates a Rework account today and keeps the UI ready for
              provider-linked identity later.
            </p>
          </div>

          <div className="mt-6 grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => handleProvider("google")}
              className="flex items-center justify-center gap-2 rounded-lg border border-border px-3 py-2.5 text-sm font-medium transition hover:bg-muted"
            >
              <GoogleMark />
              Google
            </button>
            <button
              type="button"
              onClick={() => handleProvider("github")}
              className="flex items-center justify-center gap-2 rounded-lg border border-border px-3 py-2.5 text-sm font-medium transition hover:bg-muted"
            >
              <GitHubMark />
              GitHub
            </button>
          </div>

          <div className="my-6 flex items-center gap-3 text-xs text-muted-foreground">
            <span className="h-px flex-1 bg-border" />
            Email password
            <span className="h-px flex-1 bg-border" />
          </div>

          <div className="space-y-3">
            <label className="block">
              <span className="mb-1.5 block text-sm font-medium">Username</span>
              <span className="flex items-center gap-2 rounded-lg border border-border bg-background px-3">
                <UserRound size={16} className="text-muted-foreground" />
                <input
                  type="text"
                  placeholder="abhay"
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                  className="min-w-0 flex-1 bg-transparent py-2.5 text-sm outline-none"
                  required
                />
              </span>
            </label>

            <label className="block">
              <span className="mb-1.5 block text-sm font-medium">Email</span>
              <span className="flex items-center gap-2 rounded-lg border border-border bg-background px-3">
                <Mail size={16} className="text-muted-foreground" />
                <input
                  type="email"
                  placeholder="you@company.com"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  className="min-w-0 flex-1 bg-transparent py-2.5 text-sm outline-none"
                  required
                />
              </span>
            </label>

            <label className="block">
              <span className="mb-1.5 block text-sm font-medium">Password</span>
              <span className="flex items-center gap-2 rounded-lg border border-border bg-background px-3">
                <LockKeyhole size={16} className="text-muted-foreground" />
                <input
                  type="password"
                  placeholder="Create a password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  className="min-w-0 flex-1 bg-transparent py-2.5 text-sm outline-none"
                  required
                />
              </span>
            </label>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="mt-5 w-full rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground transition hover:opacity-90 disabled:opacity-50"
          >
            {loading ? "Creating..." : "Create account"}
          </button>

          <p className="mt-5 text-center text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link href="/login" className="font-semibold text-foreground hover:underline">
              Sign in
            </Link>
          </p>
        </form>
      </div>
    </main>
  );
}
