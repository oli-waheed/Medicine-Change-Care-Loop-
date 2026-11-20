import type { OpenReviewCase } from "./openReviewCases";
import { evidenceUnavailable } from "./changeSummary";
import EvidenceClassificationLabel from "./evidence/EvidenceClassificationLabel";
import TimestampDisplay from "./evidence/TimestampDisplay";
import ProvenancePanel from "./ProvenancePanel";
import RemovedPackageReview from "./RemovedPackageReview";
import UpdatedPackageReview from "./UpdatedPackageReview";

export default function CaseDetail({
  reviewCase,
}: {
  reviewCase: OpenReviewCase;
}) {
  const removed = reviewCase.changeSet.kind === "NO_LONGER_PRESENT";
  return (
    <article
      className={`case-evidence case-evidence--${removed ? "removed" : "updated"}`}
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
        <div className="case-heading-badges">
          <span
            className={`change-kind-badge change-kind-badge--${removed ? "removed" : "updated"}`}
          >
            {removed ? "Removed package" : "Updated package"}
          </span>
          <span className="status-badge">{reviewCase.status}</span>
        </div>
      </header>

      {evidenceUnavailable(reviewCase) && (
        <p className="evidence-unavailable" role="status">
          Source evidence is no longer stored. The values below reflect the case as recorded.
        </p>
      )}

      <section className="record-card" aria-label="Simulated medication record">
        <h3>Matched simulated record</h3>
        <p className="record-name">
          {reviewCase.matchedRecord.medicineDisplay}
        </p>
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
            <dd>
              <TimestampDisplay
                value={reviewCase.createdAt}
                fallback={reviewCase.createdAt}
              />
            </dd>
          </div>
          <div>
            <dt>Evidence classification</dt>
            <dd>
              <EvidenceClassificationLabel
                classification={reviewCase.evidenceClass}
                warningSuffix={
                  evidenceUnavailable(reviewCase)
                    ? " when recorded; source evidence now unavailable"
                    : undefined
                }
              />
            </dd>
          </div>
        </dl>
      </section>

      {removed ? (
        <RemovedPackageReview reviewCase={reviewCase} />
      ) : (
        <UpdatedPackageReview reviewCase={reviewCase} />
      )}

      <ProvenancePanel reviewCase={reviewCase} />

      <p className="review-boundary">
        This case presents source information for pharmacist review only. It
        does not make a clinical decision.
      </p>
    </article>
  );
}
