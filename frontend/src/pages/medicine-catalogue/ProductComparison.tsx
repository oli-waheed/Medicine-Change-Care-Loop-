import { FieldPath, SourceValueDisplay } from "./catalogueParts";
import { CatalogueErrorMessage, LoadingMessage } from "./CatalogueStates";
import { NoOccurrences } from "../open-review-cases/evidence/SourceValueDisplay";
import {
  fetchComparison,
  type ProductSummary,
  type SourceField,
} from "./medicineCatalogue";
import { useCatalogueRequest } from "./useCatalogueRequest";

function Values({ values }: { values: SourceField[] }) {
  if (values.length === 0) return <NoOccurrences />;
  return (
    <>
      {values.map((value, index) => (
        <span key={index} className="catalogue-value">
          <SourceValueDisplay field={value} />
        </span>
      ))}
    </>
  );
}

function Slot({
  label,
  product,
  onClear,
}: {
  label: string;
  product: ProductSummary | null;
  onClear: () => void;
}) {
  return (
    <div className="catalogue-slot">
      <p className="catalogue-slot-label">{label}</p>
      {product ? (
        <>
          <p className="catalogue-slot-name">
            <SourceValueDisplay field={product.name} />
          </p>
          <p className="monospace-value catalogue-subtitle">
            {product.productReference}
          </p>
          <button
            type="button"
            className="catalogue-link-button"
            onClick={onClear}
          >
            Remove {label}
          </button>
        </>
      ) : (
        <p className="catalogue-note">
          Open a product in Packages and choose “Add to comparison”.
        </p>
      )}
    </div>
  );
}

// FR-007: source fields side by side; a match or difference is not an equivalence claim.
export default function ProductComparison({
  productA,
  productB,
  onClear,
}: {
  productA: ProductSummary | null;
  productB: ProductSummary | null;
  onClear: (slot: "A" | "B") => void;
}) {
  const ready =
    productA?.productReference && productB?.productReference
      ? `compare:${productA.productReference}|${productB.productReference}`
      : null;
  const state = useCatalogueRequest(ready, (signal) =>
    fetchComparison(
      productA!.productReference!,
      productB!.productReference!,
      signal,
    ),
  );

  return (
    <section className="catalogue-compare" aria-label="Product comparison">
      <div className="catalogue-slots">
        <Slot
          label="Product A"
          product={productA}
          onClear={() => onClear("A")}
        />
        <Slot
          label="Product B"
          product={productB}
          onClear={() => onClear("B")}
        />
      </div>
      {state.status === "loading" && (
        <LoadingMessage>Comparing products…</LoadingMessage>
      )}
      {state.status === "error" && (
        <CatalogueErrorMessage error={state.error} />
      )}
      {state.status === "loaded" && (
        <>
          <p className="catalogue-notice">{state.data.notice}</p>
          <div className="catalogue-table-wrap">
            <table className="catalogue-table catalogue-compare-table">
              <caption className="visually-hidden">
                Source fields of the two products
              </caption>
              <thead>
                <tr>
                  <th scope="col">Source field</th>
                  <th scope="col">Product A</th>
                  <th scope="col">Product B</th>
                  <th scope="col">Result</th>
                </tr>
              </thead>
              <tbody>
                {state.data.fields.map((field) => (
                  <tr
                    key={field.field}
                    className={`catalogue-compare-row catalogue-compare-row--${field.result.toLowerCase()}`}
                  >
                    <th scope="row" className="monospace-value">
                      <FieldPath path={field.field} />
                    </th>
                    <td>
                      <Values values={field.a} />
                    </td>
                    <td>
                      <Values values={field.b} />
                    </td>
                    <td>
                      <span
                        className={`catalogue-compare-result catalogue-compare-result--${field.result.toLowerCase()}`}
                      >
                        {field.result === "SAME" ? "Same" : "Different"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </section>
  );
}
