import {
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import OpenReviewCasesPage from "./OpenReviewCasesPage";
import { sourceValue } from "./sourceValue";
import type { OpenReviewCase } from "./openReviewCases";

const caseFixture: OpenReviewCase = {
  caseId: "CASE-SIM-100",
  createdAt: "2099-01-03T00:00:00+00:00",
  status: "NEW",
  medicineIdentifier: "SIM-PKG-100",
  identifierGranularity: "package",
  matchedRecord: {
    recordId: "SIM-MED-100",
    personReference: "SIM-PERSON-100",
    medicineDisplay: "Fictional Alpha",
  },
  changeSet: {
    changeSetId: "CHANGESET-SIM-100",
    kind: "FIELDS_CHANGED",
    detectedAt: "2099-01-03T00:00:00+00:00",
    changes: [
      {
        changeId: "CHANGE-SIM-100",
        field: "Laakevalmiste/Kauppanimi",
        before: [{ state: "value", value: "Fictional Alpha", attributes: {} }],
        after: [
          { state: "value", value: "Fictional Alpha Revised", attributes: {} },
        ],
      },
    ],
    lastKnownFields: null,
  },
  sources: {
    prior: {
      sourceName: "Fimea Basic Register",
      releaseDate: { state: "value", value: "2099-01-01", attributes: {} },
      releaseReference: {
        state: "value",
        value: "SIM-2099-001",
        attributes: {},
      },
      fileName: "prior-release.xml",
      checksum: "synthetic-prior-checksum",
      recordIdentifier: "SIM-PKG-100",
      recordLocator: "/Perusrekisteri/Pakkaus[1]",
      fieldReference: null,
      evidenceClass: "VERIFIED",
      note: null,
      retrievedAt: null,
    },
    current: {
      sourceName: "Fimea Basic Register",
      releaseDate: { state: "value", value: "2099-01-02", attributes: {} },
      releaseReference: {
        state: "value",
        value: "SIM-2099-002",
        attributes: {},
      },
      fileName: "current-release.xml",
      checksum: "synthetic-current-checksum",
      recordIdentifier: "SIM-PKG-100",
      recordLocator: "/Perusrekisteri/Pakkaus[1]",
      fieldReference: null,
      evidenceClass: "VERIFIED",
      note: null,
      retrievedAt: null,
    },
  },
  sourceOrder: {
    prior: 1,
    current: 2,
    basis: "Controlled synthetic source order, not retrieval time.",
    evidenceClass: "VERIFIED",
  },
  evidenceClass: "VERIFIED",
  initialStatusEvent: {
    eventId: "EVENT-SIM-100",
    caseId: "CASE-SIM-100",
    fromStatus: null,
    toStatus: "NEW",
    occurredAt: "2099-01-03T00:00:00+00:00",
  },
};

describe("OpenReviewCasesPage", () => {
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("shows the open-case list and source evidence without decision or closure actions", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => [caseFixture],
      }),
    );
    render(<OpenReviewCasesPage />);

    expect(
      await screen.findByRole("heading", { name: "Open review cases" }),
    ).toBeVisible();
    expect(
      screen.getAllByText("Fictional Alpha Revised").length,
    ).toBeGreaterThan(0);
    expect(screen.getByText("SIM-PKG-100")).toBeVisible();
    expect(screen.getAllByText("Fictional Alpha").length).toBeGreaterThan(0);
    expect(screen.getByText("SIM-PERSON-100")).toBeVisible();
    expect(screen.getByText("prior-release.xml")).toBeVisible();
    expect(screen.getByText("current-release.xml")).toBeVisible();
    expect(
      screen.getByText(
        "Controlled synthetic source order, not retrieval time.",
      ),
    ).toBeVisible();
    expect(
      screen.queryByRole("button", { name: /close|resolve|recommend/i }),
    ).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: /Fictional Alpha/ }));
    expect(
      screen.getByRole("button", { name: /Fictional Alpha/ }),
    ).toHaveAttribute("aria-pressed", "true");
  });

  it("shows an explicit load error and an empty state", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 503,
      }),
    );
    const { unmount } = render(<OpenReviewCasesPage />);
    expect(await screen.findByRole("alert")).toHaveTextContent("HTTP 503");
    unmount();

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => [],
      }),
    );
    render(<OpenReviewCasesPage />);
    expect(
      await screen.findByText("There are no open review cases."),
    ).toBeVisible();
  });

  it("shows code-table attribute values instead of 'Present but empty'", async () => {
    const statusChange: OpenReviewCase = {
      ...caseFixture,
      changeSet: {
        ...caseFixture.changeSet,
        changes: [
          {
            changeId: "CHANGE-SIM-STATUS",
            field: "Laakevalmiste/Myyntilupa[0]/Tila",
            before: [
              {
                state: "empty",
                value: "",
                attributes: {
                  listname: "SIM-AUTH",
                  id: "SIM-ACTIVE",
                  value: "synthetic active",
                },
              },
            ],
            after: [
              {
                state: "empty",
                value: "",
                attributes: {
                  listname: "SIM-AUTH",
                  id: "SIM-REVOKED",
                  value: "synthetic revoked",
                },
              },
            ],
          },
        ],
      },
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => [statusChange] }),
    );
    render(<OpenReviewCasesPage />);

    expect(
      await screen.findByText(
        "synthetic active (code SIM-ACTIVE, list SIM-AUTH)",
      ),
    ).toBeVisible();
    expect(
      screen.getByText("synthetic revoked (code SIM-REVOKED, list SIM-AUTH)"),
    ).toBeVisible();
    expect(screen.queryByText("Present but empty")).toBeNull();
  });

  it("shows every field change of one package update in a single case", async () => {
    const multiField: OpenReviewCase = {
      ...caseFixture,
      changeSet: {
        ...caseFixture.changeSet,
        changes: [
          ...caseFixture.changeSet.changes,
          {
            changeId: "CHANGE-SIM-101",
            field: "Pakkaus/JulkinenTarkenne",
            before: [{ state: "empty", value: "", attributes: {} }],
            after: [{ state: "value", value: "SIM tarkenne", attributes: {} }],
          },
        ],
      },
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => [multiField] }),
    );
    render(<OpenReviewCasesPage />);

    expect(await screen.findByText("Cases (1)")).toBeVisible();
    expect(screen.getByText("2 field changes")).toBeVisible();
    expect(screen.getByText("2 fields")).toBeVisible();
    expect(screen.getByText("Laakevalmiste/Kauppanimi")).toBeVisible();
    expect(screen.getByText("Pakkaus/JulkinenTarkenne")).toBeVisible();
    expect(screen.getByText("SIM tarkenne")).toBeVisible();
  });

  it("shows a package that is no longer present with its last known values", async () => {
    const removed: OpenReviewCase = {
      ...caseFixture,
      changeSet: {
        changeSetId: "CHANGESET-SIM-300",
        kind: "NO_LONGER_PRESENT",
        detectedAt: "2099-01-03T00:00:00+00:00",
        changes: [],
        lastKnownFields: [
          {
            field: "Laakevalmiste/Kauppanimi",
            values: [
              { state: "value", value: "Fictional Cedar", attributes: {} },
            ],
          },
          { field: "Laakevalmiste/Antoreitti", values: [] },
        ],
      },
      sources: {
        ...caseFixture.sources,
        current: {
          ...caseFixture.sources.current,
          recordLocator: null,
          note: "No Pakkaus with this Pakkaustunnus in this release.",
        },
      },
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => [removed] }),
    );
    render(<OpenReviewCasesPage />);

    expect(
      await screen.findByRole("heading", {
        name: "Package no longer present in the register",
      }),
    ).toBeVisible();
    expect(screen.getByText("No longer in the register")).toBeVisible();
    expect(screen.getByText("Fictional Cedar")).toBeVisible();
    expect(screen.getByText("No occurrences")).toBeVisible();
    expect(screen.getByText(/does not state why/)).toBeVisible();
    expect(screen.getByText("Not in this release")).toBeVisible();
    expect(screen.queryByText("Before")).toBeNull();
    expect(
      screen.queryByRole("button", { name: /close|resolve|recommend/i }),
    ).toBeNull();
  });

  it("shows when a case's source evidence is no longer stored", async () => {
    const unavailable: OpenReviewCase = {
      ...caseFixture,
      evidenceAvailability: "UNAVAILABLE",
      sources: {
        prior: { ...caseFixture.sources.prior, evidenceAvailable: false },
        current: { ...caseFixture.sources.current, evidenceAvailable: true },
      },
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => [unavailable] }),
    );
    render(<OpenReviewCasesPage />);

    expect(
      await screen.findByText(/Source evidence unavailable/),
    ).toBeVisible();
    expect(screen.getByText("Evidence unavailable")).toBeVisible();
    expect(screen.getAllByText(/no longer stored/).length).toBeGreaterThan(0);
    expect(
      screen.getByText(
        "VERIFIED when recorded; source evidence now unavailable",
      ),
    ).toBeVisible();
    expect(
      screen.getByText("VERIFIED when recorded; source file now unavailable"),
    ).toBeVisible();
  });

  it("shows no warning while the evidence is available", async () => {
    const available: OpenReviewCase = {
      ...caseFixture,
      evidenceAvailability: "AVAILABLE",
      sources: {
        prior: { ...caseFixture.sources.prior, evidenceAvailable: true },
        current: { ...caseFixture.sources.current, evidenceAvailable: true },
      },
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => [available] }),
    );
    render(<OpenReviewCasesPage />);

    expect(await screen.findByText("Cases (1)")).toBeVisible();
    expect(screen.queryByText(/Source evidence unavailable/)).toBeNull();
    expect(screen.queryByText("Evidence unavailable")).toBeNull();
  });

  it("renders all four evidence classifications as distinct labels", async () => {
    const classifiedCase: OpenReviewCase = {
      ...caseFixture,
      evidenceClass: "VERIFIED",
      sourceOrder: {
        ...caseFixture.sourceOrder,
        evidenceClass: "CONFLICTING",
      },
      sources: {
        prior: {
          ...caseFixture.sources.prior,
          evidenceClass: "INFERRED",
        },
        current: {
          ...caseFixture.sources.current,
          evidenceClass: "UNKNOWN",
        },
      },
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => [classifiedCase],
      }),
    );
    render(<OpenReviewCasesPage />);

    expect(await screen.findByText("Cases (1)")).toBeVisible();
    for (const classification of [
      "VERIFIED",
      "INFERRED",
      "UNKNOWN",
      "CONFLICTING",
    ] as const) {
      expect(screen.getByText(classification, { exact: true })).toHaveClass(
        "evidence-classification",
        `evidence-classification--${classification.toLowerCase()}`,
      );
    }
  });

  it("marks unavailable evidence classifications as warnings", async () => {
    const unavailable: OpenReviewCase = {
      ...caseFixture,
      evidenceAvailability: "UNAVAILABLE",
      sources: {
        prior: { ...caseFixture.sources.prior, evidenceAvailable: false },
        current: { ...caseFixture.sources.current, evidenceAvailable: true },
      },
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => [unavailable],
      }),
    );
    render(<OpenReviewCasesPage />);

    expect(
      await screen.findByText(
        "VERIFIED when recorded; source evidence now unavailable",
      ),
    ).toHaveClass("evidence-classification--warning");
    expect(
      screen.getByText("VERIFIED when recorded; source file now unavailable"),
    ).toHaveClass("evidence-classification--warning");
  });

  it("visually distinguishes missing, empty, and no-occurrence values", async () => {
    const missingAndEmpty: OpenReviewCase = {
      ...caseFixture,
      changeSet: {
        ...caseFixture.changeSet,
        changes: [
          {
            ...caseFixture.changeSet.changes[0],
            before: [{ state: "missing", value: null, attributes: {} }],
            after: [{ state: "empty", value: "", attributes: {} }],
          },
        ],
      },
    };
    const noOccurrences: OpenReviewCase = {
      ...caseFixture,
      caseId: "CASE-SIM-101",
      medicineIdentifier: "SIM-PKG-101",
      matchedRecord: {
        ...caseFixture.matchedRecord,
        medicineDisplay: "Fictional Beta",
      },
      changeSet: {
        ...caseFixture.changeSet,
        changeSetId: "CHANGESET-SIM-101",
        kind: "NO_LONGER_PRESENT",
        changes: [],
        lastKnownFields: [{ field: "Laakevalmiste/Antoreitti", values: [] }],
      },
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => [missingAndEmpty, noOccurrences],
      }),
    );
    render(<OpenReviewCasesPage />);

    expect(
      await screen.findByText("Not present in source", { exact: true }),
    ).toHaveClass("source-value--missing");
    expect(screen.getByText("Present but empty", { exact: true })).toHaveClass(
      "source-value--empty",
    );

    fireEvent.click(screen.getByRole("button", { name: /Fictional Beta/ }));
    expect(await screen.findByText("No occurrences")).toHaveClass(
      "source-value--no-occurrences",
    );
  });
});

