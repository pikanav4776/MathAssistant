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

const NON_COUNTING_ERROR_TYPES = new Set(["no_progress", "term_reorder"]);

const state = {
  problemId: "",
  problemExpression: "",
  expectedFinal: "",
  currentExpression: "",
  topic: "",
  sessionId: null,
  sessionComplete: false,
  incorrectAttemptCount: 0,
  totalAttempts: 0,
  stepIndex: 1,
  stepCount: 1,
  attemptHistory: [],
};

const views = {
  selection: document.getElementById("view-problem-selection"),
  session: document.getElementById("view-active-session"),
  complete: document.getElementById("view-session-complete"),
};

const els = {
  problemInput: document.getElementById("problem-input"),
  btnStartSession: document.getElementById("btn-start-session"),
  btnGetProblem: document.getElementById("btn-get-problem"),
  problemLoading: document.getElementById("problem-loading"),
  problemError: document.getElementById("problem-error"),
  sessionExpression: document.getElementById("session-expression"),
  sessionTopic: document.getElementById("session-topic"),
  sessionStepCounter: document.getElementById("session-step-counter"),
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
  completeEndedExpression: document.getElementById("complete-ended-expression"),
  completeEndedAnswer: document.getElementById("complete-ended-answer"),
  completeEndedStats: document.getElementById("complete-ended-stats"),
  btnTryAnother: document.getElementById("btn-try-another"),
};

function countsTowardAttemptLimit(errorType) {
  return (
    errorType != null &&
    !INPUT_ERROR_TYPES.has(errorType) &&
    !NON_COUNTING_ERROR_TYPES.has(errorType)
  );
}

function resetState() {
  state.problemId = "";
  state.problemExpression = "";
  state.expectedFinal = "";
  state.currentExpression = "";
  state.topic = "";
  state.sessionId = null;
  state.sessionComplete = false;
  state.incorrectAttemptCount = 0;
  state.totalAttempts = 0;
  state.stepIndex = 1;
  state.stepCount = 1;
  state.attemptHistory = [];
}

function showView(name) {
  Object.values(views).forEach((view) => view.classList.add("hidden"));
  views[name].classList.remove("hidden");
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function updateAttemptTracker(allGreen = false) {
  const nextAttempt = state.incorrectAttemptCount + 1;
  els.attemptLabel.textContent = `Attempt ${Math.min(
    nextAttempt,
    MAX_ATTEMPTS_BEFORE_REVEAL
  )} of ${MAX_ATTEMPTS_BEFORE_REVEAL}`;

  const dots = els.attemptDots.querySelectorAll(".dot");
  dots.forEach((dot, index) => {
    dot.classList.remove("dot--filled", "dot--success");
    if (allGreen) dot.classList.add("dot--success");
    else if (index < state.incorrectAttemptCount) dot.classList.add("dot--filled");
  });
}

function renderAttemptHistory() {
  els.attemptHistoryList.innerHTML = "";
  const items = [...state.attemptHistory].reverse();
  if (!items.length) {
    const li = document.createElement("li");
    li.className = "attempt-history-item";
    li.textContent = "No attempts yet.";
    els.attemptHistoryList.appendChild(li);
    return;
  }

  items.forEach((item) => {
    const li = document.createElement("li");
    li.className = "attempt-history-item";
    const mark = item.isEquivalent ? "✓" : item.isInputError ? "⚠" : "✗";
    li.innerHTML = `
      <div class="attempt-history-step">${mark} [Step ${item.stepOrder}] ${escapeHtml(
      item.step
    )}</div>
      <div class="attempt-history-meta">${escapeHtml(item.hint || "")}</div>
    `;
    els.attemptHistoryList.appendChild(li);
  });
}

function showFeedback(result) {
  const errorType = result.error_classification?.error_type ?? null;
  const inputError = errorType != null && INPUT_ERROR_TYPES.has(errorType);
  els.feedbackPanel.classList.remove("hidden");
  els.feedbackBanner.className = "feedback-banner";
  els.deeperHintLabel.classList.add("hidden");

  if (result.is_equivalent) {
    els.feedbackBanner.classList.add("feedback-banner--correct");
    els.feedbackBanner.textContent = "✓ Correct!";
  } else if (inputError) {
    els.feedbackBanner.classList.add("feedback-banner--warning");
    els.feedbackBanner.textContent = "⚠ Input error";
  } else {
    els.feedbackBanner.classList.add("feedback-banner--incorrect");
    els.feedbackBanner.textContent = "✗ Not quite.";
    if (state.incorrectAttemptCount >= MAX_ATTEMPTS_BEFORE_ESCALATION) {
      els.deeperHintLabel.classList.remove("hidden");
    }
  }
  els.feedbackHint.textContent = result.skip_message || result.hint || "";
}

async function parseResponse(response) {
  const data = await response.json();
  if (!response.ok) {
    const detail = data?.detail ?? data;
    if (typeof detail === "string") throw new Error(detail);
    if (detail?.message) throw new Error(detail.message);
    if (detail?.error === "unsupported_problem" && detail?.message) {
      throw new Error(detail.message);
    }
    if (detail?.error) throw new Error(detail.error);
    throw new Error("Request failed.");
  }
  return data;
}

async function startSessionWithExpression(expression) {
  const response = await fetch(`${API_BASE}/start-session`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ problem_expression: expression }),
  });
  return parseResponse(response);
}

