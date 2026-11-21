// Feature 010: Source History, against a response captured from the real
// backend (src/test/sourceHistoryResponse.json).
import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import response from "../../test/sourceHistoryResponse.json";
import { CLINICAL_WORDS } from "../../test/clinicalWords";
import SourceHistoryPage from "./SourceHistoryPage";
import type { SourceHistory } from "./sourceHistoryApi";

const HISTORY = response as SourceHistory;

function serve(body: unknown, ok = true, status = 200) {
  const fetchMock = vi.fn(async (_url: string) => ({
    ok,
    status,
    json: async () => structuredClone(body),
  }));
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("Source History (feature 010)", () => {
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("shows each release check with its results and counts", async () => {
    const fetchMock = serve(HISTORY);
    render(<SourceHistoryPage />);
    const passed = await screen.findByRole("article", {
      name: "Check of 2099-01-03 to 2099-01-10",
    });
    expect(within(passed).getByText("All checks passed")).toBeVisible();
    const attention = screen.getByRole("article", {
      name: "Check of 2099-01-02 to 2099-01-03",
    });
    expect(within(attention).getByText("Worth a look")).toBeVisible();
    expect(
      within(attention).getByText(/3 packages \(75\.00 %\); limit 10%/),
    ).toBeVisible();
    expect(
      within(attention).getAllByText("Attention", {
        selector: ".check-status",
      }),
    ).toHaveLength(1);
    expect(within(attention).getByText("4 → 4")).toBeVisible();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0][0]).toBe("/api/source-history");
    expect(document.body.textContent ?? "").not.toMatch(CLINICAL_WORDS);
  });

  it("shows field completeness and marks checks made by an earlier version", async () => {
    serve({
      ...HISTORY,
      qualityChecks: [
        HISTORY.qualityChecks[0],
        {
          ...HISTORY.qualityChecks[1],
          upToDate: false,
          completeness: undefined,
        },
      ],
    });
    render(<SourceHistoryPage />);
    const current = await screen.findByRole("article", {
      name: "Check of 2099-01-03 to 2099-01-10",
    });
    const table = within(current).getByRole("table", {
      name: "Packages with each field (prior → current release)",
    });
    const vnr = within(table)
      .getAllByRole("row")
      .find((row) => row.textContent?.startsWith("VNR-numero"))!;
    expect(vnr).toHaveTextContent("VNR-numero100.00 %100.00 %");
    expect(within(current).getByText(/Source structure\./)).toBeVisible();
    expect(within(current).queryByText(/earlier version/)).toBeNull();

    const older = screen.getByRole("article", {
      name: "Check of 2099-01-02 to 2099-01-03",
    });
    expect(within(older).getByText(/Made by an earlier version/)).toBeVisible();
    expect(within(older).queryByRole("table")).toBeNull();
  });

  it("lists stored releases newest first with downloads and checksums", async () => {
    serve(HISTORY);
    render(<SourceHistoryPage />);
    await screen.findByText("Basic Register releases (3)");
    const releases = screen
      .getAllByRole("article")
      .filter((item) =>
        item.getAttribute("aria-label")?.startsWith("Basic Register release"),
      );
    expect(
      releases.map((item) => item.querySelector("h3")?.textContent),
    ).toEqual(["2099-01-10", "2099-01-03", "2099-01-02"]);
    expect(within(releases[0]).getByText("Catalogue release")).toBeVisible();
    expect(within(releases[1]).queryByText("Catalogue release")).toBeNull();
    // The 2099-01-03 file was downloaded twice.
    expect(
      within(releases[1]).getByText("Downloads").nextSibling?.textContent,
    ).toBe("2");
    expect(
      within(releases[1]).getByText(HISTORY.basicRegister[1].checksum!),
    ).toBeVisible();
  });

  it("lists shortage files and marks the one shown now", async () => {
    serve(HISTORY);
    render(<SourceHistoryPage />);
    await screen.findByText("Shortage files (2)");
    const files = screen
      .getAllByRole("article")
      .filter((item) =>
        item.getAttribute("aria-label")?.startsWith("Shortage file"),
      );
    expect(within(files[0]).getByText("Shown now")).toBeVisible();
    expect(within(files[1]).queryByText("Shown now")).toBeNull();
    expect(
      within(files[1]).getByText("Downloads").nextSibling?.textContent,
    ).toBe("2");
  });

  it("names unchecked pairs and missing files", async () => {
    serve({
      ...HISTORY,
      uncheckedPairs: [
        { priorReleaseDate: "2099-01-01", currentReleaseDate: "2099-01-02" },
      ],
      basicRegister: [
        { ...HISTORY.basicRegister[0], evidenceAvailable: false },
        ...HISTORY.basicRegister.slice(1),
      ],
    });
    render(<SourceHistoryPage />);
    expect(
      await screen.findByText(
        "2099-01-01 → 2099-01-02: not checked yet. The next daily update checks it.",
      ),
    ).toBeVisible();
    expect(screen.getByText("No longer stored")).toBeVisible();
  });

  it("shows empty states and load errors", async () => {
    serve({
      basicRegister: [],
      qualityChecks: [],
      uncheckedPairs: [],
      shortageFiles: [],
    });
    render(<SourceHistoryPage />);
    expect(await screen.findByText("No release stored yet.")).toBeVisible();
    expect(screen.getByText(/No release pair yet/)).toBeVisible();
    expect(screen.getByText("No shortage file stored yet.")).toBeVisible();
    cleanup();

    serve({}, false, 500);
    render(<SourceHistoryPage />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Source history could not be loaded (HTTP 500).",
    );
  });

  it("offers no controls at all", async () => {
    serve(HISTORY);
    render(<SourceHistoryPage />);
    await screen.findByText("Shortage files (2)");
    expect(screen.queryAllByRole("button")).toHaveLength(0);
    expect(
      document.querySelectorAll("input, select, textarea, form"),
    ).toHaveLength(0);
  });
});
