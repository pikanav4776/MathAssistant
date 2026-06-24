import { useEffect, useState } from "react";
import { fetchStarterProblems } from "../api/client";
import { friendlyErrorMessage } from "../utils/friendlyErrorMessage";
import type { StarterProblemItem } from "../types/api";

const TOPIC_OPTIONS = [
  { value: "", label: "All topics" },
  { value: "distribution", label: "Distribution" },
  { value: "simplification", label: "Simplification" },
  { value: "double_expansion", label: "FOIL" },
  { value: "linear_steps", label: "Linear steps" },
  { value: "multihop", label: "Multihop" },
  { value: "function_evaluation", label: "Function evaluation" },
  { value: "function_composition", label: "Function composition" },
  { value: "inverse_functions", label: "Inverse functions" },
  { value: "exponential_functions", label: "Exponential functions" },
  { value: "logarithms", label: "Logarithms" },
];

const DIFFICULTY_OPTIONS = [
  { value: "", label: "All levels" },
  { value: "easy", label: "Easy" },
  { value: "medium", label: "Medium" },
  { value: "hard", label: "Hard" },
];

function formatTopic(topic: string | null): string {
  if (!topic) return "algebra";
  return topic.replace(/_/g, " ");
}

interface StarterProblemsPanelProps {
  onSelectProblem: (problemId: string) => void;
  disabled?: boolean;
}

export function StarterProblemsPanel({
  onSelectProblem,
  disabled = false,
}: StarterProblemsPanelProps) {
  const [topic, setTopic] = useState("");
  const [difficulty, setDifficulty] = useState("");
  const [items, setItems] = useState<StarterProblemItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetchStarterProblems({
      topic: topic || undefined,
      difficulty: difficulty || undefined,
    })
      .then((problems) => {
        if (!cancelled) setItems(problems);
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
  }, [topic, difficulty]);

  return (
    <section className="starter-problems" aria-label="Starter problems">
      <h2 className="starter-problems__title">Starter problems</h2>
      <p className="starter-problems__hint">
        Pick a curated example to begin. Filters narrow the list below.
      </p>

      <div className="starter-problems__filters">
        <label className="starter-problems__filter">
          <span>Topic</span>
          <select
            value={topic}
            onChange={(event) => setTopic(event.target.value)}
            disabled={disabled || loading}
          >
            {TOPIC_OPTIONS.map((option) => (
              <option key={option.value || "all"} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <label className="starter-problems__filter">
          <span>Difficulty</span>
          <select
            value={difficulty}
            onChange={(event) => setDifficulty(event.target.value)}
            disabled={disabled || loading}
          >
            {DIFFICULTY_OPTIONS.map((option) => (
              <option key={option.value || "all"} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      {loading ? <p className="status-message">Loading starter problems...</p> : null}
      {error ? <p className="status-message status-error">{error}</p> : null}
      {!loading && !error ? (
        <ul className="starter-problems__list">
          {items.map((item) => (
            <li key={item.id}>
              <button
                type="button"
                className="starter-problems__item"
                onClick={() => onSelectProblem(item.id)}
                disabled={disabled}
              >
                <span className="starter-problems__expression">{item.expression}</span>
                <span className="starter-problems__meta">
                  <span className="tag">{formatTopic(item.topic)}</span>
                  {item.difficulty ? <span className="tag">{item.difficulty}</span> : null}
                </span>
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
