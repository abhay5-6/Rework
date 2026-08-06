"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { getMe, logoutUser } from "@/lib/api/auth";

type User = {
  id: number;
  username: string;
  email: string;
  is_system_admin: boolean;
};

type AuthContextType = {
  isAuthenticated: boolean;
  user: User | null;
  login: (token?: string) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);

  async function login() {
    setIsAuthenticated(true);
    try {
      const userData = await getMe();
      setUser(userData);
    } catch (error) {
      console.error("Failed to fetch user data after login", error);
    }
  }

  async function logout() {
    try {
      await logoutUser();
    } catch (error) {
      console.error("Failed to logout cleanly from server", error);
    }
    if (typeof window !== "undefined") {
      localStorage.removeItem("org-storage");
    }
    setIsAuthenticated(false);
    setUser(null);
  }

  useEffect(() => {
    function handleUnauthorized() {
      if (typeof window !== "undefined") {
        localStorage.removeItem("org-storage");
      }
      setIsAuthenticated(false);
      setUser(null);
    }

    if (typeof window !== "undefined") {
      window.addEventListener("auth-unauthorized", handleUnauthorized);
    }

    async function checkAuth() {
      try {
        const userData = await getMe();
        setUser(userData);
        setIsAuthenticated(true);
      } catch (error: any) {
        setUser(null);
        setIsAuthenticated(false);
      } finally {
        setIsLoaded(true);
      }
    }

    checkAuth();

    return () => {
      if (typeof window !== "undefined") {
        window.removeEventListener("auth-unauthorized", handleUnauthorized);
      }
    };
  }, []);

  if (!isLoaded) {
    return null;
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return context;
}
