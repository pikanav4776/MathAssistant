import { describe, expect, it } from "vitest";
import { containsTextLikeInput } from "./expressionTextLike";

describe("containsTextLikeInput", () => {
  it("flags plain-word input", () => {
    expect(containsTextLikeInput("hello")).toBe(true);
    expect(containsTextLikeInput("solve this")).toBe(true);
  });

  it("allows single-letter variables and short runs", () => {
    expect(containsTextLikeInput("2*x+3")).toBe(false);
    expect(containsTextLikeInput("x")).toBe(false);
    expect(containsTextLikeInput("ab")).toBe(false);
  });

  it("allows known math identifiers", () => {
    expect(containsTextLikeInput("sqrt(x)")).toBe(false);
    expect(containsTextLikeInput("pi*r^2")).toBe(false);
    expect(containsTextLikeInput("E+1")).toBe(false);
  });

  it("flags long alphabetic runs embedded in expressions", () => {
    expect(containsTextLikeInput("2*foobar")).toBe(true);
  });
});