export const MAX_ATTEMPTS_BEFORE_ESCALATION = 3;
export const MAX_ATTEMPTS_BEFORE_REVEAL = 5;

export const INPUT_ERROR_TYPES = new Set([
  "invalid_input",
  "malformed_syntax",
  "invalid_format",
  "division_by_zero",
  "undefined_math",
  "undefined_symbol",
  "evaluation_timeout",
  "engine_error",
]);

export const NON_COUNTING_ERROR_TYPES = new Set(["no_progress", "term_reorder"]);

export function countsTowardAttemptLimit(errorType: string | null): boolean {
  return (
    errorType != null &&
    !INPUT_ERROR_TYPES.has(errorType) &&
    !NON_COUNTING_ERROR_TYPES.has(errorType)
  );
}

export function isInputErrorType(errorType: string | null): boolean {
  return errorType != null && INPUT_ERROR_TYPES.has(errorType);
}
