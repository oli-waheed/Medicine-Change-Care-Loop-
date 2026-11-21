import { isShortageCase, type ReviewCase } from "./openReviewCases";

export const SHORTAGE_KIND_LABELS = {
  SHORTAGE_STARTED: "Shortage started",
  SHORTAGE_CHANGED: "Shortage changed",
  SHORTAGE_ENDED: "Shortage ended",
} as const;

export function changeSummary(reviewCase: ReviewCase): string {
  if (isShortageCase(reviewCase)) {
    const change = reviewCase.shortageChange;
    const label = SHORTAGE_KIND_LABELS[change.kind];
    return change.changedColumns.length > 0
      ? `${label}: ${change.changedColumns.join(", ")}`
      : label;
  }
  const { kind, changes } = reviewCase.changeSet;
  if (kind === "NO_LONGER_PRESENT") return "No longer in the register";
  if (changes.length === 1) return changes[0].field;
  return `${changes.length} field changes`;
}

// The list and detail styling: updated, removed or shortage.
export function caseVariant(
  reviewCase: ReviewCase,
): "updated" | "removed" | "shortage" {
  if (isShortageCase(reviewCase)) return "shortage";
  return reviewCase.changeSet.kind === "NO_LONGER_PRESENT"
    ? "removed"
    : "updated";
}

export function evidenceUnavailable(reviewCase: ReviewCase): boolean {
  return reviewCase.evidenceAvailability === "UNAVAILABLE";
}
