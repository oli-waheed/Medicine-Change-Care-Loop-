import { useEffect, useRef, useState } from "react";
import { formatTimestamp } from "../open-review-cases/timestamp";
import {
  fetchLatestReleaseCheck,
  startLatestReleaseCheck,
  type CheckStatus,
} from "./releaseCheckApi";

export const POLL_INTERVAL_MS = 2000;

const RUNNING_TEXT: Record<string, string> = {
  DOWNLOADING: "Downloading the latest release from Fimea…",
  INGESTING: "Checking and saving the release…",
  PREPARING_CATALOGUE: "Preparing the Medicine Catalogue…",
};

function megabytes(bytes: number | null) {
  return bytes === null ? "" : ` (${(bytes / 1024 / 1024).toFixed(1)} MB)`;
}

function Outcome({ status }: { status: CheckStatus }) {
  const result = status.result;
  if (status.phase === "FAILED") {
    return (
      <div
        className="release-check-outcome release-check-outcome--failed"
        role="alert"
      >
        <p className="release-check-title">The check did not complete.</p>
        <p>{status.error}</p>
      </div>
    );
  }
  if (status.phase !== "SUCCEEDED" || !result) return null;
  if (result.alreadyCaptured) {
    return (
      <div className="release-check-outcome">
        <p className="release-check-title">No new release.</p>
        <p>
          The file on Fimea’s site{megabytes(status.downloadedBytes)} is the one
          already loaded. Its retrieval time was recorded.
        </p>
      </div>
    );
  }
  const cases = result.reviewCasesCreated;
  return (
    <div className="release-check-outcome release-check-outcome--new">
      <p className="release-check-title">
        New release loaded
        {result.releaseDate ? `: release date ${result.releaseDate}` : ""}.
      </p>
      <p>
        {cases === 0
          ? "No new review cases were created."
          : `${cases} new review ${cases === 1 ? "case was" : "cases were"} created. See Open Review Cases.`}{" "}
        The Medicine Catalogue now shows the latest validated release.
      </p>
    </div>
  );
}

// Feature 005: the one control in the app that loads data. It does what the
// daily n8n workflow does: download Perusrekisteri.xml and ingest it.
export default function LatestReleaseCheck() {
  const [status, setStatus] = useState<CheckStatus | null>(null);
  const [requestError, setRequestError] = useState<string | null>(null);
  const timer = useRef<number | undefined>(undefined);

  useEffect(() => () => window.clearTimeout(timer.current), []);

  function follow(next: CheckStatus) {
    setStatus(next);
    window.clearTimeout(timer.current);
    if (next.running) {
      timer.current = window.setTimeout(async () => {
        try {
          follow(await fetchLatestReleaseCheck());
        } catch (error) {
          setRequestError((error as Error).message);
        }
      }, POLL_INTERVAL_MS);
    }
  }

  async function start() {
    setRequestError(null);
    try {
      follow(await startLatestReleaseCheck());
    } catch (error) {
      setRequestError((error as Error).message);
    }
  }

  const running = status?.running ?? false;
  return (
    <section
      className="about-card release-check"
      aria-labelledby="about-release-check"
    >
      <h2 id="about-release-check">Fimea release updates</h2>
      <p>
        The backend downloads the latest Basic Register file from Fimea and
        loads it, exactly as the daily scheduled workflow does. An unchanged
        file is recognised and not stored twice; a newer release is compared
        with the previous one. This takes about one to two minutes.
      </p>
      <button
        type="button"
        className="release-check-button"
        onClick={start}
        disabled={running}
        aria-describedby="release-check-status"
      >
        Check for new Fimea release
      </button>
      <div
        id="release-check-status"
        role="status"
        className="release-check-status"
      >
        {running && status && <p>{RUNNING_TEXT[status.phase]}</p>}
        {requestError && (
          <p className="release-check-error">
            The backend could not be reached. {requestError}
          </p>
        )}
      </div>
      {status && !running && <Outcome status={status} />}
      {status?.finishedAt && !running && (
        <p className="release-check-time">
          Checked {formatTimestamp(status.finishedAt) ?? status.finishedAt}
        </p>
      )}
    </section>
  );
}
