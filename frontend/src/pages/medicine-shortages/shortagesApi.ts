// Feature 006: client for /api/shortages and /api/daily-updates.
import type { SourceField } from "../medicine-catalogue/medicineCatalogue";

export type ShortagePackage = {
  pakkaustunnus: string;
  productReference: string | null;
  productName: SourceField;
  strength: SourceField;
  pharmaceuticalForm: SourceField;
  packageSizeText: SourceField;
};

export type Shortage = {
  line: number;
  vnr: string;
  valid: string;
  unavailableFrom: string;
  endingDate: string;
  notificationDate: string;
  updated: string;
  company: string;
  /** null while the catalogue is not in memory or not available. */
  packages: ShortagePackage[] | null;
};

export type ShortagePage = {
  source: {
    sourceName: string;
    sourceUrl: string;
    captureReference: string;
    sizeBytes: number;
    recordCount: number;
    firstRetrievedAt: string;
    lastRetrievedAt: string;
    retrievalCount: number;
    latestUpdated: string | null;
    licence: string;
  };
  catalogue: {
    status: "READY" | "LOADING" | "UNAVAILABLE";
    releaseId: string | null;
    releaseDate: string | null;
  };
  validCounts: Record<string, number>;
  total: number;
  page: number;
  pageSize: number;
  items: Shortage[];
};

export type UpdateResult = {
  processingStatus: string;
  alreadyCaptured: boolean;
  captureReference: string;
  recordCount: number | null;
  failureDetail: string | null;
  downloadedBytes?: number;
};

export type UpdateStatus = {
  phase: "IDLE" | "RUNNING" | "SUCCEEDED" | "FAILED";
  running: boolean;
  trigger: string | null;
  startedAt: string | null;
  finishedAt: string | null;
  result: UpdateResult | null;
  error: string | null;
  started?: boolean;
};

export type DailyUpdates = {
  enabled: boolean;
  time: string | null;
  timeZone: string | null;
  lastRun: {
    date: string;
    trigger: string;
    startedAt: string;
    finishedAt: string | null;
    outcome: {
      shortages?: {
        phase: string;
        error: string | null;
        result: UpdateResult | null;
      };
      basicRegister?: {
        phase: string;
        error: string | null;
        result: { alreadyCaptured: boolean; releaseDate: string | null } | null;
      };
      error?: string;
    } | null;
  } | null;
};

export class ShortageError extends Error {
  readonly code: string;

  constructor(code: string, message: string) {
    super(message);
    this.code = code;
  }
}

async function getJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  if (!response.ok) {
    let code = `HTTP_${response.status}`;
    let message = `The request failed (HTTP ${response.status}).`;
    try {
      const body = await response.json();
      if (body.detail && typeof body.detail === "object") {
        code = body.detail.code ?? code;
        message = body.detail.message ?? message;
      } else if (typeof body.detail === "string") {
        message = body.detail;
      }
    } catch {
      // keep the HTTP message
    }
    throw new ShortageError(code, message);
  }
  return (await response.json()) as T;
}

export const SHORTAGE_PAGE_SIZE = 50;

export function fetchShortages(
  query: string,
  valid: string,
  page: number,
  signal?: AbortSignal,
) {
  const params = new URLSearchParams();
  if (query.trim()) params.set("q", query.trim());
  if (valid) params.set("valid", valid);
  if (page > 1) params.set("page", String(page));
  params.set("pageSize", String(SHORTAGE_PAGE_SIZE));
  return getJson<ShortagePage>(`/api/shortages?${params}`, { signal });
}

export function startShortageUpdate() {
  return getJson<UpdateStatus>("/api/shortages/update", { method: "POST" });
}

export function fetchShortageUpdate() {
  return getJson<UpdateStatus>("/api/shortages/update");
}

export function fetchDailyUpdates(signal?: AbortSignal) {
  return getJson<DailyUpdates>("/api/daily-updates", { signal });
}
