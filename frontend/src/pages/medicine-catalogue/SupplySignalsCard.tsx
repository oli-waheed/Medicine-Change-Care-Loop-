import { formatTimestamp } from "../open-review-cases/timestamp";
import { FieldPath, SourceValueDisplay } from "./catalogueParts";
import {
  fetchSupplySignals,
  type SourceField,
  type SupplySignals,
} from "./medicineCatalogue";
import { useCatalogueRequest } from "./useCatalogueRequest";

function ago(days: number | null): string {
  if (days === null) return "";
  if (days === 0) return " (today)";
  return days > 0 ? ` (${days} days ago)` : ` (in ${-days} days)`;
}

function ahead(days: number | null): string {
  if (days === null) return "";
  if (days === 0) return " (today)";
  return days > 0 ? ` (in ${days} days)` : ` (${-days} days ago)`;
}

function time(value: string): string {
  return formatTimestamp(value) ?? value;
}

function Values({ fields }: { fields: SourceField[] }) {
  if (fields.length === 0) return <>none</>;
  return (
    <>
      {fields.map((field, index) => (
        <SourceValueDisplay key={index} field={field} />
      ))}
    </>
  );
}

function Status({ data }: { data: SupplySignals }) {
  const downloaded = data.shortageFile
    ? ` (file downloaded ${time(data.shortageFile.lastRetrievedAt)})`
    : "";
  const text = {
    LISTED: `Listed in Fimea's shortage file${downloaded}.`,
    NOT_LISTED: `Not listed in Fimea's shortage file${downloaded}. This does not show that it is available.`,
    NO_VNR: "No VNR in the source, so Fimea's shortage file cannot be linked.",
    NO_FILE: "No shortage file has been downloaded yet.",
  }[data.status];
  return (
    <p className={`supply-status supply-status--${data.status.toLowerCase()}`}>
      {text}
    </p>
  );
}

// Feature 016: shortage and register facts side by side. No forecast.
export default function SupplySignalsCard({
  kind,
  id,
  onOpenProduct,
}: {
  kind: "package" | "product";
  id: string;
  onOpenProduct?: (productReference: string) => void;
}) {
  const state = useCatalogueRequest(`supply:${kind}:${id}`, (signal) =>
    fetchSupplySignals(kind, id, signal),
  );
  return (
    <section className="catalogue-card" aria-label="Supply signals">
      <h3>Supply signals</h3>
      {(state.status === "idle" || state.status === "loading") && (
        <p className="catalogue-note" role="status">
          Loading supply signals…
        </p>
      )}
      {state.status === "error" && (
        <p className="catalogue-note">Supply signals could not be loaded.</p>
      )}
      {state.status === "loaded" && (
        <Signals data={state.data} onOpenProduct={onOpenProduct} />
      )}
    </section>
  );
}

