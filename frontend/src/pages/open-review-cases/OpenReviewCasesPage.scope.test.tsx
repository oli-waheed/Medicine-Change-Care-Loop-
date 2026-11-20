// T035: the pharmacist view presents source evidence only. It must not diagnose,
// recommend treatment, select substitutions, set urgency, or change/close cases.
import {
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import OpenReviewCasesPage from "./OpenReviewCasesPage";
import type { OpenReviewCase, SourceEvidence } from "./openReviewCases";

const CLINICAL_WORDS =
  /\b(urgen\w*|priorit\w*|severity|risk\w*|recommend\w*|diagnos\w*|substitut\w*|treatment|dos(e|es|ing|age)|contraindicat\w*|interaction\w*|should|stop taking|switch to)\b/i;

function source(
  fileName: string,
  recordLocator: string | null,
): SourceEvidence {
  return {
    sourceName: "Fimea Basic Register",
    releaseDate: { state: "value", value: "2099-01-01", attributes: {} },
    releaseReference: { state: "value", value: "SIM-2099-001", attributes: {} },
    fileName,
    checksum: "synthetic-checksum",
    recordIdentifier: "SIM-PKG-100",
    recordLocator,
    fieldReference: null,
    evidenceClass: "VERIFIED",
    note: "Source-data difference only.",
    retrievedAt: "2099-01-03T06:00:00+00:00",
  };
}

function reviewCase(
  caseId: string,
  kind: "FIELDS_CHANGED" | "NO_LONGER_PRESENT",
): OpenReviewCase {
  return {
    caseId,
    createdAt: "2099-01-04T00:00:00+00:00",
    status: "NEW",
    medicineIdentifier: `SIM-PKG-${caseId}`,
    identifierGranularity: "package",
    matchedRecord: {
      recordId: `SIM-MED-${caseId}`,
      personReference: `SIM-PERSON-${caseId}`,
      medicineDisplay: `Fictional Product ${caseId}`,
    },
    changeSet: {
      changeSetId: `CHANGESET-${caseId}`,
      kind,
      detectedAt: "2099-01-04T00:00:00+00:00",
      changes:
        kind === "FIELDS_CHANGED"
          ? [
              {
                changeId: `CHANGE-${caseId}`,
                field: "Laakevalmiste/Kauppanimi",
                before: [
                  { state: "value", value: "Fictional A", attributes: {} },
                ],
                after: [
                  { state: "value", value: "Fictional B", attributes: {} },
                ],
              },
            ]
          : [],
      lastKnownFields:
        kind === "NO_LONGER_PRESENT"
          ? [
              {
                field: "Laakevalmiste/Kauppanimi",
                values: [
                  { state: "value", value: "Fictional C", attributes: {} },
                ],
              },
            ]
          : null,
    },
    sources: {
      prior: source("prior-release.xml", "/Perusrekisteri/Pakkaus[1]"),
      current: source(
        "current-release.xml",
        kind === "FIELDS_CHANGED" ? "/x" : null,
      ),
    },
    sourceOrder: {
      prior: 20990101,
      current: 20990102,
      basis: "Ajopvm read from each release.",
      evidenceClass: "VERIFIED",
    },
    evidenceClass: "VERIFIED",
    initialStatusEvent: {
      eventId: `EVENT-${caseId}`,
      caseId,
      fromStatus: null,
      toStatus: "NEW",
      occurredAt: "2099-01-04T00:00:00+00:00",
    },
  };
}

describe("OpenReviewCasesPage clinical scope (T035)", () => {
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("only reads cases, offers no case actions and uses no clinical wording", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [
        reviewCase("100", "FIELDS_CHANGED"),
        {
          ...reviewCase("300", "NO_LONGER_PRESENT"),
          evidenceAvailability: "UNAVAILABLE",
        },
      ],
    });
    vi.stubGlobal("fetch", fetchMock);
    render(<OpenReviewCasesPage />);
    await screen.findByText("Cases (2)");

    // The page's only controls are the case-selection buttons in the case
    // list: one per case, each naming the package it selects.
    const caseList = screen.getByRole("navigation", {
      name: "Open review cases",
    });
    const buttons = within(caseList).getAllByRole("button");
    expect(buttons).toHaveLength(2);
    expect(screen.getAllByRole("button")).toEqual(buttons);
    for (const button of buttons) {
      expect(button.textContent).toMatch(/SIM-PKG-/);
      fireEvent.click(button);
      expect(document.body.textContent ?? "").not.toMatch(CLINICAL_WORDS);
    }

    // No form controls that could set status, priority or a decision. The
    // only input is the read-only case search (feature 003), which filters
    // the cases already loaded and sends nothing.
    const search = screen.getByRole("searchbox", { name: "Search cases" });
    expect(document.querySelectorAll("input")).toEqual(
      document.querySelectorAll('input[type="search"]'),
    );
    expect(document.querySelectorAll("input")).toHaveLength(1);
    expect(document.querySelectorAll("select, textarea, form")).toHaveLength(0);
    fireEvent.change(search, { target: { value: "SIM-PKG-300" } });
    expect(document.body.textContent ?? "").not.toMatch(CLINICAL_WORDS);
    fireEvent.change(search, { target: { value: "" } });
    // The view never changes data: one read on load, nothing on selection.
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/open-review-cases");
    expect(options?.method ?? "GET").toBe("GET");
    expect(options?.body).toBeUndefined();
    expect(
      screen.getAllByText(/does not make a clinical decision/).length,
    ).toBeGreaterThan(0);
  });
});
