import type { KeyboardEvent } from "react";
import { CalculatorPanel } from "../components/CalculatorPanel";

interface ProblemSelectionViewProps {
  problemInput: string;
  onProblemInputChange: (value: string) => void;
  onStartSession: () => void;
  onTryExample: () => void;
  onUseExpression: (expression: string) => void;
  loading: boolean;
  error: string | null;
}

export function ProblemSelectionView({
  problemInput,
  onProblemInputChange,
  onStartSession,
  onTryExample,
  onUseExpression,
  loading,
  error,
}: ProblemSelectionViewProps) {
  const buttonsDisabled = loading;

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter" && !buttonsDisabled) onStartSession();
  };

  return (
    <section className="view">
      <header className="view-header">
        <h1 className="app-title">MathAssistant</h1>
        <p className="app-subtitle">Algebra Co-Solving (v1.0)</p>
      </header>

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

      <button
        type="button"
        className="link-button"
        onClick={onTryExample}
        disabled={buttonsDisabled}
      >
        Try an example from library
      </button>

      {loading ? <p className="status-message">Starting session...</p> : null}
      {error ? <p className="status-message status-error">{error}</p> : null}
    </section>
  );
}
