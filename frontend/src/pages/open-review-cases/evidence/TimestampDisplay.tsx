import { formatTimestamp } from "../timestamp";

export default function TimestampDisplay({
  value,
  fallback,
}: {
  value: string | null;
  fallback: string;
}) {
  if (value === null)
    return <span className="timestamp-fallback">{fallback}</span>;

  const formatted = formatTimestamp(value);
  if (formatted === null) {
    return <span className="timestamp-fallback">{value}</span>;
  }

  return (
    <span className="timestamp-display">
      <time dateTime={value}>{formatted}</time>
      <small className="timestamp-exact">{value}</small>
    </span>
  );
}
