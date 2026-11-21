// Feature 003 (FR-023): the whole application, including the sidebar, top bar
// and About the Data, offers only reading and navigation controls and uses no
// clinical wording. Extends the page-level T035 guard to every page.
// Feature 004 adds the read-only Medicine Catalogue: its search fields, filter
// selects and view, record and comparison buttons are listed here deliberately.
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "../App";
import type { OpenReviewCase } from "../pages/open-review-cases/openReviewCases";
import { CLINICAL_WORDS } from "../test/clinicalWords";
import { catalogueFetch } from "../test/catalogueFixtures";
import { shortageFetch } from "../test/shortageFixtures";

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

// Feature 005: About the Data offers one control that loads the latest Fimea
// release, the same as the daily ingestion workflow; it never changes cases.
const ALLOWED_BUTTONS = [
  /^Fictional Product \d+/,
  /^Menu$/,
  /^Sidebar$/,
  /^Check for new Fimea release$/,
];
// Feature 004: catalogue reading controls (open records, switch views, page).
const CATALOGUE_BUTTONS = [
  /^Fictional Product /,
  /^Packages$/,
  /^Active substances$/,
  /^Compare( \(\d\))?$/,
  /^SYN-/,
  /^SIM-/,
  /^Open product /,
  /^Add to comparison$/,
  /^Remove Product [AB]$/,
  /^Clear search and filters$/,
  /^(Show occurrences \(\d+\)|Hide occurrences)$/,
  /^(Previous|Next) page$/,
];
const CATALOGUE_INPUTS = [
  "Search medicines",
  "Active substance",
  "ATC code starts with",
  "Pharmaceutical form",
  "Administration route",
  "VNR",
  "Search active substances",
];
const CATALOGUE_SELECTS = ["On the market (Kaupan)", "Not present in source"];
// Feature 006: the shortage list's search, status filter, paging and its one
// Update button, which downloads Fimea's shortage file and changes no cases.
const SHORTAGE_BUTTONS = [/^Update shortage data$/, /^(Previous|Next) page$/];
const SHORTAGE_INPUTS = ["Search shortages"];
const SHORTAGE_SELECTS = ["Status (Valid)"];
const ALLOWED_LINKS: [string, string][] = [
  ["Skip to main content", "#main-content"],
  ["Open Review Cases", "/"],
  ["Medicine Catalogue", "/medicine-catalogue"],
  ["Medicine Shortages", "/medicine-shortages"],
  ["About the Data", "/about-data"],
  ["CC BY 4.0", "https://creativecommons.org/licenses/by/4.0/"],
  ["CC BY 4.0 licence", "https://creativecommons.org/licenses/by/4.0/"],
  ["Fimea open data", "https://fimea.fi/en/about_us/open-data"],
];

type Mode = "cases" | "catalogue" | "shortages";

const MODE_CONTROLS: Record<
  Exclude<Mode, "cases">,
  { buttons: RegExp[]; inputs: string[]; selects: string[] }
> = {
  catalogue: {
    buttons: CATALOGUE_BUTTONS,
    inputs: CATALOGUE_INPUTS,
    selects: CATALOGUE_SELECTS,
  },
  shortages: {
    buttons: SHORTAGE_BUTTONS,
    inputs: SHORTAGE_INPUTS,
    selects: SHORTAGE_SELECTS,
  },
};

function expectOnlyAllowedControls(mode: Mode = "cases") {
  const controls = mode === "cases" ? null : MODE_CONTROLS[mode];
  const buttons = controls
    ? [...ALLOWED_BUTTONS, ...controls.buttons]
    : ALLOWED_BUTTONS;
  for (const button of screen.queryAllByRole("button", { hidden: true })) {
    const name = button.textContent?.trim() ?? "";
    expect(
      buttons.some((pattern) => pattern.test(name)),
      `unexpected button "${name}"`,
    ).toBe(true);
  }
  expect(screen.queryAllByRole("switch", { hidden: true })).toHaveLength(0);
  for (const link of screen.queryAllByRole("link", { hidden: true })) {
    const pair = [link.textContent?.trim(), link.getAttribute("href")];
    expect(ALLOWED_LINKS, `unexpected link ${pair.join(" → ")}`).toContainEqual(
      pair,
    );
  }
  if (controls) {
    // These fields only narrow what is read; nothing is ever submitted.
    for (const input of document.querySelectorAll("input")) {
      expect(["search", "text"]).toContain(input.getAttribute("type"));
      expect(controls.inputs).toContain(input.labels?.[0]?.textContent);
    }
    for (const select of document.querySelectorAll("select")) {
      expect(controls.selects).toContain(select.labels?.[0]?.textContent);
    }
    expect(document.querySelectorAll("textarea, form")).toHaveLength(0);
  } else {
    // The only form control allowed is the read-only case search.
    for (const input of document.querySelectorAll("input")) {
      expect(input).toHaveAttribute("type", "search");
      expect(input).toHaveAccessibleName("Search cases");
    }
    expect(document.querySelectorAll("select, textarea, form")).toHaveLength(0);
  }
  expect(document.body.textContent ?? "").not.toMatch(CLINICAL_WORDS);
}

