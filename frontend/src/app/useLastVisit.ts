import { useSyncExternalStore } from "react";
import { previousVisit, subscribeToVisits } from "./lastVisit";

// Feature 012: the previous visit's time, updating when marks are cleared.
export function usePreviousVisit(): string | null {
  return useSyncExternalStore(subscribeToVisits, () => previousVisit());
}
