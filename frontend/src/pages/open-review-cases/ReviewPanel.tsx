import { useId, useState } from "react";
import { formatTimestamp } from "./timestamp";
import {
  STATUS_LABELS,
  isReviewed,
  recordReviewStep,
  type CaseStatus,
  type ReviewCase,
} from "./openReviewCases";

// Feature 007 FR-002: the steps a reviewer can take from each status.
const ACTIONS: Record<CaseStatus, { to: CaseStatus; label: string }[]> = {
  NEW: [
    { to: "IN_PROGRESS", label: "Mark in progress" },
    { to: "REVIEWED_NO_ACTION", label: "Reviewed – no action needed" },
    { to: "REVIEWED_FOLLOW_UP", label: "Reviewed – follow-up needed" },
  ],
  IN_PROGRESS: [
    { to: "REVIEWED_NO_ACTION", label: "Reviewed – no action needed" },
    { to: "REVIEWED_FOLLOW_UP", label: "Reviewed – follow-up needed" },
  ],
  REVIEWED_NO_ACTION: [{ to: "IN_PROGRESS", label: "Reopen" }],
  REVIEWED_FOLLOW_UP: [{ to: "IN_PROGRESS", label: "Reopen" }],
};

function History({ reviewCase }: { reviewCase: ReviewCase }) {
  const events = reviewCase.statusHistory ?? [];
  if (events.length === 0) return null;
  return (
    <ol className="review-history" aria-label="Review history">
      {events.map((event) => (
        <li key={event.eventId}>
          <span className="review-history-time">
            {formatTimestamp(event.occurredAt) ?? event.occurredAt}
          </span>
          <span className="review-history-step">
            {event.fromStatus === null
              ? `Case created: ${STATUS_LABELS[event.toStatus]}`
              : `${STATUS_LABELS[event.fromStatus]} → ${STATUS_LABELS[event.toStatus]}`}
          </span>
          {event.reviewerInitials && (
            <span className="review-history-who">
              by {event.reviewerInitials}
            </span>
          )}
          {event.note && <p className="review-history-note">{event.note}</p>}
        </li>
      ))}
    </ol>
  );
}

export default function ReviewPanel({
  reviewCase,
  initials,
  onInitialsChange,
  onRecorded,
}: {
  reviewCase: ReviewCase;
  initials: string;
  onInitialsChange: (value: string) => void;
  onRecorded: (updated: ReviewCase, label: string) => void;
}) {
  const id = useId();
  const [note, setNote] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const status = reviewCase.status;
  const noteNeeded = isReviewed(status);

  async function record(to: CaseStatus, label: string) {
    setPending(true);
    setError(null);
    try {
      const updated = await recordReviewStep(reviewCase.caseId, {
        expectedStatus: status,
        toStatus: to,
        reviewerInitials: initials.trim(),
        note,
      });
      setNote("");
      onRecorded(updated, label);
    } catch (reason) {
      setError((reason as Error).message);
    } finally {
      setPending(false);
    }
  }

  return (
    <section className="case-review" aria-labelledby={`${id}-heading`}>
      <div className="case-review-heading">
        <h3 id={`${id}-heading`}>Review</h3>
        <span className={`status-badge case-status--${status.toLowerCase()}`}>
          {STATUS_LABELS[status]}
        </span>
      </div>
      <p className="case-review-help">
        Record what you did with this case. Each step is kept in the history
        with your initials; nothing here is changed automatically.
      </p>
      <div className="review-fields">
        <div className="review-field review-field--initials">
          <label htmlFor={`${id}-initials`}>Your initials</label>
          <input
            id={`${id}-initials`}
            type="text"
            value={initials}
            maxLength={10}
            autoComplete="off"
            spellCheck={false}
            onChange={(event) => onInitialsChange(event.target.value)}
          />
        </div>
        <div className="review-field">
          <label htmlFor={`${id}-note`}>Note</label>
          <textarea
            id={`${id}-note`}
            value={note}
            maxLength={1000}
            rows={3}
            aria-describedby={`${id}-note-help`}
            onChange={(event) => setNote(event.target.value)}
          />
          <p id={`${id}-note-help`} className="review-field-help">
            {noteNeeded
              ? "Required to reopen a reviewed case."
              : "Required for a reviewed outcome; optional for in progress."}
          </p>
        </div>
      </div>
      <div className="review-actions">
        {ACTIONS[status].map((action) => (
          <button
            key={action.to}
            type="button"
            className={`review-action review-action--${action.to.toLowerCase()}`}
            disabled={pending}
            onClick={() => record(action.to, action.label)}
          >
            {action.label}
          </button>
        ))}
      </div>
      {error && (
        <p className="review-error" role="alert">
          {error}
        </p>
      )}
      <h4 className="review-history-heading">History</h4>
      <History reviewCase={reviewCase} />
    </section>
  );
}
