import type { FieldChange, OpenReviewCase } from "./openReviewCases";
import { CHANGE_INDICATOR_LABELS, changeIndicator } from "./changeIndicator";
import FieldPath from "./evidence/FieldPath";
import { SourceValueParagraphs } from "./evidence/SourceValueDisplay";
import { SourceOrder } from "./ProvenancePanel";

function FieldChangeRow({ change }: { change: FieldChange }) {
  const indicator = changeIndicator(change);
  return (
    <li className={`field-change field-change--${indicator}`}>
      <div className="field-change-heading">
        <p className="field-path">
          <FieldPath path={change.field} />
        </p>
        <span className={`change-indicator change-indicator--${indicator}`}>
          {CHANGE_INDICATOR_LABELS[indicator]}
        </span>
        {change.formattingOnly && (
          <span className="formatting-only">Spacing or letter case only</span>
        )}
      </div>
      <div className="before-after">
        <div className="before-after-side before-after-side--before">
          <h4>
            <span className="before-after-label">Before</span>{" "}
            <span className="before-after-release">Prior release</span>
          </h4>
          <SourceValueParagraphs
            fields={change.before}
            keyPrefix={`${change.changeId}-before`}
          />
        </div>
        <span className="before-after-arrow" aria-hidden="true">
          →
        </span>
        <div className="before-after-side before-after-side--after">
          <h4>
            <span className="before-after-label">After</span>{" "}
            <span className="before-after-release">Current release</span>
          </h4>
          <SourceValueParagraphs
            fields={change.after}
            keyPrefix={`${change.changeId}-after`}
          />
        </div>
      </div>
    </li>
  );
}

// FIELDS_CHANGED: the package is still in the register with changed fields.
export default function UpdatedPackageReview({
  reviewCase,
}: {
  reviewCase: OpenReviewCase;
}) {
  const { changes } = reviewCase.changeSet;
  return (
    <section
      className="change-card review-panel review-panel--updated"
      aria-label="Detected source-data change"
    >
      <div className="section-heading">
        <h3>Detected source-data changes</h3>
        <span className="field-count">
          {changes.length} {changes.length === 1 ? "field" : "fields"}
        </span>
      </div>
      <ul className="field-changes">
        {changes.map((change) => (
          <FieldChangeRow key={change.changeId} change={change} />
        ))}
      </ul>
      <SourceOrder reviewCase={reviewCase} />
    </section>
  );
}
