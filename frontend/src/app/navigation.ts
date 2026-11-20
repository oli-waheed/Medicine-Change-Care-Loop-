import { useSyncExternalStore, type MouseEvent } from "react";

export type PageId =
  "open-review-cases" | "medicine-catalogue" | "about-data" | "not-found";

export type NavigationItem = {
  page: Exclude<PageId, "not-found">;
  path: string;
  label: string;
};

// The only pages in the sidebar. Do not add items without a working page.
export const NAVIGATION_ITEMS: readonly NavigationItem[] = [
  { page: "open-review-cases", path: "/", label: "Open Review Cases" },
  // Feature 004 (supersedes 003 FR-001/FR-002 in part).
  {
    page: "medicine-catalogue",
    path: "/medicine-catalogue",
    label: "Medicine Catalogue",
  },
  { page: "about-data", path: "/about-data", label: "About the Data" },
];

export const PAGE_TITLES: Record<PageId, string> = {
  "open-review-cases": "Open Review Cases",
  "medicine-catalogue": "Medicine Catalogue",
  "about-data": "About the Data",
  "not-found": "Page not found",
};

export const PRODUCT_NAME = "Medicine Change Care Loop";

export function normalisePath(pathname: string): string {
  const trimmed = pathname.replace(/\/+$/, "");
  return trimmed === "" ? "/" : trimmed;
}

export function pageForPath(pathname: string): PageId {
  const path = normalisePath(pathname);
  return (
    NAVIGATION_ITEMS.find((item) => item.path === path)?.page ?? "not-found"
  );
}

export function documentTitle(page: PageId): string {
  return `${PAGE_TITLES[page]} | ${PRODUCT_NAME}`;
}

const NAVIGATE_EVENT = "mccl:navigate";

function subscribe(onChange: () => void): () => void {
  window.addEventListener("popstate", onChange);
  window.addEventListener(NAVIGATE_EVENT, onChange);
  return () => {
    window.removeEventListener("popstate", onChange);
    window.removeEventListener(NAVIGATE_EVENT, onChange);
  };
}

function currentPath(): string {
  return normalisePath(window.location.pathname);
}

export function useCurrentPath(): string {
  return useSyncExternalStore(subscribe, currentPath, () => "/");
}

export function navigate(path: string): void {
  if (normalisePath(path) === currentPath()) return;
  window.history.pushState(null, "", path);
  window.dispatchEvent(new Event(NAVIGATE_EVENT));
}

// Keeps native behaviour for new-tab, modified and non-primary clicks.
export function handleLinkClick(
  event: MouseEvent<HTMLAnchorElement>,
  path: string,
  afterNavigate?: () => void,
): void {
  if (
    event.defaultPrevented ||
    event.button !== 0 ||
    event.metaKey ||
    event.ctrlKey ||
    event.shiftKey ||
    event.altKey
  ) {
    return;
  }
  event.preventDefault();
  navigate(path);
  afterNavigate?.();
}
