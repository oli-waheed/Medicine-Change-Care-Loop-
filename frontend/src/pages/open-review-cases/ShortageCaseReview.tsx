import type { ShortageCase, ShortageRow } from "./openReviewCases";
import { SHORTAGE_KIND_LABELS } from "./changeSummary";
import { SourceValueDisplay } from "./evidence/SourceValueDisplay";
import { formatTimestamp } from "./timestamp";

const COLUMNS: { key: keyof ShortageRow; column: string; label: string }[] = [
  { key: "valid", column: "Valid", label: "Valid" },
  {
    key: "unavailableFrom",
    column: "UnavailableFrom",
    label: "Unavailable from",
  },
  { key: "endingDate", column: "EndingDate", label: "Estimated end" },
  {
    key: "notificationDate",
    column: "DateOfTheNotification",
    label: "Notified",
  },
  { key: "updated", column: "Updated", label: "Updated" },
  { key: "company", column: "Company", label: "Company" },
];

function Value({
  row,
  field,
}: {
  row: ShortageRow | null;
  field: keyof ShortageRow;
}) {
  if (row === null) {
    return (
      <span className="source-value source-value--missing">Not in file</span>
    );
  }
  const value = String(row[field]);
  return value ? (
    <>{value}</>
  ) : (
    <span className="source-value source-value--empty">Empty in source</span>
  );
}

// Feature 007: a change in Fimea's shortage data for a matched package.
export function ShortageChangeReview({
  reviewCase,
}: {
  reviewCase: ShortageCase;
}) {
  const change = reviewCase.shortageChange;
  const pkg = change.package;
  return (
    <section
      className="change-card review-panel review-panel--shortage"
      aria-label="Shortage change"
    >
      <div className="section-heading">
        <h3>{SHORTAGE_KIND_LABELS[change.kind]}</h3>
        <span className="field-count">VNR {change.vnr}</span>
      </div>
      <p className="shortage-change-package">
        <span className="shortage-change-product">
          <SourceValueDisplay field={pkg.productName} />
        </span>{" "}
        <SourceValueDisplay field={pkg.strength} /> ·{" "}
        <SourceValueDisplay field={pkg.packageSizeText} /> · Package ID{" "}
        <span className="monospace-value">{pkg.pakkaustunnus}</span>
        {change.catalogue && (
          <span className="shortage-change-catalogue">
            {" "}
            (matched by VNR in the catalogue release{" "}
            {change.catalogue.releaseDate ?? change.catalogue.releaseId})
          </span>
        )}
      </p>
      <div className="shortage-change-table-wrap">
        <table className="shortage-change-table">
          <caption className="visually-hidden">
            Shortage row before and after, as published
          </caption>
          <thead>
            <tr>
              <th scope="col">Column</th>
              <th scope="col">Previous file</th>
              <th scope="col">Current file</th>
            </tr>
          </thead>
          <tbody>
            {COLUMNS.map(({ key, column, label }) => {
              const changed = change.changedColumns.includes(column);
              return (
                <tr
                  key={key}
                  className={
                    changed ? "shortage-change-row--changed" : undefined
                  }
                >
                  <th scope="row">
                    {label}
                    {changed && (
                      <span className="field-indicator">Changed</span>
                    )}
                  </th>
                  <td>
                    <Value row={change.before} field={key} />
                  </td>
                  <td>
                    <Value row={change.after} field={key} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="shortage-change-notice">{change.notice}</p>
    </section>
  );
}

export function ShortageProvenance({
  reviewCase,
}: {
  reviewCase: ShortageCase;
}) {
  return (
    <section className="sources" aria-label="Source evidence">
      {(["prior", "current"] as const).map((side) => {
        const source = reviewCase.sources[side];
        const label = side === "prior" ? "Previous file" : "Current file";
        return (
          <section
            key={side}
            className={`source-card source-card--${side}`}
            aria-label={`${label} source evidence`}
          >
            <h4>{label} source evidence</h4>
            <dl>
              <div>
                <dt>Source</dt>
                <dd>{source.sourceName}</dd>
              </div>
              <div>
                <dt>Raw file</dt>
                <dd className="monospace-value">
                  {source.fileName}
                  {source.evidenceAvailable === false && (
                    <span className="evidence-missing">
                      {" "}
                      (no longer stored)
                    </span>
                  )}
                </dd>
              </div>
              <div>
                <dt>Checksum</dt>
                <dd className="monospace-value">{source.checksum}</dd>
              </div>
              <div>
                <dt>Line</dt>
                <dd className="monospace-value">
                  {source.lineNumber ?? "Not in this file"}
                </dd>
              </div>
              <div>
                <dt>Downloaded</dt>
                <dd>
                  {formatTimestamp(source.retrievedAt) ?? source.retrievedAt}
                </dd>
              </div>
              <div>
                <dt>Licence</dt>
                <dd>{source.licence}</dd>
              </div>
            </dl>
            <p className="evidence-note">{source.note}</p>
          </section>
        );
      })}
    </section>
  );
}
