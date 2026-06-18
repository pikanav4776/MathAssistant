import { useEffect } from "react";
import { AttemptHistory } from "../components/AttemptHistory";
import { AttemptTracker } from "../components/AttemptTracker";
import { ExpressionDisplay } from "../components/ExpressionDisplay";
import { FeedbackPanel } from "../components/FeedbackPanel";
import { StepInputField } from "../components/StepInput";
import type { FeedbackState, SessionState } from "../types/api";

interface ActiveSessionViewProps {
  state: SessionState;
  stepInput: string;
  onStepInputChange: (value: string) => void;
  onSubmitStep: () => void;
  onGiveUp: () => void;
  feedback: FeedbackState | null;
  showFeedback: boolean;
  inputError: boolean;
  submitDisabled: boolean;
  giveUpDisabled: boolean;
  attemptHistoryOpen: boolean;
  onAttemptHistoryToggle: (open: boolean) => void;
  allGreenDots: boolean;
}

export function ActiveSessionView({
  state,
  stepInput,
  onStepInputChange,
  onSubmitStep,
  onGiveUp,
  feedback,
  showFeedback,
  inputError,
  submitDisabled,
  giveUpDisabled,
  attemptHistoryOpen,
  onAttemptHistoryToggle,
  allGreenDots,
}: ActiveSessionViewProps) {
  useEffect(() => {
    document.getElementById("step-input")?.focus();
  }, []);

  const stepLabel = `Step ${Math.min(state.stepIndex, state.stepCount)}/${state.stepCount}`;

  return (
    <section className="view">
      <div className="problem-bar">
        <ExpressionDisplay
          label="Current expression:"
          expression={state.currentExpression}
        />
        <div className="problem-meta">
          <span className="tag">{state.topic || "algebra"}</span>
          <span className="tag">{stepLabel}</span>
        </div>
      </div>

      <AttemptTracker
        incorrectAttemptCount={state.incorrectAttemptCount}
        allGreen={allGreenDots}
      />

      <StepInputField
        id="step-input"
        label="Your step:"
        value={stepInput}
        onChange={onStepInputChange}
        onSubmit={onSubmitStep}
        placeholder="e.g. 2x + 6"
        disabled={submitDisabled}
        submitDisabled={submitDisabled}
        submitLabel="Check Step"
        inputError={inputError}
      />

      {showFeedback && feedback ? <FeedbackPanel feedback={feedback} /> : null}

      <AttemptHistory
        items={state.attemptHistory}
        open={attemptHistoryOpen}
        onToggle={onAttemptHistoryToggle}
      />

      <button
        type="button"
        className="link-button"
        onClick={onGiveUp}
        disabled={giveUpDisabled}
      >
        Reveal solution
      </button>
    </section>
  );
}
