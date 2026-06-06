"use client";

import { useCallback, useEffect, useState } from "react";

type StepResponse = {
  session_id: string;
  received_step: string;
  expected_step: string;
  is_equivalent: boolean;
  structural_diff: Record<string, unknown> | null;
  error_classification: {
    error_type: string;
    confidence: string;
    reason: string;
  } | null;
  hint: string;
};

const API_BASE = "http://127.0.0.1:8000";

export default function Home() {
  const [step, setStep] = useState("");
  const [expected, setExpected] = useState("x^2+5*x+6");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [response, setResponse] = useState<StepResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [sessionLoading, setSessionLoading] = useState(true);

  const startSession = useCallback(async () => {
    setSessionLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/start-session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          problem_id: "mvp-demo",
          problem_expression: expected,
          expected_final: expected,
        }),
      });
      const data = await res.json();
      if (!res.ok || !data.session_id) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : (data.message ?? "Failed to start session")
        );
      }
      setSessionId(data.session_id);
    } catch (err) {
      setSessionId(null);
      setError(
        err instanceof Error && err.message !== "Failed to fetch"
          ? err.message
          : "Cannot reach the backend at http://127.0.0.1:8000. " +
              "Start it with: python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000 " +
              "(from MathAssistant/backend, with your .venv active)."
      );
    } finally {
      setSessionLoading(false);
    }
  }, [expected]);

  useEffect(() => {
    startSession();
  }, [startSession]);

  const submitStep = async () => {
    if (!sessionId) {
      setError("No active session. Refresh the page to start a new one.");
      return;
    }

    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const res = await fetch(`${API_BASE}/submit-step`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ step, expected, session_id: sessionId }),
      });

      const data = await res.json();
      if (!res.ok) {
        setError(
          typeof data.detail === "string"
            ? data.detail
            : JSON.stringify(data.detail ?? data, null, 2)
        );
        return;
      }
      setResponse(data);
    } catch {
      setError(
        "Cannot reach the backend at http://127.0.0.1:8000. " +
          "Start it with: python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000 " +
          "(from MathAssistant/backend, with your .venv active)."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-10 max-w-2xl">
      <h1 className="text-xl font-bold">MathAssistant MVP</h1>
      {sessionLoading && (
        <p className="mt-2 text-sm text-gray-600">Starting session…</p>
      )}
      {sessionId && (
        <p className="mt-2 text-xs text-gray-500 break-all">
          Session: {sessionId}
        </p>
      )}

      <label className="block mt-4 text-sm font-medium">Your step</label>
      <input
        className="border p-2 mt-1 w-full"
        value={step}
        onChange={(e) => setStep(e.target.value)}
        placeholder="e.g. x^2+6*x+5"
      />

      <label className="block mt-4 text-sm font-medium">Expected answer</label>
      <input
        className="border p-2 mt-1 w-full"
        value={expected}
        onChange={(e) => setExpected(e.target.value)}
        placeholder="e.g. x^2+5*x+6"
      />

      <button
        className="mt-4 p-2 bg-blue-500 text-white disabled:opacity-50"
        onClick={submitStep}
        disabled={
          loading || sessionLoading || !sessionId || !step.trim() || !expected.trim()
        }
      >
        {loading ? "Submitting…" : "Submit"}
      </button>

      {error && (
        <p className="mt-4 p-3 bg-red-100 text-red-800 rounded">{error}</p>
      )}

      {response && (
        <div
          className={`mt-4 p-4 rounded ${
            response.is_equivalent ? "bg-green-100" : "bg-amber-100"
          }`}
        >
          <p className="font-semibold">
            {response.is_equivalent ? "Correct" : "Not equivalent"}
          </p>
          <p className="mt-2">{response.hint}</p>
          {!response.is_equivalent && response.error_classification && (
            <p className="mt-2 text-sm">
              Error type: {response.error_classification.error_type}
            </p>
          )}
          <pre className="mt-4 text-xs overflow-auto">
            {JSON.stringify(response, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}