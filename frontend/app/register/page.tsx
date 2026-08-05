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
    <svg className="h-4 w-4" viewBox="0 0 24 24">
      <path
        fill="#4285F4"
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
      />
      <path
        fill="#34A853"
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
      />
      <path
        fill="#FBBC05"
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
      />
      <path
        fill="#EA4335"
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
      />
    </svg>
  );
}

function GitHubMark() {
  return (
    <svg className="h-4 w-4 fill-current" viewBox="0 0 24 24">
      <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
    </svg>
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

  const [submitted, setSubmitted] = useState(false);

  async function handleRegister(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);

    try {
      await register(username, email, password);
      toast.success("Account created successfully");
      setSubmitted(true);
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

        {submitted ? (
          <div className="rounded-lg border border-border bg-card p-8 shadow-sm text-center space-y-4">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-primary/10 text-primary">
              <Mail size={28} />
            </div>
            <h2 className="text-2xl font-bold tracking-tight">Check your email</h2>
            <p className="text-sm text-muted-foreground">
              We&apos;ve generated a verification link for <span className="font-semibold text-foreground">{email}</span>. Please verify your email before logging in.
            </p>
            <div className="pt-2">
              <Link
                href="/login"
                className="inline-block w-full rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground transition hover:opacity-90"
              >
                Proceed to Sign In
              </Link>
            </div>
          </div>
        ) : (
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
                  placeholder="username"
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
        )}
      </div>
    </main>
  );
}
