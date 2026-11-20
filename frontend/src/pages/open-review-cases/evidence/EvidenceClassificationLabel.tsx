import type { SourceEvidence } from "../openReviewCases";

export default function EvidenceClassificationLabel({
  classification,
  warningSuffix,
}: {
  classification: SourceEvidence["evidenceClass"];
  warningSuffix?: string;
}) {
  const className = warningSuffix
    ? "evidence-classification evidence-classification--warning"
    : `evidence-classification evidence-classification--${classification.toLowerCase()}`;

  return (
    <span className={className}>
      {classification}
      {warningSuffix}
    </span>
  );
}
