import { useEffect, useRef, useState } from "react";
import { formatTimestamp } from "../open-review-cases/timestamp";
import {
  fetchShortageUpdate,
  startShortageUpdate,
  type DailyUpdates,
  type UpdateStatus,
} from "./shortagesApi";

export const POLL_INTERVAL_MS = 1500;

function time(value: string | null | undefined) {
  return value ? (formatTimestamp(value) ?? value) : null;
}

function Outcome({ status }: { status: UpdateStatus }) {
  if (status.phase === "FAILED") {
    return (
      <div className="shortage-outcome shortage-outcome--failed" role="alert">
        <p className="shortage-outcome-title">The update did not complete.</p>
        <p>{status.error}</p>
      </div>
    );
  }
  if (status.phase !== "SUCCEEDED" || !status.result) return null;
  return (
    <div className="shortage-outcome">
      <p className="shortage-outcome-title">
        {status.result.alreadyCaptured
          ? "No change: Fimea’s shortage file is the one already loaded."
          : `Shortage data updated: ${status.result.recordCount} shortages in Fimea’s file.`}
      </p>
    </div>
  );
}

function DailyLine({ daily }: { daily: DailyUpdates | null }) {
  if (!daily) return null;
  if (!daily.enabled) {
    return (
      <p className="shortage-daily">
        The daily automatic update is switched off (DAILY_UPDATE_TIME).
      </p>
    );
  }
  const run = daily.lastRun;
  const shortages = run?.outcome?.shortages;
  const register = run?.outcome?.basicRegister;
  return (
    <div className="shortage-daily">
      <p>
        Updates automatically every day at {daily.time}
        {daily.timeZone ? ` (${daily.timeZone})` : ""} while the backend runs,
        together with the Basic Register.
      </p>
      {run && (
        <p>
          Last automatic update {time(run.finishedAt ?? run.startedAt)}:
          shortages{" "}
          {shortages?.phase === "SUCCEEDED"
            ? shortages.result?.alreadyCaptured
              ? "unchanged"
              : "updated"
            : "not completed"}
          ; Basic Register{" "}
          {register?.phase === "SUCCEEDED"
            ? register.result?.alreadyCaptured
              ? "unchanged"
              : `new release ${register.result?.releaseDate ?? ""}`.trim()
            : "not completed"}
          .
        </p>
      )}
    </div>
  );
}

export default function ShortageUpdatePanel({
  daily,
  onUpdated,
}: {
  daily: DailyUpdates | null;
  onUpdated: () => void;
}) {
  const [status, setStatus] = useState<UpdateStatus | null>(null);
  const [requestError, setRequestError] = useState<string | null>(null);
  const timer = useRef<number | undefined>(undefined);

  useEffect(() => () => window.clearTimeout(timer.current), []);

  function follow(next: UpdateStatus) {
    setStatus(next);
    window.clearTimeout(timer.current);
    if (next.running) {
      timer.current = window.setTimeout(async () => {
        try {
          follow(await fetchShortageUpdate());
        } catch (error) {
          setRequestError((error as Error).message);
        }
      }, POLL_INTERVAL_MS);
    } else if (next.phase === "SUCCEEDED") {
      onUpdated();
    }
  }

  async function start() {
    setRequestError(null);
    try {
      follow(await startShortageUpdate());
    } catch (error) {
      setRequestError((error as Error).message);
    }
  }

  const running = status?.running ?? false;
  return (
    <section
      className="catalogue-card shortage-update"
      aria-labelledby="shortage-update-heading"
    >
      <h2 id="shortage-update-heading">Updates</h2>
      <button
        type="button"
        className="shortage-update-button"
        onClick={start}
        disabled={running}
        aria-describedby="shortage-update-status"
      >
        Update shortage data
      </button>
      <div
        id="shortage-update-status"
        role="status"
        className="shortage-update-status"
      >
        {running && <p>Downloading Fimea’s shortage file…</p>}
        {requestError && (
          <p className="shortage-update-error">
            The backend could not be reached. {requestError}
          </p>
        )}
      </div>
      {status && !running && <Outcome status={status} />}
      <DailyLine daily={daily} />
    </section>
  );
}
