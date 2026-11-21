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
  // Whether the raw capture file behind this source is still stored.
  evidenceAvailable?: boolean;
};

export type ChangeKind = "FIELDS_CHANGED" | "NO_LONGER_PRESENT";

export type FieldChange = {
  changeId: string;
  field: string;
  before: SourceField[];
  after: SourceField[];
  // Feature 008: the values differ only in spaces or letter case.
  formattingOnly?: boolean;
};

// Feature 008: a label for likely source clean-ups; it never hides a value.
export type CleanupLabel = "FORMATTING_ONLY" | "ACTIVE_SUBSTANCE_ONLY";

// Feature 007: NEW is set by the system; the other three only by a reviewer.
export type CaseStatus =
  "NEW" | "IN_PROGRESS" | "REVIEWED_NO_ACTION" | "REVIEWED_FOLLOW_UP";

export type StatusEvent = {
  eventId: string;
  fromStatus: CaseStatus | null;
  toStatus: CaseStatus;
  occurredAt: string;
  reviewerInitials: string | null;
  note: string | null;
};

export type MatchedRecord = {
  recordId: string;
  personReference: string;
  medicineDisplay: string;
};

export type OpenReviewCase = {
  caseId: string;
  // Absent in cases stored before feature 007; the API adds "RELEASE".
  caseType?: "RELEASE";
  createdAt: string;
  status: CaseStatus;
  statusHistory?: StatusEvent[];
  medicineIdentifier: string;
  identifierGranularity: string;
  matchedRecord: {
    recordId: string;
    personReference: string;
    medicineDisplay: string;
  };
  changeSet: {
    changeSetId: string;
    kind: ChangeKind;
    detectedAt: string;
    changes: FieldChange[];
    cleanupLabel?: CleanupLabel | null;
    // Only for NO_LONGER_PRESENT: the package as it was in the prior release.
    lastKnownFields: { field: string; values: SourceField[] }[] | null;
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
  // UNAVAILABLE when a raw source file behind the case is no longer stored.
  evidenceAvailability?: "AVAILABLE" | "UNAVAILABLE";
  initialStatusEvent: {
    eventId: string;
    caseId: string;
    fromStatus: null;
    toStatus: "NEW";
    occurredAt: string;
  };
};

// Feature 007: a row of Fimea's shortage file as published.
export type ShortageRow = {
  line: number;
  valid: string;
  unavailableFrom: string;
  endingDate: string;
  notificationDate: string;
  updated: string;
  company: string;
};

export type ShortageSource = {
  sourceName: string;
  sourceUrl: string;
  fileName: string;
  checksum: string;
  captureReference: string;
  retrievedAt: string;
  lineNumber: number | null;
  licence: string;
  evidenceClass: "VERIFIED";
  note: string;
  evidenceAvailable?: boolean;
};

export type ShortageChangeKind =
  "SHORTAGE_STARTED" | "SHORTAGE_CHANGED" | "SHORTAGE_ENDED";

export type ShortageCase = {
  caseId: string;
  caseType: "SHORTAGE";
  createdAt: string;
  status: CaseStatus;
  statusHistory?: StatusEvent[];
  medicineIdentifier: string;
  identifierGranularity: string;
  matchedRecord: MatchedRecord;
  shortageChange: {
    changeSetId: string;
    kind: ShortageChangeKind;
    vnr: string;
    changedColumns: string[];
    before: ShortageRow | null;
    after: ShortageRow | null;
    detectedAt: string;
    package: {
      pakkaustunnus: string;
      productName: SourceField;
      strength: SourceField;
      packageSizeText: SourceField;
    };
    catalogue: { releaseId: string; releaseDate: string | null } | null;
    notice: string;
  };
  sources: { prior: ShortageSource; current: ShortageSource };
  evidenceClass: "VERIFIED";
  evidenceAvailability?: "AVAILABLE" | "UNAVAILABLE";
};

export type ReviewCase = OpenReviewCase | ShortageCase;

export function isShortageCase(item: ReviewCase): item is ShortageCase {
  return item.caseType === "SHORTAGE";
}

export const STATUS_LABELS: Record<CaseStatus, string> = {
  NEW: "New",
  IN_PROGRESS: "In progress",
  REVIEWED_NO_ACTION: "Reviewed – no action needed",
  REVIEWED_FOLLOW_UP: "Reviewed – follow-up needed",
};

export function isReviewed(status: CaseStatus): boolean {
  return status === "REVIEWED_NO_ACTION" || status === "REVIEWED_FOLLOW_UP";
}

export async function fetchOpenReviewCases(
  signal?: AbortSignal,
  includeReviewed = false,
): Promise<ReviewCase[]> {
  const url = includeReviewed
    ? "/api/open-review-cases?includeReviewed=true"
    : "/api/open-review-cases";
  const response = await fetch(url, { signal });
  if (!response.ok) {
    throw new Error(
      `Open cases could not be loaded (HTTP ${response.status}).`,
    );
  }
  return (await response.json()) as ReviewCase[];
}

export type ReviewStep = {
  expectedStatus: CaseStatus;
  toStatus: CaseStatus;
  reviewerInitials: string;
  note: string;
};

// Feature 007: the only request that changes a case. Errors carry the server's message.
export async function recordReviewStep(
  caseId: string,
  step: ReviewStep,
): Promise<ReviewCase> {
  const response = await fetch(
    `/api/review-cases/${encodeURIComponent(caseId)}/status-events`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...step, note: step.note.trim() || null }),
    },
  );
  if (!response.ok) {
    let message = `The review step could not be recorded (HTTP ${response.status}).`;
    try {
      const body = await response.json();
      if (body.detail?.message) message = body.detail.message;
    } catch {
      // keep the HTTP message
    }
    throw new Error(message);
  }
  return (await response.json()) as ReviewCase;
}

// Feature 011: read-only CSV downloads (semicolon-separated, UTF-8 with BOM).
export const EXPORT_CASES_URL = "/api/exports/review-cases.csv";
export const EXPORT_HISTORY_URL = "/api/exports/review-history.csv";