describe("OpenReviewCasesPage review layouts (feature 003)", () => {
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  const removedCase: OpenReviewCase = {
    ...caseFixture,
    caseId: "CASE-SIM-300",
    medicineIdentifier: "SIM-PKG-300",
    matchedRecord: {
      recordId: "SIM-MED-300",
      personReference: "SIM-PERSON-300",
      medicineDisplay: "Fictional Removed",
    },
    changeSet: {
      changeSetId: "CHANGESET-SIM-300",
      kind: "NO_LONGER_PRESENT",
      detectedAt: "2099-01-03T00:00:00+00:00",
      changes: [],
      lastKnownFields: [
        {
          field: "Laakevalmiste/Kauppanimi",
          values: [
            { state: "value", value: "Fictional Removed", attributes: {} },
          ],
        },
      ],
    },
  };

  function serve(cases: OpenReviewCase[]) {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => cases }),
    );
  }

  it("uses the updated-package layout for changed fields", async () => {
    serve([caseFixture]);
    render(<OpenReviewCasesPage />);
    const evidence = await screen.findByRole("article", {
      name: "Evidence for CASE-SIM-100",
    });
    expect(evidence).toHaveClass("case-evidence--updated");
    expect(within(evidence).getByText("Updated package")).toBeVisible();
    expect(within(evidence).getByText("Before")).toBeVisible();
    expect(within(evidence).getByText("After")).toBeVisible();
    expect(within(evidence).getByText("1 field")).toBeVisible();
  });

  it("uses the removed-package layout without before and after", async () => {
    serve([removedCase]);
    render(<OpenReviewCasesPage />);
    const evidence = await screen.findByRole("article", {
      name: "Evidence for CASE-SIM-300",
    });
    expect(evidence).toHaveClass("case-evidence--removed");
    expect(within(evidence).getByText("Removed package")).toBeVisible();
    expect(
      within(evidence).getByRole("heading", {
        name: "Package no longer present in the register",
      }),
    ).toBeVisible();
    expect(within(evidence).queryByText("Before")).toBeNull();
    expect(within(evidence).queryByText("After")).toBeNull();
  });

  it("keeps every source-evidence field visible for both layouts", async () => {
    serve([caseFixture, removedCase]);
    render(<OpenReviewCasesPage />);
    await screen.findByText("Cases (2)");
    for (const name of [/Fictional Alpha/, /Fictional Removed/]) {
      fireEvent.click(screen.getByRole("button", { name }));
      for (const label of [
        "Record",
        "Simulated person",
        "Case created",
        "Source",
        "Release reference",
        "Release date",
        "Raw file",
        "Checksum",
        "Record locator",
        "Retrieved at",
      ]) {
        for (const term of screen.getAllByText(label, { exact: true })) {
          expect(term).toBeVisible();
        }
      }
      expect(screen.getByText(/^Source order:/)).toBeVisible();
      expect(
        screen.getByText(
          "Controlled synthetic source order, not retrieval time.",
        ),
      ).toBeVisible();
      expect(screen.getByText("synthetic-prior-checksum")).toBeVisible();
      expect(screen.getByText("synthetic-current-checksum")).toBeVisible();
    }
  });

  it("shows 'No occurrences' when a before or after list is empty", async () => {
    serve([
      {
        ...caseFixture,
        changeSet: {
          ...caseFixture.changeSet,
          changes: [
            {
              changeId: "CHANGE-SIM-EMPTY",
              field: "Laakevalmiste/Antoreitti",
              before: [],
              after: [
                { state: "value", value: "synthetic route", attributes: {} },
              ],
            },
          ],
        },
      },
    ]);
    render(<OpenReviewCasesPage />);
    expect(await screen.findByText("No occurrences")).toHaveClass(
      "source-value",
      "source-value--no-occurrences",
    );
    expect(screen.getByText("synthetic route")).toHaveClass(
      "source-value--value",
    );
  });

  it("marks a present field without a delivered value as unavailable", async () => {
    serve([
      {
        ...caseFixture,
        changeSet: {
          ...caseFixture.changeSet,
          changes: [
            {
              changeId: "CHANGE-SIM-NULL",
              field: "Laakevalmiste/Kauppanimi",
              before: [{ state: "value", value: null, attributes: {} }],
              after: [
                { state: "value", value: "Fictional Alpha", attributes: {} },
              ],
            },
          ],
        },
      },
    ]);
    render(<OpenReviewCasesPage />);
    const unavailable = await screen.findByText("Value unavailable");
    expect(unavailable).toHaveClass("source-value--value-unavailable");
    expect(unavailable).not.toHaveClass("source-value--value");
  });
});

