import { afterEach, describe, expect, it } from "vitest";
import {
  NAVIGATION_ITEMS,
  documentTitle,
  navigate,
  normalisePath,
  pageForPath,
} from "./navigation";

describe("navigation", () => {
  afterEach(() => window.history.replaceState(null, "", "/"));

  it("offers only the implemented Open Review Cases page", () => {
    expect(NAVIGATION_ITEMS.map((item) => item.label)).toEqual([
      "Open Review Cases",
    ]);
  });

  it("matches the implemented page and ignores trailing slashes", () => {
    expect(pageForPath("/")).toBe("open-review-cases");
    expect(pageForPath("/")).toBe("open-review-cases");
    expect(normalisePath("//")).toBe("/");
  });

  it("treats unimplemented pages and unknown addresses as not found", () => {
    expect(pageForPath("/about-data")).toBe("not-found");
    expect(pageForPath("/catalogue")).toBe("not-found");
    expect(pageForPath("/dashboard")).toBe("not-found");
    expect(pageForPath("/processing-outcomes")).toBe("not-found");
  });

  it("names the page and product in the tab title", () => {
    expect(documentTitle("open-review-cases")).toBe(
      "Open Review Cases | Medicine Change Care Loop",
    );
    expect(documentTitle("not-found")).toBe(
      "Page not found | Medicine Change Care Loop",
    );
  });

  it("changes the address without reloading", () => {
    const before = window.history.length;
    navigate("/unknown");
    expect(window.location.pathname).toBe("/unknown");
    expect(window.history.length).toBe(before + 1);
    navigate("/unknown/");
    expect(window.history.length).toBe(before + 1);
  });
});
