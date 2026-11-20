import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";

const DESKTOP_QUERY = "(min-width: 1024px)";
const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]), [tabindex]:not([tabindex="-1"])';

function focusableIn(container: HTMLElement | null): HTMLElement[] {
  return container
    ? Array.from(container.querySelectorAll<HTMLElement>(FOCUSABLE)).filter(
        (element) => getComputedStyle(element).display !== "none",
      )
    : [];
}

// Disclosure navigation below 1024 px (mobile drawer and expanded tablet
// sidebar): focus moves to the first navigation link on open, Tab stays
// inside, and Escape or the opening control closes it and returns focus.
export function useNavigationDrawer() {
  const [open, setOpen] = useState(false);
  const drawerRef = useRef<HTMLElement>(null);
  const openerRef = useRef<HTMLElement | null>(null);

  const close = useCallback((returnFocus: boolean) => {
    setOpen(false);
    if (returnFocus) openerRef.current?.focus();
  }, []);

  const toggle = useCallback(
    (opener: HTMLElement) => {
      if (open) {
        close(true);
        return;
      }
      openerRef.current = opener;
      setOpen(true);
    },
    [open, close],
  );

  useEffect(() => {
    if (!open) return;
    drawerRef.current
      ?.querySelector<HTMLElement>(".sidebar-nav a[href]")
      ?.focus();
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event: globalThis.KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        close(true);
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [open, close]);

  useEffect(() => {
    if (typeof window.matchMedia !== "function") return;
    const query = window.matchMedia(DESKTOP_QUERY);
    const onChange = () => {
      if (query.matches) setOpen(false);
    };
    query.addEventListener("change", onChange);
    return () => query.removeEventListener("change", onChange);
  }, []);

  const onDrawerKeyDown = useCallback(
    (event: KeyboardEvent<HTMLElement>) => {
      if (!open || event.key !== "Tab") return;
      const items = focusableIn(drawerRef.current);
      if (items.length === 0) return;
      const first = items[0];
      const last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    },
    [open],
  );

  return { open, toggle, close, drawerRef, onDrawerKeyDown };
}
