const DEFAULT_UNSUPPORTED =
  "This problem type isn't supported yet. Try distribution, FOIL, or simplification.";

const NETWORK_MESSAGE =
  "Can't reach the server. Check your connection and try again.";

const DEFAULT_MESSAGE = "Something went wrong. Please try again.";

function messageFromDetail(detail: unknown): string | null {
  if (typeof detail === "string") return detail;
  if (detail !== null && typeof detail === "object") {
    const obj = detail as Record<string, unknown>;
    if (typeof obj.message === "string") return obj.message;
    if (obj.error === "unsupported_problem") {
      return typeof obj.message === "string" ? obj.message : DEFAULT_UNSUPPORTED;
    }
    if (obj.error === "not_authenticated") {
      return "Sign in to access this session.";
    }
    if (typeof obj.error === "string") return obj.error;
  }
  return null;
}

export function friendlyErrorMessage(err: unknown): string {
  if (err instanceof TypeError && /fetch/i.test(err.message)) {
    return NETWORK_MESSAGE;
  }

  if (err instanceof Error) {
    const msg = err.message.trim();
    if (msg === "Failed to fetch") return NETWORK_MESSAGE;
    if (msg.includes("unsupported_problem") || msg.includes("isn't supported")) {
      return msg.length > 30 ? msg : DEFAULT_UNSUPPORTED;
    }
    if (msg.includes("not_authenticated") || msg.includes("Sign in to access")) {
      return "Sign in to access this session.";
    }
    if (msg) return msg;
  }

  const fromDetail = messageFromDetail(err);
  if (fromDetail) return fromDetail;

  return DEFAULT_MESSAGE;
}
