import { describe, expect, it } from "vitest";
import { validateExpressionHeuristic } from "./expressionHeuristic";

describe("validateExpressionHeuristic", () => {
  it("rejects empty expressions", () => {
    const result = validateExpressionHeuristic("   ");
    expect(result.isValid).toBe(false);
    expect(result.errors).toContain("Expression is empty.");
  });

  it("flags unbalanced parentheses", () => {
    const result = validateExpressionHeuristic("2*(x+3");
    expect(result.isValid).toBe(false);
    expect(result.errors).toContain("Unbalanced parentheses.");
  });

  it("allows partial expressions with trailing operators", () => {
    const result = validateExpressionHeuristic("2 +");
    expect(result.isValid).toBe(true);
    expect(result.warnings).toContain("Expression ends with an operator.");
  });

  it("warns about v1.0 unsupported syntax in problem context", () => {
    const result = validateExpressionHeuristic("sqrt(x)", "problem");
    expect(result.warnings.some((w) => w.includes("v1.0"))).toBe(true);
  });

  it("does not warn about comparisons in step context", () => {
    const result = validateExpressionHeuristic("x <= 5", "step");
    expect(result.warnings.some((w) => w.includes("v1.0"))).toBe(false);
  });

  it("rejects word-like text input", () => {
    const result = validateExpressionHeuristic("hello");
    expect(result.isValid).toBe(false);
    expect(result.errors.some((e) => e.includes("word-like"))).toBe(true);
  });

  it("allows math with single-letter variables", () => {
    const result = validateExpressionHeuristic("2*x+3");
    expect(result.isValid).toBe(true);
  });

  it("allows capital E as Euler's number", () => {
    const result = validateExpressionHeuristic("E+2");
    expect(result.isValid).toBe(true);
  });
});
