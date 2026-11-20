import { useId, useRef, useState, type KeyboardEvent } from "react";
import type { OpenReviewCase } from "./openReviewCases";
import { changeSummary, evidenceUnavailable } from "./changeSummary";

// Case-insensitive; every word must appear in the name, identifier or summary.
export function matchesSearch(
  reviewCase: OpenReviewCase,
  query: string,
): boolean {
  const words = query.toLowerCase().split(/\s+/).filter(Boolean);
  if (words.length === 0) return true;
  const haystack = [
    reviewCase.matchedRecord.medicineDisplay,
    reviewCase.medicineIdentifier,
    changeSummary(reviewCase),
  ]
    .join(" ")
    .toLowerCase();
  return words.every((word) => haystack.includes(word));
}

const QUEUE_KEYS = new Set(["ArrowDown", "ArrowUp", "Home", "End"]);

export default function CaseList({
  cases,
  selectedId,
  onSelect,
}: {
  cases: OpenReviewCase[];
  selectedId: string | null;
  onSelect: (caseId: string) => void;
}) {
  const [query, setQuery] = useState("");
  const searchId = useId();
  const listRef = useRef<HTMLDivElement>(null);
  const visible = cases.filter((reviewCase) =>
    matchesSearch(reviewCase, query),
  );
  const filtering = query.trim() !== "";

  // Arrow keys, Home and End move focus through the queue; Enter or Space
  // selects the focused case.
  function onQueueKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (!QUEUE_KEYS.has(event.key)) return;
    const buttons = Array.from(
      listRef.current?.querySelectorAll<HTMLButtonElement>("button") ?? [],
    );
    const index = buttons.indexOf(document.activeElement as HTMLButtonElement);
    if (index === -1 || buttons.length === 0) return;
    event.preventDefault();
    const next =
      event.key === "Home"
        ? 0
        : event.key === "End"
          ? buttons.length - 1
          : event.key === "ArrowDown"
            ? Math.min(index + 1, buttons.length - 1)
            : Math.max(index - 1, 0);
    buttons[next].focus();
  }

  return (
    <nav className="case-list" aria-label="Open review cases">
      <h2>Cases ({cases.length})</h2>

      <div className="case-search">
        <label className="case-search-label" htmlFor={searchId}>
          Search cases
        </label>
        <input
          id={searchId}
          className="case-search-input"
          type="search"
          value={query}
          autoComplete="off"
          spellCheck={false}
          placeholder="Name, identifier or change"
          onChange={(event) => setQuery(event.target.value)}
        />
      </div>
      <p className="case-search-status" role="status">
        {filtering ? `Showing ${visible.length} of ${cases.length}` : ""}
      </p>

      <div className="case-queue" ref={listRef} onKeyDown={onQueueKeyDown}>
        {visible.map((reviewCase) => (
          <button
            className={`case-list-item case-list-item--${
              reviewCase.changeSet.kind === "NO_LONGER_PRESENT"
                ? "removed"
                : "updated"
            }`}
            type="button"
            key={reviewCase.caseId}
            aria-pressed={reviewCase.caseId === selectedId}
            onClick={() => onSelect(reviewCase.caseId)}
          >
            <span className="case-list-title">
              {reviewCase.matchedRecord.medicineDisplay}
            </span>
            <span className="case-list-id">
              {reviewCase.medicineIdentifier}
            </span>
            <span className="case-list-summary">
              {changeSummary(reviewCase)}
            </span>
            {evidenceUnavailable(reviewCase) && (
              <span className="case-list-warning">Evidence unavailable</span>
            )}
            <span className="case-list-status">{reviewCase.status}</span>
          </button>
        ))}
        {filtering && visible.length === 0 && (
          <p className="case-search-empty">No cases match this search.</p>
        )}
      </div>
    </nav>
  );
}
