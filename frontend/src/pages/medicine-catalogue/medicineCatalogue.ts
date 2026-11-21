// Client for the read-only catalogue API (specs/004…/contracts/catalogue-api.md).
import type { SourceField } from "../open-review-cases/openReviewCases";

export type { SourceField };

export type CatalogueRelease = {
  releaseId: string;
  sourceName: string;
  releaseDate: SourceField | null;
  releaseReference: SourceField | null;
  retrievedAt: string | null;
  fileName: string | null;
  checksum: string | null;
  chronologyEvidence: string;
};

export type PackageSummary = {
  pakkaustunnus: string;
  vnr: SourceField;
  productReference: string | null;
  productName: SourceField;
  strength: SourceField;
  pharmaceuticalForm: SourceField;
  atcCode: SourceField;
  packageSizeText: SourceField;
  available: SourceField;
};

export type ProductSummary = {
  productReference: string | null;
  name: SourceField;
  strength: SourceField;
  pharmaceuticalForm: SourceField;
  atcCode: SourceField;
};

export type ActiveSubstance = {
  name: SourceField;
  casNumber: SourceField;
  quantity: SourceField;
  quantityUnit: SourceField;
  undividedStrength: SourceField;
};

export type Authorization = {
  branch: string;
  status: SourceField;
  grantedOn: SourceField;
  endsOn: SourceField;
};

export type PackageProvenance = {
  sourceName: string;
  releaseReference: SourceField;
  releaseDate: SourceField;
  retrievedAt: string | null;
  fileName: string | null;
  checksum: string | null;
  recordIdentifier: string;
  recordLocator: string | null;
  evidenceClass: "VERIFIED" | "INFERRED" | "UNKNOWN" | "CONFLICTING";
};

export type CataloguePage = {
  release: CatalogueRelease;
  total: number;
  page: number;
  pageSize: number;
  items: PackageSummary[];
};

export type ProductDetail = {
  release: CatalogueRelease;
  product: ProductSummary & {
    administrationRoutes: SourceField[];
    activeSubstances: ActiveSubstance[];
    activeSubstancesVaryByPackage: boolean;
    authorizations: Authorization[];
  };
  packages: PackageSummary[];
};

export type PackageDetail = {
  release: CatalogueRelease;
  package: {
    pakkaustunnus: string;
    vnr: SourceField;
    packageSizeText: SourceField;
    packageSize: SourceField;
    packageSizeMultiplier: SourceField;
    packageSizeUnit: SourceField;
    publicClarification: SourceField;
    availability: {
      available: SourceField;
      availableFrom: SourceField;
      availableUntil: SourceField;
    };
    activeSubstances: ActiveSubstance[];
    provenance: PackageProvenance;
  };
  product: ProductSummary;
  authorizations: Authorization[];
  sameVnrPackages: string[];
};

export type SubstanceOccurrence = {
  pakkaustunnus: string;
  productReference: string;
  productName: SourceField;
  position: number;
  quantity: SourceField;
  quantityUnit: SourceField;
  undividedStrength: SourceField;
};

export type SubstancePage = {
  release: CatalogueRelease;
  total: number;
  page: number;
  pageSize: number;
  items: {
    identity: string;
    name: SourceField;
    casNumber: SourceField;
    occurrences: SubstanceOccurrence[];
  }[];
};

export type ComparedField = {
  field: string;
  a: SourceField[];
  b: SourceField[];
  result: "SAME" | "DIFFERENT";
};

export type Comparison = {
  release: CatalogueRelease;
  productA: ProductSummary;
  productB: ProductSummary;
  fields: ComparedField[];
  notice: string;
};

export type SourceSummary = {
  release: CatalogueRelease;
  packageCount: number;
  productCount: number;
  activeSubstanceCount: number;
};

export type CatalogueFilters = {
  q: string;
  activeSubstance: string;
  atc: string;
  form: string;
  route: string;
  vnr: string;
  available: "" | "1" | "0";
  missing: "" | "vnr" | "atc" | "form" | "route" | "available";
};

export const EMPTY_FILTERS: CatalogueFilters = {
  q: "",
  activeSubstance: "",
  atc: "",
  form: "",
  route: "",
  vnr: "",
  available: "",
  missing: "",
};

export type CatalogueErrorCode =
  | "CATALOGUE_UNAVAILABLE"
  | "CATALOGUE_SOURCE_UNREADABLE"
  | "PRODUCT_NOT_FOUND"
  | "PACKAGE_NOT_FOUND"
  | "REQUEST_FAILED";

export class CatalogueError extends Error {
  readonly code: CatalogueErrorCode;

  constructor(code: CatalogueErrorCode, message: string) {
    super(message);
    this.code = code;
  }
}

const BASE = "/api/medicine-catalogue";

