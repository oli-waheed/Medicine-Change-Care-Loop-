import { describe, expect, it } from "vitest";
import { formatTimestamp } from "./timestamp";

describe("formatTimestamp", () => {
  it("formats a UTC timestamp", () => {
    expect(formatTimestamp("2025-01-02T03:04:05Z")).toBe(
      "2025-01-02 03:04 UTC",
    );
  });

  it("converts an offset timestamp to UTC", () => {
    expect(formatTimestamp("2025-04-03T08:15:00+02:00")).toBe(
      "2025-04-03 06:15 UTC",
    );
  });

  it("returns null for an invalid timestamp", () => {
    expect(formatTimestamp("not-a-timestamp")).toBeNull();
  });

  it("rejects impossible calendar dates", () => {
    expect(formatTimestamp("2025-02-31T00:00:00Z")).toBeNull();
    expect(formatTimestamp("2025-02-29T00:00:00Z")).toBeNull();
    expect(formatTimestamp("2024-02-29T00:00:00Z")).toBe(
      "2024-02-29 00:00 UTC",
    );
  });

  it("rejects out-of-range clock components", () => {
    expect(formatTimestamp("2025-01-01T25:00:00Z")).toBeNull();
    expect(formatTimestamp("2025-01-01T03:60:00Z")).toBeNull();
    expect(formatTimestamp("2025-01-01T03:04:60Z")).toBeNull();
  });

  it("returns null for a missing timestamp", () => {
    expect(formatTimestamp(null)).toBeNull();
    expect(formatTimestamp(undefined)).toBeNull();
  });
});
