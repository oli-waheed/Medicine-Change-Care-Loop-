// Feature 012: new source files and checks on Source History and Medicine
// Shortages, against responses captured from the real backend.
import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { resetVisitForTests } from "../../app/lastVisit";
import MedicineShortagesPage from "../medicine-shortages/MedicineShortagesPage";
import { shortageFetch } from "../../test/shortageFixtures";
import response from "../../test/sourceHistoryResponse.json";
import SourceHistoryPage from "./SourceHistoryPage";

function visitedBefore(previous: string) {
  resetVisitForTests();
  window.localStorage.setItem(
    "mccl:visits",
    // The stored visit is still running (its last time is not 30 minutes
    // old), so its previous visit is the one this page compares with.
    JSON.stringify({ previous, last: "2999-01-01T00:00:00.000Z" }),
  );
}

describe("New since your last visit on other pages (feature 012)", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    window.localStorage.clear();
  });

  it("marks releases and shortage files first downloaded since the last visit", async () => {
    visitedBefore("2099-01-05T00:00:00.000Z");
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({
        ok: true,
        status: 200,
        json: async () => structuredClone(response),
      })),
    );
    render(<SourceHistoryPage />);
    await screen.findByText("Shortage files (2)");
    // Releases of 2099-01-11 and 2099-01-05 (06:00), and the 2099-01-11 file.
    expect(
      screen.getByText(
        "3 items are new since your last visit (2099-01-05 00:00 UTC).",
      ),
    ).toBeVisible();
    const marked = screen
      .getAllByRole("article")
      .filter((card) => within(card).queryByText("New since last visit"))
      .map((card) => card.getAttribute("aria-label"));
    expect(marked).toEqual([
      "Basic Register release 2099-01-10",
      "Basic Register release 2099-01-03",
      expect.stringMatching(/^Shortage file first downloaded 2099-01-11/),
    ]);
  });

  it("marks shortages whose Updated date is on or after the last visit's day", async () => {
    visitedBefore("2099-01-02T12:00:00.000Z");
    vi.stubGlobal("fetch", vi.fn(shortageFetch));
    render(<MedicineShortagesPage />);
    await screen.findByText("Showing 1–3 of 3 shortages");
    const rows = screen.getAllByRole("row").slice(1);
    const marked = rows
      .filter((row) => within(row).queryByText("Since last visit"))
      .map((row) => within(row).getByRole("rowheader").textContent);
    expect(marked).toEqual(["SIM-VNR-200", "SIM-VNR-500"]);
  });
});
