import type { LocalAttemptHistoryItem } from "../types/api";
import { MathExpression } from "./MathExpression";

interface AttemptHistoryProps {
  items: LocalAttemptHistoryItem[];
  open: boolean;
  onToggle: (open: boolean) => void;
}

export function AttemptHistory({ items, open, onToggle }: AttemptHistoryProps) {
  const reversed = [...items].reverse();

  return (
    <details
      className="attempt-history"
      open={open}
      onToggle={(event) => onToggle((event.target as HTMLDetailsElement).open)}
    >
      <summary>Show previous attempts ▾</summary>
      <ul className="attempt-history-list">
        {reversed.length === 0 ? (
          <li className="attempt-history-item">No attempts yet.</li>
        ) : (
          reversed.map((item, index) => {
            const mark = item.isEquivalent ? "✓" : item.isInputError ? "⚠" : "✗";
            return (
              <li key={`${item.stepOrder}-${index}-${item.step}`} className="attempt-history-item">
                <div className="attempt-history-step">
                  {mark} [Step {item.stepOrder}]{" "}
                  <MathExpression expression={item.step} />
                </div>
                {item.hint ? <div className="attempt-history-meta">{item.hint}</div> : null}
              </li>
            );
          })
        )}
      </ul>
    </details>
  );
}
