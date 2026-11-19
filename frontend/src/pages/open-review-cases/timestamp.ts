const timestampPattern =
  /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::(\d{2})(?:\.(\d+))?)?(?:Z|[+-]\d{2}:\d{2})$/i;

function hasValidComponents(value: string): boolean {
  const components = timestampPattern.exec(value);
  if (!components) return false;

  const year = Number(components[1]);
  const month = Number(components[2]);
  const day = Number(components[3]);
  const hour = Number(components[4]);
  const minute = Number(components[5]);
  const second = Number(components[6] ?? "0");
  const fraction = components[7] ?? "";
  const leapYear = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const daysInMonth = [
    31,
    leapYear ? 29 : 28,
    31,
    30,
    31,
    30,
    31,
    31,
    30,
    31,
    30,
    31,
  ];

  if (month < 1 || month > 12 || day < 1 || day > daysInMonth[month - 1])
    return false;

  if (minute > 59 || second > 59 || hour > 24) return false;
  if (hour === 24 && (minute !== 0 || second !== 0 || /[1-9]/.test(fraction)))
    return false;

  return true;
}

export function formatTimestamp(
  value: string | null | undefined,
): string | null {
  if (!value || !hasValidComponents(value)) return null;

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;

  const year = date.getUTCFullYear().toString().padStart(4, "0");
  const month = (date.getUTCMonth() + 1).toString().padStart(2, "0");
  const day = date.getUTCDate().toString().padStart(2, "0");
  const hours = date.getUTCHours().toString().padStart(2, "0");
  const minutes = date.getUTCMinutes().toString().padStart(2, "0");

  return `${year}-${month}-${day} ${hours}:${minutes} UTC`;
}
