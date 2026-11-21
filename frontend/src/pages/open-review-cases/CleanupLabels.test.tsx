// Feature 008: labels for likely source clean-ups, against API responses
// captured from the real backend (src/test/cleanupLabelResponses.json).
import {
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import responses from "../../test/cleanupLabelResponses.json";
import { CLINICAL_WORDS } from "../../test/clinicalWords";
import OpenReviewCasesPage from "./OpenReviewCasesPage";
import type { ReviewCase } from "./openReviewCases";

const CASES = responses as unknown as ReviewCase[];

function list() {
  return screen.getByRole("navigation", { name: "Open review cases" });
}

// The page has other notes; this is the clean-up one.
function cleanupNotice() {
  return document.querySelector<HTMLElement>(".cleanup-notice");
}

function caseButtons() {
  return within(list()).getAllByRole("button");
}

function open(name: RegExp) {
  fireEvent.click(
    caseButtons().find((item) => name.test(item.textContent ?? ""))!,
  );
}

describe("Source clean-up labels (feature 008)", () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn(async () => ({
      ok: true,
      status: 200,
      json: async () => structuredClone(CASES),
    }));
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("labels cases in the list without hiding any", async () => {
    render(<OpenReviewCasesPage />);
    await screen.findByText("Cases (3)");
    const labels = caseButtons().map(
      (button) =>
        button.querySelector(".case-list-cleanup")?.textContent ?? null,
    );
    expect(labels).toEqual([
      null,
      "Active-substance fields only",
      "Spacing or letter case only",
    ]);
    expect(
      screen.getByRole("checkbox", {
        name: "Set aside likely source clean-ups",
      }),
    ).not.toBeChecked();
  });

  it("shows the published values and marks a spacing-only field", async () => {
    render(<OpenReviewCasesPage />);
    await screen.findByText("Cases (3)");
    open(/SIM-PKG-100/);

    const notice = cleanupNotice();
    expect(notice).toHaveAttribute("role", "note");
    expect(notice).toHaveTextContent(
      "Likely source clean-up: Spacing or letter case only.",
    );
    expect(notice).toHaveTextContent("never changes the case's status");
    const change = screen.getByRole("region", {
      name: "Detected source-data change",
    });
    expect(
      within(change).getByText("Spacing or letter case only"),
    ).toBeVisible();
    // Values exactly as published, spaces included.
    const values = Array.from(
      change.querySelectorAll(".before-after-side"),
    ).map((side) => side.textContent ?? "");
    expect(values[0]).toContain("Fictional Product Amber Revised");
    expect(values[1]).toContain("Fictional  product AMBER revised ");
    expect(document.body.textContent ?? "").not.toMatch(CLINICAL_WORDS);
  });

  it("explains active-substance-only cases and leaves mixed cases unlabelled", async () => {
    render(<OpenReviewCasesPage />);
    await screen.findByText("Cases (3)");
    open(/SIM-PKG-200/);
    expect(cleanupNotice()).toHaveTextContent(
      "Only active-substance fields changed.",
    );
    expect(document.body.textContent ?? "").not.toMatch(CLINICAL_WORDS);

    open(/SIM-PKG-500/);
    expect(cleanupNotice()).toBeNull();
    expect(
      screen.queryByText("Spacing or letter case only", {
        selector: ".formatting-only",
      }),
    ).not.toBeInTheDocument();
  });

  it("sets labelled cases aside only when the reviewer chooses, with no request", async () => {
    render(<OpenReviewCasesPage />);
    await screen.findByText("Cases (3)");
    const toggle = screen.getByRole("checkbox", {
      name: "Set aside likely source clean-ups",
    });

    fireEvent.click(toggle);
    expect(caseButtons().map((button) => button.textContent)).toEqual([
      expect.stringContaining("SIM-PKG-500"),
    ]);
    expect(screen.getByText("Showing 1 of 3")).toBeVisible();
    expect(screen.getByText("Cases (3)")).toBeVisible();

    fireEvent.click(toggle);
    expect(caseButtons()).toHaveLength(3);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("offers no set-aside switch when no case is labelled", async () => {
    const unlabelled = CASES.filter(
      (item) => item.medicineIdentifier === "SIM-PKG-500",
    );
    fetchMock.mockImplementation(async () => ({
      ok: true,
      status: 200,
      json: async () => structuredClone(unlabelled),
    }));
    render(<OpenReviewCasesPage />);
    await screen.findByText("Cases (1)");
    expect(screen.queryByRole("checkbox", { name: /source clean-ups/ })).toBe(
      null,
    );
  });
});
