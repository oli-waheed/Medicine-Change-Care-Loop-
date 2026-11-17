import type { SourceField } from "./openReviewCases";

// Fimea code-table (CT) elements carry their meaning in attributes:
// listname (code list), id (code) and value (display text). The element text is
// usually empty, so the attributes must be shown or the change is invisible.
export function codeTableValue(
  attributes: Record<string, string>,
): string | null {
  const { value, id, listname, ...other } = attributes;
  const details = [
    id !== undefined && value !== undefined ? `code ${id}` : null,
    listname !== undefined ? `list ${listname}` : null,
    ...Object.entries(other).map(([name, attribute]) => `${name} ${attribute}`),
  ].filter((part): part is string => part !== null);
  const label = value ?? id;
  if (label === undefined) return details.length ? details.join(", ") : null;
  return details.length ? `${label} (${details.join(", ")})` : label;
}

export function sourceValue(field: SourceField): string {
  if (field.state === "missing") return "Not present in source";
  const code = codeTableValue(field.attributes);
  if (field.state === "empty") return code ?? "Present but empty";
  const text = field.value ?? "Value unavailable";
  return code ? `${text} — ${code}` : text;
}
