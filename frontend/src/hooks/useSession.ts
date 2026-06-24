import { useCallback, useEffect, useRef, useState } from "react";
import {
  fetchSession,
  finalizeSession,
  fetchProblem,
  getSampleProblem,
  startSessionWithExpression,
  startSessionWithProblemId,
  submitStep,
} from "../api/client";
import { containsTextLikeInput } from "../utils/expressionTextLike";
import { friendlyErrorMessage } from "../utils/friendlyErrorMessage";
import {
  countsTowardAttemptLimit,
  isInputErrorType,
  MAX_ATTEMPTS_BEFORE_ESCALATION,
  MAX_ATTEMPTS_BEFORE_REVEAL,
} from "../constants";
import type {
  AppView,
  CompleteMode,
  FeedbackState,
  LocalAttemptHistoryItem,
  SessionState,
  SessionSummary,
  StartSessionResponse,
  StepResult,
} from "../types/api";
import { initialSessionState } from "../types/api";

const ACTIVE_SESSION_STORAGE_KEY = "mathassistant_active_session_id";

function persistActiveSessionId(sessionId: string | null): void {
  if (typeof sessionStorage === "undefined") return;
  if (sessionId) sessionStorage.setItem(ACTIVE_SESSION_STORAGE_KEY, sessionId);
  else sessionStorage.removeItem(ACTIVE_SESSION_STORAGE_KEY);
}

function readActiveSessionId(): string | null {
  if (typeof sessionStorage === "undefined") return null;
  return sessionStorage.getItem(ACTIVE_SESSION_STORAGE_KEY);
}

function attemptHistoryFromServer(
  entries: SessionSummary["attempt_history"]
): LocalAttemptHistoryItem[] {
  return entries.map((entry) => {
    const errorType = entry.error_type ?? null;
    return {
      step: String(entry.step ?? ""),
      stepOrder: Number(entry.step_order ?? 1),
      hint: typeof entry.hint === "string" ? entry.hint : undefined,
      isEquivalent: Boolean(entry.is_equivalent),
      isInputError: isInputErrorType(errorType),
    };
  });
}

function hydrateSessionState(data: SessionSummary): SessionState {
  const attemptHistory = attemptHistoryFromServer(data.attempt_history);
  const incorrectAttemptCount =
    data.incorrect_attempt_count ??
    attemptHistory.filter(
      (attempt) =>
        !attempt.isEquivalent &&
        countsTowardAttemptLimit(
          data.attempt_history.find((e) => e.step === attempt.step)?.error_type ?? null
        )
    ).length;

  return {
    problemId: data.problem_id || "",
    problemExpression: data.problem_expression,
    expectedFinal: data.expected_final || "",
    currentExpression: data.current_expression || data.problem_expression,
    sessionId: data.session_id,
    topic: data.topic || "algebra",
    stepCount: data.step_count || 1,
    stepIndex: data.step_index || 1,
    incorrectAttemptCount,
    totalAttempts: data.attempt_count,
    attemptHistory,
    sessionComplete: Boolean(data.completed),
  };
}

function applyStartSessionData(
  prev: SessionState,
  data: StartSessionResponse,
  fallbackTopic = ""
): SessionState {
  return {
    ...prev,
    problemId: data.problem_id || "",
    problemExpression: data.problem_expression,
    expectedFinal: data.expected_final,
    currentExpression: data.current_expression || data.problem_expression,
    sessionId: data.session_id,
    topic: data.topic || fallbackTopic || "algebra",
    stepCount: data.step_count || 1,
    stepIndex: 1,
    incorrectAttemptCount: 0,
    totalAttempts: 0,
    attemptHistory: [],
    sessionComplete: false,
  };
}

function feedbackFromResult(result: StepResult, incorrectAttemptCount: number): FeedbackState {
  const errorType = result.error_classification?.error_type ?? null;
  const inputError = isInputErrorType(errorType);

  if (result.is_equivalent) {
    return {
      isEquivalent: true,
      isInputError: false,
      hint: result.skip_message || result.hint || "",
      showDeeperHint: false,
    };
  }

  if (inputError) {
    return {
      isEquivalent: false,
      isInputError: true,
      hint: result.skip_message || result.hint || "",
      showDeeperHint: false,
    };
  }

  return {
    isEquivalent: false,
    isInputError: false,
    hint: result.skip_message || result.hint || "",
    showDeeperHint: incorrectAttemptCount >= MAX_ATTEMPTS_BEFORE_ESCALATION,
  };
}

