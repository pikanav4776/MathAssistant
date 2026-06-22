import type {
  AuthResponse,
  ProblemResponse,
  SessionSummary,
  StartSessionResponse,
  StepResult,
  UserProfile,
} from "../types/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

const TOKEN_STORAGE_KEY = "mathassistant_auth_token";

let authToken: string | null =
  typeof localStorage !== "undefined" ? localStorage.getItem(TOKEN_STORAGE_KEY) : null;

export function getAuthToken(): string | null {
  return authToken;
}

export function setAuthToken(token: string | null): void {
  authToken = token;
  if (typeof localStorage === "undefined") return;
  if (token) localStorage.setItem(TOKEN_STORAGE_KEY, token);
  else localStorage.removeItem(TOKEN_STORAGE_KEY);
}

function buildHeaders(includeJson = true): HeadersInit {
  const headers: Record<string, string> = {};
  if (includeJson) headers["Content-Type"] = "application/json";
  if (authToken) headers.Authorization = `Bearer ${authToken}`;
  return headers;
}

async function parseResponse<T>(response: Response): Promise<T> {
  const data: unknown = await response.json();
  if (!response.ok) {
    const detail =
      data !== null && typeof data === "object" && "detail" in data
        ? (data as { detail: unknown }).detail
        : data;

    if (typeof detail === "string") throw new Error(detail);
    if (detail !== null && typeof detail === "object") {
      const obj = detail as Record<string, unknown>;
      if (typeof obj.message === "string") throw new Error(obj.message);
      if (obj.error === "unsupported_problem" && typeof obj.message === "string") {
        throw new Error(obj.message);
      }
      if (typeof obj.error === "string") throw new Error(obj.error);
    }
    throw new Error("Request failed.");
  }
  return data as T;
}

export async function registerAccount(
  email: string,
  password: string,
  displayName?: string
): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: buildHeaders(),
    body: JSON.stringify({
      email,
      password,
      display_name: displayName || null,
    }),
  });
  return parseResponse<AuthResponse>(response);
}

export async function loginAccount(email: string, password: string): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: buildHeaders(),
    body: JSON.stringify({ email, password }),
  });
  return parseResponse<AuthResponse>(response);
}

export async function fetchCurrentUser(): Promise<UserProfile> {
  const response = await fetch(`${API_BASE}/auth/me`, {
    headers: buildHeaders(false),
  });
  return parseResponse<UserProfile>(response);
}

export async function getSampleProblem(): Promise<ProblemResponse> {
  const response = await fetch(`${API_BASE}/sample-problem`, {
    headers: buildHeaders(false),
  });
  return parseResponse<ProblemResponse>(response);
}

export async function startSessionWithExpression(
  expression: string
): Promise<StartSessionResponse> {
  const response = await fetch(`${API_BASE}/start-session`, {
    method: "POST",
    headers: buildHeaders(),
    body: JSON.stringify({ problem_expression: expression }),
  });
  return parseResponse<StartSessionResponse>(response);
}

export async function startSessionWithProblemId(
  problemId: string
): Promise<StartSessionResponse> {
  const response = await fetch(`${API_BASE}/start-session`, {
    method: "POST",
    headers: buildHeaders(),
    body: JSON.stringify({ problem_id: problemId }),
  });
  return parseResponse<StartSessionResponse>(response);
}

export async function submitStep(sessionId: string, step: string): Promise<StepResult> {
  const response = await fetch(`${API_BASE}/submit-step`, {
    method: "POST",
    headers: buildHeaders(),
    body: JSON.stringify({ session_id: sessionId, step }),
  });
  return parseResponse<StepResult>(response);
}

export async function deleteSession(sessionId: string | null): Promise<void> {
  if (!sessionId) return;
  await fetch(`${API_BASE}/session/${sessionId}`, {
    method: "DELETE",
    headers: buildHeaders(false),
  });
}

export async function fetchSession(sessionId: string): Promise<SessionSummary> {
  const response = await fetch(`${API_BASE}/session/${sessionId}`, {
    headers: buildHeaders(false),
  });
  const data = (await response.json()) as SessionSummary;
  if (!response.ok || data.error) {
    throw new Error(data.error || "Could not load session.");
  }
  return data;
}

export async function fetchProblem(problemId: string): Promise<ProblemResponse> {
  const response = await fetch(`${API_BASE}/problem/${problemId}`, {
    headers: buildHeaders(false),
  });
  return parseResponse<ProblemResponse>(response);
}