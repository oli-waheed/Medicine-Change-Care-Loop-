import { useEffect, useId, useState } from "react";
import "../open-review-cases/OpenReviewCasesPage.css";
import "../medicine-catalogue/MedicineCataloguePage.css";
import "./MedicineShortagesPage.css";
import { SourceValueDisplay } from "../open-review-cases/evidence/SourceValueDisplay";
import { formatTimestamp } from "../open-review-cases/timestamp";
import { useDebouncedValue } from "../medicine-catalogue/useCatalogueRequest";
import ShortageUpdatePanel from "./ShortageUpdatePanel";
import {
  ShortageError,
  fetchDailyUpdates,
  fetchShortages,
  type DailyUpdates,
  type Shortage,
  type ShortagePage,
} from "./shortagesApi";

// While the catalogue is still being prepared, ask again after this delay.
export const CATALOGUE_RETRY_MS = 5000;

// The answer to one request; `key` tells which, so a newer request shows as loading.
type Answer =
  | { key: string; data: ShortagePage; error?: undefined }
  | { key: string; data?: ShortagePage; error: ShortageError };

const VALID_LABELS: Record<string, string> = {
  K: "K (ongoing: yes)",
  E: "E (ongoing: no)",
};

function Published({ value }: { value: string }) {
  return value ? (
    <>{value}</>
  ) : (
    <span className="source-value source-value--empty">Empty in source</span>
  );
}

function Packages({
  shortage,
  catalogueStatus,
}: {
  shortage: Shortage;
  catalogueStatus: string;
}) {
  if (shortage.packages === null) {
    return (
      <span className="shortage-muted">
        {catalogueStatus === "LOADING"
          ? "Loading from the Medicine Catalogue…"
          : "No catalogue release loaded"}
      </span>
    );
  }
  if (shortage.packages.length === 0) {
    return (
      <span className="shortage-muted">
        No package with this VNR in the active catalogue release
      </span>
    );
  }
  return (
    <ul className="shortage-packages">
      {shortage.packages.map((pkg) => (
        <li key={pkg.pakkaustunnus}>
          <span className="shortage-product">
            <SourceValueDisplay field={pkg.productName} />
          </span>{" "}
          <SourceValueDisplay field={pkg.strength} />
          <span className="shortage-muted">
            {" · "}
            <SourceValueDisplay field={pkg.packageSizeText} />
            {" · Package ID "}
            <span className="monospace-value">{pkg.pakkaustunnus}</span>
          </span>
        </li>
      ))}
    </ul>
  );
}

function SourceSummary({ data }: { data: ShortagePage }) {
  const source = data.source;
  const counts = Object.entries(data.validCounts)
    .map(([value, count]) => `${count} ${value}`)
    .join(" · ");
  return (
    <section className="catalogue-source" aria-label="Shortage data source">
      <h2>Fimea shortage data</h2>
      <dl className="catalogue-fields catalogue-fields--inline">
        <div>
          <dt>Source</dt>
          <dd>{source.sourceName}</dd>
        </div>
        <div>
          <dt>Last downloaded</dt>
          <dd>
            {formatTimestamp(source.lastRetrievedAt) ?? source.lastRetrievedAt}
          </dd>
        </div>
        <div>
          <dt>Content first downloaded</dt>
          <dd>
            {formatTimestamp(source.firstRetrievedAt) ??
              source.firstRetrievedAt}
          </dd>
        </div>
        <div>
          <dt>Latest “Updated” date in file</dt>
          <dd>{source.latestUpdated ?? "—"}</dd>
        </div>
        <div>
          <dt>Shortages (Valid)</dt>
          <dd>
            {source.recordCount} ({counts})
          </dd>
        </div>
        <div>
          <dt>Matched by VNR to catalogue release</dt>
          <dd>
            {data.catalogue.status === "READY"
              ? (data.catalogue.releaseDate ?? data.catalogue.releaseId)
              : data.catalogue.status === "LOADING"
                ? "Loading…"
                : "No catalogue release loaded"}
          </dd>
        </div>
      </dl>
      <p className="catalogue-checksum">
        Checksum{" "}
        <span className="monospace-value">{source.captureReference}</span> ·{" "}
        {source.licence} ·{" "}
        <span className="monospace-value">{source.sourceUrl}</span>
      </p>
    </section>
  );
}

