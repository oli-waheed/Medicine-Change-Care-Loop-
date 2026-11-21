// Feature 012: how the previous visit is remembered in this browser.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  SESSION_GAP_MS,
  isDateOnOrAfterVisit,
  isNewSince,
  markAllSeen,
  previousVisit,
  resetVisitForTests,
} from "./lastVisit";

const KEY = "mccl:visits";
const at = (iso: string) => new Date(iso);

describe("last visit (feature 012)", () => {
  beforeEach(() => {
    window.localStorage.clear();
    resetVisitForTests();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("has no previous visit the first time, and stores this one", () => {
    expect(previousVisit(at("2099-01-05T10:00:00Z"))).toBeNull();
    expect(JSON.parse(window.localStorage.getItem(KEY)!)).toEqual({
      previous: null,
      last: "2099-01-05T10:00:00.000Z",
    });
  });

  it("starts a new visit after a 30-minute gap", () => {
    window.localStorage.setItem(
      KEY,
      JSON.stringify({ previous: null, last: "2099-01-05T10:00:00.000Z" }),
    );
    const later = new Date(
      Date.parse("2099-01-05T10:00:00Z") + SESSION_GAP_MS + 1,
    );
    expect(previousVisit(later)).toBe("2099-01-05T10:00:00.000Z");
  });

  it("keeps the same previous visit for reloads within 30 minutes", () => {
    window.localStorage.setItem(
      KEY,
      JSON.stringify({
        previous: "2099-01-01T08:00:00.000Z",
        last: "2099-01-05T10:00:00.000Z",
      }),
    );
    expect(previousVisit(at("2099-01-05T10:20:00Z"))).toBe(
      "2099-01-01T08:00:00.000Z",
    );
    // Within this page load the answer never changes.
    expect(previousVisit(at("2099-02-01T00:00:00Z"))).toBe(
      "2099-01-01T08:00:00.000Z",
    );
  });

  it("clears the marks when everything is marked as seen", () => {
    window.localStorage.setItem(
      KEY,
      JSON.stringify({ previous: null, last: "2099-01-01T00:00:00.000Z" }),
    );
    expect(previousVisit(at("2099-01-05T10:00:00Z"))).toBe(
      "2099-01-01T00:00:00.000Z",
    );
    markAllSeen(at("2099-01-05T10:05:00Z"));
    expect(previousVisit()).toBe("2099-01-05T10:05:00.000Z");
  });

  it("treats unreadable or blocked storage as a first visit", () => {
    window.localStorage.setItem(KEY, "not json");
    expect(previousVisit(at("2099-01-05T10:00:00Z"))).toBeNull();

    resetVisitForTests();
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    expect(previousVisit(at("2099-01-05T10:00:00Z"))).toBeNull();
    expect(() => markAllSeen()).not.toThrow();
  });

  it("compares times and Fimea dates with the previous visit", () => {
    const previous = "2099-01-05T10:00:00.000Z";
    expect(isNewSince(previous, "2099-01-05T10:00:01+00:00")).toBe(true);
    expect(isNewSince(previous, "2099-01-05T09:59:59+00:00")).toBe(false);
    expect(isNewSince(null, "2099-01-06T00:00:00+00:00")).toBe(false);
    expect(isNewSince(previous, "not a time")).toBe(false);
    expect(isDateOnOrAfterVisit(previous, "2099-01-05")).toBe(true);
    expect(isDateOnOrAfterVisit(previous, "2099-01-04")).toBe(false);
    expect(isDateOnOrAfterVisit(previous, "5.1.2099")).toBe(false);
    expect(isDateOnOrAfterVisit(null, "2099-01-09")).toBe(false);
  });
});
