// Feature 011: the CSV download links on the case page.
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import OpenReviewCasesPage from "./OpenReviewCasesPage";

describe("CSV exports (feature 011)", () => {
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("offers both downloads as plain links, even with no open cases", async () => {
    const fetchMock = vi.fn(async () => ({ ok: true, json: async () => [] }));
    vi.stubGlobal("fetch", fetchMock);
    render(<OpenReviewCasesPage />);
    await screen.findByText("There are no open review cases.");

    const cases = screen.getByRole("link", { name: "Cases (CSV)" });
    const history = screen.getByRole("link", { name: "Review history (CSV)" });
    expect(cases).toHaveAttribute("href", "/api/exports/review-cases.csv");
    expect(history).toHaveAttribute("href", "/api/exports/review-history.csv");
    expect(cases).toHaveAttribute("download");
    expect(history).toHaveAttribute("download");
    expect(
      screen.getByText("Export all cases, open and reviewed:"),
    ).toBeVisible();
    // Showing the links sends nothing; the only request is the case list.
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
