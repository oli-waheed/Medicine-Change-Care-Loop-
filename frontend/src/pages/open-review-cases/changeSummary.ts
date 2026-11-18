import type { OpenReviewCase } from "./openReviewCases";

export function changeSummary(reviewCase: OpenReviewCase): string {
  const { kind, changes } = reviewCase.changeSet;
  if (kind === "NO_LONGER_PRESENT") return "No longer in the register";
  if (changes.length === 1) return changes[0].field;
  return `${changes.length} field changes`;
}

export function evidenceUnavailable(reviewCase: OpenReviewCase): boolean {
  return reviewCase.evidenceAvailability === "UNAVAILABLE";
}
