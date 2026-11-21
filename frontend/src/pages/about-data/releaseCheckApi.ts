// Feature 005: client for GET/POST /api/source-releases/latest-check.

export type CheckPhase =
  | "IDLE"
  | "DOWNLOADING"
  | "INGESTING"
  | "PREPARING_CATALOGUE"
  | "SUCCEEDED"
  | "FAILED";

export type CheckResult = {
  processingStatus: string;
  chronologyStatus: string;
  capturedReleaseReference: string | null;
  failureDetail: string | null;
  alreadyCaptured: boolean;
  releaseDate: string | null;
  reviewCasesCreated: number;
};

export type CheckStatus = {
  phase: CheckPhase;
  running: boolean;
  sourceUrl: string | null;
  startedAt: string | null;
  finishedAt: string | null;
  downloadedBytes: number | null;
  result: CheckResult | null;
  error: string | null;
  started?: boolean;
};

const URL = "/api/source-releases/latest-check";

async function read(response: Response): Promise<CheckStatus> {
  if (!response.ok) {
    throw new Error(`The backend answered HTTP ${response.status}.`);
  }
  return (await response.json()) as CheckStatus;
}

export async function startLatestReleaseCheck(): Promise<CheckStatus> {
  return read(await fetch(URL, { method: "POST" }));
}

export async function fetchLatestReleaseCheck(): Promise<CheckStatus> {
  return read(await fetch(URL));
}
