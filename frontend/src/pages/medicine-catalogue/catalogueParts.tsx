import type { ReactNode } from "react";
import EvidenceClassificationLabel from "../open-review-cases/evidence/EvidenceClassificationLabel";
import FieldPath from "../open-review-cases/evidence/FieldPath";
import {
  NoOccurrences,
  SourceValueDisplay,
} from "../open-review-cases/evidence/SourceValueDisplay";
import TimestampDisplay from "../open-review-cases/evidence/TimestampDisplay";
import type {
  ActiveSubstance,
  Authorization,
  CatalogueRelease,
  PackageProvenance,
  SourceField,
} from "./medicineCatalogue";

export { FieldPath, SourceValueDisplay };

// One labelled source value; missing, empty and no-occurrences keep their own look.
export function SourceRow({
  label,
  field,
  mono = false,
}: {
  label: string;
  field: SourceField | SourceField[];
  mono?: boolean;
}) {
  const values = Array.isArray(field) ? field : [field];
  return (
    <div>
      <dt>{label}</dt>
      <dd className={mono ? "monospace-value" : undefined}>
        {values.length === 0 ? (
          <NoOccurrences />
        ) : (
          values.map((value, index) => (
            <span key={index} className="catalogue-value">
              <SourceValueDisplay field={value} />
            </span>
          ))
        )}
      </dd>
    </div>
  );
}

export function TextRow({
  label,
  children,
  mono = false,
}: {
  label: string;
  children: ReactNode;
  mono?: boolean;
}) {
  return (
    <div>
      <dt>{label}</dt>
      <dd className={mono ? "monospace-value" : undefined}>{children}</dd>
    </div>
  );
}

// Package identity and VNR are shown side by side but never as one value (FR-012, §4).
export function IdentityBlock({
  pakkaustunnus,
  vnr,
}: {
  pakkaustunnus: string;
  vnr: SourceField;
}) {
  return (
    <dl className="catalogue-identity">
      <div className="catalogue-identity-item">
        <dt>Package ID (Pakkaustunnus)</dt>
        <dd className="monospace-value">{pakkaustunnus}</dd>
      </div>
      <div className="catalogue-identity-item catalogue-identity-item--vnr">
        <dt>VNR</dt>
        <dd className="monospace-value">
          <SourceValueDisplay field={vnr} />
        </dd>
      </div>
    </dl>
  );
}

export function SubstanceTable({
  substances,
  caption,
}: {
  substances: ActiveSubstance[];
  caption: string;
}) {
  if (substances.length === 0) {
    return (
      <p className="catalogue-note">
        <NoOccurrences />
      </p>
    );
  }
  return (
    <div className="catalogue-table-wrap">
      <table className="catalogue-table">
        <caption className="visually-hidden">{caption}</caption>
        <thead>
          <tr>
            <th scope="col">#</th>
            <th scope="col">Substance</th>
            <th scope="col">CAS number</th>
            <th scope="col">Quantity</th>
            <th scope="col">Unit</th>
            <th scope="col">Undivided strength</th>
          </tr>
        </thead>
        <tbody>
          {substances.map((substance, index) => (
            <tr key={index}>
              <td>{index + 1}</td>
              <td>
                <SourceValueDisplay field={substance.name} />
              </td>
              <td className="monospace-value">
                <SourceValueDisplay field={substance.casNumber} />
              </td>
              <td>
                <SourceValueDisplay field={substance.quantity} />
              </td>
              <td>
                <SourceValueDisplay field={substance.quantityUnit} />
              </td>
              <td>
                <SourceValueDisplay field={substance.undividedStrength} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function AuthorizationList({ items }: { items: Authorization[] }) {
  if (items.length === 0) {
    return (
      <p className="catalogue-note">
        <NoOccurrences />
      </p>
    );
  }
  return (
    <ul className="catalogue-authorizations">
      {items.map((item, index) => (
        <li key={index}>
          <p className="catalogue-authorization-branch">{item.branch}</p>
          <dl className="catalogue-fields">
            <SourceRow label="Status (Tila)" field={item.status} />
            <SourceRow label="Granted on" field={item.grantedOn} />
            <SourceRow label="Ends on" field={item.endsOn} />
          </dl>
        </li>
      ))}
    </ul>
  );
}

export function ProvenanceCard({
  provenance,
}: {
  provenance: PackageProvenance;
}) {
  return (
    <section className="catalogue-card" aria-label="Source provenance">
      <h3>Source provenance</h3>
      <dl className="catalogue-fields">
        <TextRow label="Source">{provenance.sourceName}</TextRow>
        <SourceRow
          label="Release reference"
          field={provenance.releaseReference}
          mono
        />
        <SourceRow label="Release date" field={provenance.releaseDate} />
        <TextRow label="Retrieved at">
          <TimestampDisplay
            value={provenance.retrievedAt}
            fallback="Not captured"
          />
        </TextRow>
        <TextRow label="Raw file" mono>
          {provenance.fileName ?? "Unknown"}
        </TextRow>
        <TextRow label="Checksum" mono>
          <span className="checksum">{provenance.checksum ?? "Unknown"}</span>
        </TextRow>
        <TextRow label="Record locator" mono>
          {provenance.recordLocator ?? "Unknown"}
        </TextRow>
        <TextRow label="Evidence classification">
          <EvidenceClassificationLabel
            classification={provenance.evidenceClass}
          />
        </TextRow>
      </dl>
    </section>
  );
}

export function ReleaseSummary({
  release,
  counts,
}: {
  release: CatalogueRelease;
  counts?: { packages: number; products: number; substances: number };
}) {
  return (
    <section className="catalogue-source" aria-label="Active catalogue release">
      <h2>Active catalogue release</h2>
      <dl className="catalogue-fields catalogue-fields--inline">
        <TextRow label="Source">{release.sourceName}</TextRow>
        {release.releaseDate && (
          <SourceRow
            label="Release date (Ajopvm)"
            field={release.releaseDate}
          />
        )}
        {release.releaseReference && (
          <SourceRow
            label="Release reference"
            field={release.releaseReference}
            mono
          />
        )}
        <TextRow label="Retrieved at">
          <TimestampDisplay
            value={release.retrievedAt}
            fallback="Not captured"
          />
        </TextRow>
        <TextRow label="Raw file" mono>
          {release.fileName ?? "Unknown"}
        </TextRow>
        <TextRow label="Chronology">{release.chronologyEvidence}</TextRow>
        {counts && (
          <TextRow label="Records">
            {counts.packages} packages · {counts.products} products ·{" "}
            {counts.substances} active substances
          </TextRow>
        )}
      </dl>
      {release.checksum && (
        <p className="catalogue-checksum">
          <span>Checksum</span>{" "}
          <span className="monospace-value checksum">{release.checksum}</span>
        </p>
      )}
    </section>
  );
}
