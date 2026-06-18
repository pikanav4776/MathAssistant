import type { FeedbackState } from "../types/api";
import { HintWithMath } from "./HintWithMath";

interface FeedbackPanelProps {
  feedback: FeedbackState;
}

export function FeedbackPanel({ feedback }: FeedbackPanelProps) {
  let bannerClass = "feedback-banner";
  let bannerText = "";

  if (feedback.requestFailed) {
    bannerClass += " feedback-banner--warning";
    bannerText = feedback.bannerOverride ?? "⚠ Request failed";
  } else if (feedback.isEquivalent) {
    bannerClass += " feedback-banner--correct";
    bannerText = "✓ Correct!";
  } else if (feedback.isInputError) {
    bannerClass += " feedback-banner--warning";
    bannerText = "⚠ Input error";
  } else {
    bannerClass += " feedback-banner--incorrect";
    bannerText = "✗ Not quite.";
  }

  return (
    <div className="feedback-panel">
      <div className={bannerClass}>{bannerText}</div>
      {feedback.showDeeperHint && !feedback.requestFailed && (
        <p className="deeper-hint-label">Deeper hint:</p>
      )}
      <HintWithMath text={feedback.hint} className="feedback-hint" />
    </div>
  );
}