describe("OpenReviewCasesPage case queue and change indicators (feature 003)", () => {
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  function caseWith(
    id: string,
    name: string,
    kind: "FIELDS_CHANGED" | "NO_LONGER_PRESENT" = "FIELDS_CHANGED",
  ): OpenReviewCase {
    return {
      ...caseFixture,
      caseId: `CASE-${id}`,
      medicineIdentifier: `SIM-PKG-${id}`,
      matchedRecord: { ...caseFixture.matchedRecord, medicineDisplay: name },
      changeSet: {
        ...caseFixture.changeSet,
        kind,
        changes: kind === "FIELDS_CHANGED" ? caseFixture.changeSet.changes : [],
        lastKnownFields: kind === "FIELDS_CHANGED" ? null : [],
      },
    };
  }

  const queue = [
    caseWith("100", "Fictional Alpha"),
    caseWith("200", "Fictional Beta"),
    caseWith("300", "Fictional Gamma", "NO_LONGER_PRESENT"),
  ];

  function serve(cases: OpenReviewCase[]) {
    const fetchMock = vi
      .fn()
      .mockResolvedValue({ ok: true, json: async () => cases });
    vi.stubGlobal("fetch", fetchMock);
    return fetchMock;
  }

  function caseButtons() {
    return within(
      screen.getByRole("navigation", { name: "Open review cases" }),
    ).queryAllByRole("button");
  }

  it("filters the loaded cases by name, identifier or summary without new requests", async () => {
    const fetchMock = serve(queue);
    render(<OpenReviewCasesPage />);
    await screen.findByText("Cases (3)");
    const search = screen.getByRole("searchbox", { name: "Search cases" });

    fireEvent.change(search, { target: { value: "beta" } });
    expect(caseButtons().map((b) => b.textContent)).toEqual([
      expect.stringContaining("Fictional Beta"),
    ]);
    expect(screen.getByText("Showing 1 of 3")).toBeInTheDocument();

    fireEvent.change(search, { target: { value: "SIM-PKG-300" } });
    expect(caseButtons()).toHaveLength(1);

    fireEvent.change(search, { target: { value: "no longer" } });
    expect(caseButtons().map((b) => b.textContent)).toEqual([
      expect.stringContaining("Fictional Gamma"),
    ]);

    fireEvent.change(search, { target: { value: "fictional alpha" } });
    expect(caseButtons()).toHaveLength(1);

    fireEvent.change(search, { target: { value: "" } });
    expect(caseButtons()).toHaveLength(3);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("says when no case matches and keeps the selected case's details", async () => {
    serve(queue);
    render(<OpenReviewCasesPage />);
    await screen.findByText("Cases (3)");
    fireEvent.change(screen.getByRole("searchbox", { name: "Search cases" }), {
      target: { value: "nothing like this" },
    });
    expect(caseButtons()).toHaveLength(0);
    expect(screen.getByText("No cases match this search.")).toBeVisible();
    expect(screen.getByText("Showing 0 of 3")).toBeInTheDocument();
    expect(
      screen.getByRole("article", { name: "Evidence for CASE-100" }),
    ).toBeVisible();
  });

  it("moves through the queue with arrow keys, Home and End", async () => {
    serve(queue);
    render(<OpenReviewCasesPage />);
    await screen.findByText("Cases (3)");
    const [first, second, third] = caseButtons();
    first.focus();
    fireEvent.keyDown(first, { key: "ArrowDown" });
    expect(second).toHaveFocus();
    fireEvent.keyDown(second, { key: "End" });
    expect(third).toHaveFocus();
    fireEvent.keyDown(third, { key: "ArrowDown" });
    expect(third).toHaveFocus();
    fireEvent.keyDown(third, { key: "Home" });
    expect(first).toHaveFocus();
    fireEvent.keyDown(first, { key: "ArrowUp" });
    expect(first).toHaveFocus();
    // Moving focus does not change the selection; Enter (a click) does.
    fireEvent.keyDown(first, { key: "ArrowDown" });
    expect(second).toHaveAttribute("aria-pressed", "false");
    fireEvent.click(second);
    expect(second).toHaveAttribute("aria-pressed", "true");
  });

  it("labels each changed field as added, removed or changed from source presence", async () => {
    const value = (v: string) => ({
      state: "value" as const,
      value: v,
      attributes: {},
    });
    const missing = { state: "missing" as const, value: null, attributes: {} };
    const empty = { state: "empty" as const, value: null, attributes: {} };
    serve([
      {
        ...caseFixture,
        changeSet: {
          ...caseFixture.changeSet,
          changes: [
            {
              changeId: "C1",
              field: "Field/Added",
              before: [missing],
              after: [value("new")],
            },
            {
              changeId: "C2",
              field: "Field/AddedFromNone",
              before: [],
              after: [empty],
            },
            {
              changeId: "C3",
              field: "Field/Removed",
              before: [value("old")],
              after: [missing],
            },
            {
              changeId: "C4",
              field: "Field/RemovedToNone",
              before: [value("old")],
              after: [],
            },
            {
              changeId: "C5",
              field: "Field/Changed",
              before: [value("a")],
              after: [value("b")],
            },
          ],
        },
      },
    ]);
    render(<OpenReviewCasesPage />);
    await screen.findByText("5 fields");
    const indicatorFor = (field: string) =>
      screen
        .getByText(field)
        .closest("li")!
        .querySelector(".change-indicator")!;
    expect(indicatorFor("Field/Added")).toHaveTextContent("Field added");
    expect(indicatorFor("Field/AddedFromNone")).toHaveTextContent(
      "Field added",
    );
    expect(indicatorFor("Field/Removed")).toHaveTextContent("Field removed");
    expect(indicatorFor("Field/RemovedToNone")).toHaveTextContent(
      "Field removed",
    );
    expect(indicatorFor("Field/Changed")).toHaveTextContent("Value changed");
    expect(indicatorFor("Field/Changed")).toHaveClass(
      "change-indicator--changed",
    );
    // The underlying value states keep their own wording.
    expect(screen.getAllByText("Not present in source")).toHaveLength(2);
    expect(screen.getAllByText("No occurrences")).toHaveLength(2);
    expect(screen.getByText("Present but empty")).toBeVisible();
  });

  it("labels the before and after sides with their releases", async () => {
    serve([caseFixture]);
    render(<OpenReviewCasesPage />);
    const evidence = await screen.findByRole("article", {
      name: "Evidence for CASE-SIM-100",
    });
    expect(
      within(evidence).getByRole("heading", { name: "Before Prior release" }),
    ).toBeVisible();
    expect(
      within(evidence).getByRole("heading", { name: "After Current release" }),
    ).toBeVisible();
  });
});

describe("sourceValue", () => {
  it("keeps missing, empty and plain values distinct", () => {
    expect(sourceValue({ state: "missing", value: null, attributes: {} })).toBe(
      "Not present in source",
    );
    expect(sourceValue({ state: "empty", value: "", attributes: {} })).toBe(
      "Present but empty",
    );
    expect(
      sourceValue({ state: "value", value: "10 mg", attributes: {} }),
    ).toBe("10 mg");
  });

  it("shows both text and attributes when an element has both", () => {
    expect(
      sourceValue({
        state: "value",
        value: "1",
        attributes: { listname: "L", id: "X" },
      }),
    ).toBe("1 — X (list L)");
  });
});
