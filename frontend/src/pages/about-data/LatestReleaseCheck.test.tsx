// Feature 005: the "Check for new Fimea release" control on About the Data.
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { CLINICAL_WORDS } from "../../test/clinicalWords";
import AboutDataPage from "./AboutDataPage";
import { POLL_INTERVAL_MS } from "./LatestReleaseCheck";
import type { CheckStatus } from "./releaseCheckApi";

const URL = "/api/source-releases/latest-check";

function status(overrides: Partial<CheckStatus>): CheckStatus {
  return {
    phase: "IDLE",
    running: false,
    sourceUrl: "https://data.pilvi.fimea.fi/avoin-data/Perusrekisteri.xml",
    startedAt: "2026-11-21T09:00:00+00:00",
    finishedAt: null,
    downloadedBytes: null,
    result: null,
    error: null,
    ...overrides,
  };
}

const RESULT = {
  processingStatus: "VALIDATED",
  chronologyStatus: "AVAILABLE",
  capturedReleaseReference: "sha256-401a",
  failureDetail: null,
  alreadyCaptured: false,
  releaseDate: "2026-11-20",
  reviewCasesCreated: 3,
};

function reply(body: CheckStatus, ok = true) {
  return { ok, status: ok ? 202 : 500, json: async () => body };
}

describe("Fimea release updates (feature 005)", () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    cleanup();
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  function button() {
    return screen.getByRole("button", { name: "Check for new Fimea release" });
  }

  it("makes no request until the button is pressed", () => {
    render(<AboutDataPage />);
    expect(button()).toBeEnabled();
    expect(fetchMock).not.toHaveBeenCalled();
    expect(document.body.textContent ?? "").not.toMatch(CLINICAL_WORDS);
  });

  it("starts a check, follows its progress and reports a new release", async () => {
    fetchMock
      .mockResolvedValueOnce(
        reply(status({ phase: "DOWNLOADING", running: true, started: true })),
      )
      .mockResolvedValueOnce(
        reply(status({ phase: "INGESTING", running: true })),
      )
      .mockResolvedValueOnce(
        reply(
          status({
            phase: "SUCCEEDED",
            finishedAt: "2026-11-21T09:01:30+00:00",
            downloadedBytes: 199_465_476,
            result: RESULT,
          }),
        ),
      );
    render(<AboutDataPage />);
    fireEvent.click(button());

    expect(
      await screen.findByText("Downloading the latest release from Fimea…"),
    ).toBeVisible();
    expect(button()).toBeDisabled();
    expect(fetchMock).toHaveBeenNthCalledWith(1, URL, { method: "POST" });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(POLL_INTERVAL_MS);
    });
    expect(screen.getByText("Checking and saving the release…")).toBeVisible();
    expect(fetchMock).toHaveBeenNthCalledWith(2, URL);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(POLL_INTERVAL_MS);
    });
    expect(
      screen.getByText("New release loaded: release date 2026-11-20."),
    ).toBeVisible();
    expect(
      screen.getByText(
        /3 new review cases were created\. See Open Review Cases\./,
      ),
    ).toBeVisible();
    expect(screen.getByText("Checked 2026-11-21 09:01 UTC")).toBeVisible();
    expect(button()).toBeEnabled();

    // Polling stops once the check has finished.
    await act(async () => {
      await vi.advanceTimersByTimeAsync(POLL_INTERVAL_MS * 3);
    });
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(document.body.textContent ?? "").not.toMatch(CLINICAL_WORDS);
  });

  it("says plainly when Fimea's file is the one already loaded", async () => {
    fetchMock.mockResolvedValueOnce(
      reply(
        status({
          phase: "SUCCEEDED",
          finishedAt: "2026-11-21T09:01:30+00:00",
          downloadedBytes: 199_465_476,
          result: { ...RESULT, alreadyCaptured: true, reviewCasesCreated: 0 },
          started: true,
        }),
      ),
    );
    render(<AboutDataPage />);
    fireEvent.click(button());
    expect(await screen.findByText("No new release.")).toBeVisible();
    expect(
      screen.getByText(
        /The file on Fimea’s site \(190\.2 MB\) is the one already loaded/,
      ),
    ).toBeVisible();
  });

  it("shows a failed check as an alert with the backend's reason", async () => {
    fetchMock.mockResolvedValueOnce(
      reply(
        status({
          phase: "FAILED",
          finishedAt: "2026-11-21T09:00:05+00:00",
          error: "Could not reach Fimea: timed out.",
          started: true,
        }),
      ),
    );
    render(<AboutDataPage />);
    fireEvent.click(button());
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("The check did not complete.");
    expect(alert).toHaveTextContent("Could not reach Fimea: timed out.");
    expect(button()).toBeEnabled();
  });

  it("follows a check that is already running instead of starting another", async () => {
    fetchMock.mockResolvedValueOnce(
      reply(
        status({ phase: "PREPARING_CATALOGUE", running: true, started: false }),
      ),
    );
    render(<AboutDataPage />);
    fireEvent.click(button());
    expect(
      await screen.findByText("Preparing the Medicine Catalogue…"),
    ).toBeVisible();
    expect(button()).toBeDisabled();
  });

  it("reports when the backend cannot be reached", async () => {
    fetchMock.mockRejectedValueOnce(new TypeError("Failed to fetch"));
    render(<AboutDataPage />);
    fireEvent.click(button());
    expect(
      await screen.findByText(
        "The backend could not be reached. Failed to fetch",
      ),
    ).toBeVisible();
    expect(button()).toBeEnabled();
  });
});