const NOT_FOUND_MESSAGES: Partial<Record<CatalogueErrorCode, string>> = {
  PRODUCT_NOT_FOUND: "This product is not in the active catalogue release.",
  PACKAGE_NOT_FOUND: "This package is not in the active catalogue release.",
};

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(path, { signal });
  if (response.ok) return (await response.json()) as T;
  let code: CatalogueErrorCode = "REQUEST_FAILED";
  let message = `The catalogue request failed (HTTP ${response.status}).`;
  try {
    const body = (await response.json()) as {
      detail?: { code?: CatalogueErrorCode; message?: string } | string;
    };
    if (body.detail && typeof body.detail === "object") {
      code = body.detail.code ?? code;
      message = body.detail.message ?? NOT_FOUND_MESSAGES[code] ?? message;
    } else if (typeof body.detail === "string") {
      message = body.detail;
    }
  } catch {
    // Keep the generic message when the body is not JSON.
  }
  throw new CatalogueError(code, message);
}

export function catalogueQuery(filters: CatalogueFilters, page: number) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value.trim()) params.set(key, value.trim());
  }
  if (page > 1) params.set("page", String(page));
  return params.toString();
}

export function fetchCatalogue(
  filters: CatalogueFilters,
  page: number,
  signal?: AbortSignal,
) {
  const query = catalogueQuery(filters, page);
  return getJson<CataloguePage>(query ? `${BASE}?${query}` : BASE, signal);
}

export function fetchProduct(reference: string, signal?: AbortSignal) {
  return getJson<ProductDetail>(
    `${BASE}/products/${encodeURIComponent(reference)}`,
    signal,
  );
}

export function fetchPackage(pakkaustunnus: string, signal?: AbortSignal) {
  return getJson<PackageDetail>(
    `${BASE}/packages/${encodeURIComponent(pakkaustunnus)}`,
    signal,
  );
}

// Feature 013: a package's recorded changes across compared releases.
export type PackageHistoryEvent = {
  priorReleaseDate: string | null;
  currentReleaseDate: string | null;
  kind: "FIELDS_CHANGED" | "NO_LONGER_PRESENT" | "NEWLY_PRESENT";
  cleanupLabel: "FORMATTING_ONLY" | "ACTIVE_SUBSTANCE_ONLY" | null;
  changes: {
    field: string;
    before: SourceField[];
    after: SourceField[];
    formattingOnly: boolean;
  }[];
};

export type PackageHistory = {
  pakkaustunnus: string;
  comparedPairs: {
    priorReleaseDate: string | null;
    currentReleaseDate: string | null;
  }[];
  events: PackageHistoryEvent[];
};

export function fetchPackageHistory(
  pakkaustunnus: string,
  signal?: AbortSignal,
) {
  return getJson<PackageHistory>(
    `${BASE}/packages/${encodeURIComponent(pakkaustunnus)}/history`,
    signal,
  );
}

// Feature 015: records linked to a package or product.
export type LinkCertainty = "VERIFIED" | "POSSIBLE" | "MISSING";

export type LinkedPackage = {
  pakkaustunnus: string;
  productReference: string;
  name: SourceField;
  strength: SourceField;
  packageSizeText: SourceField;
  vnr: SourceField;
};

export type LinkedProduct = {
  productReference: string;
  name: SourceField;
  strength: SourceField;
  form: SourceField;
  holders: string[];
  packageCount: number;
};

export type LinkedShortage = {
  line: number;
  vnr: string;
  valid: string;
  unavailableFrom: string;
  endingDate: string;
  updated: string;
  company: string;
};

export type LinkGroup = {
  id: string;
  label: string;
  certainty: LinkCertainty;
  basis: string;
  total: number;
  note: string | null;
} & (
  | { itemKind: "package"; items: LinkedPackage[] }
  | { itemKind: "product"; items: LinkedProduct[] }
  | { itemKind: "shortage"; items: LinkedShortage[] }
  | { itemKind: "none"; items: [] }
);

export type LinkedRecords = {
  releaseId: string;
  anchorPackages: string[];
  shortageSource: { captureReference: string; lastRetrievedAt: string } | null;
  notice: string;
  groups: LinkGroup[];
};

export function fetchLinks(
  kind: "package" | "product",
  id: string,
  signal?: AbortSignal,
) {
  const segment = kind === "package" ? "packages" : "products";
  return getJson<LinkedRecords>(
    `${BASE}/${segment}/${encodeURIComponent(id)}/links`,
    signal,
  );
}

// Substances can occur in thousands of packages, so pages stay small.
export const SUBSTANCE_PAGE_SIZE = 25;

export function fetchSubstances(
  query: string,
  page: number,
  signal?: AbortSignal,
) {
  const params = new URLSearchParams();
  if (query.trim()) params.set("q", query.trim());
  if (page > 1) params.set("page", String(page));
  params.set("pageSize", String(SUBSTANCE_PAGE_SIZE));
  return getJson<SubstancePage>(`${BASE}/active-substances?${params}`, signal);
}

export function fetchComparison(
  productA: string,
  productB: string,
  signal?: AbortSignal,
) {
  const params = new URLSearchParams({ productA, productB });
  return getJson<Comparison>(`${BASE}/compare?${params}`, signal);
}

export function fetchSource(signal?: AbortSignal) {
  return getJson<SourceSummary>(`${BASE}/source`, signal);
}
