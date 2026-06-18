import { MathExpression } from "../components/MathExpression";
import type { CompleteMode, SessionState } from "../types/api";

interface SessionCompleteViewProps {
  mode: CompleteMode;
  state: SessionState;
  onTryAnother: () => void;
}

export function SessionCompleteView({ mode, state, onTryAnother }: SessionCompleteViewProps) {
  const attemptsLabel =
    state.totalAttempts === 1 ? "1 attempt" : `${state.totalAttempts} attempts`;

  return (
    <section className="view">
      {mode === "solved" ? (
        <div className="complete-state">
          <div className="checkmark" aria-hidden="true" />
          <h2 className="complete-heading complete-heading--success">Well done!</h2>
          <p className="complete-detail complete-expression">
            Problem: <MathExpression expression={state.problemExpression} />
          </p>
          <p className="complete-detail complete-expression">
            Final: <MathExpression expression={state.expectedFinal} />
          </p>
          <p className="complete-stats">Solved in {attemptsLabel}.</p>
        </div>
      ) : null}

      {mode === "ended" ? (
        <div className="complete-state">
          <h2 className="complete-heading">Session ended</h2>
          <p className="complete-detail complete-expression">
            Problem: <MathExpression expression={state.problemExpression} />
          </p>
          <p className="complete-detail complete-expression">
            Final answer: <MathExpression expression={state.expectedFinal} />
          </p>
          <p className="complete-stats">
            Incorrect attempts: {state.incorrectAttemptCount}.
          </p>
        </div>
      ) : null}

      <button type="button" className="btn btn-primary" onClick={onTryAnother}>
        Start a new session
      </button>
    </section>
  );
}
