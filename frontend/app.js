/* =============================================================================
   CONSTANTS
   ============================================================================= */

const API_BASE = window.API_BASE;

const MAX_ATTEMPTS_BEFORE_ESCALATION = 3;
const MAX_ATTEMPTS_BEFORE_REVEAL = 5;

const INPUT_ERROR_TYPES = new Set([
  "invalid_input",
  "malformed_syntax",
  "invalid_format",
  "division_by_zero",
  "undefined_math",
  "undefined_symbol",
  "evaluation_timeout",
  "engine_error",
]);

const ERROR_TYPE_LABELS = {
  distribution_error: "Missing terms",
  sign_error: "Sign error",
  arithmetic_error: "Arithmetic error",
  unknown: "Check your work",
};

/* =============================================================================
   STATE
   ============================================================================= */

const state = {
  currentProblem: null,
  sessionId: null,
  incorrectAttemptCount: 0,
  attemptHistory: [],
  hintLevel: 1,
  sessionComplete: false,
  totalAttempts: 0,
  endedByGiveUp: false,
};

function resetState() {
  state.currentProblem = null;
  state.sessionId = null;
  state.incorrectAttemptCount = 0;
  state.attemptHistory = [];
  state.hintLevel = 1;
  state.sessionComplete = false;
  state.totalAttempts = 0;
  state.endedByGiveUp = false;
}

/* =============================================================================
   API LAYER
   ============================================================================= */

async function parseResponse(response) {
  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error("Unexpected response from server.");
  }

  if (!response.ok) {
    const detail = data?.detail ?? data?.error ?? data?.message;
    if (typeof detail === "string") {
      throw new Error(detail);
    }
    if (detail && typeof detail === "object" && detail.error) {
      throw new Error(detail.error);
    }
    throw new Error("Request failed. Please try again.");
  }

  return data;
}

