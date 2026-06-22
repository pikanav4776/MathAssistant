import { containsTextLikeInput } from "./expressionTextLike";

export type ExpressionContextHint = "problem" | "step";

export interface HeuristicResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

const TRAILING_OPERATOR_PATTERN = /(?:[+\-*/^]|<=|>=|==|!=|<|>)$/;

const V03_UNSUPPORTED_FOR_PROBLEMS = /(?:sqrt\s*\(|mod\s*\(|<=|>=|==|!=|<|>)/i;

function countParentheses(expression: string): { open: number; close: number } {
  let open = 0;
  let close = 0;
  for (const ch of expression) {
    if (ch === "(") open += 1;
    if (ch === ")") close += 1;
  }
  return { open, close };
}

export function validateExpressionHeuristic(
  expression: string,
  contextHint?: ExpressionContextHint
): HeuristicResult {
  const trimmed = expression.trim();
  const errors: string[] = [];
  const warnings: string[] = [];

  if (!trimmed) {
    return {
      isValid: false,
      errors: ["Expression is empty."],
      warnings,
    };
  }

  if (containsTextLikeInput(trimmed)) {
    errors.push("Plain text and word-like input are not allowed. Use math notation.");
  }

  const { open, close } = countParentheses(trimmed);
  if (close > open) {
    errors.push("Too many closing parentheses.");
  } else if (open > close) {
    errors.push("Unbalanced parentheses.");
  }

  if (TRAILING_OPERATOR_PATTERN.test(trimmed)) {
    warnings.push("Expression ends with an operator.");
  }

  if (contextHint === "problem" && V03_UNSUPPORTED_FOR_PROBLEMS.test(trimmed)) {
    warnings.push(
      "Comparisons, sqrt, and mod are not supported for new problems in v0.3."
    );
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings,
  };
}
