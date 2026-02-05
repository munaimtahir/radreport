import { describe, expect, it } from "vitest";
import { resolveReportingErrorMessage } from "../errors";

describe("resolveReportingErrorMessage", () => {
  it("returns no-template message for mapped backend error", () => {
    expect(resolveReportingErrorMessage({ detail: { code: "no_active_template" } })).toBe(
      "No active template configured for this service"
    );
    expect(resolveReportingErrorMessage({ detail: { error: "NO_ACTIVE_V2_TEMPLATE" } })).toBe(
      "No active template configured for this service"
    );
  });

  it("falls back to generic message", () => {
    expect(resolveReportingErrorMessage({ message: "boom" })).toBe("boom");
  });
});
