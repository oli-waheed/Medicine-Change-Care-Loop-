import { cleanup, fireEvent, render, screen } from "@testing-library/react";
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
      await screen.findByText("There are no NEW review cases."),
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
