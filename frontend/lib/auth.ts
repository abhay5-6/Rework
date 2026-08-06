import { getMe } from "@/lib/api/auth";

export async function isAuthenticated(): Promise<boolean> {
  if (typeof window === "undefined") {
    return false;
  }
  try {
    await getMe();
    return true;
  } catch {
    return false;
  }
}