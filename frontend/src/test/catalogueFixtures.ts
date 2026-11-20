// Feature 004: catalogue API responses captured from the real backend over the
// synthetic varied release used by tests/integration/medicine-catalogue
// (missing VNR on SIM-PKG-400, SIM-PKG-200/500 sharing a VNR, two substances
// on SYN-PROD-100). Only synthetic fixtures; no Fimea data.
import responses from "./catalogueResponses.json";

const RESPONSES = responses as Record<string, unknown>;
const LISTING = "/api/medicine-catalogue";

type FakeResponse = {
  ok: boolean;
  status: number;
  json: () => Promise<unknown>;
};

function reply(status: number, body: unknown): FakeResponse {
  return { ok: status < 400, status, json: async () => body };
}

export function catalogueResponse<T>(url: string): T {
  return RESPONSES[url] as T;
}

// Answers like the backend for the captured URLs; any other listing query gets
// the full listing so tests can assert on the query string that was sent.
export function catalogueFetch(url: string): FakeResponse {
  if (url in RESPONSES) return reply(200, RESPONSES[url]);
  if (url.startsWith(`${LISTING}?`)) return reply(200, RESPONSES[LISTING]);
  if (url.startsWith(`${LISTING}/active-substances`))
    return reply(200, RESPONSES[`${LISTING}/active-substances`]);
  if (url.startsWith(`${LISTING}/products/`))
    return reply(404, { detail: { code: "PRODUCT_NOT_FOUND" } });
  if (url.startsWith(`${LISTING}/packages/`))
    return reply(404, { detail: { code: "PACKAGE_NOT_FOUND" } });
  return reply(404, { detail: "Not Found" });
}

export function unavailableFetch(): FakeResponse {
  return reply(503, {
    detail: {
      code: "CATALOGUE_UNAVAILABLE",
      message:
        "No validated source release with verified chronology is available.",
    },
  });
}
