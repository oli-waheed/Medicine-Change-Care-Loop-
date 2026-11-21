import {
  AuthorizationList,
  SourceRow,
  SourceValueDisplay,
  SubstanceTable,
} from "./catalogueParts";
import { CatalogueErrorMessage, LoadingMessage } from "./CatalogueStates";
import LinkedRecordsCard from "./LinkedRecordsCard";
import { fetchProduct, type ProductSummary } from "./medicineCatalogue";
import { useCatalogueRequest } from "./useCatalogueRequest";

export default function ProductDetailPanel({
  productReference,
  onOpenPackage,
  onOpenProduct,
  onAddToComparison,
}: {
  productReference: string;
  onOpenPackage: (pakkaustunnus: string) => void;
  onOpenProduct?: (productReference: string) => void;
  onAddToComparison: (product: ProductSummary) => void;
}) {
  const state = useCatalogueRequest(`product:${productReference}`, (signal) =>
    fetchProduct(productReference, signal),
  );
  if (state.status === "idle" || state.status === "loading")
    return <LoadingMessage>Loading product details…</LoadingMessage>;
  if (state.status === "error")
    return <CatalogueErrorMessage error={state.error} />;

  const { product, packages } = state.data;
  return (
    <article
      className="catalogue-detail"
      aria-label={`Product ${product.productReference}`}
    >
      <header className="catalogue-detail-header">
        <p className="eyebrow">Product (Laakevalmiste)</p>
        <h2>
          <SourceValueDisplay field={product.name} />
        </h2>
        <p className="catalogue-subtitle monospace-value">
          Product reference {product.productReference}
        </p>
        <button
          type="button"
          className="catalogue-link-button"
          onClick={() => onAddToComparison(product)}
        >
          Add to comparison
        </button>
      </header>

      <section className="catalogue-card" aria-label="Product information">
        <h3>Product information</h3>
        <dl className="catalogue-fields">
          <SourceRow label="Product name (Kauppanimi)" field={product.name} />
          <SourceRow label="Strength (Vahvuus)" field={product.strength} />
          <SourceRow
            label="Pharmaceutical form (Laakemuoto)"
            field={product.pharmaceuticalForm}
          />
          <SourceRow label="ATC code" field={product.atcCode} />
          <SourceRow
            label="Administration route (Antoreitti)"
            field={product.administrationRoutes}
          />
        </dl>
      </section>

      <section
        className="catalogue-card"
        aria-label="Product active substances"
      >
        <h3>Active substances (source order)</h3>
        {product.activeSubstancesVaryByPackage ? (
          <p className="catalogue-note">
            The packages of this product list different active substances in the
            source. Open a package to see its own list.
          </p>
        ) : (
          <SubstanceTable
            substances={product.activeSubstances}
            caption={`Active substances of product ${product.productReference}`}
          />
        )}
      </section>

      <section className="catalogue-card" aria-label="Product packages">
        <h3>Packages ({packages.length})</h3>
        <p className="catalogue-note">
          Each package keeps its own package ID; the VNR is shown per package.
        </p>
        <ul className="catalogue-package-list">
          {packages.map((pkg) => (
            <li key={pkg.pakkaustunnus}>
              <button
                type="button"
                className="catalogue-package-button"
                onClick={() => onOpenPackage(pkg.pakkaustunnus)}
              >
                <span className="monospace-value">{pkg.pakkaustunnus}</span>
                <span className="catalogue-package-vnr">
                  VNR <SourceValueDisplay field={pkg.vnr} />
                </span>
                <span>
                  <SourceValueDisplay field={pkg.packageSizeText} />
                </span>
              </button>
            </li>
          ))}
        </ul>
      </section>

      <section className="catalogue-card" aria-label="Product authorizations">
        <h3>Authorization and registration</h3>
        <AuthorizationList items={product.authorizations} />
      </section>

      {product.productReference && (
        <LinkedRecordsCard
          kind="product"
          id={product.productReference}
          onOpenPackage={onOpenPackage}
          onOpenProduct={onOpenProduct}
        />
      )}
    </article>
  );
}
