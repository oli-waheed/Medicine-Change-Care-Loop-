import type { FieldChange, SourceField } from "./openReviewCases";

// Describes source-data presence only; it carries no clinical meaning.
export type ChangeIndicator = "added" | "removed" | "changed";

export const CHANGE_INDICATOR_LABELS: Record<ChangeIndicator, string> = {
  added: "Field added",
  removed: "Field removed",
  changed: "Value changed",
};

// A field is present when at least one occurrence exists in the source, even
// if it is empty. Missing elements and zero occurrences count as absent.
function present(fields: SourceField[]): boolean {
  return fields.some((field) => field.state !== "missing");
}

export function changeIndicator(change: FieldChange): ChangeIndicator {
  const before = present(change.before);
  const after = present(change.after);
  if (!before && after) return "added";
  if (before && !after) return "removed";
  return "changed";
}
