import { useEffect, useState } from "react";
import {
  fetchOpenReviewCases,
  type FieldChange,
  type OpenReviewCase,
  type SourceEvidence,
} from "./openReviewCases";
import { changeSummary } from "./changeSummary";
import { sourceValue } from "./sourceValue";
import "./OpenReviewCasesPage.css";

function SourceCard({
  label,
  evidence,
  recordAbsent = false,
}: {
  label: string;
  evidence: SourceEvidence;
  recordAbsent?: boolean;
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
          <dd>
            {evidence.recordLocator ??
              (recordAbsent ? "Not in this release" : "Unknown")}
          </dd>
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

function FieldChangeRow({ change }: { change: FieldChange }) {
  return (
    <li className="field-change">
      <p className="field-path">{change.field}</p>
      <div className="before-after">
        <div>
          <h4>Before</h4>
          {change.before.map((field, index) => (
            <p key={`before-${index}`}>{sourceValue(field)}</p>
          ))}
        </div>
        <div>
          <h4>After</h4>
          {change.after.map((field, index) => (
            <p key={`after-${index}`}>{sourceValue(field)}</p>
          ))}
        </div>
      </div>
    </li>
  );
}

function ChangeSetEvidence({ reviewCase }: { reviewCase: OpenReviewCase }) {
  const { changeSet } = reviewCase;
  if (changeSet.kind === "NO_LONGER_PRESENT") {
    return (
      <>
        <div className="section-heading">
          <h3>Package no longer present in the register</h3>
        </div>
        <p className="removal-notice">
          The prior release contained this package. The current release, which
          covers the whole register, does not. The source does not state why.
        </p>
        <h4>Last known values (prior release)</h4>
        <dl className="last-known">
          {(changeSet.lastKnownFields ?? []).map((item) => (
            <div key={item.field}>
              <dt>{item.field}</dt>
              <dd>
                {item.values.length === 0
                  ? "No occurrences"
                  : item.values.map(sourceValue).join("; ")}
              </dd>
            </div>
          ))}
        </dl>
      </>
    );
  }
  return (
    <>
      <div className="section-heading">
        <h3>Detected source-data changes</h3>
        <span>
          {changeSet.changes.length}{" "}
          {changeSet.changes.length === 1 ? "field" : "fields"}
        </span>
      </div>
      <ul className="field-changes">
        {changeSet.changes.map((change) => (
          <FieldChangeRow key={change.changeId} change={change} />
        ))}
      </ul>
    </>
  );
}

function CaseEvidence({ reviewCase }: { reviewCase: OpenReviewCase }) {
  return (
    <article
      className="case-evidence"
      aria-label={`Evidence for ${reviewCase.caseId}`}
    >
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
        <ChangeSetEvidence reviewCase={reviewCase} />
        <p className="classification-line">
          Source order: {reviewCase.sourceOrder.prior} →{" "}
          {reviewCase.sourceOrder.current} ·{" "}
          {reviewCase.sourceOrder.evidenceClass}
        </p>
        <p className="evidence-note">{reviewCase.sourceOrder.basis}</p>
      </section>

      <section className="sources" aria-label="Source evidence">
        <SourceCard label="Prior" evidence={reviewCase.sources.prior} />
        <SourceCard
          label="Current"
          evidence={reviewCase.sources.current}
          recordAbsent={reviewCase.changeSet.kind === "NO_LONGER_PRESENT"}
        />
      </section>

      <p className="review-boundary">
        This case presents source information for pharmacist review only. It
        does not make a clinical decision.
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
    <main className="open-cases-page">
      <header className="page-header">
        <p className="eyebrow">Medicine Change Care Loop</p>
        <h1>Open review cases</h1>
        <p>
          Review source-data changes with their simulated record match and
          evidence.
        </p>
      </header>

      {loading && <p role="status">Loading open cases…</p>}
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
                <span className="case-list-title">
                  {reviewCase.matchedRecord.medicineDisplay}
                </span>
                <span>{reviewCase.medicineIdentifier}</span>
                <span>{changeSummary(reviewCase)}</span>
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
