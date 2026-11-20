import type { OpenReviewCase } from "./openReviewCases";
import FieldPath from "./evidence/FieldPath";
import { SourceValueInline } from "./evidence/SourceValueDisplay";
import { SourceOrder } from "./ProvenancePanel";

// NO_LONGER_PRESENT: the package was in the prior release but not the current one.
export default function RemovedPackageReview({
  reviewCase,
}: {
  reviewCase: OpenReviewCase;
}) {
  const fields = reviewCase.changeSet.lastKnownFields ?? [];
  return (
    <section
      className="change-card review-panel review-panel--removed"
      aria-label="Detected source-data change"
    >
      <div className="removal-banner">
        <h3>Package no longer present in the register</h3>
        <p className="removal-notice">
          The prior release contained this package. The current release, which
          covers the whole register, does not. The source does not state why.
        </p>
      </div>
      <h4 className="last-known-heading">Last known values (prior release)</h4>
      <dl className="last-known">
        {fields.map((item) => (
          <div key={item.field}>
            <dt>
              <FieldPath path={item.field} />
            </dt>
            <dd>
              <SourceValueInline fields={item.values} keyPrefix={item.field} />
            </dd>
          </div>
        ))}
      </dl>
      <SourceOrder reviewCase={reviewCase} />
    </section>
  );
}
