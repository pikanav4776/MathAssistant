import { useEffect, useState } from "react";
import { fetchUserSessionHistory } from "../api/client";
import { friendlyErrorMessage } from "../utils/friendlyErrorMessage";
import type { UserSessionHistoryItem } from "../types/api";

function outcomeLabel(item: UserSessionHistoryItem): string {
  if (item.completed) return "Solved";
  if (item.revealed_solution) return "Revealed";
  return "Incomplete";
}

function formatDate(iso: string | null): string {
  if (!iso) return "";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

interface SessionHistoryPanelProps {
  userId: number;
}

export function SessionHistoryPanel({ userId }: SessionHistoryPanelProps) {
  const [items, setItems] = useState<UserSessionHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetchUserSessionHistory()
      .then((history) => {
        if (!cancelled) setItems(history);
      })
      .catch((err) => {
        if (!cancelled) setError(friendlyErrorMessage(err));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [userId]);

  return (
    <section className="session-history" aria-label="Recent sessions">
      <h2 className="session-history__title">Recent sessions</h2>
      {loading ? <p className="status-message">Loading history...</p> : null}
      {error ? <p className="status-message status-error">{error}</p> : null}
      {!loading && !error && items.length === 0 ? (
        <p className="status-message">No completed sessions yet.</p>
      ) : null}
      {!loading && !error && items.length > 0 ? (
        <ul className="session-history__list">
          {items.map((item) => (
            <li key={item.session_id} className="session-history__item">
              <div className="session-history__expression">{item.problem_expression}</div>
              <div className="session-history__meta">
                <span className={`session-history__badge session-history__badge--${outcomeLabel(item).toLowerCase()}`}>
                  {outcomeLabel(item)}
                </span>
                <span>
                  {item.total_attempts} attempt{item.total_attempts === 1 ? "" : "s"}
                </span>
                {item.completed_at ? <span>{formatDate(item.completed_at)}</span> : null}
              </div>
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
