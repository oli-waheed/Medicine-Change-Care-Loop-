// Feature 003 (FR-023): the whole application, including the sidebar, top bar
// and the Open Review Cases page, offers only reading and navigation controls and uses no
// clinical wording. Extends the page-level T035 guard to every page.
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "../App";
import type { OpenReviewCase } from "../pages/open-review-cases/openReviewCases";
import { CLINICAL_WORDS } from "../test/clinicalWords";

function fixture(id: string, removed: boolean): OpenReviewCase {
  const source = {
    sourceName: "Fimea Basic Register",
    releaseDate: {
      state: "value" as const,
      value: "2099-01-01",
      attributes: {},
    },
    releaseReference: {
      state: "value" as const,
      value: "SIM-2099-001",
      attributes: {},
    },
    fileName: "release.xml",
    checksum: "synthetic-checksum",
    recordIdentifier: `SIM-PKG-${id}`,
    recordLocator: removed ? null : "/Perusrekisteri/Pakkaus[1]",
    fieldReference: null,
    evidenceClass: "VERIFIED" as const,
    note: null,
    retrievedAt: "2099-01-03T06:00:00+00:00",
    evidenceAvailable: !removed,
  };
  return {
    caseId: `CASE-${id}`,
    createdAt: "2099-01-04T00:00:00+00:00",
    status: "NEW",
    medicineIdentifier: `SIM-PKG-${id}`,
    identifierGranularity: "package",
    matchedRecord: {
      recordId: `SIM-MED-${id}`,
      personReference: `SIM-PERSON-${id}`,
      medicineDisplay: `Fictional Product ${id}`,
    },
    changeSet: {
      changeSetId: `CHANGESET-${id}`,
      kind: removed ? "NO_LONGER_PRESENT" : "FIELDS_CHANGED",
      detectedAt: "2099-01-04T00:00:00+00:00",
      changes: removed
        ? []
        : [
            {
              changeId: `CHANGE-${id}`,
              field: "Laakevalmiste/Kauppanimi",
              before: [
                { state: "value", value: "Fictional A", attributes: {} },
              ],
              after: [{ state: "missing", value: null, attributes: {} }],
            },
          ],
      lastKnownFields: removed
        ? [
            { field: "Laakevalmiste/Antoreitti", values: [] },
            {
              field: "Laakevalmiste/Laakemuoto",
              values: [{ state: "empty", value: null, attributes: {} }],
            },
          ]
        : null,
    },
    sources: { prior: source, current: source },
    sourceOrder: {
      prior: 20990101,
      current: 20990102,
      basis: "Ajopvm read from each release.",
      evidenceClass: "VERIFIED",
    },
    evidenceClass: "VERIFIED",
    evidenceAvailability: removed ? "UNAVAILABLE" : "AVAILABLE",
    initialStatusEvent: {
      eventId: `EVENT-${id}`,
      caseId: `CASE-${id}`,
      fromStatus: null,
      toStatus: "NEW",
      occurredAt: "2099-01-04T00:00:00+00:00",
    },
  };
}

const ALLOWED_BUTTONS = [/^Fictional Product \d+/, /^Menu$/, /^Sidebar$/];
const ALLOWED_LINKS: [string, string][] = [
  ["Skip to main content", "#main-content"],
  ["Open Review Cases", "/"],
  ["CC BY 4.0", "https://creativecommons.org/licenses/by/4.0/"],
  ["CC BY 4.0 licence", "https://creativecommons.org/licenses/by/4.0/"],
  ["Fimea open data", "https://fimea.fi/en/about_us/open-data"],
];

function expectOnlyAllowedControls() {
  for (const button of screen.queryAllByRole("button", { hidden: true })) {
    const name = button.textContent?.trim() ?? "";
    expect(
      ALLOWED_BUTTONS.some((pattern) => pattern.test(name)),
      `unexpected button "${name}"`,
    ).toBe(true);
  }
  expect(screen.queryAllByRole("switch", { hidden: true })).toHaveLength(0);
  for (const link of screen.queryAllByRole("link", { hidden: true })) {
    const pair = [link.textContent?.trim(), link.getAttribute("href")];
    expect(ALLOWED_LINKS, `unexpected link ${pair.join(" â†’ ")}`).toContainEqual(
      pair,
    );
  }
  // The only form control allowed is the read-only case search.
  for (const input of document.querySelectorAll("input")) {
    expect(input).toHaveAttribute("type", "search");
    expect(input).toHaveAccessibleName("Search cases");
  }
  expect(document.querySelectorAll("select, textarea, form")).toHaveLength(0);
  expect(document.body.textContent ?? "").not.toMatch(CLINICAL_WORDS);
}

describe("Application clinical scope (feature 003)", () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [fixture("100", false), fixture("300", true)],
    });
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    window.history.replaceState(null, "", "/");
  });

  it("allows only reading and navigation controls on every page", async () => {
    window.history.replaceState(null, "", "/");
    render(<App />);
    await screen.findByText("Cases (2)");

    for (const caseName of [/Fictional Product 100/, /Fictional Product 300/]) {
      fireEvent.click(screen.getByRole("button", { name: caseName }));
      expectOnlyAllowedControls();
    }

    fireEvent.change(screen.getByRole("searchbox", { name: "Search cases" }), {
      target: { value: "300" },
    });
    expectOnlyAllowedControls();

    fireEvent.click(screen.getByRole("button", { name: "Menu" }));
    expectOnlyAllowedControls();
    fireEvent.keyDown(document, { key: "Escape" });

    window.history.pushState(null, "", "/about-data");
    window.dispatchEvent(new PopStateEvent("popstate"));
    await screen.findByRole("heading", { level: 1, name: "Page not found" });
    expectOnlyAllowedControls();

    window.history.pushState(null, "", "/unknown");
    window.dispatchEvent(new PopStateEvent("popstate"));
    await screen.findByRole("heading", { level: 1, name: "Page not found" });
    expectOnlyAllowedControls();

    // Only GET reads of the open cases, once per display of the page.
    for (const [url, options] of fetchMock.mock.calls) {
      expect(url).toBe("/api/open-review-cases");
      expect(options?.method ?? "GET").toBe("GET");
    }
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});


