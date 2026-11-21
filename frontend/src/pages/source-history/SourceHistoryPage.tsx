import { useEffect, useState } from "react";
import NewSinceVisit, { NewBadge } from "../../app/NewSinceVisit";
import { isNewSince } from "../../app/lastVisit";
import { usePreviousVisit } from "../../app/useLastVisit";
import TimestampDisplay from "../open-review-cases/evidence/TimestampDisplay";
import {
  fetchSourceHistory,
  type CheckStatus,
  type QualityCheck,
  type SourceHistory,
  type StoredRelease,
  type StoredShortageFile,
} from "./sourceHistoryApi";
import "./SourceHistoryPage.css";

const STATUS_LABELS: Record<CheckStatus, string> = {
  PASSED: "Passed",
  ATTENTION: "Attention",
  INFO: "Info",
};

const number = new Intl.NumberFormat("en-GB");

function size(bytes: number | null): string {
  if (bytes === null) return "unknown size";
  if (bytes >= 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  return `${Math.max(1, Math.round(bytes / 1024))} kB`;
}

function Downloads({
  first,
  last,
  count,
}: {
  first: string;
  last: string;
  count: number;
}) {
  return (
    <>
      <div>
        <dt>First downloaded</dt>
        <dd>
          <TimestampDisplay value={first} fallback={first} />
        </dd>
      </div>
      <div>
        <dt>Last downloaded</dt>
        <dd>
          <TimestampDisplay value={last} fallback={last} />
        </dd>
      </div>
      <div>
        <dt>Downloads</dt>
        <dd>{count}</dd>
      </div>
    </>
  );
}

function FileFacts({
  checksum,
  sizeBytes,
  evidenceAvailable,
}: {
  checksum: string | null;
  sizeBytes: number | null;
  evidenceAvailable: boolean;
}) {
  return (
    <>
      <div>
        <dt>Size</dt>
        <dd>{size(sizeBytes)}</dd>
      </div>
      <div className="history-facts-wide">
        <dt>SHA-256 checksum</dt>
        <dd className="monospace-value history-checksum">
          {checksum ?? "not recorded"}
        </dd>
      </div>
      <div>
        <dt>Stored file</dt>
        <dd>
          {evidenceAvailable ? (
            "Available"
          ) : (
            <span className="history-warning">No longer stored</span>
          )}
        </dd>
      </div>
    </>
  );
}

function CheckCard({ check }: { check: QualityCheck }) {
  const c = check.counts;
  const isNew = isNewSince(usePreviousVisit(), check.checkedAt);
  return (
    <article
      className={`history-card check-card check-card--${check.overall.toLowerCase()}`}
      aria-label={`Check of ${check.priorReleaseDate} to ${check.currentReleaseDate}`}
    >
      <header className="history-card-heading">
        <h3>
          {check.priorReleaseDate} → {check.currentReleaseDate}
        </h3>
        {isNew && <NewBadge />}
        <span
          className={`check-status check-status--${check.overall.toLowerCase()}`}
        >
          {check.overall === "PASSED" ? "All checks passed" : "Worth a look"}
        </span>
      </header>
      <p className="history-meta">
        Checked{" "}
        <TimestampDisplay value={check.checkedAt} fallback={check.checkedAt} />
      </p>
      {check.upToDate === false && (
        <p className="history-note">
          Made by an earlier version of the checks. The next daily update checks
          this pair again with the current checks.
        </p>
      )}
      <ul className="check-list">
        {check.checks.map((item) => (
          <li key={item.id}>
            <span
              className={`check-status check-status--${item.status.toLowerCase()}`}
            >
              {STATUS_LABELS[item.status]}
            </span>
            <span>
              <strong>{item.label}.</strong> {item.detail}
            </span>
          </li>
        ))}
      </ul>
      {check.completeness && (
        <div className="history-table-wrap">
          <table className="history-completeness">
            <caption>
              Packages with each field (prior → current release)
            </caption>
            <thead>
              <tr>
                <th scope="col">Field</th>
                <th scope="col">Prior</th>
                <th scope="col">Current</th>
              </tr>
            </thead>
            <tbody>
              {check.completeness.map((row) => (
                <tr key={row.field}>
                  <th scope="row">{row.field}</th>
                  <td>{row.prior.toFixed(2)} %</td>
                  <td>{row.current.toFixed(2)} %</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <dl className="history-facts">
        <div>
          <dt>Packages</dt>
          <dd>
            {number.format(c.priorPackages)} →{" "}
            {number.format(c.currentPackages)}
          </dd>
        </div>
        <div>
          <dt>Changed</dt>
          <dd>{number.format(c.changed)}</dd>
        </div>
        <div>
          <dt>No longer present</dt>
          <dd>{number.format(c.noLongerPresent)}</dd>
        </div>
        <div>
          <dt>New</dt>
          <dd>{number.format(c.new)}</dd>
        </div>
        <div>
          <dt>VNR gained / lost / changed</dt>
          <dd>
            {c.vnrGained} / {c.vnrLost} / {c.vnrChanged}
          </dd>
        </div>
        <div>
          <dt>Spacing or letter case only</dt>
          <dd>{number.format(c.formattingOnly)}</dd>
        </div>
        <div>
          <dt>Active-substance fields only</dt>
          <dd>{number.format(c.activeSubstanceOnly)}</dd>
        </div>
      </dl>
    </article>
  );
}

function ReleaseCard({ release }: { release: StoredRelease }) {
  const isNew = isNewSince(usePreviousVisit(), release.firstRetrievedAt);
  return (
    <article
      className="history-card"
      aria-label={`Basic Register release ${release.releaseDate ?? "without a date"}`}
    >
      <header className="history-card-heading">
        <h3>{release.releaseDate ?? "No verified release date"}</h3>
        {isNew && <NewBadge />}
        {release.isCatalogueRelease && (
          <span className="history-badge">Catalogue release</span>
        )}
        {release.processingStatus !== "VALIDATED" && (
          <span className="history-badge history-badge--warning">
            Not accepted
          </span>
        )}
      </header>
      {release.failureDetail && (
        <p className="history-warning">{release.failureDetail}</p>
      )}
      <dl className="history-facts">
        <div>
          <dt>File</dt>
          <dd className="monospace-value">{release.fileName ?? "unknown"}</dd>
        </div>
        <Downloads
          first={release.firstRetrievedAt}
          last={release.lastRetrievedAt}
          count={release.retrievalCount}
        />
        <FileFacts
          checksum={release.checksum}
          sizeBytes={release.sizeBytes}
          evidenceAvailable={release.evidenceAvailable}
        />
      </dl>
    </article>
  );
}

function ShortageFileCard({ file }: { file: StoredShortageFile }) {
  const isNew = isNewSince(usePreviousVisit(), file.firstRetrievedAt);
  return (
    <article
      className="history-card"
      aria-label={`Shortage file first downloaded ${file.firstRetrievedAt}`}
    >
      <header className="history-card-heading">
        <h3>
          {file.recordCount === null
            ? "Shortage file"
            : `${number.format(file.recordCount)} shortages`}
        </h3>
        {isNew && <NewBadge />}
        {file.isActive && <span className="history-badge">Shown now</span>}
        {file.processingStatus !== "VALIDATED" && (
          <span className="history-badge history-badge--warning">
            Not accepted
          </span>
        )}
      </header>
      {file.failureDetail && (
        <p className="history-warning">{file.failureDetail}</p>
      )}
      <dl className="history-facts">
        <Downloads
          first={file.firstRetrievedAt}
          last={file.lastRetrievedAt}
          count={file.retrievalCount}
        />
        <FileFacts
          checksum={file.checksum.replace(/^sha256-/, "")}
          sizeBytes={file.sizeBytes}
          evidenceAvailable={file.evidenceAvailable}
        />
      </dl>
    </article>
  );
}

export default function SourceHistoryPage() {
  const [history, setHistory] = useState<SourceHistory | null>(null);
  const [error, setError] = useState<string | null>(null);
  const previousVisit = usePreviousVisit();
  const newCount = history
    ? history.qualityChecks.filter((item) =>
        isNewSince(previousVisit, item.checkedAt),
      ).length +
      history.basicRegister.filter((item) =>
        isNewSince(previousVisit, item.firstRetrievedAt),
      ).length +
      history.shortageFiles.filter((item) =>
        isNewSince(previousVisit, item.firstRetrievedAt),
      ).length
    : 0;

  useEffect(() => {
    const controller = new AbortController();
    fetchSourceHistory(controller.signal)
      .then(setHistory)
      .catch((reason: unknown) => {
        if (controller.signal.aborted) return;
        setError(
          reason instanceof Error
            ? reason.message
            : "Source history could not be loaded.",
        );
      });
    return () => controller.abort();
  }, []);

  return (
    <div className="history-page">
      <header className="page-header">
        <p className="eyebrow">Medicine Change Care Loop</p>
        <h1>Source History</h1>
        <p className="page-description">
          Every source file the app has stored, and the automatic checks of each
          new Basic Register release. This page only reads; nothing here changes
          data or cases.
        </p>
      </header>

      {error && (
        <p className="history-error" role="alert">
          {error}
        </p>
      )}
      {!history && !error && (
        <p className="history-loading" role="status">
          Loading source history…
        </p>
      )}

      {history && (
        <>
          <NewSinceVisit count={newCount} noun={["item is", "items are"]} />
          <section className="history-section" aria-labelledby="history-checks">
            <h2 id="history-checks">Release checks</h2>
            <p className="history-intro">
              When a newer release is compared with the previous one, the pair
              is checked automatically. “Attention” only marks a pair worth a
              look; it never stops a release or changes a case.
            </p>
            {history.uncheckedPairs.map((pair) => (
              <p
                className="history-note"
                key={`${pair.priorReleaseDate}-${pair.currentReleaseDate}`}
              >
                {pair.priorReleaseDate} → {pair.currentReleaseDate}: not checked
                yet. The next daily update checks it.
              </p>
            ))}
            {history.qualityChecks.length === 0 &&
              history.uncheckedPairs.length === 0 && (
                <p className="history-empty">
                  No release pair yet. A check appears when a second, newer
                  release is loaded.
                </p>
              )}
            <div className="history-list">
              {history.qualityChecks.map((check) => (
                <CheckCard key={check.checkId} check={check} />
              ))}
            </div>
          </section>

          <section
            className="history-section"
            aria-labelledby="history-releases"
          >
            <h2 id="history-releases">
              Basic Register releases ({history.basicRegister.length})
            </h2>
            {history.basicRegister.length === 0 ? (
              <p className="history-empty">No release stored yet.</p>
            ) : (
              <div className="history-list">
                {history.basicRegister.map((release) => (
                  <ReleaseCard key={release.releaseId} release={release} />
                ))}
              </div>
            )}
          </section>

          <section
            className="history-section"
            aria-labelledby="history-shortages"
          >
            <h2 id="history-shortages">
              Shortage files ({history.shortageFiles.length})
            </h2>
            {history.shortageFiles.length === 0 ? (
              <p className="history-empty">No shortage file stored yet.</p>
            ) : (
              <div className="history-list">
                {history.shortageFiles.map((file) => (
                  <ShortageFileCard key={file.checksum} file={file} />
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}
