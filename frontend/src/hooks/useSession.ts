import { useCallback, useRef, useState } from "react";
import {
  deleteSession,
  fetchProblem,
  fetchSession,
  getSampleProblem,
  startSessionWithExpression,
  startSessionWithProblemId,
  submitStep,
} from "../api/client";
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
  SessionState,
  StartSessionResponse,
  StepResult,
} from "../types/api";
import { initialSessionState } from "../types/api";

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
  const [giveUpDisabled, setGiveUpDisabled] = useState(false);
  const [attemptHistoryOpen, setAttemptHistoryOpen] = useState(false);
  const [allGreenDots, setAllGreenDots] = useState(false);

  const stateRef = useRef(state);
  stateRef.current = state;

  const showCompleteSolved = useCallback(async () => {
    const current = stateRef.current;
    await deleteSession(current.sessionId);
    setState((prev) => ({ ...prev, sessionId: null }));
    setCompleteMode("solved");
    setView("complete");
  }, []);

  const showCompleteEnded = useCallback(async () => {
    const current = stateRef.current;
    await deleteSession(current.sessionId);
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
    setAllGreenDots(false);
    setView("session");
  }, []);

  const handleStartSession = useCallback(async () => {
    const expression = problemInput.trim();
    if (!expression) {
      setProblemError("Please enter a problem expression.");
      return;
    }
    setProblemError(null);
    setProblemLoading(true);
    try {
      const data = await startSessionWithExpression(expression);
      setState((prev) => applyStartSessionData(prev, data));
      enterActiveSession();
    } catch (err) {
      setProblemError(err instanceof Error ? err.message : "Could not start session.");
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
      enterActiveSession();
    } catch (err) {
      setProblemError(err instanceof Error ? err.message : "Could not load sample.");
    } finally {
      setProblemLoading(false);
    }
  }, [enterActiveSession]);

  const handleSubmitStep = useCallback(async () => {
    const step = stepInput.trim();
    if (!step) {
      setInputError(true);
      return;
    }
    setInputError(false);
    setSubmitDisabled(true);
    setGiveUpDisabled(true);

    const current = stateRef.current;
    if (!current.sessionId) return;

    let sessionComplete = current.sessionComplete;

    try {
      const result = await submitStep(current.sessionId, step);
      const errorType = result.error_classification?.error_type ?? null;
      const isInputError = isInputErrorType(errorType);

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
            isInputError,
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

      if (!isInputError) setStepInput("");
    } catch (err) {
      setShowFeedback(true);
      setFeedback({
        isEquivalent: false,
        isInputError: false,
        hint: err instanceof Error ? err.message : "Please try again.",
        showDeeperHint: false,
        requestFailed: true,
      });
    } finally {
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
        hint: err instanceof Error ? err.message : "Please try again.",
        showDeeperHint: false,
        requestFailed: true,
        bannerOverride: "⚠ Could not reveal solution",
      });
      setGiveUpDisabled(false);
      setSubmitDisabled(false);
    }
  }, [showCompleteEnded]);

  const handleTryAnother = useCallback(() => {
    setState(initialSessionState());
    setProblemInput("");
    setStepInput("");
    setFeedback(null);
    setShowFeedback(false);
    setCompleteMode(null);
    setAllGreenDots(false);
    setView("selection");
  }, []);

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
    giveUpDisabled,
    attemptHistoryOpen,
    setAttemptHistoryOpen,
    allGreenDots,
    handleStartSession,
    handleTryExample,
    handleSubmitStep,
    handleGiveUp,
    handleTryAnother,
  };
}
