import { FormEvent, useState } from "react";
import type { UserProfile } from "../types/api";

interface AuthPanelProps {
  user: UserProfile | null;
  loading: boolean;
  error: string | null;
  onLogin: (email: string, password: string) => Promise<void>;
  onRegister: (email: string, password: string, displayName?: string) => Promise<void>;
  onLogout: () => void;
  onClearError: () => void;
}

export function AuthPanel({
  user,
  loading,
  error,
  onLogin,
  onRegister,
  onLogout,
  onClearError,
}: AuthPanelProps) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  if (loading) {
    return <p className="auth-panel status-message">Checking account...</p>;
  }

  if (user) {
    const label = user.display_name?.trim() || user.email;
    return (
      <div className="auth-panel auth-panel--signed-in">
        <p className="auth-panel__greeting">Signed in as {label}</p>
        <p className="auth-panel__hint">Sessions you start will be linked to your account. Guest tutoring still works when signed out.</p>
        <button type="button" className="link-button" onClick={onLogout}>
          Sign out
        </button>
      </div>
    );
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setLocalError(null);
    onClearError();
    setSubmitting(true);
    try {
      if (mode === "login") {
        await onLogin(email, password);
      } else {
        await onRegister(email, password, displayName || undefined);
      }
      setPassword("");
    } catch (err) {
      setLocalError(err instanceof Error ? err.message : "Authentication failed.");
    } finally {
      setSubmitting(false);
    }
  };

  const message = localError || error;

  return (
    <section className="auth-panel" aria-label="Account">
      <div className="auth-panel__tabs">
        <button
          type="button"
          className={mode === "login" ? "auth-tab auth-tab--active" : "auth-tab"}
          onClick={() => setMode("login")}
        >
          Sign in
        </button>
        <button
          type="button"
          className={mode === "register" ? "auth-tab auth-tab--active" : "auth-tab"}
          onClick={() => setMode("register")}
        >
          Register
        </button>
      </div>

      <form className="auth-form" onSubmit={handleSubmit}>
        {mode === "register" ? (
          <label className="input-label" htmlFor="auth-display-name">
            Display name (optional)
            <input
              id="auth-display-name"
              className="step-input"
              type="text"
              autoComplete="name"
              value={displayName}
              onChange={(event) => setDisplayName(event.target.value)}
            />
          </label>
        ) : null}

        <label className="input-label" htmlFor="auth-email">
          Email
          <input
            id="auth-email"
            className="step-input"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </label>

        <label className="input-label" htmlFor="auth-password">
          Password
          <input
            id="auth-password"
            className="step-input"
            type="password"
            autoComplete={mode === "login" ? "current-password" : "new-password"}
            required
            minLength={8}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>

        <button type="submit" className="btn btn-primary" disabled={submitting}>
          {submitting ? "Please wait..." : mode === "login" ? "Sign in" : "Create account"}
        </button>
      </form>

      {message ? <p className="status-message status-error">{message}</p> : null}
    </section>
  );
}