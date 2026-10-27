export type SourceField = {
  state: "missing" | "empty" | "value";
  value: string | null;
  attributes: Record<string, string>;
};

export type SourceEvidence = {
  sourceName: string;
  releaseDate: SourceField;
  releaseReference: SourceField;
  fileName: string | null;
  checksum: string | null;
  recordIdentifier: string;
  recordLocator: string | null;
  fieldReference: string | null;
  evidenceClass: "VERIFIED" | "INFERRED" | "UNKNOWN" | "CONFLICTING";
  note: string | null;
  retrievedAt: string | null;
};

export type OpenReviewCase = {
  caseId: string;
  createdAt: string;
  status: "NEW";
  medicineIdentifier: string;
  identifierGranularity: string;
  matchedRecord: {
    recordId: string;
    personReference: string;
    medicineDisplay: string;
  };
  change: {
    changeId: string;
    field: string;
    before: SourceField[];
    after: SourceField[];
    detectedAt: string;
  };
  sources: {
    prior: SourceEvidence;
    current: SourceEvidence;
  };
  sourceOrder: {
    prior: number;
    current: number;
    basis: string;
    evidenceClass: "VERIFIED" | "INFERRED" | "UNKNOWN" | "CONFLICTING";
  };
  evidenceClass: "VERIFIED" | "INFERRED" | "UNKNOWN" | "CONFLICTING";
  initialStatusEvent: {
    eventId: string;
    caseId: string;
    fromStatus: null;
    toStatus: "NEW";
    occurredAt: string;
  };
};

export async function fetchOpenReviewCases(
  signal?: AbortSignal,
): Promise<OpenReviewCase[]> {
  const response = await fetch("/api/open-review-cases", { signal });
  if (!response.ok) {
    throw new Error(`Open cases could not be loaded (HTTP ${response.status}).`);
  }
  return (await response.json()) as OpenReviewCase[];
}
