import { useRef, useState } from "react";
import "../open-review-cases/OpenReviewCasesPage.css";
import "./MedicineCataloguePage.css";
import { ReleaseSummary } from "./catalogueParts";
import CatalogueSearch from "./CatalogueSearch";
import { CatalogueErrorMessage, LoadingMessage } from "./CatalogueStates";
import { fetchSource, type ProductSummary } from "./medicineCatalogue";
import PackageDetailPanel from "./PackageDetailPanel";
import ProductComparison from "./ProductComparison";
import ProductDetailPanel from "./ProductDetailPanel";
import SubstanceExplorer from "./SubstanceExplorer";
import { useCatalogueRequest } from "./useCatalogueRequest";

type View = "packages" | "substances" | "compare";
type Detail =
  { kind: "package"; id: string } | { kind: "product"; id: string } | null;

const VIEWS: { id: View; label: string }[] = [
  { id: "packages", label: "Packages" },
  { id: "substances", label: "Active substances" },
  { id: "compare", label: "Compare" },
];

// Feature 004: read-only catalogue of the active validated baseline release.
export default function MedicineCataloguePage() {
  const source = useCatalogueRequest("source", (signal) => fetchSource(signal));
  const [view, setView] = useState<View>("packages");
  const [detail, setDetail] = useState<Detail>(null);
  const [compareA, setCompareA] = useState<ProductSummary | null>(null);
  const [compareB, setCompareB] = useState<ProductSummary | null>(null);
  const detailRef = useRef<HTMLDivElement>(null);

  function show(next: Detail) {
    setDetail(next);
    setView("packages");
    // Move focus to the detail so keyboard and screen-reader users follow it.
    window.requestAnimationFrame(() => detailRef.current?.focus());
  }

  function addToComparison(product: ProductSummary) {
    if (!product.productReference) return;
    if (compareA?.productReference === product.productReference) return;
    if (compareB?.productReference === product.productReference) return;
    if (!compareA) setCompareA(product);
    else setCompareB(product);
    setView("compare");
  }

  const header = (
    <header className="page-header">
      <p className="eyebrow">Medicine Change Care Loop</p>
      <h1>Medicine Catalogue</h1>
      <p className="page-description">
        Browse the packages, products and active substances of the active
        validated Fimea release exactly as the source records them. Read-only;
        nothing here changes review cases.
      </p>
    </header>
  );

  if (source.status === "idle" || source.status === "loading") {
    return (
      <div className="catalogue-page">
        {header}
        <LoadingMessage>Loading catalogue release…</LoadingMessage>
      </div>
    );
  }
  if (source.status === "error") {
    return (
      <div className="catalogue-page">
        {header}
        <CatalogueErrorMessage error={source.error} />
      </div>
    );
  }

  const summary = source.data;
  const compareCount = (compareA ? 1 : 0) + (compareB ? 1 : 0);
  return (
    <div className="catalogue-page">
      {header}
      <ReleaseSummary
        release={summary.release}
        counts={{
          packages: summary.packageCount,
          products: summary.productCount,
          substances: summary.activeSubstanceCount,
        }}
      />

      <div className="catalogue-views" role="group" aria-label="Catalogue view">
        {VIEWS.map(({ id, label }) => (
          <button
            key={id}
            type="button"
            className="catalogue-view-button"
            aria-pressed={view === id}
            onClick={() => setView(id)}
          >
            {label}
            {id === "compare" && compareCount > 0 && ` (${compareCount})`}
          </button>
        ))}
      </div>

      {view === "packages" && (
        <div className="catalogue-layout">
          <CatalogueSearch
            selectedPackage={detail?.kind === "package" ? detail.id : null}
            onSelectPackage={(id) => show({ kind: "package", id })}
          />
          <div
            className="catalogue-detail-region"
            ref={detailRef}
            tabIndex={-1}
            aria-label="Catalogue record details"
            role="region"
          >
            {detail === null && (
              <p className="catalogue-state">
                Select a package to see its source record.
              </p>
            )}
            {detail?.kind === "package" && (
              <PackageDetailPanel
                key={detail.id}
                pakkaustunnus={detail.id}
                onOpenPackage={(id) => show({ kind: "package", id })}
                onOpenProduct={(id) => show({ kind: "product", id })}
              />
            )}
            {detail?.kind === "product" && (
              <ProductDetailPanel
                key={detail.id}
                productReference={detail.id}
                onOpenPackage={(id) => show({ kind: "package", id })}
                onAddToComparison={addToComparison}
              />
            )}
          </div>
        </div>
      )}

      {view === "substances" && (
        <SubstanceExplorer
          onOpenPackage={(id) => show({ kind: "package", id })}
        />
      )}

      {view === "compare" && (
        <ProductComparison
          productA={compareA}
          productB={compareB}
          onClear={(slot) =>
            slot === "A" ? setCompareA(null) : setCompareB(null)
          }
        />
      )}
    </div>
  );
}
