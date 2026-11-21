// Feature 006: shortage API responses captured from the real backend over the
// synthetic files in tests/fixtures/fimea-shortages and the synthetic current
// release (SIM-VNR-200 and SIM-VNR-500 match packages; SIM-VNR-900 does not).
import responses from "./shortageResponses.json";

const RESPONSES = responses as Record<string, unknown>;

type FakeResponse = {
  ok: boolean;
  status: number;
  json: () => Promise<unknown>;
};

function reply(status: number, body: unknown): FakeResponse {
  return { ok: status < 400, status, json: async () => body };
}

export function shortageResponse<T>(url: string): T {
  return RESPONSES[url] as T;
}

export function shortageFetch(url: string, init?: RequestInit): FakeResponse {
  if (init?.method === "POST" && url === "/api/shortages/update") {
    return reply(202, {
      ...(RESPONSES["/api/shortages/update"] as object),
      phase: "RUNNING",
      running: true,
      trigger: "BUTTON",
      finishedAt: null,
      result: null,
      started: true,
    });
  }
  if (url in RESPONSES) return reply(200, RESPONSES[url]);
  if (url.startsWith("/api/shortages?"))
    return reply(200, RESPONSES["/api/shortages?pageSize=50"]);
  return reply(404, { detail: "Not Found" });
}
