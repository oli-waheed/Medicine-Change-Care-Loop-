import {
  STATUS_LABELS,
  isShortageCase,
  type ReviewCase,
} from "./openReviewCases";
import { caseVariant, evidenceUnavailable } from "./changeSummary";
import EvidenceClassificationLabel from "./evidence/EvidenceClassificationLabel";
import TimestampDisplay from "./evidence/TimestampDisplay";
import ProvenancePanel from "./ProvenancePanel";
import RemovedPackageReview from "./RemovedPackageReview";
import ReviewPanel from "./ReviewPanel";
import { ShortageChangeReview, ShortageProvenance } from "./ShortageCaseReview";
import UpdatedPackageReview from "./UpdatedPackageReview";

const KIND_BADGES = {
  updated: "Updated package",
  removed: "Removed package",
  shortage: "Shortage",
} as const;

export default function CaseDetail({
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
  const variant = caseVariant(reviewCase);
  return (
    <article
      className={`case-evidence case-evidence--${variant}`}
      aria-label={`Evidence for ${reviewCase.caseId}`}
    >
      <header className="case-heading">
        <div>
          <p className="eyebrow">Review case</p>
          <h2>{reviewCase.matchedRecord.medicineDisplay}</h2>
          <p className="case-identity">
            {reviewCase.medicineIdentifier} · {reviewCase.identifierGranularity}
          </p>
        </div>
        <div className="case-heading-badges">
          <span className={`change-kind-badge change-kind-badge--${variant}`}>
            {KIND_BADGES[variant]}
          </span>
          <span
            className={`status-badge case-status--${reviewCase.status.toLowerCase()}`}
          >
            {STATUS_LABELS[reviewCase.status]}
          </span>
        </div>
      </header>

      {evidenceUnavailable(reviewCase) && (
        <p className="evidence-unavailable" role="status">
          Source evidence unavailable. One or more raw source files behind this
          case are no longer stored, so the values below, recorded when the case
          was created, cannot be checked against the source again.
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

      {isShortageCase(reviewCase) ? (
        <>
          <ShortageChangeReview reviewCase={reviewCase} />
          <ShortageProvenance reviewCase={reviewCase} />
        </>
      ) : (
        <>
          {variant === "removed" ? (
            <RemovedPackageReview reviewCase={reviewCase} />
          ) : (
            <UpdatedPackageReview reviewCase={reviewCase} />
          )}
          <ProvenancePanel reviewCase={reviewCase} />
        </>
      )}

      <ReviewPanel
        key={reviewCase.caseId}
        reviewCase={reviewCase}
        initials={initials}
        onInitialsChange={onInitialsChange}
        onRecorded={onRecorded}
      />

      <p className="review-boundary">
        This case presents source information for pharmacist review only. It
        does not make a clinical decision.
      </p>
    </article>
  );
}
