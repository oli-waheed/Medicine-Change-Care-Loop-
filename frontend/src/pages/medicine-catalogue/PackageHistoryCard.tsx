import { CLEANUP_LABELS } from "../open-review-cases/changeSummary";
import { FieldPath, SourceValueDisplay } from "./catalogueParts";
import {
  fetchPackageHistory,
  type PackageHistoryEvent,
  type SourceField,
} from "./medicineCatalogue";
import { useCatalogueRequest } from "./useCatalogueRequest";

const KIND_LABELS: Record<PackageHistoryEvent["kind"], string> = {
  FIELDS_CHANGED: "Fields changed",
  NO_LONGER_PRESENT: "No longer in the register",
  NEWLY_PRESENT: "New in the register",
};

function Values({ fields }: { fields: SourceField[] }) {
  if (fields.length === 0) return <span className="catalogue-note">None</span>;
  return (
    <>
      {fields.map((field, index) => (
        <span key={index} className="catalogue-value">
          <SourceValueDisplay field={field} />
        </span>
      ))}
    </>
  );
}

function range(item: {
  priorReleaseDate: string | null;
  currentReleaseDate: string | null;
}) {
  return `${item.priorReleaseDate ?? "?"} → ${item.currentReleaseDate ?? "?"}`;
}

// Feature 013: what changed in this package between the compared releases.
export default function PackageHistoryCard({
  pakkaustunnus,
}: {
  pakkaustunnus: string;
}) {
  const state = useCatalogueRequest(`history:${pakkaustunnus}`, (signal) =>
    fetchPackageHistory(pakkaustunnus, signal),
  );
  return (
    <section className="catalogue-card" aria-label="Package change history">
      <h3>Change history</h3>
      {(state.status === "idle" || state.status === "loading") && (
        <p className="catalogue-note" role="status">
          Loading change history…
        </p>
      )}
      {state.status === "error" && (
        <p className="catalogue-note">
          The change history could not be loaded.
        </p>
      )}
      {state.status === "loaded" &&
        (state.data.comparedPairs.length === 0 ? (
          <p className="catalogue-note">
            No two releases have been compared yet, so there is no history.
          </p>
        ) : state.data.events.length === 0 ? (
          <p className="catalogue-note">
            No change recorded for this package in the compared releases (
            {state.data.comparedPairs.map(range).join(", ")}).
          </p>
        ) : (
          <>
            <p className="catalogue-note">
              Compared releases:{" "}
              {state.data.comparedPairs.map(range).join(", ")}. Values are shown
              as published.
            </p>
            <ol className="package-history">
              {state.data.events.map((event) => (
                <li key={`${range(event)}-${event.kind}`}>
                  <p className="package-history-heading">
                    <strong>{range(event)}</strong>
                    <span className="package-history-kind">
                      {KIND_LABELS[event.kind]}
                    </span>
                    {event.cleanupLabel && (
                      <span className="package-history-cleanup">
                        {CLEANUP_LABELS[event.cleanupLabel].badge}
                      </span>
                    )}
                  </p>
                  {event.changes.length > 0 && (
                    <div className="catalogue-table-wrap">
                      <table className="catalogue-table package-history-table">
                        <caption className="visually-hidden">
                          Changed fields {range(event)}
                        </caption>
                        <thead>
                          <tr>
                            <th scope="col">Field</th>
                            <th scope="col">Before</th>
                            <th scope="col">After</th>
                          </tr>
                        </thead>
                        <tbody>
                          {event.changes.map((change) => (
                            <tr key={change.field}>
                              <th scope="row" className="monospace-value">
                                <FieldPath path={change.field} />
                              </th>
                              <td>
                                <Values fields={change.before} />
                              </td>
                              <td>
                                <Values fields={change.after} />
                                {change.formattingOnly && (
                                  <span className="package-history-cleanup">
                                    Spacing or letter case only
                                  </span>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </li>
              ))}
            </ol>
          </>
        ))}
    </section>
  );
}
