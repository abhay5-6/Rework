"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";
import { ShieldAlert } from "lucide-react";

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const auth = useAuth();
  const router = useRouter();
  const [isAuthorized, setIsAuthorized] = useState(false);

  useEffect(() => {
    // If auth state is known and they are not a system admin
    if (auth.isAuthenticated === false) {
      router.push("/login");
    } else if (auth.isAuthenticated === true && auth.user) {
      if (!auth.user.is_system_admin) {
        router.push("/workspaces");
      } else {
        setIsAuthorized(true);
      }
    }
  }, [auth.isAuthenticated, auth.user, router]);

  if (!isAuthorized) {
    return (
      <div className="min-h-[calc(100vh-73px)] flex flex-col items-center justify-center text-muted-foreground">
        <ShieldAlert size={48} className="text-red-500/20 mb-4" />
        <p>Verifying administrator privileges...</p>
      </div>
    );
  }

  return <>{children}</>;
}
