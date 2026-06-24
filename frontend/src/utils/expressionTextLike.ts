const KNOWN_MATH_IDENTIFIERS = new Set([
  "pi",
  "tau",
  "sqrt",
  "mod",
  "log",
  "inv",
  "finv",
  "sin",
  "cos",
  "tan",
]);

const TEXT_ONLY_PATTERN = /^[a-zA-Z\s]+$/;

/** True when the string looks like plain text/words rather than algebra. */
export function containsTextLikeInput(expression: string): boolean {
  const trimmed = expression.trim();
  if (trimmed.length >= 3 && TEXT_ONLY_PATTERN.test(trimmed)) {
    return true;
  }

  const runs = trimmed.match(/[a-zA-Z]+/g) ?? [];
  for (const run of runs) {
    if (run === "E") continue;
    if (KNOWN_MATH_IDENTIFIERS.has(run.toLowerCase())) continue;
    if (run.length >= 4) return true;
  }

  return false;
}