const api = {
  async getSampleProblem(difficulty, topic) {
    const params = new URLSearchParams();
    if (difficulty) params.set("difficulty", difficulty);
    if (topic) params.set("topic", topic);
    const qs = params.toString();
    const url = `${API_BASE}/sample-problem${qs ? `?${qs}` : ""}`;

    try {
      const response = await fetch(url);
      return await parseResponse(response);
    } catch (err) {
      if (err instanceof Error && err.message !== "Failed to fetch") {
        throw err;
      }
      throw new Error("Could not reach the server. Is the backend running?");
    }
  },

  async startSession(problemId) {
    try {
      const response = await fetch(`${API_BASE}/start-session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ problem_id: problemId }),
      });
      return await parseResponse(response);
    } catch (err) {
      if (err instanceof Error && err.message !== "Failed to fetch") {
        throw err;
      }
      throw new Error("Could not reach the server. Is the backend running?");
    }
  },

  async submitStep(sessionId, step, expected) {
    try {
      const response = await fetch(`${API_BASE}/submit-step`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, step, expected }),
      });
      return await parseResponse(response);
    } catch (err) {
      if (err instanceof Error && err.message !== "Failed to fetch") {
        throw err;
      }
      throw new Error("Could not reach the server. Is the backend running?");
    }
  },

  async deleteSession(sessionId) {
    try {
      const response = await fetch(`${API_BASE}/session/${sessionId}`, {
        method: "DELETE",
      });
      return await parseResponse(response);
    } catch (err) {
      console.error("Failed to delete session:", err);
      return null;
    }
  },
};

/* =============================================================================
   DOM REFERENCES
   ============================================================================= */

const views = {
  selection: document.getElementById("view-problem-selection"),
  session: document.getElementById("view-active-session"),
  complete: document.getElementById("view-session-complete"),
};

const els = {
  filterDifficulty: document.getElementById("filter-difficulty"),
  filterTopic: document.getElementById("filter-topic"),
  btnGetProblem: document.getElementById("btn-get-problem"),
  problemLoading: document.getElementById("problem-loading"),
  problemError: document.getElementById("problem-error"),
  problemCard: document.getElementById("problem-card"),
  problemExpression: document.getElementById("problem-expression"),
  problemDifficulty: document.getElementById("problem-difficulty"),
  problemTopic: document.getElementById("problem-topic"),
  btnStartSession: document.getElementById("btn-start-session"),
  startSessionError: document.getElementById("start-session-error"),
  sessionExpression: document.getElementById("session-expression"),
  sessionDifficulty: document.getElementById("session-difficulty"),
  sessionTopic: document.getElementById("session-topic"),
  attemptLabel: document.getElementById("attempt-label"),
  attemptDots: document.getElementById("attempt-dots"),
  stepInput: document.getElementById("step-input"),
  inputError: document.getElementById("input-error"),
  btnSubmitStep: document.getElementById("btn-submit-step"),
  feedbackPanel: document.getElementById("feedback-panel"),
  feedbackBanner: document.getElementById("feedback-banner"),
  deeperHintLabel: document.getElementById("deeper-hint-label"),
  feedbackHint: document.getElementById("feedback-hint"),
  attemptHistory: document.getElementById("attempt-history"),
  attemptHistoryList: document.getElementById("attempt-history-list"),
  btnGiveUp: document.getElementById("btn-give-up"),
  completeSolved: document.getElementById("complete-solved"),
  completeEnded: document.getElementById("complete-ended"),
  completeSolvedExpression: document.getElementById("complete-solved-expression"),
  completeSolvedAnswer: document.getElementById("complete-solved-answer"),
  completeSolvedStats: document.getElementById("complete-solved-stats"),
  completeEndedAnswer: document.getElementById("complete-ended-answer"),
  completeEndedStats: document.getElementById("complete-ended-stats"),
  btnTryAnother: document.getElementById("btn-try-another"),
};

/* =============================================================================
   VIEW SWITCHING
   ============================================================================= */

function showView(name) {
  Object.values(views).forEach((view) => view.classList.add("hidden"));
  views[name].classList.remove("hidden");
}

/* =============================================================================
   HELPERS
   ============================================================================= */

function isInputError(errorType) {
  return errorType != null && INPUT_ERROR_TYPES.has(errorType);
}

function setBadge(el, difficulty) {
  el.textContent = difficulty || "—";
  el.className = "badge";
  if (difficulty) {
    el.classList.add(`badge--${difficulty.toLowerCase()}`);
  }
}

function renderProblemCard(problem) {
  els.problemExpression.textContent = problem.expression;
  setBadge(els.problemDifficulty, problem.difficulty);
  els.problemTopic.textContent = problem.topic || "—";
  els.problemCard.classList.remove("hidden");
}

function updateAttemptTracker(allGreen = false) {
  const nextAttempt = state.incorrectAttemptCount + 1;
  els.attemptLabel.textContent = `Attempt ${Math.min(nextAttempt, MAX_ATTEMPTS_BEFORE_REVEAL)} of ${MAX_ATTEMPTS_BEFORE_REVEAL}`;

  const dots = els.attemptDots.querySelectorAll(".dot");
  dots.forEach((dot, index) => {
    dot.classList.remove("dot--filled", "dot--success");
    if (allGreen) {
      dot.classList.add("dot--success");
    } else if (index < state.incorrectAttemptCount) {
      dot.classList.add("dot--filled");
    }
  });
}

function renderAttemptHistory() {
  els.attemptHistoryList.innerHTML = "";
  const items = [...state.attemptHistory].reverse();

  if (items.length === 0) {
    const li = document.createElement("li");
    li.className = "attempt-history-item";
    li.textContent = "No attempts yet.";
    els.attemptHistoryList.appendChild(li);
    return;
  }

  items.forEach((item) => {
    const li = document.createElement("li");
    li.className = "attempt-history-item";

    const mark = item.is_equivalent ? "✓" : item.isInputError ? "⚠" : "✗";
    li.innerHTML = `
      <div class="attempt-history-step">${mark} ${escapeHtml(item.step)}</div>
      <div class="attempt-history-meta">${escapeHtml(item.hint || "")}</div>
    `;
    els.attemptHistoryList.appendChild(li);
  });
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function showFeedback(result) {
  const errorType = result.error_classification?.error_type ?? null;
  const inputError = isInputError(errorType);

  els.feedbackPanel.classList.remove("hidden");
  els.feedbackBanner.className = "feedback-banner";
  els.deeperHintLabel.classList.add("hidden");

  if (result.is_equivalent) {
    els.feedbackBanner.classList.add("feedback-banner--correct");
    els.feedbackBanner.textContent = "✓ Correct!";
    els.feedbackHint.textContent = result.hint || "";
    return;
  }

  if (inputError) {
    els.feedbackBanner.classList.add("feedback-banner--warning");
    els.feedbackBanner.textContent = "⚠ Input error";
    els.feedbackHint.textContent = result.hint || "";
    return;
  }

  els.feedbackBanner.classList.add("feedback-banner--incorrect");
  const label = ERROR_TYPE_LABELS[errorType] || "Check your work";
  els.feedbackBanner.innerHTML = `✗ Not quite. <span class="error-badge">${escapeHtml(label)}</span>`;

  if (state.hintLevel >= 2) {
    els.deeperHintLabel.classList.remove("hidden");
  }

  els.feedbackHint.textContent = result.hint || "";
}

function setSubmitLoading(loading) {
  els.btnSubmitStep.disabled = loading;
  els.stepInput.disabled = loading;
}

function setProblemLoading(loading) {
  els.btnGetProblem.disabled = loading;
  els.btnStartSession.disabled = loading;
  els.problemLoading.classList.toggle("hidden", !loading);
}

/* =============================================================================
   VIEW 1 — PROBLEM SELECTION
   ============================================================================= */

async function loadProblem() {
  els.problemError.classList.add("hidden");
  els.startSessionError.classList.add("hidden");
  els.problemCard.classList.add("hidden");
  els.btnStartSession.disabled = false;
  setProblemLoading(true);

  try {
    const difficulty = els.filterDifficulty.value;
    const topic = els.filterTopic.value;
    const problem = await api.getSampleProblem(difficulty, topic);
    state.currentProblem = problem;
    renderProblemCard(problem);
  } catch (err) {
    els.problemError.classList.remove("hidden");
  } finally {
    setProblemLoading(false);
  }
}

async function handleStartSession() {
  if (!state.currentProblem) return;

  els.startSessionError.classList.add("hidden");
  els.btnStartSession.disabled = true;

  try {
    const data = await api.startSession(state.currentProblem.id);
    state.sessionId = data.session_id;
    state.currentProblem = {
      id: data.problem_id,
      expression: data.problem_expression,
      expected_final: data.expected_final,
      difficulty: state.currentProblem.difficulty,
      topic: state.currentProblem.topic,
    };
    enterActiveSession();
  } catch {
    els.startSessionError.classList.remove("hidden");
    els.btnStartSession.disabled = false;
  }
}

/* =============================================================================
   VIEW 2 — ACTIVE SESSION
   ============================================================================= */

function enterActiveSession() {
  const problem = state.currentProblem;
  els.sessionExpression.textContent = problem.expression;
  setBadge(els.sessionDifficulty, problem.difficulty);
  els.sessionTopic.textContent = problem.topic || "—";

  els.stepInput.value = "";
  els.inputError.classList.add("hidden");
  els.feedbackPanel.classList.add("hidden");
  els.attemptHistory.open = false;

  updateAttemptTracker();
  renderAttemptHistory();
  showView("session");
  els.stepInput.focus();
}

async function handleSubmitStep() {
  const step = els.stepInput.value.trim();

  if (!step) {
    els.inputError.classList.remove("hidden");
    return;
  }
  els.inputError.classList.add("hidden");

  setSubmitLoading(true);

  try {
    const result = await api.submitStep(
      state.sessionId,
      step,
      state.currentProblem.expected_final
    );

    const errorType = result.error_classification?.error_type ?? null;
    const inputError = isInputError(errorType);

    state.attemptHistory.push({
      step,
      is_equivalent: result.is_equivalent,
      error_type: errorType,
      hint: result.hint,
      isInputError: inputError,
    });

    if (result.is_equivalent) {
      state.totalAttempts += 1;
      state.sessionComplete = true;
      showFeedback(result);
      updateAttemptTracker(true);
      renderAttemptHistory();
      setTimeout(() => finishSessionSolved(), 1500);
      return;
    }

    if (!inputError) {
      state.incorrectAttemptCount += 1;
      state.totalAttempts += 1;

      if (state.incorrectAttemptCount >= MAX_ATTEMPTS_BEFORE_ESCALATION) {
        state.hintLevel = 2;
      }
    }

    showFeedback(result);
    updateAttemptTracker();
    renderAttemptHistory();

    if (!inputError) {
      els.stepInput.value = "";
    }

    if (state.incorrectAttemptCount >= MAX_ATTEMPTS_BEFORE_REVEAL) {
      state.sessionComplete = true;
      setTimeout(() => finishSessionEnded(), 2000);
    }
  } catch (err) {
    els.feedbackPanel.classList.remove("hidden");
    els.feedbackBanner.className = "feedback-banner feedback-banner--warning";
    els.feedbackBanner.textContent = "⚠ Request failed";
    els.feedbackHint.textContent =
      err instanceof Error ? err.message : "Please try again.";
    els.deeperHintLabel.classList.add("hidden");
  } finally {
    setSubmitLoading(false);
    if (!state.sessionComplete) {
      els.stepInput.focus();
    }
  }
}

function handleGiveUp() {
  const confirmed = window.confirm(
    "Are you sure? This will end your session."
  );
  if (!confirmed) return;

  state.endedByGiveUp = true;
  state.sessionComplete = true;

  els.feedbackPanel.classList.remove("hidden");
  els.feedbackBanner.className = "feedback-banner feedback-banner--incorrect";
  els.feedbackBanner.textContent = "✗ Session ended";
  els.deeperHintLabel.classList.add("hidden");
  els.feedbackHint.textContent = `The correct answer was: ${state.currentProblem.expected_final}`;

  setTimeout(() => finishSessionEnded(), 2000);
}

/* =============================================================================
   VIEW 3 — SESSION COMPLETE
   ============================================================================= */

async function finishSessionSolved() {
  if (state.sessionId) {
    await api.deleteSession(state.sessionId);
  }
  showCompleteSolved();
}

async function finishSessionEnded() {
  if (state.sessionId) {
    await api.deleteSession(state.sessionId);
  }
  showCompleteEnded();
}

function showCompleteSolved() {
  const problem = state.currentProblem;
  els.completeSolvedExpression.textContent = `You simplified: ${problem.expression}`;
  els.completeSolvedAnswer.textContent = `Answer: ${problem.expected_final}`;
  const attempts = state.totalAttempts;
  els.completeSolvedStats.textContent = `Solved in ${attempts} attempt${attempts === 1 ? "" : "s"}`;

  els.completeSolved.classList.remove("hidden");
  els.completeEnded.classList.add("hidden");
  showView("complete");
}

function showCompleteEnded() {
  const problem = state.currentProblem;
  els.completeEndedAnswer.textContent = `The correct answer was: ${problem.expected_final}`;
  els.completeEndedStats.textContent = `You made ${state.incorrectAttemptCount} incorrect attempt${state.incorrectAttemptCount === 1 ? "" : "s"}`;

  els.completeEnded.classList.remove("hidden");
  els.completeSolved.classList.add("hidden");
  showView("complete");
}

async function handleTryAnother() {
  resetState();
  els.completeSolved.classList.add("hidden");
  els.completeEnded.classList.add("hidden");
  showView("selection");
  await loadProblem();
}

/* =============================================================================
   INITIALIZATION
   ============================================================================= */

els.btnGetProblem.addEventListener("click", loadProblem);
els.btnStartSession.addEventListener("click", handleStartSession);
els.btnSubmitStep.addEventListener("click", handleSubmitStep);
els.btnGiveUp.addEventListener("click", handleGiveUp);
els.btnTryAnother.addEventListener("click", handleTryAnother);

els.stepInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !els.btnSubmitStep.disabled) {
    handleSubmitStep();
  }
});

loadProblem();
