import { useEffect, useState } from "react";
import {
  EXPORT_CASES_URL,
  EXPORT_HISTORY_URL,
  STATUS_LABELS,
  fetchOpenReviewCases,
  isReviewed,
  type ReviewCase,
} from "./openReviewCases";
import NewSinceVisit from "../../app/NewSinceVisit";
import { isNewSince } from "../../app/lastVisit";
import { usePreviousVisit } from "../../app/useLastVisit";
import CaseDetail from "./CaseDetail";
import CaseList from "./CaseList";
import "./OpenReviewCasesPage.css";

// Loads the open cases once, keeps the selection, and shows the loading,
// error and empty states. Case presentation lives in CaseList and CaseDetail.
export default function OpenReviewCasesPage() {
  const [cases, setCases] = useState<ReviewCase[]>([]);
  const [includeReviewed, setIncludeReviewed] = useState(false);
  const [initials, setInitials] = useState("");
  const [recorded, setRecorded] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    fetchOpenReviewCases(controller.signal, includeReviewed)
      .then((result) => {
        setCases(result);
        setSelectedId((selected) =>
          result.some((item) => item.caseId === selected)
            ? selected
            : (result[0]?.caseId ?? null),
        );
      })
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === "AbortError")
          return;
        setError(
          reason instanceof Error
            ? reason.message
            : "Open cases could not be loaded.",
        );
      })
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, [includeReviewed]);

  // Feature 007: show the recorded step at once; a reviewed case leaves the
  // default list but stays findable with "Show reviewed cases".
  function onRecorded(updated: ReviewCase, label: string) {
    setRecorded(
      `Recorded for ${updated.matchedRecord.medicineDisplay}: ${label}. Status: ${STATUS_LABELS[updated.status]}.`,
    );
    const next =
      !includeReviewed && isReviewed(updated.status)
        ? cases.filter((item) => item.caseId !== updated.caseId)
        : cases.map((item) =>
            item.caseId === updated.caseId ? updated : item,
          );
    setCases(next);
    if (!next.some((item) => item.caseId === selectedId)) {
      setSelectedId(next[0]?.caseId ?? null);
    }
  }

  const selectedCase = cases.find((item) => item.caseId === selectedId);
  // Feature 012: cases created since this browser's previous visit.
  const previousVisit = usePreviousVisit();
  const newCount = cases.filter((item) =>
    isNewSince(previousVisit, item.createdAt),
  ).length;

  return (
    <div className="open-cases-page">
      <header className="page-header">
        <p className="eyebrow">Medicine Change Care Loop</p>
        <h1>Open review cases</h1>
        <p className="page-description">
          Review source-data changes with their simulated record match and
          evidence.
        </p>
        <p className="simulated-notice" role="note">
          All records shown are simulated.
        </p>
        {/* Feature 011: read-only CSV downloads of every case, open and reviewed. */}
        <p className="case-exports">
          <span>Export all cases, open and reviewed:</span>
          <a href={EXPORT_CASES_URL} download>
            Cases (CSV)
          </a>
          <a href={EXPORT_HISTORY_URL} download>
            Review history (CSV)
          </a>
        </p>
      </header>

      {loading && (
        <p className="loading-state" role="status">
          Loading open cases…
        </p>
      )}
      {error && (
        <p className="load-error" role="alert">
          {error}
        </p>
      )}
      <p className="review-recorded" role="status">
        {recorded ?? ""}
      </p>
      {!loading && !error && (
        <NewSinceVisit count={newCount} noun={["case is", "cases are"]} />
      )}
      {!loading && !error && cases.length === 0 && (
        <div className="empty-state">
          <p>
            {includeReviewed
              ? "There are no review cases."
              : "There are no open review cases."}
          </p>
          <label className="case-reviewed-toggle">
            <input
              type="checkbox"
              checked={includeReviewed}
              onChange={(event) => setIncludeReviewed(event.target.checked)}
            />
            Show reviewed cases
          </label>
        </div>
      )}
      {!loading && !error && cases.length > 0 && (
        <div className="case-layout">
          <CaseList
            cases={cases}
            selectedId={selectedId}
            onSelect={(caseId) => {
              setRecorded(null);
              setSelectedId(caseId);
            }}
            includeReviewed={includeReviewed}
            onIncludeReviewedChange={setIncludeReviewed}
          />
          {selectedCase && (
            <CaseDetail
              reviewCase={selectedCase}
              initials={initials}
              onInitialsChange={setInitials}
              onRecorded={onRecorded}
            />
          )}
        </div>
      )}
    </div>
  );
}
