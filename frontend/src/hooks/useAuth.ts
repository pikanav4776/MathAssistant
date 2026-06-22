import { useCallback, useEffect, useState } from "react";
import {
  fetchCurrentUser,
  loginAccount,
  registerAccount,
  setAuthToken,
} from "../api/client";
import type { UserProfile } from "../types/api";

export function useAuth() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => setError(null), []);

  const applyAuth = useCallback((accessToken: string, profile: UserProfile) => {
    setAuthToken(accessToken);
    setUser(profile);
    setError(null);
  }, []);

  const logout = useCallback(() => {
    setAuthToken(null);
    setUser(null);
    setError(null);
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      setError(null);
      const result = await loginAccount(email, password);
      applyAuth(result.access_token, result.user);
    },
    [applyAuth]
  );

  const register = useCallback(
    async (email: string, password: string, displayName?: string) => {
      setError(null);
      const result = await registerAccount(email, password, displayName);
      applyAuth(result.access_token, result.user);
    },
    [applyAuth]
  );

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const profile = await fetchCurrentUser();
        if (!cancelled) setUser(profile);
      } catch {
        setAuthToken(null);
        if (!cancelled) setUser(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return {
    user,
    loading,
    error,
    setError,
    clearError,
    login,
    register,
    logout,
    isAuthenticated: user !== null,
  };
}