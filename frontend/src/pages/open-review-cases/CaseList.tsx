import { useId, useRef, useState, type KeyboardEvent } from "react";
import { STATUS_LABELS, type ReviewCase } from "./openReviewCases";
import {
  caseVariant,
  changeSummary,
  evidenceUnavailable,
} from "./changeSummary";

// Case-insensitive; every word must appear in the name, identifier or summary.
function matchesSearch(reviewCase: ReviewCase, query: string): boolean {
  const words = query.toLowerCase().split(/\s+/).filter(Boolean);
  if (words.length === 0) return true;
  const haystack = [
    reviewCase.matchedRecord.medicineDisplay,
    reviewCase.medicineIdentifier,
    changeSummary(reviewCase),
    STATUS_LABELS[reviewCase.status],
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
  includeReviewed,
  onIncludeReviewedChange,
}: {
  cases: ReviewCase[];
  selectedId: string | null;
  onSelect: (caseId: string) => void;
  includeReviewed: boolean;
  onIncludeReviewedChange: (include: boolean) => void;
}) {
  const reviewedId = useId();
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
      <div className="case-reviewed-toggle">
        <input
          id={reviewedId}
          type="checkbox"
          checked={includeReviewed}
          onChange={(event) => onIncludeReviewedChange(event.target.checked)}
        />
        <label htmlFor={reviewedId}>Show reviewed cases</label>
      </div>
      <p className="case-search-status" role="status">
        {filtering ? `Showing ${visible.length} of ${cases.length}` : ""}
      </p>

      <div className="case-queue" ref={listRef} onKeyDown={onQueueKeyDown}>
        {visible.map((reviewCase) => (
          <button
            className={`case-list-item case-list-item--${caseVariant(reviewCase)}`}
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
            <span
              className={`case-list-status case-status--${reviewCase.status.toLowerCase()}`}
            >
              {STATUS_LABELS[reviewCase.status]}
            </span>
          </button>
        ))}
        {filtering && visible.length === 0 && (
          <p className="case-search-empty">No cases match this search.</p>
        )}
      </div>
    </nav>
  );
}
