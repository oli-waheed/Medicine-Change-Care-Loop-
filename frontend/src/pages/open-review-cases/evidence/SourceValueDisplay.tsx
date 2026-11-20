import type { SourceField } from "../openReviewCases";
import { sourceValue } from "../sourceValue";

type ValueState = "missing" | "empty" | "value-unavailable" | "value";

function valueState(field: SourceField, text: string): ValueState {
  if (field.state === "missing") return "missing";
  if (field.state === "empty" && text === "Present but empty") return "empty";
  // Present in the source, but no value was delivered for it.
  if (field.state === "value" && field.value === null)
    return "value-unavailable";
  return "value";
}

export function SourceValueDisplay({ field }: { field: SourceField }) {
  const text = sourceValue(field);
  return (
    <span className={`source-value source-value--${valueState(field, text)}`}>
      {text}
    </span>
  );
}

// Zero occurrences of a repeated source element.
export function NoOccurrences() {
  return (
    <span className="source-value source-value--no-occurrences">
      No occurrences
    </span>
  );
}

// Inline list of values, for last-known values: "a; b; c".
export function SourceValueInline({
  fields,
  keyPrefix,
}: {
  fields: SourceField[];
  keyPrefix: string;
}) {
  if (fields.length === 0) return <NoOccurrences />;
  return (
    <>
      {fields.map((field, index) => (
        <span key={`${keyPrefix}-${index}`}>
          {index > 0 && "; "}
          <SourceValueDisplay field={field} />
        </span>
      ))}
    </>
  );
}

// One paragraph per value, for the before and after sides of a change.
export function SourceValueParagraphs({
  fields,
  keyPrefix,
}: {
  fields: SourceField[];
  keyPrefix: string;
}) {
  if (fields.length === 0)
    return (
      <p>
        <NoOccurrences />
      </p>
    );
  return (
    <>
      {fields.map((field, index) => (
        <p key={`${keyPrefix}-${index}`}>
          <SourceValueDisplay field={field} />
        </p>
      ))}
    </>
  );
}
