import { markAllSeen } from "./lastVisit";
import { usePreviousVisit } from "./useLastVisit";
import "./NewSinceVisit.css";

function shortTime(iso: string): string {
  return `${iso.slice(0, 10)} ${iso.slice(11, 16)} UTC`;
}

// Feature 012: the line that says how much is new since the last visit.
export default function NewSinceVisit({
  count,
  noun,
}: {
  count: number;
  noun: [singular: string, plural: string];
}) {
  const previous = usePreviousVisit();
  if (previous === null) return null;
  return (
    <p className="new-since-visit" role="status">
      <span>
        {count === 0
          ? `Nothing new here since your last visit (${shortTime(previous)}).`
          : `${count} ${count === 1 ? noun[0] : noun[1]} new since your last visit (${shortTime(previous)}).`}
      </span>
      {count > 0 && (
        <button type="button" onClick={() => markAllSeen()}>
          Mark all as seen
        </button>
      )}
    </p>
  );
}

export function NewBadge({
  label = "New since last visit",
}: {
  label?: string;
}) {
  return <span className="new-badge">{label}</span>;
}
