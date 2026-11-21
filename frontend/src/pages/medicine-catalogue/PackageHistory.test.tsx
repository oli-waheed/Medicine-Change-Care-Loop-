// Feature 013: a package's change history in the Medicine Catalogue, against
// responses captured from the real backend over three synthetic releases.
import {
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "../../App";
import { catalogueFetch } from "../../test/catalogueFixtures";
import { CLINICAL_WORDS } from "../../test/clinicalWords";
import PackageHistoryCard from "./PackageHistoryCard";

function history() {
  return screen.getByRole("region", { name: "Package change history" });
}

describe("Package change history (feature 013)", () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn(async (url: string) => catalogueFetch(url));
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    window.history.replaceState(null, "", "/");
  });

  it("shows each compared release with the values before and after, newest first", async () => {
    window.history.replaceState(null, "", "/medicine-catalogue");
    render(<App />);
    await screen.findByText("Showing 1–4 of 4 packages");
    fireEvent.click(screen.getByRole("button", { name: /SIM-PKG-100/ }));
    await screen.findByRole("article", { name: "Package SIM-PKG-100" });
    const entries = await within(history()).findAllByRole("listitem");
    expect(
      entries.map((entry) => entry.querySelector("strong")?.textContent),
    ).toEqual(["2099-01-02 → 2099-01-03", "2099-01-01 → 2099-01-02"]);
    expect(
      within(entries[0]).getAllByText("Spacing or letter case only"),
    ).toHaveLength(2);
    const table = within(entries[1]).getByRole("table", {
      name: "Changed fields 2099-01-01 → 2099-01-02",
    });
    const name = within(table)
      .getAllByRole("row")
      .find((row) => row.textContent?.includes("Kauppanimi"))!;
    expect(name).toHaveTextContent("Fictional Product Amber");
    expect(name).toHaveTextContent("Fictional Product Amber Revised");
    expect(document.body.textContent ?? "").not.toMatch(CLINICAL_WORDS);
    // Only reads.
    for (const [url, options] of fetchMock.mock.calls) {
      expect(String(url)).toMatch(/^\/api\/medicine-catalogue/);
      expect(options?.method ?? "GET").toBe("GET");
    }
  });

  it("names removed and new packages", async () => {
    render(<PackageHistoryCard pakkaustunnus="SIM-PKG-300" />);
    expect(
      await within(history()).findByText("No longer in the register"),
    ).toBeVisible();
    cleanup();
    render(<PackageHistoryCard pakkaustunnus="SIM-PKG-400" />);
    expect(
      await within(history()).findByText("New in the register"),
    ).toBeVisible();
    expect(within(history()).queryByRole("table")).toBeNull();
  });

  it("explains when there is no history", async () => {
    render(<PackageHistoryCard pakkaustunnus="SIM-PKG-UNKNOWN" />);
    expect(
      await screen.findByText(
        "No two releases have been compared yet, so there is no history.",
      ),
    ).toBeVisible();
    cleanup();

    fetchMock.mockImplementation(async () => ({
      ok: true,
      status: 200,
      json: async () => ({
        pakkaustunnus: "SIM-PKG-9",
        comparedPairs: [
          { priorReleaseDate: "2099-01-01", currentReleaseDate: "2099-01-02" },
        ],
        events: [],
      }),
    }));
    render(<PackageHistoryCard pakkaustunnus="SIM-PKG-9" />);
    expect(
      await screen.findByText(
        /No change recorded for this package in the compared releases \(\s*2099-01-01 → 2099-01-02\)/,
      ),
    ).toBeVisible();
  });
});
