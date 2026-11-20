import { useEffect, useState } from "react";
import { fetchOpenReviewCases, type OpenReviewCase } from "./openReviewCases";
import CaseDetail from "./CaseDetail";
import CaseList from "./CaseList";
import "./OpenReviewCasesPage.css";

// Loads the open cases once, keeps the selection, and shows the loading,
// error and empty states. Case presentation lives in CaseList and CaseDetail.
export default function OpenReviewCasesPage() {
  const [cases, setCases] = useState<OpenReviewCase[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    fetchOpenReviewCases(controller.signal)
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
  }, []);

  const selectedCase = cases.find((item) => item.caseId === selectedId);

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
      {!loading && !error && cases.length === 0 && (
        <p className="empty-state">There are no NEW review cases.</p>
      )}
      {!loading && !error && cases.length > 0 && (
        <div className="case-layout">
          <CaseList
            cases={cases}
            selectedId={selectedId}
            onSelect={setSelectedId}
          />
          {selectedCase && <CaseDetail reviewCase={selectedCase} />}
        </div>
      )}
    </div>
  );
}
