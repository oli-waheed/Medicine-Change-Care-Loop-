import { useState } from "react";
import { SourceValueDisplay } from "./catalogueParts";
import {
  fetchLinks,
  type LinkCertainty,
  type LinkGroup,
} from "./medicineCatalogue";
import { useCatalogueRequest } from "./useCatalogueRequest";

const CERTAINTY_LABELS: Record<LinkCertainty, string> = {
  VERIFIED: "Verified link",
  POSSIBLE: "Possible link",
  MISSING: "Missing: cannot be linked",
};

// Long groups start folded so the most common groups stay readable.
const FOLDED_COUNT = 5;

function GroupItems({
  group: fullGroup,
  expanded,
  onOpenPackage,
  onOpenProduct,
}: {
  group: LinkGroup;
  expanded: boolean;
  onOpenPackage: (pakkaustunnus: string) => void;
  onOpenProduct?: (productReference: string) => void;
}) {
  const group = (
    expanded
      ? fullGroup
      : { ...fullGroup, items: fullGroup.items.slice(0, FOLDED_COUNT) }
  ) as LinkGroup;
  if (group.itemKind === "package") {
    return (
      <ul className="link-items">
        {group.items.map((item) => (
          <li key={item.pakkaustunnus}>
            <button
              type="button"
              className="catalogue-chip"
              onClick={() => onOpenPackage(item.pakkaustunnus)}
            >
              {item.pakkaustunnus}
            </button>{" "}
            <SourceValueDisplay field={item.name} />
            {" · "}
            <SourceValueDisplay field={item.strength} />
            {" · "}
            <SourceValueDisplay field={item.packageSizeText} />
          </li>
        ))}
      </ul>
    );
  }
  if (group.itemKind === "product") {
    return (
      <ul className="link-items">
        {group.items.map((item) => (
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
              <span className="monospace-value">{item.productReference}</span>
            )}{" "}
            <SourceValueDisplay field={item.name} />
            {" · "}
            <SourceValueDisplay field={item.strength} />
            {" · "}
            <SourceValueDisplay field={item.form} />
            {item.holders.length > 0 && ` · ${item.holders.join(", ")}`}
          </li>
        ))}
      </ul>
    );
  }
  if (group.itemKind === "shortage") {
    return (
      <ul className="link-items">
        {group.items.map((row) => (
          <li key={`${row.vnr}-${row.line}`}>
            VNR {row.vnr} · Valid {row.valid || "—"} · Unavailable from{" "}
            {row.unavailableFrom || "—"} · Estimated end {row.endingDate || "—"}{" "}
            · Updated {row.updated || "—"} · {row.company} (line {row.line})
          </li>
        ))}
      </ul>
    );
  }
  return null;
}

function GroupView({
  group,
  onOpenPackage,
  onOpenProduct,
}: {
  group: LinkGroup;
  onOpenPackage: (pakkaustunnus: string) => void;
  onOpenProduct?: (productReference: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const shown = expanded
    ? group.items.length
    : Math.min(group.items.length, FOLDED_COUNT);
  return (
    <li
      className={`link-group link-group--${group.certainty.toLowerCase()}`}
      aria-label={group.label}
    >
      <p className="link-group-heading">
        <strong>{group.label}</strong>
        <span
          className={`link-certainty link-certainty--${group.certainty.toLowerCase()}`}
        >
          {CERTAINTY_LABELS[group.certainty]}
        </span>
        {group.certainty !== "MISSING" && (
          <span className="link-count">{group.total}</span>
        )}
      </p>
      <p className="link-basis">{group.basis}</p>
      {group.note && <p className="link-basis">{group.note}</p>}
      <GroupItems
        group={group}
        expanded={expanded}
        onOpenPackage={onOpenPackage}
        onOpenProduct={onOpenProduct}
      />
      {group.items.length > FOLDED_COUNT && (
        <button
          type="button"
          className="catalogue-link-button"
          aria-expanded={expanded}
          onClick={() => setExpanded((value) => !value)}
        >
          {expanded
            ? "Show fewer"
            : `Show more (${group.items.length - FOLDED_COUNT})`}
        </button>
      )}
      {shown < group.total && (
        <p className="link-basis">
          Showing {shown} of {group.total}.
        </p>
      )}
    </li>
  );
}

// Feature 015: everything linked to a package or product, with how sure each link is.
export default function LinkedRecordsCard({
  kind,
  id,
  onOpenPackage,
  onOpenProduct,
}: {
  kind: "package" | "product";
  id: string;
  onOpenPackage: (pakkaustunnus: string) => void;
  onOpenProduct?: (productReference: string) => void;
}) {
  const state = useCatalogueRequest(`links:${kind}:${id}`, (signal) =>
    fetchLinks(kind, id, signal),
  );
  return (
    <section className="catalogue-card" aria-label="Linked records">
      <h3>Linked records</h3>
      {(state.status === "idle" || state.status === "loading") && (
        <p className="catalogue-note" role="status">
          Loading linked records…
        </p>
      )}
      {state.status === "error" && (
        <p className="catalogue-note">Linked records could not be loaded.</p>
      )}
      {state.status === "loaded" && (
        <>
          <p className="catalogue-note">{state.data.notice}</p>
          {state.data.groups.length === 0 ? (
            <p className="catalogue-note">No linked records.</p>
          ) : (
            <ul className="link-groups">
              {state.data.groups.map((group) => (
                <GroupView
                  key={group.id}
                  group={group}
                  onOpenPackage={onOpenPackage}
                  onOpenProduct={onOpenProduct}
                />
              ))}
            </ul>
          )}
        </>
      )}
    </section>
  );
}
