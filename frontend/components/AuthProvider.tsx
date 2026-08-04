"use client";

import {

  createContext,

  useContext,

  useEffect,

  useState

} from "react";

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

  function login(token: string) {
    sessionStorage.setItem("token", token);
    localStorage.setItem("token", token);
    setIsAuthenticated(true);
  }

  function logout() {
    sessionStorage.removeItem("token");
    localStorage.removeItem("token");
    setIsAuthenticated(false);
    setUser(null);
  }

  useEffect(() => {
    queueMicrotask(async () => {
      const token = sessionStorage.getItem("token") || localStorage.getItem("token");
      if (token) {
        try {
          // Dynamic import to avoid circular dependencies if any
          const { getMe } = await import("@/lib/api/auth");
          const userData = await getMe();
          setUser(userData);
          setIsAuthenticated(true);
        } catch (error) {
          console.error("Failed to fetch user data", error);
          // If token is invalid, the interceptor will handle it, but we set false just in case
          setIsAuthenticated(false);
        }
      } else {
        setIsAuthenticated(false);
      }
      setIsLoaded(true);
    });
  }, [isAuthenticated]); // Re-run when authentication status changes (like after login)

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
