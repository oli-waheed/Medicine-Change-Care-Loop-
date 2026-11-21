// Feature 012: cases new since the previous visit, on the case page.
import {
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { resetVisitForTests } from "../../app/lastVisit";
import responses from "../../test/cleanupLabelResponses.json";
import { CLINICAL_WORDS } from "../../test/clinicalWords";
import OpenReviewCasesPage from "./OpenReviewCasesPage";
import type { ReviewCase } from "./openReviewCases";

const CASES = responses as unknown as ReviewCase[];
const PREVIOUS = "2026-11-21T13:00:00.000Z";

function serve(cases: ReviewCase[]) {
  const fetchMock = vi.fn(async () => ({
    ok: true,
    status: 200,
    json: async () => structuredClone(cases),
  }));
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function listItems() {
  return within(
    screen.getByRole("navigation", { name: "Open review cases" }),
  ).getAllByRole("button");
}

describe("New since your last visit (feature 012)", () => {
  beforeEach(() => {
    resetVisitForTests();
    // The previous visit ended long ago, so this page load is a new visit.
    window.localStorage.setItem(
      "mccl:visits",
      JSON.stringify({ previous: null, last: PREVIOUS }),
    );
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    window.localStorage.clear();
  });

  it("marks cases created after the previous visit and counts them", async () => {
    const older = { ...CASES[0], createdAt: "2026-11-20T09:00:00+00:00" };
    const fetchMock = serve([older, CASES[1], CASES[2]]);
    render(<OpenReviewCasesPage />);
    await screen.findByText("Cases (3)");

    expect(
      screen.getByText(
        "2 cases are new since your last visit (2026-11-21 13:00 UTC).",
      ),
    ).toBeVisible();
    expect(
      listItems().map((item) => item.querySelector(".new-badge") !== null),
    ).toEqual([false, true, true]);
    expect(document.body.textContent ?? "").not.toMatch(CLINICAL_WORDS);

    fireEvent.click(screen.getByRole("button", { name: "Mark all as seen" }));
    expect(document.querySelectorAll(".new-badge")).toHaveLength(0);
    expect(
      screen.getByText(/^Nothing new here since your last visit/),
    ).toBeVisible();
    // Marking as seen is kept in this browser; nothing is sent.
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(
      JSON.parse(window.localStorage.getItem("mccl:visits")!).previous,
    ).not.toBe(PREVIOUS);
  });

  it("says nothing on the first visit", async () => {
    window.localStorage.clear();
    serve(CASES);
    render(<OpenReviewCasesPage />);
    await screen.findByText("Cases (3)");
    expect(screen.queryByText(/since your last visit/)).toBeNull();
    expect(document.querySelectorAll(".new-badge")).toHaveLength(0);
  });
});
