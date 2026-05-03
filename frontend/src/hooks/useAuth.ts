import { useCallback, useEffect, useState } from "react";
import { getCurrentUser, logout } from "../api/auth";
import type { User } from "../types";

type AuthStatus = "checking" | "authenticated" | "guest";

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [status, setStatus] = useState<AuthStatus>("checking");
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setStatus("checking");
    setError(null);

    try {
      setUser(await getCurrentUser());
      setStatus("authenticated");
    } catch {
      setUser(null);
      setStatus("guest");
    }
  }, []);

  const signOut = useCallback(async () => {
    setError(null);

    try {
      await logout();
    } catch {
      setError("Could not sign out. Please try again.");
      return;
    }

    setUser(null);
    setStatus("guest");
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return {
    user,
    status,
    error,
    refresh,
    signOut,
  };
}
