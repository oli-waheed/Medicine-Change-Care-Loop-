import { useId, useState } from "react";
import { SourceValueDisplay } from "./catalogueParts";
import { CatalogueErrorMessage, LoadingMessage } from "./CatalogueStates";
import { fetchSubstances } from "./medicineCatalogue";
import { useCatalogueRequest, useDebouncedValue } from "./useCatalogueRequest";

// FR-006: substances with every occurrence, in source order, repeats kept.
export default function SubstanceExplorer({
  onOpenPackage,
}: {
  onOpenPackage: (pakkaustunnus: string) => void;
}) {
  const id = useId();
  const [query, setQuery] = useState("");
  const debounced = useDebouncedValue(query, 250);
  const state = useCatalogueRequest(
    `substances:${debounced.trim()}`,
    (signal) => fetchSubstances(debounced, signal),
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
          onChange={(event) => setQuery(event.target.value)}
        />
      </div>
      {(state.status === "idle" || state.status === "loading") && (
        <LoadingMessage>Loading active substances…</LoadingMessage>
      )}
      {state.status === "error" && (
        <CatalogueErrorMessage error={state.error} />
      )}
      {state.status === "loaded" && state.data.items.length === 0 && (
        <p className="catalogue-state">
          No active substances match this search.
        </p>
      )}
      {state.status === "loaded" &&
        state.data.items.map((item) => (
          <article
            className="catalogue-card catalogue-substance"
            key={item.identity}
          >
            <h3>
              <SourceValueDisplay field={item.name} />
            </h3>
            <p className="catalogue-subtitle">
              <span className="monospace-value">{item.identity}</span>
              {" · CAS "}
              <span className="monospace-value">
                <SourceValueDisplay field={item.casNumber} />
              </span>
            </p>
            <div className="catalogue-table-wrap">
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
                          onClick={() =>
                            onOpenPackage(occurrence.pakkaustunnus)
                          }
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
                        <SourceValueDisplay
                          field={occurrence.undividedStrength}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </article>
        ))}
    </section>
  );
}
