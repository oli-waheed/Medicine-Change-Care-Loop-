import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import OpenReviewCasesPage from "./OpenReviewCasesPage";
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
  change: {
    changeId: "CHANGE-SIM-100",
    field: "Laakevalmiste/Kauppanimi",
    before: [{ state: "value", value: "Fictional Alpha", attributes: {} }],
    after: [{ state: "value", value: "Fictional Alpha Revised", attributes: {} }],
    detectedAt: "2099-01-03T00:00:00+00:00",
  },
  sources: {
    prior: {
      sourceName: "Fimea Basic Register",
      releaseDate: { state: "value", value: "2099-01-01", attributes: {} },
      releaseReference: { state: "value", value: "SIM-2099-001", attributes: {} },
      fileName: "prior-release.xml",
      checksum: "synthetic-prior-checksum",
      recordIdentifier: "SIM-PKG-100",
      recordLocator: "/Perusrekisteri/Pakkaus[1]",
      fieldReference: "Laakevalmiste/Kauppanimi",
      evidenceClass: "VERIFIED",
      note: null,
      retrievedAt: null,
    },
    current: {
      sourceName: "Fimea Basic Register",
      releaseDate: { state: "value", value: "2099-01-02", attributes: {} },
      releaseReference: { state: "value", value: "SIM-2099-002", attributes: {} },
      fileName: "current-release.xml",
      checksum: "synthetic-current-checksum",
      recordIdentifier: "SIM-PKG-100",
      recordLocator: "/Perusrekisteri/Pakkaus[1]",
      fieldReference: "Laakevalmiste/Kauppanimi",
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
  it("shows the open-case list and source evidence without decision or closure actions", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => [caseFixture],
      }),
    );
    render(<OpenReviewCasesPage />);

    expect(await screen.findByRole("heading", { name: "Open review cases" })).toBeVisible();
    expect(screen.getAllByText("Fictional Alpha Revised").length).toBeGreaterThan(0);
    expect(screen.getByText("SIM-PKG-100")).toBeVisible();
    expect(screen.getAllByText("Fictional Alpha").length).toBeGreaterThan(0);
    expect(screen.getByText("SIM-PERSON-100")).toBeVisible();
    expect(screen.getByText("prior-release.xml")).toBeVisible();
    expect(screen.getByText("current-release.xml")).toBeVisible();
    expect(screen.getByText("Controlled synthetic source order, not retrieval time.")).toBeVisible();
    expect(screen.queryByRole("button", { name: /close|resolve|recommend/i })).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: /Fictional Alpha/ }));
    expect(screen.getByRole("button", { name: /Fictional Alpha/ })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
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
    expect(await screen.findByText("There are no NEW review cases.")).toBeVisible();
  });
});