function Signals({
  data,
  onOpenProduct,
}: {
  data: SupplySignals;
  onOpenProduct?: (productReference: string) => void;
}) {
  return (
    <>
      <p className="catalogue-note">
        {data.notice} Days are counted to {data.asOf}.
      </p>
      <Status data={data} />

      {data.current.length > 0 && (
        <ul className="supply-list" aria-label="Rows in the shortage file now">
          {data.current.map((row) => (
            <li key={`${row.vnr}-${row.line}`}>
              <strong>VNR {row.vnr}</strong> · Valid {row.valid || "—"} ·
              Unavailable from {row.unavailableFrom || "—"}
              {ago(row.daysSinceUnavailableFrom)} · Estimated end{" "}
              {row.endingDate || "—"}
              {ahead(row.daysUntilEstimatedEnd)} · Notified{" "}
              {row.notificationDate || "—"} · Updated {row.updated || "—"} ·{" "}
              {row.company} (line {row.line})
            </li>
          ))}
        </ul>
      )}

      {data.vnrs.length > 0 && (
        <div className="supply-block">
          <h4>Listings in downloaded shortage files</h4>
          <p className="link-basis">
            {data.downloadsChecked}{" "}
            {data.downloadsChecked === 1 ? "download" : "downloads"} checked
            {data.unreadableDownloads > 0 &&
              `; ${data.unreadableDownloads} stored files could not be read`}
            . A listing is a run of downloads that listed the VNR.
          </p>
          {data.listings.length === 0 ? (
            <p className="link-basis">Never listed in a downloaded file.</p>
          ) : (
            <div className="supply-table-wrap">
              <table className="supply-table">
                <caption className="visually-hidden">
                  Listings in downloaded shortage files
                </caption>
                <thead>
                  <tr>
                    <th scope="col">VNR</th>
                    <th scope="col">First listed</th>
                    <th scope="col">Last listed</th>
                    <th scope="col">Downloads</th>
                    <th scope="col">Listed now</th>
                  </tr>
                </thead>
                <tbody>
                  {data.listings.map((listing) => (
                    <tr key={`${listing.vnr}-${listing.firstSeen}`}>
                      <th scope="row" className="monospace-value">
                        {listing.vnr}
                      </th>
                      <td>{time(listing.firstSeen)}</td>
                      <td>{time(listing.lastSeen)}</td>
                      <td>{listing.downloads}</td>
                      <td>{listing.listedNow ? "Yes" : "No"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      <div className="supply-block">
        <h4>In the Basic Register</h4>
        <ul className="supply-list">
          {data.register.map((item) => (
            <li key={item.pakkaustunnus}>
              <strong>{item.pakkaustunnus}</strong> · On the market (Kaupan){" "}
              <SourceValueDisplay field={item.onMarket} /> · From{" "}
              <SourceValueDisplay field={item.marketedFrom} /> · Until{" "}
              <SourceValueDisplay field={item.marketedUntil} />
              {item.authorisations.map((authorisation, index) => (
                <span key={index}>
                  {" "}
                  · {authorisation.branch}{" "}
                  <SourceValueDisplay field={authorisation.status} />
                </span>
              ))}
            </li>
          ))}
        </ul>
      </div>

      <div className="supply-block">
        <h4>Recorded register changes</h4>
        {data.registerChanges.length === 0 ? (
          <p className="link-basis">
            No change to market or authorisation fields in the compared
            releases.
          </p>
        ) : (
          <ul className="supply-list">
            {data.registerChanges.map((change, index) => (
              <li key={index}>
                {change.priorReleaseDate} → {change.currentReleaseDate} ·{" "}
                {change.pakkaustunnus} ·{" "}
                {change.field ? (
                  <>
                    <FieldPath path={change.field} />:{" "}
                    <Values fields={change.before} /> →{" "}
                    <Values fields={change.after} />
                  </>
                ) : change.kind === "NEWLY_PRESENT" ? (
                  "new in the register"
                ) : (
                  "no longer in the register"
                )}
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="supply-block">
        <h4>Products with the same active substances</h4>
        {!data.related.available ? (
          <p className="link-basis">
            Not available: no shortage file, or no active-substance codes.
          </p>
        ) : (
          <>
            <p className="link-basis">
              {data.related.listedNow} of {data.related.sameSubstanceProducts}{" "}
              have a VNR listed in the shortage file now.
            </p>
            {data.related.items.length > 0 && (
              <ul className="supply-list">
                {data.related.items.map((item) => (
                  <li key={item.productReference}>
                    {onOpenProduct ? (
                      <button
                        type="button"
                        className="catalogue-chip"
                        onClick={() => onOpenProduct(item.productReference)}
                      >
                        {item.productReference}
                      </button>
                    ) : (
                      <span className="monospace-value">
                        {item.productReference}
                      </span>
                    )}{" "}
                    <SourceValueDisplay field={item.name} /> ·{" "}
                    <SourceValueDisplay field={item.strength} /> · VNR{" "}
                    {item.listedVnrs.join(", ")}
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </div>
    </>
  );
}
