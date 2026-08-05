"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { getMe } from "@/lib/api/auth";

type User = {
  id: number;
  username: string;
  email: string;
  is_system_admin: boolean;
};

type AuthContextType = {
  isAuthenticated: boolean;
  user: User | null;
  login: (token: string) => void;
  logout: () => void;
};

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);

  async function login(token: string) {
    sessionStorage.setItem("token", token);
    localStorage.setItem("token", token);
    setIsAuthenticated(true);
    try {
      const userData = await getMe();
      setUser(userData);
    } catch (error) {
      console.error("Failed to fetch user data after login", error);
    }
  }

  function logout() {
    sessionStorage.removeItem("token");
    localStorage.removeItem("token");
    if (typeof window !== "undefined") {
      localStorage.removeItem("org-storage");
    }
    setIsAuthenticated(false);
    setUser(null);
  }

  useEffect(() => {
    function handleUnauthorized() {
      sessionStorage.removeItem("token");
      localStorage.removeItem("token");
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
      const token = typeof window !== "undefined"
        ? (sessionStorage.getItem("token") || localStorage.getItem("token"))
        : null;

      if (token) {
        try {
          const userData = await getMe();
          setUser(userData);
          setIsAuthenticated(true);
        } catch (error: any) {
          console.error("Failed to fetch user data:", error);
          if (error?.response?.status === 401) {
            sessionStorage.removeItem("token");
            localStorage.removeItem("token");
            setUser(null);
            setIsAuthenticated(false);
          } else {
            setIsAuthenticated(true);
          }
        }
      } else {
        setIsAuthenticated(false);
      }
      setIsLoaded(true);
    }

    checkAuth();

    return () => {
      if (typeof window !== "undefined") {
        window.removeEventListener("auth-unauthorized", handleUnauthorized);
      }
    };
  }, []); // Re-run when authentication status changes (like after login)

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

  const context =
    useContext(
      AuthContext
    );

  if (!context) {

    throw new Error(
      "useAuth must be used inside AuthProvider"
    );
  }

  return context;
}
