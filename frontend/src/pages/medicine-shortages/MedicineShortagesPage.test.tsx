// Feature 006: the Medicine Shortages page against API responses captured from
// the real backend over synthetic files (src/test/shortageResponses.json).
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "../../App";
import { shortageFetch, shortageResponse } from "../../test/shortageFixtures";
import { CLINICAL_WORDS } from "../../test/clinicalWords";
import { CATALOGUE_RETRY_MS } from "./MedicineShortagesPage";
import { POLL_INTERVAL_MS } from "./ShortageUpdatePanel";
import type { ShortagePage } from "./shortagesApi";

const LISTING = "/api/shortages?pageSize=50";

function renderPage() {
  window.history.replaceState(null, "", "/medicine-shortages");
  return render(<App />);
}

async function loaded() {
  await screen.findByText("Showing 1–3 of 3 shortages");
}

function rows() {
  const table = screen.getByRole("table", {
    name: "Shortages in Fimea’s file, in the file’s order",
  });
  return within(table).getAllByRole("row").slice(1);
}

describe("Medicine Shortages (feature 006)", () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn(async (url: string, init?: RequestInit) =>
      shortageFetch(url, init),
    );
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    cleanup();
    vi.useRealTimers();
    vi.unstubAllGlobals();
    window.history.replaceState(null, "", "/");
  });

  function requested() {
    return fetchMock.mock.calls.map(([url]) => String(url));
  }

  it("is reachable from the sidebar and lists the file as published", async () => {
    window.history.replaceState(null, "", "/about-data");
    render(<App />);
    const nav = screen.getByRole("navigation", { name: "Main navigation" });
    fireEvent.click(
      within(nav).getByRole("link", { name: "Medicine Shortages" }),
    );
    expect(
      await screen.findByRole("heading", {
        level: 1,
        name: "Medicine Shortages",
      }),
    ).toBeVisible();
    expect(window.location.pathname).toBe("/medicine-shortages");
    expect(document.title).toBe(
      "Medicine Shortages | Medicine Change Care Loop",
    );
    await loaded();

    const source = screen.getByRole("region", { name: "Shortage data source" });
    expect(source).toHaveTextContent("Fimea shortage data (Shortages.txt)");
    expect(source).toHaveTextContent("2099-01-05 04:00 UTC");
    expect(source).toHaveTextContent("2099-01-02");
    expect(source).toHaveTextContent("3 (1 E · 2 K)");
    expect(source).toHaveTextContent("CC BY 4.0");
    expect(source).toHaveTextContent(
      "https://data.pilvi.fimea.fi/avoin-data/Shortages.txt",
    );

    const cells = rows().map((row) =>
      Array.from((row as HTMLTableRowElement).cells).map(
        (cell) => cell.textContent,
      ),
    );
    expect(cells.map((row) => row[0])).toEqual([
      "SIM-VNR-200",
      "SIM-VNR-900",
      "SIM-VNR-500",
    ]);
    expect(cells[0][1]).toContain("Fictional Product Blue");
    expect(cells[0][1]).toContain("Package ID SIM-PKG-200");
    expect(cells[0].slice(2)).toEqual([
      "K",
      "2099-01-01",
      "2099-02-15",
      "2098-12-01",
      "2099-01-02",
      "Fictional Pharma Oy",
    ]);
    expect(cells[1][1]).toBe(
      "No package with this VNR in the active catalogue release",
    );
    expect(document.body.textContent ?? "").not.toMatch(CLINICAL_WORDS);
  });

  it("states that the dates are the company's report and points to no other products", async () => {
    renderPage();
    await loaded();
    expect(
      screen.getByText(/Dates and status are the company’s report to Fimea/),
    ).toBeVisible();
    expect(screen.getByText(/does not point to other products/)).toBeVisible();
  });

  it("searches and filters through the API", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    renderPage();
    await loaded();
    fireEvent.change(
      screen.getByRole("searchbox", { name: "Search shortages" }),
      {
        target: { value: " Fictional " },
      },
    );
    await act(async () => {
      await vi.advanceTimersByTimeAsync(400);
    });
    expect(requested()).toContain("/api/shortages?q=Fictional&pageSize=50");

    const status = screen.getByRole("combobox", { name: "Status (Valid)" });
    expect(
      within(status)
        .getAllByRole("option")
        .map((option) => option.textContent),
    ).toEqual(["All", "E (ongoing: no)", "K (ongoing: yes)"]);
    fireEvent.change(status, { target: { value: "E" } });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(10);
    });
    expect(requested()).toContain(
      "/api/shortages?q=Fictional&valid=E&pageSize=50",
    );
  });

  it("downloads the latest file with the Update button and reloads the list", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    renderPage();
    await loaded();
    const listingsBefore = requested().filter((url) => url === LISTING).length;

    fireEvent.click(
      screen.getByRole("button", { name: "Update shortage data" }),
    );
    expect(
      await screen.findByText("Downloading Fimea’s shortage file…"),
    ).toBeVisible();
    expect(
      screen.getByRole("button", { name: "Update shortage data" }),
    ).toBeDisabled();
    expect(fetchMock).toHaveBeenCalledWith("/api/shortages/update", {
      method: "POST",
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(POLL_INTERVAL_MS);
    });
    expect(
      screen.getByText("Shortage data updated: 3 shortages in Fimea’s file."),
    ).toBeVisible();
    expect(
      screen.getByRole("button", { name: "Update shortage data" }),
    ).toBeEnabled();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(10);
    });
    expect(requested().filter((url) => url === LISTING).length).toBe(
      listingsBefore + 1,
    );
  });

  it("reports a failed update as an alert and keeps the list", async () => {
    renderPage();
    await loaded();
    fetchMock.mockImplementation(async (url: string, init?: RequestInit) =>
      init?.method === "POST"
        ? {
            ok: true,
            status: 202,
            json: async () => ({
              phase: "FAILED",
              running: false,
              trigger: "BUTTON",
              startedAt: "2099-01-06T04:00:00+00:00",
              finishedAt: "2099-01-06T04:00:01+00:00",
              result: null,
              error: "Could not reach Fimea: timed out.",
              started: true,
            }),
          }
        : shortageFetch(url, init),
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Update shortage data" }),
    );
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("The update did not complete.");
    expect(alert).toHaveTextContent("Could not reach Fimea: timed out.");
    expect(rows()).toHaveLength(3);
  });

  it("shows the daily automatic update and its last run", async () => {
    renderPage();
    await loaded();
    expect(
      await screen.findByText(
        /Updates automatically every day at 06:00 \(EET\) while the backend runs/,
      ),
    ).toBeVisible();
    expect(
      screen.getByText(
        /Last automatic update 2099-01-05 04:00 UTC: shortages updated; Basic Register new release 2099-01-02\./,
      ),
    ).toBeVisible();
  });

  it("asks for the first download when there is no shortage data yet", async () => {
    fetchMock.mockImplementation(async (url: string, init?: RequestInit) =>
      url.startsWith("/api/shortages?")
        ? {
            ok: false,
            status: 503,
            json: async () => ({
              detail: {
                code: "SHORTAGES_UNAVAILABLE",
                message: "No shortage data has been downloaded yet.",
              },
            }),
          }
        : shortageFetch(url, init),
    );
    renderPage();
    expect(await screen.findByText("No shortage data yet")).toBeVisible();
    expect(
      screen.getByRole("button", { name: "Update shortage data" }),
    ).toBeEnabled();
    expect(screen.queryByRole("table")).toBeNull();
  });

  it("shows the list at once and adds catalogue packages when they are ready", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const ready = shortageResponse<ShortagePage>(LISTING);
    const loading: ShortagePage = {
      ...ready,
      catalogue: { status: "LOADING", releaseId: null, releaseDate: null },
      items: ready.items.map((item) => ({ ...item, packages: null })),
    };
    let first = true;
    fetchMock.mockImplementation(async (url: string, init?: RequestInit) => {
      if (url === LISTING && first) {
        first = false;
        return { ok: true, status: 200, json: async () => loading };
      }
      return shortageFetch(url, init);
    });
    renderPage();
    await loaded();
    expect(rows()[0]).toHaveTextContent("Loading from the Medicine Catalogue…");
    await act(async () => {
      await vi.advanceTimersByTimeAsync(CATALOGUE_RETRY_MS + 10);
    });
    expect(rows()[0]).toHaveTextContent("Fictional Product Blue");
  });
});