async function startSessionWithProblemId(problemId) {
  const response = await fetch(`${API_BASE}/start-session`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ problem_id: problemId }),
  });
  return parseResponse(response);
}

async function getSampleProblem() {
  const response = await fetch(`${API_BASE}/sample-problem`);
  return parseResponse(response);
}

async function submitStep(sessionId, step) {
  const response = await fetch(`${API_BASE}/submit-step`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, step }),
  });
  return parseResponse(response);
}

async function deleteSession(sessionId) {
  if (!sessionId) return;
  await fetch(`${API_BASE}/session/${sessionId}`, { method: "DELETE" });
}

async function fetchSession(sessionId) {
  const response = await fetch(`${API_BASE}/session/${sessionId}`);
  const data = await response.json();
  if (!response.ok || data.error) {
    throw new Error(data.error || "Could not load session.");
  }
  return data;
}

async function fetchProblem(problemId) {
  const response = await fetch(`${API_BASE}/problem/${problemId}`);
  return parseResponse(response);
}

function applyStartSessionData(data, fallbackTopic = "") {
  state.problemId = data.problem_id || "";
  state.problemExpression = data.problem_expression;
  state.expectedFinal = data.expected_final;
  state.currentExpression = data.current_expression || data.problem_expression;
  state.sessionId = data.session_id;
  state.topic = data.topic || fallbackTopic || "algebra";
  state.stepCount = data.step_count || 1;
  state.stepIndex = 1;
  state.incorrectAttemptCount = 0;
  state.totalAttempts = 0;
  state.attemptHistory = [];
  state.sessionComplete = false;
}

function syncStepCounter() {
  els.sessionStepCounter.textContent = `Step ${Math.min(
    state.stepIndex,
    state.stepCount
  )}/${state.stepCount}`;
}

function enterActiveSession() {
  els.sessionExpression.textContent = state.currentExpression;
  els.sessionTopic.textContent = state.topic || "algebra";
  syncStepCounter();
  els.stepInput.value = "";
  els.feedbackPanel.classList.add("hidden");
  els.inputError.classList.add("hidden");
  els.attemptHistory.open = false;
  els.btnGiveUp.disabled = false;
  updateAttemptTracker();
  renderAttemptHistory();
  showView("session");
  els.stepInput.focus();
}

async function handleStartSession() {
  const expression = els.problemInput.value.trim();
  if (!expression) {
    els.problemError.textContent = "Please enter a problem expression.";
    els.problemError.classList.remove("hidden");
    return;
  }
  els.problemError.classList.add("hidden");
  els.problemLoading.classList.remove("hidden");
  els.btnStartSession.disabled = true;
  els.btnGetProblem.disabled = true;
  try {
    const data = await startSessionWithExpression(expression);
    applyStartSessionData(data);
    enterActiveSession();
  } catch (err) {
    els.problemError.textContent = err instanceof Error ? err.message : "Could not start session.";
    els.problemError.classList.remove("hidden");
  } finally {
    els.problemLoading.classList.add("hidden");
    els.btnStartSession.disabled = false;
    els.btnGetProblem.disabled = false;
  }
}

async function handleTryExample() {
  els.problemError.classList.add("hidden");
  els.problemLoading.classList.remove("hidden");
  els.btnStartSession.disabled = true;
  els.btnGetProblem.disabled = true;
  try {
    const sample = await getSampleProblem();
    els.problemInput.value = sample.expression;
    const data = await startSessionWithProblemId(sample.id);
    applyStartSessionData(data, sample.topic);
    enterActiveSession();
  } catch (err) {
    els.problemError.textContent = err instanceof Error ? err.message : "Could not load sample.";
    els.problemError.classList.remove("hidden");
  } finally {
    els.problemLoading.classList.add("hidden");
    els.btnStartSession.disabled = false;
    els.btnGetProblem.disabled = false;
  }
}

