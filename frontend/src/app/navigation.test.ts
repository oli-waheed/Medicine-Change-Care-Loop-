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

  it("offers exactly the two working pages", () => {
    expect(NAVIGATION_ITEMS.map((item) => item.label)).toEqual([
      "Open Review Cases",
      "About the Data",
    ]);
  });

  it("matches pages and ignores trailing slashes", () => {
    expect(pageForPath("/")).toBe("open-review-cases");
    expect(pageForPath("/about-data")).toBe("about-data");
    expect(pageForPath("/about-data/")).toBe("about-data");
    expect(normalisePath("//")).toBe("/");
  });

  it("treats every other address as not found", () => {
    expect(pageForPath("/dashboard")).toBe("not-found");
    expect(pageForPath("/processing-outcomes")).toBe("not-found");
    expect(pageForPath("/catalogue")).toBe("not-found");
  });

  it("names the page and product in the tab title", () => {
    expect(documentTitle("open-review-cases")).toBe(
      "Open Review Cases | Medicine Change Care Loop",
    );
    expect(documentTitle("about-data")).toBe(
      "About the Data | Medicine Change Care Loop",
    );
    expect(documentTitle("not-found")).toBe(
      "Page not found | Medicine Change Care Loop",
    );
  });

  it("changes the address without reloading", () => {
    const before = window.history.length;
    navigate("/about-data");
    expect(window.location.pathname).toBe("/about-data");
    expect(window.history.length).toBe(before + 1);
    navigate("/about-data/");
    expect(window.history.length).toBe(before + 1);
  });
});
