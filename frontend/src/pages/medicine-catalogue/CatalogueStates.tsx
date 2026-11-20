import type { CatalogueError } from "./medicineCatalogue";

export function LoadingMessage({ children }: { children: string }) {
  return (
    <p className="catalogue-state" role="status">
      {children}
    </p>
  );
}

// FR-009: an explicit unavailable message; never a fallback to another release.
export function CatalogueErrorMessage({ error }: { error: CatalogueError }) {
  if (error.code === "CATALOGUE_UNAVAILABLE") {
    return (
      <div
        className="catalogue-state catalogue-state--unavailable"
        role="status"
      >
        <p className="catalogue-state-title">Catalogue unavailable</p>
        <p>
          No validated Fimea release with verified chronology has been loaded
          yet, so there is nothing to show. The catalogue never falls back to an
          unverified release.
        </p>
      </div>
    );
  }
  if (error.code === "CATALOGUE_SOURCE_UNREADABLE") {
    return (
      <div className="catalogue-state catalogue-state--error" role="alert">
        <p className="catalogue-state-title">
          Source release could not be read
        </p>
        <p>
          The stored release behind the catalogue no longer matches its recorded
          checksum or cannot be opened, so its records are not shown.
        </p>
        <p className="catalogue-state-detail">{error.message}</p>
      </div>
    );
  }
  return (
    <p className="catalogue-state catalogue-state--error" role="alert">
      {error.message}
    </p>
  );
}
