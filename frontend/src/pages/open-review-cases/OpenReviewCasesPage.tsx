import { useEffect, useState } from "react";
import {
  fetchOpenReviewCases,
  type OpenReviewCase,
  type SourceEvidence,
  type SourceField,
} from "./openReviewCases";
import "./OpenReviewCasesPage.css";

function sourceValue(field: SourceField): string {
  if (field.state === "missing") return "Not present in source";
  if (field.state === "empty") return "Present but empty";
  return field.value ?? "Value unavailable";
}

function SourceCard({
  label,
  evidence,
}: {
  label: string;
  evidence: SourceEvidence;
}) {
  return (
    <section className="source-card" aria-label={`${label} source evidence`}>
      <h4>{label} source evidence</h4>
      <dl>
        <div>
          <dt>Source</dt>
          <dd>{evidence.sourceName}</dd>
        </div>
        <div>
          <dt>Release reference</dt>
          <dd>{sourceValue(evidence.releaseReference)}</dd>
        </div>
        <div>
          <dt>Release date</dt>
          <dd>{sourceValue(evidence.releaseDate)}</dd>
        </div>
        <div>
          <dt>Raw file</dt>
          <dd>{evidence.fileName ?? "Unknown"}</dd>
        </div>
        <div>
          <dt>Checksum</dt>
          <dd>{evidence.checksum ?? "Unknown"}</dd>
        </div>
        <div>
          <dt>Record locator</dt>
          <dd>{evidence.recordLocator ?? "Unknown"}</dd>
        </div>
        <div>
          <dt>Field reference</dt>
          <dd>{evidence.fieldReference ?? "Not field-specific"}</dd>
        </div>
        <div>
          <dt>Retrieved at</dt>
          <dd>{evidence.retrievedAt ?? "Not captured"}</dd>
        </div>
        <div>
          <dt>Evidence classification</dt>
          <dd>{evidence.evidenceClass}</dd>
        </div>
      </dl>
      {evidence.note && <p className="evidence-note">{evidence.note}</p>}
    </section>
  );
}

function CaseEvidence({ reviewCase }: { reviewCase: OpenReviewCase }) {
  return (
    <article className="case-evidence" aria-label={`Evidence for ${reviewCase.caseId}`}>
      <header className="case-heading">
        <div>
          <p className="eyebrow">Open review case</p>
          <h2>{reviewCase.matchedRecord.medicineDisplay}</h2>
          <p className="case-identity">
            {reviewCase.medicineIdentifier} · {reviewCase.identifierGranularity}
          </p>
        </div>
        <span className="status-badge">{reviewCase.status}</span>
      </header>

      <section className="record-card" aria-label="Simulated medication record">
        <h3>Matched simulated record</h3>
        <p>{reviewCase.matchedRecord.medicineDisplay}</p>
        <dl>
          <div>
            <dt>Record</dt>
            <dd>{reviewCase.matchedRecord.recordId}</dd>
          </div>
          <div>
            <dt>Simulated person</dt>
            <dd>{reviewCase.matchedRecord.personReference}</dd>
          </div>
          <div>
            <dt>Case created</dt>
            <dd>{reviewCase.createdAt}</dd>
          </div>
          <div>
            <dt>Evidence classification</dt>
            <dd>{reviewCase.evidenceClass}</dd>
          </div>
        </dl>
      </section>

      <section className="change-card" aria-label="Detected source-data change">
        <div className="section-heading">
          <h3>Detected source-data change</h3>
          <span>{reviewCase.change.field}</span>
        </div>
        <div className="before-after">
          <div>
            <h4>Before</h4>
            {reviewCase.change.before.map((field, index) => (
              <p key={`before-${index}`}>{sourceValue(field)}</p>
            ))}
          </div>
          <div>
            <h4>After</h4>
            {reviewCase.change.after.map((field, index) => (
              <p key={`after-${index}`}>{sourceValue(field)}</p>
            ))}
          </div>
        </div>
        <p className="classification-line">
          Source order: {reviewCase.sourceOrder.prior} → {reviewCase.sourceOrder.current} ·{" "}
          {reviewCase.sourceOrder.evidenceClass}
        </p>
        <p className="evidence-note">{reviewCase.sourceOrder.basis}</p>
      </section>

      <section className="sources" aria-label="Source evidence">
        <SourceCard label="Prior" evidence={reviewCase.sources.prior} />
        <SourceCard label="Current" evidence={reviewCase.sources.current} />
      </section>

      <p className="review-boundary">
        This case presents source information for pharmacist review only. It does not make a clinical
        decision.
      </p>
    </article>
  );
}

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
        if (reason instanceof DOMException && reason.name === "AbortError") return;
        setError(reason instanceof Error ? reason.message : "Open cases could not be loaded.");
      })
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, []);

  const selectedCase = cases.find((item) => item.caseId === selectedId);

  return (
    <main className="open-cases-page">
      <header className="page-header">
        <p className="eyebrow">Medicine Change Care Loop</p>
        <h1>Open review cases</h1>
        <p>Review source-data changes with their simulated record match and evidence.</p>
      </header>

      {loading && <p role="status">Loading open cases…</p>}
      {error && <p className="load-error" role="alert">{error}</p>}
      {!loading && !error && cases.length === 0 && (
        <p className="empty-state">There are no NEW review cases.</p>
      )}
      {!loading && !error && cases.length > 0 && (
        <div className="case-layout">
          <nav className="case-list" aria-label="Open review cases">
            <h2>Cases ({cases.length})</h2>
            {cases.map((reviewCase) => (
              <button
                className="case-list-item"
                type="button"
                key={reviewCase.caseId}
                aria-pressed={reviewCase.caseId === selectedId}
                onClick={() => setSelectedId(reviewCase.caseId)}
              >
                <span className="case-list-title">{reviewCase.matchedRecord.medicineDisplay}</span>
                <span>{reviewCase.medicineIdentifier}</span>
                <span>{reviewCase.change.field}</span>
                <span className="case-list-status">{reviewCase.status}</span>
              </button>
            ))}
          </nav>
          {selectedCase && <CaseEvidence reviewCase={selectedCase} />}
        </div>
      )}
    </main>
  );
}
