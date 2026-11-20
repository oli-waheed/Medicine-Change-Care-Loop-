import { describe, expect, it } from "vitest";
import { displayableVersion } from "./appVersion";

describe("displayableVersion", () => {
  it("hides the scaffold placeholder version", () => {
    expect(displayableVersion("0.0.0")).toBeNull();
  });

  it("hides a missing or blank version", () => {
    expect(displayableVersion(undefined)).toBeNull();
    expect(displayableVersion("  ")).toBeNull();
  });

  it("shows a real version", () => {
    expect(displayableVersion("0.3.0")).toBe("0.3.0");
  });
});