export function useSession() {
  const [view, setView] = useState<AppView>("selection");
  const [state, setState] = useState<SessionState>(initialSessionState);
  const [completeMode, setCompleteMode] = useState<CompleteMode>(null);
  const [feedback, setFeedback] = useState<FeedbackState | null>(null);
  const [showFeedback, setShowFeedback] = useState(false);
  const [problemInput, setProblemInput] = useState("");
  const [stepInput, setStepInput] = useState("");
  const [problemLoading, setProblemLoading] = useState(false);
  const [problemError, setProblemError] = useState<string | null>(null);
  const [inputError, setInputError] = useState(false);
  const [submitDisabled, setSubmitDisabled] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [giveUpDisabled, setGiveUpDisabled] = useState(false);
  const [resuming, setResuming] = useState(false);
  const [attemptHistoryOpen, setAttemptHistoryOpen] = useState(false);
  const [allGreenDots, setAllGreenDots] = useState(false);

  const stateRef = useRef(state);
  stateRef.current = state;

  const showCompleteSolved = useCallback(async () => {
    const current = stateRef.current;
    try {
      await finalizeSession(current.sessionId, {
        completed: true,
        revealedSolution: false,
      });
    } catch {
      // Still show complete screen even if finalize fails offline.
    }
    persistActiveSessionId(null);
    setState((prev) => ({ ...prev, sessionId: null }));
    setCompleteMode("solved");
    setView("complete");
  }, []);

  const showCompleteEnded = useCallback(async () => {
    const current = stateRef.current;
    try {
      await finalizeSession(current.sessionId, {
        completed: false,
        revealedSolution: true,
      });
    } catch {
      // Still show complete screen even if finalize fails offline.
    }
    persistActiveSessionId(null);
    setState((prev) => ({ ...prev, sessionId: null }));
    setCompleteMode("ended");
    setView("complete");
  }, []);

  const enterActiveSession = useCallback(() => {
    setStepInput("");
    setFeedback(null);
    setShowFeedback(false);
    setInputError(false);
    setAttemptHistoryOpen(false);
    setGiveUpDisabled(false);
    setSubmitDisabled(false);
    setSubmitting(false);
    setAllGreenDots(false);
    setView("session");
  }, []);

  useEffect(() => {
    const storedId = readActiveSessionId();
    if (!storedId) return;

    let cancelled = false;
    setResuming(true);

    fetchSession(storedId)
      .then((data) => {
        if (cancelled) return;
        if (data.completed) {
          persistActiveSessionId(null);
          return;
        }
        setState(hydrateSessionState(data));
        enterActiveSession();
      })
      .catch(() => {
        if (cancelled) return;
        persistActiveSessionId(null);
      })
      .finally(() => {
        if (!cancelled) setResuming(false);
      });

    return () => {
      cancelled = true;
    };
  }, [enterActiveSession]);

  const handleStartSession = useCallback(async () => {
    const expression = problemInput.trim();
    if (!expression) {
      setProblemError("Please enter a problem expression.");
      return;
    }
    if (containsTextLikeInput(expression)) {
      setProblemError("Plain text and word-like input are not allowed. Use math notation.");
      return;
    }
    setProblemError(null);
    setProblemLoading(true);
    try {
      const data = await startSessionWithExpression(expression);
      if (!data.session_id?.trim()) {
        setProblemError(data.message || "Could not start a session. Please try again.");
        return;
      }
      setState((prev) => applyStartSessionData(prev, data));
      persistActiveSessionId(data.session_id);
      enterActiveSession();
    } catch (err) {
      setProblemError(friendlyErrorMessage(err));
    } finally {
      setProblemLoading(false);
    }
  }, [problemInput, enterActiveSession]);

  const handleTryExample = useCallback(async () => {
    setProblemError(null);
    setProblemLoading(true);
    try {
      const sample = await getSampleProblem();
      setProblemInput(sample.expression);
      const data = await startSessionWithProblemId(sample.id);
      setState((prev) => applyStartSessionData(prev, data, sample.topic ?? ""));
      persistActiveSessionId(data.session_id);
      enterActiveSession();
    } catch (err) {
      setProblemError(friendlyErrorMessage(err));
    } finally {
      setProblemLoading(false);
    }
  }, [enterActiveSession]);

  const handleSelectStarter = useCallback(
    async (problemId: string) => {
      setProblemError(null);
      setProblemLoading(true);
      try {
        const problem = await fetchProblem(problemId);
        setProblemInput(problem.expression);
        const data = await startSessionWithProblemId(problemId);
        setState((prev) => applyStartSessionData(prev, data, problem.topic ?? ""));
        persistActiveSessionId(data.session_id);
        enterActiveSession();
      } catch (err) {
        setProblemError(friendlyErrorMessage(err));
      } finally {
        setProblemLoading(false);
      }
    },
    [enterActiveSession]
  );

  const handleSubmitStep = useCallback(async () => {
    const step = stepInput.trim();
    if (!step) {
      setInputError(true);
      return;
    }
    setInputError(false);
    setSubmitDisabled(true);
    setSubmitting(true);
    setGiveUpDisabled(true);

    const current = stateRef.current;
    if (!current.sessionId?.trim()) {
      setShowFeedback(true);
      setFeedback({
        isEquivalent: false,
        isInputError: false,
        hint: "No active session. Go back and start a new problem.",
        showDeeperHint: false,
        requestFailed: true,
      });
      return;
    }

    let sessionComplete = current.sessionComplete;

    try {
      const result = await submitStep(current.sessionId, step);
      const errorType = result.error_classification?.error_type ?? null;
      const isInputErr = isInputErrorType(errorType);

      let nextState = { ...current };
      if (result.step_count) nextState.stepCount = result.step_count;

      nextState = {
        ...nextState,
        attemptHistory: [
          ...nextState.attemptHistory,
          {
            step,
            stepOrder: result.step_index || nextState.stepIndex,
            hint: result.hint,
            isEquivalent: result.is_equivalent,
            isInputError: isInputErr,
          },
        ],
      };

      if (result.is_equivalent) {
        nextState.totalAttempts += 1;
        nextState.currentExpression = result.current_expression || step;

        if (result.session_complete) {
          nextState.stepIndex = result.step_index || nextState.stepCount;
          nextState.sessionComplete = true;
          sessionComplete = true;
          stateRef.current = nextState;
          setState(nextState);
          setFeedback(feedbackFromResult(result, nextState.incorrectAttemptCount));
          setShowFeedback(true);
          setAllGreenDots(true);
          setTimeout(showCompleteSolved, 1200);
          return;
        }

        nextState.stepIndex = (result.step_index || nextState.stepIndex) + 1;
        nextState.incorrectAttemptCount = 0;
      } else if (countsTowardAttemptLimit(errorType)) {
        nextState.incorrectAttemptCount += 1;
        nextState.totalAttempts += 1;
      }

      if (nextState.incorrectAttemptCount >= MAX_ATTEMPTS_BEFORE_REVEAL) {
        nextState.sessionComplete = true;
        sessionComplete = true;
      }

      stateRef.current = nextState;
      setState(nextState);
      setFeedback(feedbackFromResult(result, nextState.incorrectAttemptCount));
      setShowFeedback(true);
      setAllGreenDots(false);

      if (sessionComplete && !result.session_complete) {
        setTimeout(showCompleteEnded, 1500);
        return;
      }

      if (!isInputErr) setStepInput("");
    } catch (err) {
      setShowFeedback(true);
      setFeedback({
        isEquivalent: false,
        isInputError: false,
        hint: friendlyErrorMessage(err),
        showDeeperHint: false,
        requestFailed: true,
      });
    } finally {
      setSubmitting(false);
      setSubmitDisabled(sessionComplete);
      if (!sessionComplete) {
        setGiveUpDisabled(false);
        requestAnimationFrame(() => document.getElementById("step-input")?.focus());
      }
    }
  }, [stepInput, showCompleteSolved, showCompleteEnded]);

  const handleGiveUp = useCallback(async () => {
    if (
      !window.confirm("Are you sure? This will reveal the answer and end your session.")
    ) {
      return;
    }

    const current = stateRef.current;
    if (!current.sessionId) return;

    setGiveUpDisabled(true);
    setSubmitDisabled(true);

    try {
      const [sessionData, problemData] = await Promise.all([
        fetchSession(current.sessionId),
        fetchProblem(current.problemId),
      ]);

      const incorrectAttemptCount = (sessionData.attempt_history || []).filter(
        (attempt) =>
          !attempt.is_equivalent &&
          countsTowardAttemptLimit(attempt.error_type ?? null)
      ).length;

      setState((prev) => ({
        ...prev,
        problemExpression:
          sessionData.problem_expression ||
          problemData.expression ||
          prev.problemExpression,
        expectedFinal: problemData.expected_final || prev.expectedFinal,
        currentExpression: sessionData.current_expression || prev.currentExpression,
        incorrectAttemptCount,
        sessionComplete: true,
      }));

      await showCompleteEnded();
    } catch (err) {
      setShowFeedback(true);
      setFeedback({
        isEquivalent: false,
        isInputError: false,
        hint: friendlyErrorMessage(err),
        showDeeperHint: false,
        requestFailed: true,
        bannerOverride: "Could not reveal solution",
      });
      setGiveUpDisabled(false);
      setSubmitDisabled(false);
    }
  }, [showCompleteEnded]);

  const handleTryAnother = useCallback(() => {
    persistActiveSessionId(null);
    setState(initialSessionState());
    setProblemInput("");
    setStepInput("");
    setFeedback(null);
    setShowFeedback(false);
    setCompleteMode(null);
    setAllGreenDots(false);
    setView("selection");
  }, []);

  const applyExpression = useCallback(
    (expression: string) => {
      const trimmed = expression.trim();
      if (!trimmed) return;

      if (view === "selection") {
        setProblemInput(trimmed);
        requestAnimationFrame(() => document.getElementById("problem-input")?.focus());
        return;
      }

      if (view === "session") {
        setStepInput(trimmed);
        requestAnimationFrame(() => document.getElementById("step-input")?.focus());
      }
    },
    [view]
  );

  return {
    view,
    state,
    completeMode,
    feedback,
    showFeedback,
    problemInput,
    setProblemInput,
    stepInput,
    setStepInput,
    problemLoading,
    problemError,
    inputError,
    submitDisabled: submitDisabled || state.sessionComplete,
    submitting,
    giveUpDisabled,
    resuming,
    attemptHistoryOpen,
    setAttemptHistoryOpen,
    allGreenDots,
    handleStartSession,
    handleTryExample,
    handleSelectStarter,
    handleSubmitStep,
    handleGiveUp,
    handleTryAnother,
    applyExpression,
  };
}
