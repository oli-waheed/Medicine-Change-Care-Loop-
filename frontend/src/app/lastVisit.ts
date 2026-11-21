// Feature 012: "What's new since your last visit", kept in this browser only.
//
// The app remembers when this browser last used it. A visit is a session: page
// changes and reloads less than 30 minutes apart belong to the same visit, so
// the "new" marks stay while you work and move on at your next visit. Nothing
// is sent to the server; another browser or a cleared browser starts fresh.

const STORAGE_KEY = "mccl:visits";
export const SESSION_GAP_MS = 30 * 60 * 1000;

type Visits = { previous: string | null; last: string };

let current: Visits | null = null;
const listeners = new Set<() => void>();

function read(): Visits | null {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<Visits>;
    if (
      typeof parsed.last !== "string" ||
      Number.isNaN(Date.parse(parsed.last))
    )
      return null;
    const previous =
      typeof parsed.previous === "string" &&
      !Number.isNaN(Date.parse(parsed.previous))
        ? parsed.previous
        : null;
    return { previous, last: parsed.last };
  } catch {
    return null; // storage blocked or unreadable: behave like a first visit
  }
}

function write(visits: Visits): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(visits));
  } catch {
    // Storage unavailable: the marks then last only while this page is open.
  }
}

/** Starts or continues the visit and returns the previous visit's time. */
export function previousVisit(now: Date = new Date()): string | null {
  if (current === null) {
    const stored = read();
    const nowIso = now.toISOString();
    if (stored === null) {
      current = { previous: null, last: nowIso };
    } else if (now.getTime() - Date.parse(stored.last) > SESSION_GAP_MS) {
      current = { previous: stored.last, last: nowIso }; // a new visit
    } else {
      current = { previous: stored.previous, last: nowIso }; // same visit
    }
    write(current);
  }
  return current.previous;
}

/** Clears the "new" marks: everything up to now counts as seen. */
export function markAllSeen(now: Date = new Date()): void {
  const nowIso = now.toISOString();
  current = { previous: nowIso, last: nowIso };
  write(current);
  listeners.forEach((listener) => listener());
}

export function subscribeToVisits(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

/** True when an ISO time is after the previous visit. */
export function isNewSince(
  previous: string | null,
  value: string | null | undefined,
): boolean {
  if (previous === null || !value) return false;
  const time = Date.parse(value);
  return !Number.isNaN(time) && time > Date.parse(previous);
}

/**
 * For Fimea's date-only columns (YYYY-MM-DD): true when the date is on or after
 * the day of the previous visit. Other formats are never marked.
 */
export function isDateOnOrAfterVisit(
  previous: string | null,
  date: string | null | undefined,
): boolean {
  if (previous === null || !date || !/^\d{4}-\d{2}-\d{2}/.test(date)) {
    return false;
  }
  return date.slice(0, 10) >= previous.slice(0, 10);
}

/** For tests: forget the visit held in memory. */
export function resetVisitForTests(): void {
  current = null;
}
