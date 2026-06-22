import { describe, expect, it } from "vitest";
import { friendlyErrorMessage } from "./friendlyErrorMessage";

describe("friendlyErrorMessage", () => {
  it("maps network failures to a friendly message", () => {
    expect(friendlyErrorMessage(new TypeError("Failed to fetch"))).toBe(
      "Can't reach the server. Check your connection and try again."
    );
  });

  it("uses API message for unsupported problems", () => {
    const err = new Error("Equations are not supported in v1.0.");
    expect(friendlyErrorMessage(err)).toBe("Equations are not supported in v1.0.");
  });

  it("maps not_authenticated errors", () => {
    expect(friendlyErrorMessage(new Error("not_authenticated"))).toBe(
      "Sign in to access this session."
    );
  });
});
