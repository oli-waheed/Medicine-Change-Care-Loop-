import { useId, useState } from "react";
import { SourceValueDisplay } from "./catalogueParts";
import { CatalogueErrorMessage, LoadingMessage } from "./CatalogueStates";
import { fetchSubstances, type SubstancePage } from "./medicineCatalogue";
import { useCatalogueRequest, useDebouncedValue } from "./useCatalogueRequest";

type Substance = SubstancePage["items"][number];

// Occurrences are shown on request: in the real register one substance can
// occur in thousands of packages.
function SubstanceCard({
  item,
  onOpenPackage,
}: {
  item: Substance;
  onOpenPackage: (pakkaustunnus: string) => void;
}) {
  const id = useId();
  const [open, setOpen] = useState(false);
  const count = item.occurrences.length;
  return (
    <article className="catalogue-card catalogue-substance">
      <h3>
        <SourceValueDisplay field={item.name} />
      </h3>
      <p className="catalogue-subtitle">
        <span className="monospace-value">{item.identity}</span>
        {" · CAS "}
        <span className="monospace-value">
          <SourceValueDisplay field={item.casNumber} />
        </span>
        {` · ${count} ${count === 1 ? "occurrence" : "occurrences"}`}
      </p>
      <button
        type="button"
        className="catalogue-link-button"
        aria-expanded={open}
        aria-controls={`${id}-occurrences`}
        onClick={() => setOpen((current) => !current)}
      >
        {open ? "Hide occurrences" : `Show occurrences (${count})`}
      </button>
      {open && (
        <div className="catalogue-table-wrap" id={`${id}-occurrences`}>
          <table className="catalogue-table">
            <caption className="visually-hidden">
              Occurrences of {item.identity}
            </caption>
            <thead>
              <tr>
                <th scope="col">Package</th>
                <th scope="col">Product</th>
                <th scope="col">Position</th>
                <th scope="col">Quantity</th>
                <th scope="col">Unit</th>
                <th scope="col">Undivided strength</th>
              </tr>
            </thead>
            <tbody>
              {item.occurrences.map((occurrence, index) => (
                <tr key={`${occurrence.pakkaustunnus}-${index}`}>
                  <td>
                    <button
                      type="button"
                      className="catalogue-chip"
                      onClick={() => onOpenPackage(occurrence.pakkaustunnus)}
                    >
                      {occurrence.pakkaustunnus}
                    </button>
                  </td>
                  <td>
                    <SourceValueDisplay field={occurrence.productName} />
                  </td>
                  <td>{occurrence.position}</td>
                  <td>
                    <SourceValueDisplay field={occurrence.quantity} />
                  </td>
                  <td>
                    <SourceValueDisplay field={occurrence.quantityUnit} />
                  </td>
                  <td>
                    <SourceValueDisplay field={occurrence.undividedStrength} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </article>
  );
}

// FR-006: substances with every occurrence, in source order, repeats kept.
export default function SubstanceExplorer({
  onOpenPackage,
}: {
  onOpenPackage: (pakkaustunnus: string) => void;
}) {
  const id = useId();
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const debounced = useDebouncedValue(query, 250);
  const state = useCatalogueRequest(
    `substances:${debounced.trim()}:${page}`,
    (signal) => fetchSubstances(debounced, page, signal),
  );

  return (
    <section
      className="catalogue-substances"
      aria-label="Active-substance explorer"
    >
      <div className="catalogue-filter">
        <label htmlFor={`${id}-q`}>Search active substances</label>
        <input
          id={`${id}-q`}
          type="search"
          value={query}
          autoComplete="off"
          spellCheck={false}
          placeholder="Name, code or CAS number"
          onChange={(event) => {
            setQuery(event.target.value);
            setPage(1);
          }}
        />
      </div>
      {(state.status === "idle" || state.status === "loading") && (
        <LoadingMessage>Loading active substances…</LoadingMessage>
      )}
      {state.status === "error" && (
        <CatalogueErrorMessage error={state.error} />
      )}
      {state.status === "loaded" && (
        <>
          <p className="catalogue-result-count" role="status">
            {state.data.total === 0
              ? "No active substances match this search."
              : `Showing ${(state.data.page - 1) * state.data.pageSize + 1}–${
                  (state.data.page - 1) * state.data.pageSize +
                  state.data.items.length
                } of ${state.data.total} active substances`}
          </p>
          {state.data.items.map((item) => (
            <SubstanceCard
              key={item.identity}
              item={item}
              onOpenPackage={onOpenPackage}
            />
          ))}
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
