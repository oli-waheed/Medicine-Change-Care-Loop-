import { useEffect, useState } from "react";
import { CatalogueError } from "./medicineCatalogue";

export type RequestState<T> =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "loaded"; data: T }
  | { status: "error"; error: CatalogueError };

// Runs a read-only catalogue request whenever its key changes; aborts stale ones.
export function useCatalogueRequest<T>(
  key: string | null,
  load: (signal: AbortSignal) => Promise<T>,
): RequestState<T> {
  const [state, setState] = useState<RequestState<T>>({ status: "idle" });

  useEffect(() => {
    if (key === null) {
      setState({ status: "idle" });
      return;
    }
    const controller = new AbortController();
    setState({ status: "loading" });
    load(controller.signal)
      .then((data) => setState({ status: "loaded", data }))
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === "AbortError")
          return;
        setState({
          status: "error",
          error:
            reason instanceof CatalogueError
              ? reason
              : new CatalogueError(
                  "REQUEST_FAILED",
                  "The catalogue could not be loaded.",
                ),
        });
      });
    return () => controller.abort();
    // The key identifies the request; `load` is recreated on every render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  return state;
}

export function useDebouncedValue<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(value), delayMs);
    return () => window.clearTimeout(timer);
  }, [value, delayMs]);
  return debounced;
}
