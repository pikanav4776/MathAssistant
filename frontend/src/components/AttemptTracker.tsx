import { MAX_ATTEMPTS_BEFORE_REVEAL } from "../constants";

interface AttemptTrackerProps {
  incorrectAttemptCount: number;
  allGreen?: boolean;
}

export function AttemptTracker({ incorrectAttemptCount, allGreen = false }: AttemptTrackerProps) {
  const nextAttempt = incorrectAttemptCount + 1;
  const label = `Attempt ${Math.min(nextAttempt, MAX_ATTEMPTS_BEFORE_REVEAL)} of ${MAX_ATTEMPTS_BEFORE_REVEAL}`;

  return (
    <div className="attempt-tracker">
      <p className="attempt-label">{label}</p>
      <div className="attempt-dots" aria-hidden="true">
        {Array.from({ length: MAX_ATTEMPTS_BEFORE_REVEAL }, (_, index) => {
          let className = "dot";
          if (allGreen) className += " dot--success";
          else if (index < incorrectAttemptCount) className += " dot--filled";
          return <span key={index} className={className} />;
        })}
      </div>
    </div>
  );
}