describe("Application clinical scope (feature 003)", () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn(async (url: string, init?: RequestInit) =>
      url.startsWith("/api/medicine-catalogue")
        ? catalogueFetch(url)
        : url.startsWith("/api/shortages") ||
            url.startsWith("/api/daily-updates")
          ? shortageFetch(url, init)
          : {
              ok: true,
              json: async () => [fixture("100", false), fixture("300", true)],
            },
    );
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

    fireEvent.click(screen.getByRole("link", { name: "About the Data" }));
    await screen.findByRole("heading", { level: 1, name: "About the Data" });
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

  it("keeps the Medicine Catalogue to reading controls and GET requests", async () => {
    window.history.replaceState(null, "", "/medicine-catalogue");
    render(<App />);
    await screen.findByRole("heading", {
      level: 1,
      name: "Medicine Catalogue",
    });
    await screen.findByText(/Showing 1–4 of 4 packages/);
    expectOnlyAllowedControls("catalogue");

    fireEvent.click(screen.getByText("Filters"));
    expectOnlyAllowedControls("catalogue");

    fireEvent.click(screen.getByRole("button", { name: /SIM-PKG-100/ }));
    await screen.findByRole("button", { name: "Open product SYN-PROD-100" });
    expectOnlyAllowedControls("catalogue");

    fireEvent.click(
      screen.getByRole("button", { name: "Open product SYN-PROD-100" }),
    );
    fireEvent.click(
      await screen.findByRole("button", { name: "Add to comparison" }),
    );
    await screen.findByText("Product A");
    expectOnlyAllowedControls("catalogue");

    fireEvent.click(screen.getByRole("button", { name: "Active substances" }));
    await screen.findByText("Aine=SIM-SA01");
    fireEvent.click(
      screen.getByRole("button", { name: "Show occurrences (3)" }),
    );
    expectOnlyAllowedControls("catalogue");

    for (const [url, options] of fetchMock.mock.calls) {
      expect(String(url)).toMatch(/^\/api\/medicine-catalogue(\/|\?|$)/);
      expect(options?.method ?? "GET").toBe("GET");
    }
  });

  it("keeps Medicine Shortages to reading controls and its Update button", async () => {
    window.history.replaceState(null, "", "/medicine-shortages");
    render(<App />);
    await screen.findByRole("heading", {
      level: 1,
      name: "Medicine Shortages",
    });
    await screen.findByText("Showing 1–3 of 3 shortages");
    expectOnlyAllowedControls("shortages");

    fireEvent.change(screen.getByRole("combobox", { name: "Status (Valid)" }), {
      target: { value: "E" },
    });
    await screen.findByText("Showing 1–1 of 1 shortages");
    expectOnlyAllowedControls("shortages");

    // Reads are GETs; the only POST is the shortage download, and only on press.
    for (const [url, options] of fetchMock.mock.calls) {
      expect(String(url)).toMatch(/^\/api\/(shortages|daily-updates)(\?|$)/);
      expect(options?.method ?? "GET").toBe("GET");
    }
    fireEvent.click(
      screen.getByRole("button", { name: "Update shortage data" }),
    );
    await screen.findByText("Downloading Fimea’s shortage file…");
    const posts = fetchMock.mock.calls.filter(
      ([, options]) => options?.method === "POST",
    );
    expect(posts.map(([url]) => url)).toEqual(["/api/shortages/update"]);
    expectOnlyAllowedControls("shortages");
  });
});
