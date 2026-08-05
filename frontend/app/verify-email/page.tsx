"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { CheckCircle2, XCircle, Loader2 } from "lucide-react";
import api from "@/lib/api/client";

export default function VerifyEmailPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setErrorMessage("No verification token provided in the URL.");
      return;
    }

    async function verifyToken() {
      try {
        await api.get(`/auth/verify-email?token=${token}`);
        setStatus("success");
      } catch (error: any) {
        setStatus("error");
        setErrorMessage(error.response?.data?.detail || "Verification failed or token expired.");
      }
    }

    verifyToken();
  }, [token]);

  return (
    <main className="min-h-[calc(100vh-73px)] bg-background text-foreground flex items-center justify-center p-4">
      <div className="w-full max-w-md rounded-xl border border-border bg-card p-8 text-center shadow-lg">
        {status === "loading" && (
          <div className="space-y-4">
            <Loader2 className="mx-auto h-12 w-12 animate-spin text-primary" />
            <h1 className="text-xl font-semibold">Verifying your email...</h1>
            <p className="text-sm text-muted-foreground">Please wait while we confirm your identity token.</p>
          </div>
        )}

        {status === "success" && (
          <div className="space-y-4">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-emerald-500/10 text-emerald-500">
              <CheckCircle2 size={36} />
            </div>
            <h1 className="text-2xl font-bold tracking-tight">Email Verified!</h1>
            <p className="text-sm text-muted-foreground">
              Your email address has been successfully verified. You can now access your workspaces.
            </p>
            <div className="pt-4">
              <button
                onClick={() => router.push("/login")}
                className="w-full rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground transition hover:opacity-90"
              >
                Sign in to Rework
              </button>
            </div>
          </div>
        )}

        {status === "error" && (
          <div className="space-y-4">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-destructive/10 text-destructive">
              <XCircle size={36} />
            </div>
            <h1 className="text-2xl font-bold tracking-tight">Verification Failed</h1>
            <p className="text-sm text-muted-foreground">{errorMessage}</p>
            <div className="pt-4">
              <Link
                href="/login"
                className="inline-block w-full rounded-lg border border-border px-4 py-2.5 text-sm font-semibold transition hover:bg-muted"
              >
                Return to Login
              </Link>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
