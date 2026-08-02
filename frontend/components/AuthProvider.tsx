"use client";

import {

  createContext,

  useContext,

  useEffect,

  useState

} from "react";

type AuthContextType = {

  isAuthenticated: boolean;

  login: (
    token: string
  ) => void;

  logout: () => void;
};

const AuthContext =
  createContext<
    AuthContextType | null
  >(null);

export function AuthProvider({

  children,

}: {

  children:
    React.ReactNode;

}) {

const [
  isAuthenticated,
  setIsAuthenticated
] = useState(false);

const [
  isLoaded,
  setIsLoaded
] = useState(false);


  function login(
    token: string
  ) {

    // Keep both stores in sync so route guards and API calls
    // see a consistent auth state during navigation.
    sessionStorage.setItem(
      "token",
      token
    );

    localStorage.setItem(
      "token",
      token
    );

    setIsAuthenticated(
      true
    );
  }

  function logout() {

    sessionStorage.removeItem(
      "token"
    );

    localStorage.removeItem(
      "token"
    );

    setIsAuthenticated(
      false
    );
  }

  useEffect(() => {

    queueMicrotask(() => {

      const token =
        sessionStorage.getItem("token")
        || localStorage.getItem("token");

      setIsAuthenticated(
        !!token
      );

      setIsLoaded(true);
    });

}, []);

  

    if (!isLoaded) {

      return null;
    }

    return (

      <AuthContext.Provider
      value={{

        isAuthenticated,

        login,

        logout

      }}
    >

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
