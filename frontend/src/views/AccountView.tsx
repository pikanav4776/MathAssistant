import { AuthPanel } from "../components/AuthPanel";
import { SessionHistoryPanel } from "../components/SessionHistoryPanel";
import type { useAuth } from "../hooks/useAuth";

type AuthState = ReturnType<typeof useAuth>;

interface AccountViewProps {
  auth: AuthState;
  onBack: () => void;
}

export function AccountView({ auth, onBack }: AccountViewProps) {
  return (
    <section className="view">
      <header className="view-header">
        <div className="view-header__row">
          <div>
            <h1 className="app-title">Account</h1>
            <p className="app-subtitle">Sign in, register, and view session history</p>
          </div>
          <button type="button" className="link-button" onClick={onBack}>
            Back to calculator
          </button>
        </div>
      </header>

      <AuthPanel
        user={auth.user}
        loading={auth.loading}
        error={auth.error}
        onLogin={auth.login}
        onRegister={auth.register}
        onLogout={auth.logout}
        onClearError={auth.clearError}
      />

      {auth.user ? <SessionHistoryPanel userId={auth.user.id} /> : null}
    </section>
  );
}
