export type TokenCategory =
  | "digit"
  | "operator"
  | "comparison"
  | "function"
  | "constant"
  | "variable";

export interface ExpressionToken {
  label: string;
  value: string;
  category: TokenCategory;
  ariaLabel?: string;
  title?: string;
}

function digit(label: string): ExpressionToken {
  return { label, value: label, category: "digit" };
}

function variable(letter: string): ExpressionToken {
  return {
    label: letter,
    value: letter,
    category: "variable",
    ariaLabel: `variable ${letter}`,
  };
}

function operator(label: string, value: string, ariaLabel?: string): ExpressionToken {
  return { label, value, category: "operator", ariaLabel };
}

function comparison(label: string, value: string, ariaLabel?: string): ExpressionToken {
  return { label, value, category: "comparison", ariaLabel };
}

function constant(label: string, value: string, ariaLabel: string): ExpressionToken {
  return { label, value, category: "constant", ariaLabel };
}

function fn(
  label: string,
  value: string,
  ariaLabel: string,
  title?: string
): ExpressionToken {
  return { label, value, category: "function", ariaLabel, title };
}

/** Row 1: q w e r t y u i o p π */
export const CALCULATOR_ROW_Q: ExpressionToken[] = [
  ..."qwertyuiop".split("").map(variable),
  constant("π", "pi", "pi"),
];

/** Row 2: % a s d f g h j k l . */
export const CALCULATOR_ROW_A: ExpressionToken[] = [
  fn("%", "mod(", "modulo", "mod"),
  ..."asdfghjkl".split("").map(variable),
  digit("."),
];

/** Row 3: < > z x c v b n m ≤ ≥ */
export const CALCULATOR_ROW_Z: ExpressionToken[] = [
  comparison("<", "<"),
  comparison(">", ">"),
  ..."zxcvbnm".split("").map(variable),
  comparison("≤", "<=", "less than or equal"),
  comparison("≥", ">=", "greater than or equal"),
];

/** Row 4: + − × ÷ ^ √ ( ) = ≠ τ */
export const CALCULATOR_ROW_OPS: ExpressionToken[] = [
  operator("+", "+"),
  operator("−", "-", "minus"),
  operator("*", "*", "multiply"),
  operator("÷", "/", "divide"),
  operator("^", "^", "exponent"),
  fn("√", "sqrt(", "square root"),
  operator("(", "("),
  operator(")", ")"),
  comparison("=", "==", "equals"),
  comparison("≠", "!=", "not equal"),
  constant("τ", "tau", "tau"),
];

/** Row 5: 0 1 2 3 4 5 6 7 8 9 E */
export const CALCULATOR_ROW_DIGITS: ExpressionToken[] = [
  ..."0123456789".split("").map(digit),
  constant("E", "E", "Euler's number"),
];

export const CALCULATOR_KEYPAD_ROWS: ExpressionToken[][] = [
  CALCULATOR_ROW_Q,
  CALCULATOR_ROW_A,
  CALCULATOR_ROW_Z,
  CALCULATOR_ROW_OPS,
  CALCULATOR_ROW_DIGITS,
];

const PROBLEM_ROW_A = CALCULATOR_ROW_A.filter((token) => token.category !== "function");
const PROBLEM_ROW_Z = CALCULATOR_ROW_Z.filter((token) => token.category !== "comparison");
const PROBLEM_ROW_OPS = [
  ...CALCULATOR_ROW_OPS.filter(
    (token) => token.category !== "function" && token.category !== "comparison"
  ),
  fn("inv", "inv(", "inverse function"),
  operator("=", "="),
];

export const PROBLEM_KEYPAD_ROWS: ExpressionToken[][] = [
  CALCULATOR_ROW_Q,
  PROBLEM_ROW_A,
  PROBLEM_ROW_Z,
  PROBLEM_ROW_OPS,
  CALCULATOR_ROW_DIGITS,
];

export function getKeypadRowsForContext(
  contextHint: "problem" | "step" = "problem"
): ExpressionToken[][] {
  return contextHint === "problem" ? PROBLEM_KEYPAD_ROWS : CALCULATOR_KEYPAD_ROWS;
}
