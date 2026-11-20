// The Vite scaffold placeholder is not a real release version, so it is hidden.
const PLACEHOLDER_VERSION = "0.0.0";

export function displayableVersion(version: string | undefined): string | null {
  const trimmed = version?.trim();
  if (!trimmed || trimmed === PLACEHOLDER_VERSION) return null;
  return trimmed;
}

export const appVersion = displayableVersion(__APP_VERSION__);
