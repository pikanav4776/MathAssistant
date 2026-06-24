import type { KeyboardEvent } from "react";
import { CalculatorPanel } from "../components/CalculatorPanel";
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
  onOpenAccount: () => void;
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
  onOpenAccount,
}: ProblemSelectionViewProps) {
  const buttonsDisabled = loading || resuming;

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter" && !buttonsDisabled) onStartSession();
  };

  const accountLabel = auth.user
    ? auth.user.display_name?.trim() || auth.user.email
    : "Sign in";

  return (
    <section className="view">
      <header className="view-header">
        <div className="view-header__row">
          <div>
            <h1 className="app-title">MathAssistant</h1>
            <p className="app-subtitle">Algebra Co-Solving (v1.0)</p>
          </div>
          <button type="button" className="link-button view-header__account" onClick={onOpenAccount}>
            {accountLabel}
          </button>
        </div>
      </header>

      <div className="input-area">
        <label htmlFor="problem-input" className="input-label">
          Problem:
        </label>
        <input
          type="text"
          id="problem-input"
          className="step-input"
          placeholder="e.g. 2x+5=9"
          autoComplete="off"
          value={problemInput}
          onChange={(event) => onProblemInputChange(event.target.value)}
          onKeyDown={handleKeyDown}
        />
        <p className="status-message">
          Linear and multi-step equations, quadratics, rational expressions, factoring,
          exponent rules, and functions (evaluation, composition, inverses with inv(x) or
          f^-1(x), exponentials, logarithms). Use letters, digits, + - * / ^, parentheses,
          and =.
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