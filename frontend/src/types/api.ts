export interface ErrorClassification {
  error_type?: string;
  [key: string]: unknown;
}

export interface SkippedStepInfo {
  step_order: number;
  expected: string;
}

export interface StepResult {
  session_id: string;
  received_step: string;
  expected_step: string;
  is_equivalent: boolean;
  structural_diff: Record<string, unknown> | null;
  error_classification: ErrorClassification | null;
  hint: string;
  step_index: number | null;
  step_count: number | null;
  is_final_step: boolean | null;
  session_complete: boolean | null;
  current_expression: string | null;
  skipped_steps: SkippedStepInfo[] | null;
  skip_message: string | null;
}

export interface StartSessionResponse {
  session_id: string;
  problem_id: string;
  problem_expression: string;
  expected_final: string;
  message: string;
  subject?: string | null;
  topic?: string | null;
  current_expression?: string | null;
  step_count?: number | null;
}

export interface ProblemResponse {
  id: string;
  expression: string;
  expected_final: string;
  difficulty: string | null;
  topic: string | null;
  created_at: string;
}

export interface SessionAttemptHistoryEntry {
  step?: string;
  is_equivalent?: boolean;
  error_type?: string | null;
  hint?: string;
  [key: string]: unknown;
}

export interface SessionSummary {
  session_id: string;
  problem_id: string;
  problem_expression: string;
  attempt_count: number;
  hint_level: number;
  completed?: boolean | null;
  current_expression?: string | null;
  attempt_history: SessionAttemptHistoryEntry[];
  created_at: string;
  last_active: string;
  error?: string;
  expected_final?: string | null;
  topic?: string | null;
  step_index?: number;
  step_count?: number;
  incorrect_attempt_count?: number;
}

export interface UserSessionHistoryItem {
  session_id: string;
  problem_id: string;
  problem_expression: string;
  completed: boolean;
  revealed_solution: boolean;
  total_attempts: number;
  incorrect_attempts: number;
  duration_seconds: number | null;
  completed_at: string | null;
}

export interface StarterProblemItem {
  id: string;
  expression: string;
  difficulty: string | null;
  topic: string | null;
}

export interface CalculatorAnswerResponse {
  answer: string;
}

export interface LocalAttemptHistoryItem {
  step: string;
  stepOrder: number;
  hint?: string;
  isEquivalent: boolean;
  isInputError: boolean;
}

export type AppView = "selection" | "session" | "complete";

export type CompleteMode = "solved" | "ended" | null;

export interface FeedbackState {
  isEquivalent: boolean;
  isInputError: boolean;
  hint: string;
  showDeeperHint: boolean;
  requestFailed?: boolean;
  bannerOverride?: string;
}

export interface SessionState {
  problemId: string;
  problemExpression: string;
  expectedFinal: string;
  currentExpression: string;
  topic: string;
  sessionId: string | null;
  sessionComplete: boolean;
  incorrectAttemptCount: number;
  totalAttempts: number;
  stepIndex: number;
  stepCount: number;
  attemptHistory: LocalAttemptHistoryItem[];
}

export const initialSessionState = (): SessionState => ({
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
});
export interface UserProfile {
  id: number;
  email: string;
  display_name: string | null;
  role: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: UserProfile;
}
