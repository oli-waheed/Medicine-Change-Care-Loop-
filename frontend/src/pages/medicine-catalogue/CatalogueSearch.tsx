import { useId, useState } from "react";
import { SourceValueDisplay } from "./catalogueParts";
import { CatalogueErrorMessage, LoadingMessage } from "./CatalogueStates";
import {
  EMPTY_FILTERS,
  catalogueQuery,
  fetchCatalogue,
  type CatalogueFilters,
} from "./medicineCatalogue";
import { useCatalogueRequest, useDebouncedValue } from "./useCatalogueRequest";

const TEXT_FILTERS: {
  key: keyof CatalogueFilters;
  label: string;
  hint: string;
}[] = [
  { key: "activeSubstance", label: "Active substance", hint: "Code or name" },
  { key: "atc", label: "ATC code starts with", hint: "e.g. N02" },
  { key: "form", label: "Pharmaceutical form", hint: "Code or name" },
  { key: "route", label: "Administration route", hint: "Code or name" },
  { key: "vnr", label: "VNR", hint: "Exact VNR" },
];

export default function CatalogueSearch({
  selectedPackage,
  onSelectPackage,
}: {
  selectedPackage: string | null;
  onSelectPackage: (pakkaustunnus: string) => void;
}) {
  const id = useId();
  const [filters, setFilters] = useState<CatalogueFilters>(EMPTY_FILTERS);
  const [page, setPage] = useState(1);
  const debounced = useDebouncedValue(filters, 250);
  const state = useCatalogueRequest(
    `catalogue:${catalogueQuery(debounced, page)}`,
    (signal) => fetchCatalogue(debounced, page, signal),
  );

  function update<K extends keyof CatalogueFilters>(
    key: K,
    value: CatalogueFilters[K],
  ) {
    setFilters((current) => ({ ...current, [key]: value }));
    setPage(1);
  }

  const active = Object.values(filters).some((value) => value.trim() !== "");

  return (
    <section className="catalogue-search" aria-label="Search the catalogue">
      <div className="catalogue-filter">
        <label htmlFor={`${id}-q`}>Search medicines</label>
        <input
          id={`${id}-q`}
          type="search"
          value={filters.q}
          autoComplete="off"
          spellCheck={false}
          placeholder="Product name, package ID or VNR"
          onChange={(event) => update("q", event.target.value)}
        />
      </div>

      <details className="catalogue-filters">
        <summary>Filters</summary>
        <div className="catalogue-filter-grid">
          {TEXT_FILTERS.map(({ key, label, hint }) => (
            <div className="catalogue-filter" key={key}>
              <label htmlFor={`${id}-${key}`}>{label}</label>
              <input
                id={`${id}-${key}`}
                type="text"
                value={filters[key]}
                autoComplete="off"
                spellCheck={false}
                placeholder={hint}
                onChange={(event) => update(key, event.target.value)}
              />
            </div>
          ))}
          <div className="catalogue-filter">
            <label htmlFor={`${id}-available`}>On the market (Kaupan)</label>
            <select
              id={`${id}-available`}
              value={filters.available}
              onChange={(event) =>
                update(
                  "available",
                  event.target.value as CatalogueFilters["available"],
                )
              }
            >
              <option value="">Any</option>
              <option value="1">1 (source value)</option>
              <option value="0">0 (source value)</option>
            </select>
          </div>
          <div className="catalogue-filter">
            <label htmlFor={`${id}-missing`}>Not present in source</label>
            <select
              id={`${id}-missing`}
              value={filters.missing}
              onChange={(event) =>
                update(
                  "missing",
                  event.target.value as CatalogueFilters["missing"],
                )
              }
            >
              <option value="">No condition</option>
              <option value="vnr">VNR</option>
              <option value="atc">ATC code</option>
              <option value="form">Pharmaceutical form</option>
              <option value="route">Administration route</option>
              <option value="available">On the market (Kaupan)</option>
            </select>
          </div>
        </div>
        {active && (
          <button
            type="button"
            className="catalogue-link-button"
            onClick={() => {
              setFilters(EMPTY_FILTERS);
              setPage(1);
            }}
          >
            Clear search and filters
          </button>
        )}
      </details>

      {(state.status === "idle" || state.status === "loading") && (
        <LoadingMessage>Loading catalogue…</LoadingMessage>
      )}
      {state.status === "error" && (
        <CatalogueErrorMessage error={state.error} />
      )}
      {state.status === "loaded" && (
        <>
          <p className="catalogue-result-count" role="status">
            {state.data.total === 0
              ? "No packages match this search."
              : `Showing ${(state.data.page - 1) * state.data.pageSize + 1}–${
                  (state.data.page - 1) * state.data.pageSize +
                  state.data.items.length
                } of ${state.data.total} packages`}
          </p>
          <ul className="catalogue-results" aria-label="Catalogue packages">
            {state.data.items.map((item) => (
              <li key={item.pakkaustunnus}>
                <button
                  type="button"
                  className="catalogue-result"
                  aria-pressed={item.pakkaustunnus === selectedPackage}
                  onClick={() => onSelectPackage(item.pakkaustunnus)}
                >
                  <span className="catalogue-result-name">
                    <SourceValueDisplay field={item.productName} />
                  </span>
                  <span className="catalogue-result-ids">
                    <span className="monospace-value">
                      {item.pakkaustunnus}
                    </span>
                    <span className="catalogue-result-vnr">
                      VNR <SourceValueDisplay field={item.vnr} />
                    </span>
                  </span>
                  <span className="catalogue-result-meta">
                    <SourceValueDisplay field={item.pharmaceuticalForm} />
                    {" · "}
                    <SourceValueDisplay field={item.strength} />
                  </span>
                </button>
              </li>
            ))}
          </ul>
          {state.data.total > state.data.pageSize && (
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
                disabled={page * state.data.pageSize >= state.data.total}
                onClick={() => setPage((current) => current + 1)}
              >
                Next page
              </button>
            </div>
          )}
        </>
      )}
    </section>
  );
}
