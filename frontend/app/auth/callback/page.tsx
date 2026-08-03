"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Loader } from "lucide-react";
import { toast } from "sonner";

import { useAuth } from "@/components/AuthProvider";

export default function AuthCallbackPage() {
  const auth = useAuth();
  const router = useRouter();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");
    const error = params.get("oauth_error");

    if (token) {
      auth.login(token);
      toast.success("Identity verified");
      router.replace("/workspaces");
      return;
    }

    toast.error(error || "OAuth sign-in failed");
    router.replace("/login");
  }, [auth, router]);

  return (
    <main className="flex min-h-[calc(100vh-73px)] items-center justify-center bg-background text-foreground">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Loader size={16} className="animate-spin" />
        Completing sign-in
      </div>
    </main>
  );
}
