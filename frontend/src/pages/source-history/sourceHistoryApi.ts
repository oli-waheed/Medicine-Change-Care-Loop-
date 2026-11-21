// Feature 010: client for GET /api/source-history (read-only).

export type CheckStatus = "PASSED" | "ATTENTION" | "INFO";

export type QualityCheck = {
  checkId: string;
  priorReleaseId: string;
  currentReleaseId: string;
  priorReleaseDate: string | null;
  currentReleaseDate: string | null;
  checkedAt: string;
  overall: "PASSED" | "ATTENTION";
  counts: {
    priorPackages: number;
    currentPackages: number;
    inBoth: number;
    changed: number;
    noLongerPresent: number;
    new: number;
    vnrGained: number;
    vnrLost: number;
    vnrChanged: number;
    formattingOnly: number;
    activeSubstanceOnly: number;
    unlabelled: number;
    sharedVnrs: number;
  };
  checks: { id: string; label: string; status: CheckStatus; detail: string }[];
  // Feature 014: share of packages (%) with each tracked field.
  completeness?: { field: string; prior: number; current: number }[];
  version?: number;
  upToDate?: boolean;
};

export type StoredRelease = {
  releaseId: string;
  releaseDate: string | null;
  dateEvidence: string;
  processingStatus: string;
  failureDetail: string | null;
  fileName: string | null;
  checksum: string | null;
  sizeBytes: number | null;
  evidenceAvailable: boolean;
  firstRetrievedAt: string;
  lastRetrievedAt: string;
  retrievalCount: number;
  isCatalogueRelease: boolean;
};

export type StoredShortageFile = {
  checksum: string;
  processingStatus: string;
  failureDetail: string | null;
  recordCount: number | null;
  sizeBytes: number;
  evidenceAvailable: boolean;
  firstRetrievedAt: string;
  lastRetrievedAt: string;
  retrievalCount: number;
  isActive: boolean;
};

export type SourceHistory = {
  basicRegister: StoredRelease[];
  qualityChecks: QualityCheck[];
  uncheckedPairs: {
    priorReleaseDate: string | null;
    currentReleaseDate: string | null;
  }[];
  shortageFiles: StoredShortageFile[];
};

export async function fetchSourceHistory(
  signal?: AbortSignal,
): Promise<SourceHistory> {
  const response = await fetch("/api/source-history", { signal });
  if (!response.ok) {
    throw new Error(
      `Source history could not be loaded (HTTP ${response.status}).`,
    );
  }
  return (await response.json()) as SourceHistory;
}
