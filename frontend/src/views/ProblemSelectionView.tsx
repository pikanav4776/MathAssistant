import type { KeyboardEvent } from "react";
import { AuthPanel } from "../components/AuthPanel";
import { CalculatorPanel } from "../components/CalculatorPanel";
import { SessionHistoryPanel } from "../components/SessionHistoryPanel";
import { StarterProblemsPanel } from "../components/StarterProblemsPanel";
import type { useAuth } from "../hooks/useAuth";

type AuthState = ReturnType<typeof useAuth>;

interface ProblemSelectionViewProps {
  problemInput: string;
  onProblemInputChange: (value: string) => void;
  onStartSession: () => void;
  onTryExample: () => void;
  onSelectStarter: (problemId: string) => void;
  onUseExpression: (expression: string) => void;
  loading: boolean;
  resuming?: boolean;
  error: string | null;
  auth: AuthState;
}

export function ProblemSelectionView({
  problemInput,
  onProblemInputChange,
  onStartSession,
  onTryExample,
  onSelectStarter,
  onUseExpression,
  loading,
  resuming = false,
  error,
  auth,
}: ProblemSelectionViewProps) {
  const buttonsDisabled = loading || resuming;

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter" && !buttonsDisabled) onStartSession();
  };

  return (
    <section className="view">
      <header className="view-header">
        <h1 className="app-title">MathAssistant</h1>
        <p className="app-subtitle">Algebra Co-Solving (v1.0)</p>
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

      <div className="input-area">
        <label htmlFor="problem-input" className="input-label">
          Problem:
        </label>
        <input
          type="text"
          id="problem-input"
          className="step-input"
          placeholder="e.g. 2(x+3)"
          autoComplete="off"
          value={problemInput}
          onChange={(event) => onProblemInputChange(event.target.value)}
          onKeyDown={handleKeyDown}
        />
        <p className="status-message">
          Use keyboard algebra only: letters, digits, + - * / ^ and parentheses.
        </p>
      </div>

      <button
        type="button"
        className="btn btn-primary"
        onClick={onStartSession}
        disabled={buttonsDisabled}
      >
        Start Session
      </button>

      <CalculatorPanel
        onUseExpression={onUseExpression}
        contextHint="problem"
        disabled={buttonsDisabled}
      />

      <StarterProblemsPanel
        onSelectProblem={onSelectStarter}
        disabled={buttonsDisabled}
      />

      <button
        type="button"
        className="link-button"
        onClick={onTryExample}
        disabled={buttonsDisabled}
      >
        Try a random example
      </button>

      {resuming ? <p className="status-message">Restoring session...</p> : null}
      {loading ? <p className="status-message">Starting session...</p> : null}
      {error ? <p className="status-message status-error">{error}</p> : null}
    </section>
  );
}