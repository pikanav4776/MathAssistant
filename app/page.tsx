"use client";

import { useState } from "react";

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

export default function Home() {
  const [step, setStep] = useState("");
  const [expected, setExpected] = useState("x^2+5*x+6");
  const [response, setResponse] = useState<StepResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submitStep = async () => {
    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const res = await fetch("http://127.0.0.1:8000/submit-step", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          step,
          expected,
          session_id: "test-session-1",
        }),
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
          "(from mathassistant/backend, with your .venv active)."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-10 max-w-2xl">
      <h1 className="text-xl font-bold">MathAssistant MVP</h1>

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
        disabled={loading || !step.trim() || !expected.trim()}
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
