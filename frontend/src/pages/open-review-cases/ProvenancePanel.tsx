import type { OpenReviewCase, SourceEvidence } from "./openReviewCases";
import EvidenceClassificationLabel from "./evidence/EvidenceClassificationLabel";
import { SourceValueDisplay } from "./evidence/SourceValueDisplay";
import TimestampDisplay from "./evidence/TimestampDisplay";

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
    <section
      className={`source-card source-card--${label.toLowerCase()}`}
      aria-label={`${label} source evidence`}
    >
      <h4>{label} source evidence</h4>
      <dl>
        <div>
          <dt>Source</dt>
          <dd>{evidence.sourceName}</dd>
        </div>
        <div>
          <dt>Release reference</dt>
          <dd>
            <SourceValueDisplay field={evidence.releaseReference} />
          </dd>
        </div>
        <div>
          <dt>Release date</dt>
          <dd>
            <SourceValueDisplay field={evidence.releaseDate} />
          </dd>
        </div>
        <div>
          <dt>Raw file</dt>
          <dd className="monospace-value">
            {evidence.fileName ?? "Unknown"}
            {evidence.evidenceAvailable === false && (
              <span className="evidence-missing"> (no longer stored)</span>
            )}
          </dd>
        </div>
        <div>
          <dt>Checksum</dt>
          <dd className="monospace-value">{evidence.checksum ?? "Unknown"}</dd>
        </div>
        <div>
          <dt>Record locator</dt>
          <dd className="monospace-value">
            {evidence.recordLocator ??
              (recordAbsent ? "Not in this release" : "Unknown")}
          </dd>
        </div>
        <div>
          <dt>Retrieved at</dt>
          <dd>
            <TimestampDisplay
              value={evidence.retrievedAt}
              fallback="Not captured"
            />
          </dd>
        </div>
        <div>
          <dt>Evidence classification</dt>
          <dd>
            <EvidenceClassificationLabel
              classification={evidence.evidenceClass}
              warningSuffix={
                evidence.evidenceAvailable === false
                  ? " when recorded; source file now unavailable"
                  : undefined
              }
            />
          </dd>
        </div>
      </dl>
      {evidence.note && <p className="evidence-note">{evidence.note}</p>}
    </section>
  );
}

export function SourceOrder({ reviewCase }: { reviewCase: OpenReviewCase }) {
  return (
    <div className="source-order">
      <p className="classification-line">
        Source order: {reviewCase.sourceOrder.prior} →{" "}
        {reviewCase.sourceOrder.current} ·{" "}
        <EvidenceClassificationLabel
          classification={reviewCase.sourceOrder.evidenceClass}
        />
      </p>
      <p className="evidence-note">{reviewCase.sourceOrder.basis}</p>
    </div>
  );
}

export default function ProvenancePanel({
  reviewCase,
}: {
  reviewCase: OpenReviewCase;
}) {
  return (
    <section className="sources" aria-label="Source evidence">
      <SourceCard label="Prior" evidence={reviewCase.sources.prior} />
      <SourceCard
        label="Current"
        evidence={reviewCase.sources.current}
        recordAbsent={reviewCase.changeSet.kind === "NO_LONGER_PRESENT"}
      />
    </section>
  );
}
