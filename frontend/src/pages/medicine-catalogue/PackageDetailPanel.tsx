import {
  AuthorizationList,
  IdentityBlock,
  ProvenanceCard,
  SourceRow,
  SourceValueDisplay,
  SubstanceTable,
} from "./catalogueParts";
import { CatalogueErrorMessage, LoadingMessage } from "./CatalogueStates";
import PackageHistoryCard from "./PackageHistoryCard";
import { fetchPackage } from "./medicineCatalogue";
import { useCatalogueRequest } from "./useCatalogueRequest";

export default function PackageDetailPanel({
  pakkaustunnus,
  onOpenPackage,
  onOpenProduct,
}: {
  pakkaustunnus: string;
  onOpenPackage: (pakkaustunnus: string) => void;
  onOpenProduct: (productReference: string) => void;
}) {
  const state = useCatalogueRequest(`package:${pakkaustunnus}`, (signal) =>
    fetchPackage(pakkaustunnus, signal),
  );
  if (state.status === "idle" || state.status === "loading")
    return <LoadingMessage>Loading package details…</LoadingMessage>;
  if (state.status === "error")
    return <CatalogueErrorMessage error={state.error} />;

  const { package: pkg, product, authorizations, sameVnrPackages } = state.data;
  return (
    <article
      className="catalogue-detail"
      aria-label={`Package ${pkg.pakkaustunnus}`}
    >
      <header className="catalogue-detail-header">
        <p className="eyebrow">Package record</p>
        <h2>
          <SourceValueDisplay field={product.name} />
        </h2>
        <IdentityBlock pakkaustunnus={pkg.pakkaustunnus} vnr={pkg.vnr} />
        {product.productReference && (
          <button
            type="button"
            className="catalogue-link-button"
            onClick={() => onOpenProduct(product.productReference!)}
          >
            Open product {product.productReference}
          </button>
        )}
      </header>

      <section className="catalogue-card" aria-label="Package information">
        <h3>Package information</h3>
        <dl className="catalogue-fields">
          <SourceRow label="Package size (text)" field={pkg.packageSizeText} />
          <SourceRow label="Package size" field={pkg.packageSize} />
          <SourceRow
            label="Size multiplier"
            field={pkg.packageSizeMultiplier}
          />
          <SourceRow label="Size unit" field={pkg.packageSizeUnit} />
          <SourceRow
            label="Public clarification (JulkinenTarkenne)"
            field={pkg.publicClarification}
          />
          <SourceRow
            label="On the market (Kaupan)"
            field={pkg.availability.available}
          />
          <SourceRow
            label="Available from"
            field={pkg.availability.availableFrom}
          />
          <SourceRow
            label="Available until"
            field={pkg.availability.availableUntil}
          />
        </dl>
      </section>

      <section
        className="catalogue-card"
        aria-label="Packages with the same VNR"
      >
        <h3>Other packages with the same VNR</h3>
        {pkg.vnr.state !== "value" ? (
          <p className="catalogue-note">
            This package has no VNR value in the source, so it is not grouped
            with other packages.
          </p>
        ) : sameVnrPackages.length === 0 ? (
          <p className="catalogue-note">
            No other package in this release has this VNR.
          </p>
        ) : (
          <ul className="catalogue-chip-list">
            {sameVnrPackages.map((id) => (
              <li key={id}>
                <button
                  type="button"
                  className="catalogue-chip"
                  onClick={() => onOpenPackage(id)}
                >
                  {id}
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section
        className="catalogue-card"
        aria-label="Package active substances"
      >
        <h3>Active substances (source order)</h3>
        <SubstanceTable
          substances={pkg.activeSubstances}
          caption={`Active substances of package ${pkg.pakkaustunnus}`}
        />
      </section>

      <section className="catalogue-card" aria-label="Package authorizations">
        <h3>Authorization and registration</h3>
        <AuthorizationList items={authorizations} />
      </section>

      <PackageHistoryCard pakkaustunnus={pkg.pakkaustunnus} />

      <ProvenanceCard provenance={pkg.provenance} />
    </article>
  );
}