// Feature 006: Fimea's open-data shortage file as published, matched to the
// catalogue by VNR. Read-only apart from the Update button.
export default function MedicineShortagesPage() {
  const id = useId();
  const [query, setQuery] = useState("");
  const [valid, setValid] = useState("");
  const [page, setPage] = useState(1);
  const [version, setVersion] = useState(0);
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [daily, setDaily] = useState<DailyUpdates | null>(null);
  const debounced = useDebouncedValue(query, 250);

  useEffect(() => {
    const controller = new AbortController();
    fetchDailyUpdates(controller.signal)
      .then(setDaily)
      .catch(() => setDaily(null));
    return () => controller.abort();
  }, [version]);

  const requestKey = `${debounced}|${valid}|${page}|${version}`;
  useEffect(() => {
    const controller = new AbortController();
    let retry: number | undefined;
    fetchShortages(debounced, valid, page, controller.signal)
      .then((data) => {
        setAnswer({ key: requestKey, data });
        if (data.catalogue.status === "LOADING") {
          retry = window.setTimeout(
            () => setVersion((v) => v + 1),
            CATALOGUE_RETRY_MS,
          );
        }
      })
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === "AbortError")
          return;
        setAnswer((previous) => ({
          key: requestKey,
          data: previous?.data,
          error:
            reason instanceof ShortageError
              ? reason
              : new ShortageError(
                  "REQUEST_FAILED",
                  "The shortage data could not be loaded.",
                ),
        }));
      });
    return () => {
      controller.abort();
      window.clearTimeout(retry);
    };
  }, [debounced, valid, page, version, requestKey]);

  const loading = answer?.key !== requestKey;
  const error = answer?.error;
  const data =
    error?.code === "SHORTAGES_UNAVAILABLE" ? undefined : answer?.data;

  return (
    <div className="catalogue-page shortages-page">
      <header className="page-header">
        <p className="eyebrow">Medicine Change Care Loop</p>
        <h1>Medicine Shortages</h1>
        <p className="page-description">
          Shortages reported to Fimea by marketing authorisation holders, as
          published in Fimea’s open data, with the matching packages of the
          Medicine Catalogue (by VNR).
        </p>
      </header>

      {data && <SourceSummary data={data} />}

      <ShortageUpdatePanel
        daily={daily}
        onUpdated={() => setVersion((v) => v + 1)}
      />

      <p className="catalogue-notice">
        Dates and status are the company’s report to Fimea, shown as published;
        the end date is an estimate. This page lists packages only and does not
        point to other products.
      </p>

      {error?.code === "SHORTAGES_UNAVAILABLE" && (
        <div
          className="catalogue-state catalogue-state--unavailable"
          role="status"
        >
          <p className="catalogue-state-title">No shortage data yet</p>
          <p>
            Press “Update shortage data”, or wait for the daily automatic
            update.
          </p>
        </div>
      )}
      {error && error.code !== "SHORTAGES_UNAVAILABLE" && (
        <div className="catalogue-state catalogue-state--error" role="alert">
          <p className="catalogue-state-title">
            Shortage data could not be shown
          </p>
          <p className="catalogue-state-detail">{error.message}</p>
        </div>
      )}

      {data && (
        <section className="catalogue-search" aria-label="Search shortages">
          <div className="shortage-filters">
            <div className="catalogue-filter">
              <label htmlFor={`${id}-q`}>Search shortages</label>
              <input
                id={`${id}-q`}
                type="search"
                value={query}
                autoComplete="off"
                spellCheck={false}
                placeholder="Product name, VNR or company"
                onChange={(event) => {
                  setQuery(event.target.value);
                  setPage(1);
                }}
              />
            </div>
            <div className="catalogue-filter">
              <label htmlFor={`${id}-valid`}>Status (Valid)</label>
              <select
                id={`${id}-valid`}
                value={valid}
                onChange={(event) => {
                  setValid(event.target.value);
                  setPage(1);
                }}
              >
                <option value="">All</option>
                {Object.keys(data.validCounts).map((value) => (
                  <option key={value} value={value}>
                    {VALID_LABELS[value] ?? value}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <p className="catalogue-result-count" role="status">
            {loading
              ? "Loading shortages…"
              : data.total === 0
                ? "No shortages match this search."
                : `Showing ${(data.page - 1) * data.pageSize + 1}–${
                    (data.page - 1) * data.pageSize + data.items.length
                  } of ${data.total} shortages`}
          </p>

          {data.items.length > 0 && (
            <div className="catalogue-table-wrap">
              <table className="catalogue-table shortage-table">
                <caption className="visually-hidden">
                  Shortages in Fimea’s file, in the file’s order
                </caption>
                <thead>
                  <tr>
                    <th scope="col">VNR</th>
                    <th scope="col">Package in catalogue</th>
                    <th scope="col">Valid</th>
                    <th scope="col">Unavailable from</th>
                    <th scope="col">Estimated end</th>
                    <th scope="col">Notified</th>
                    <th scope="col">Updated</th>
                    <th scope="col">Company</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((shortage) => (
                    <tr key={shortage.vnr}>
                      <th scope="row" className="monospace-value">
                        {shortage.vnr}
                      </th>
                      <td>
                        <Packages
                          shortage={shortage}
                          catalogueStatus={data.catalogue.status}
                        />
                      </td>
                      <td>
                        <span
                          className={`shortage-valid shortage-valid--${shortage.valid === "K" ? "yes" : "other"}`}
                        >
                          <Published value={shortage.valid} />
                        </span>
                      </td>
                      <td className="shortage-date">
                        <Published value={shortage.unavailableFrom} />
                      </td>
                      <td className="shortage-date">
                        <Published value={shortage.endingDate} />
                      </td>
                      <td className="shortage-date">
                        <Published value={shortage.notificationDate} />
                      </td>
                      <td className="shortage-date">
                        <Published value={shortage.updated} />
                      </td>
                      <td>
                        <Published value={shortage.company} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {data.total > data.pageSize && (
            <div className="catalogue-paging">
              <button
                type="button"
                disabled={page <= 1}
                onClick={() => setPage((current) => current - 1)}
              >
                Previous page
              </button>
              <button
                type="button"
                disabled={page * data.pageSize >= data.total}
                onClick={() => setPage((current) => current + 1)}
              >
                Next page
              </button>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