async function handleSubmitStep() {
  const step = els.stepInput.value.trim();
  if (!step) {
    els.inputError.classList.remove("hidden");
    return;
  }
  els.inputError.classList.add("hidden");
  els.btnSubmitStep.disabled = true;
  els.stepInput.disabled = true;
  els.btnGiveUp.disabled = true;
  try {
    const result = await submitStep(state.sessionId, step);
    const errorType = result.error_classification?.error_type ?? null;
    const isInputError = errorType != null && INPUT_ERROR_TYPES.has(errorType);
    if (result.step_count) state.stepCount = result.step_count;
    state.attemptHistory.push({
      step,
      stepOrder: result.step_index || state.stepIndex,
      hint: result.hint,
      isEquivalent: result.is_equivalent,
      isInputError,
    });
    if (result.is_equivalent) {
      state.totalAttempts += 1;
      state.currentExpression = result.current_expression || step;
      if (result.session_complete) {
        state.stepIndex = result.step_index || state.stepCount;
        state.sessionComplete = true;
        showFeedback(result);
        updateAttemptTracker(true);
        renderAttemptHistory();
        setTimeout(showCompleteSolved, 1200);
        return;
      }
      state.stepIndex = (result.step_index || state.stepIndex) + 1;
      state.incorrectAttemptCount = 0;
    } else if (countsTowardAttemptLimit(errorType)) {
      state.incorrectAttemptCount += 1;
      state.totalAttempts += 1;
    }

    showFeedback(result);
    renderAttemptHistory();
    updateAttemptTracker();
    els.sessionExpression.textContent = state.currentExpression;
    syncStepCounter();
    if (state.incorrectAttemptCount >= MAX_ATTEMPTS_BEFORE_REVEAL) {
      state.sessionComplete = true;
      setTimeout(showCompleteEnded, 1500);
      return;
    }
    if (!isInputError) els.stepInput.value = "";
  } catch (err) {
    els.feedbackPanel.classList.remove("hidden");
    els.feedbackBanner.className = "feedback-banner feedback-banner--warning";
    els.feedbackBanner.textContent = "⚠ Request failed";
    els.feedbackHint.textContent = err instanceof Error ? err.message : "Please try again.";
  } finally {
    els.btnSubmitStep.disabled = state.sessionComplete;
    els.stepInput.disabled = state.sessionComplete;
    if (!state.sessionComplete) {
      els.btnGiveUp.disabled = false;
      els.stepInput.focus();
    }
  }
}

async function handleGiveUp() {
  if (!window.confirm("Are you sure? This will reveal the answer and end your session.")) {
    return;
  }
  els.btnGiveUp.disabled = true;
  els.btnSubmitStep.disabled = true;
  els.stepInput.disabled = true;
  try {
    const [sessionData, problemData] = await Promise.all([
      fetchSession(state.sessionId),
      fetchProblem(state.problemId),
    ]);
    state.problemExpression =
      sessionData.problem_expression || problemData.expression || state.problemExpression;
    state.expectedFinal = problemData.expected_final || state.expectedFinal;
    state.currentExpression = sessionData.current_expression || state.currentExpression;
    state.incorrectAttemptCount = (sessionData.attempt_history || []).filter(
      (attempt) =>
        !attempt.is_equivalent &&
        countsTowardAttemptLimit(attempt.error_type ?? null)
    ).length;
    state.sessionComplete = true;
    await showCompleteEnded();
  } catch (err) {
    els.feedbackPanel.classList.remove("hidden");
    els.feedbackBanner.className = "feedback-banner feedback-banner--warning";
    els.feedbackBanner.textContent = "⚠ Could not reveal solution";
    els.feedbackHint.textContent = err instanceof Error ? err.message : "Please try again.";
    els.btnGiveUp.disabled = false;
    els.btnSubmitStep.disabled = false;
    els.stepInput.disabled = false;
  }
}

async function showCompleteSolved() {
  await deleteSession(state.sessionId);
  state.sessionId = null;
  els.completeSolvedExpression.textContent = `Problem: ${state.problemExpression}`;
  els.completeSolvedAnswer.textContent = `Final: ${state.expectedFinal}`;
  els.completeSolvedStats.textContent = `Solved in ${state.totalAttempts} attempt${
    state.totalAttempts === 1 ? "" : "s"
  }.`;
  els.completeSolved.classList.remove("hidden");
  els.completeEnded.classList.add("hidden");
  showView("complete");
}

async function showCompleteEnded() {
  await deleteSession(state.sessionId);
  state.sessionId = null;
  els.completeEndedExpression.textContent = `Problem: ${state.problemExpression}`;
  els.completeEndedAnswer.textContent = `Final answer: ${state.expectedFinal}`;
  els.completeEndedStats.textContent = `Incorrect attempts: ${state.incorrectAttemptCount}.`;
  els.completeEnded.classList.remove("hidden");
  els.completeSolved.classList.add("hidden");
  showView("complete");
}

function handleTryAnother() {
  resetState();
  els.problemInput.value = "";
  els.completeSolved.classList.add("hidden");
  els.completeEnded.classList.add("hidden");
  showView("selection");
}

els.btnStartSession.addEventListener("click", handleStartSession);
els.btnGetProblem.addEventListener("click", handleTryExample);
els.btnSubmitStep.addEventListener("click", handleSubmitStep);
els.btnGiveUp.addEventListener("click", handleGiveUp);
els.btnTryAnother.addEventListener("click", handleTryAnother);
els.problemInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !els.btnStartSession.disabled) handleStartSession();
});
els.stepInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !els.btnSubmitStep.disabled) handleSubmitStep();
});
