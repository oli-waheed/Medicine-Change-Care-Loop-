"""Feature 006: the backend's daily automatic update.

While the backend runs, a background thread checks once a minute whether
today's update has run. From the configured local time (DAILY_UPDATE_TIME,
default 06:00) it runs once per day: first the shortage file, then the Basic
Register check of feature 005. A backend started after that time catches up at
once. Each run is recorded in the database, so a restart on the same day does
not repeat it.
"""

import logging
import threading
from collections.abc import Callable
from datetime import UTC, datetime

from .pipeline_store import PipelineStore

logger = logging.getLogger(__name__)

CHECK_INTERVAL_SECONDS = 60


def local_now() -> datetime:
    return datetime.now().astimezone()


class DailyUpdateScheduler:
    def __init__(
        self,
        *,
        store: PipelineStore,
        update_time: str,
        run_jobs: Callable[[], dict],
        now: Callable[[], datetime] = local_now,
        interval_seconds: float = CHECK_INTERVAL_SECONDS,
    ) -> None:
        self.store = store
        self.update_time = update_time
        self._run_jobs = run_jobs
        self._now = now
        self._interval = interval_seconds
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._running = threading.Lock()

    def due(self) -> str | None:
        """Today's local date if the scheduled time has passed and no run is recorded."""
        now = self._now()
        if now.strftime("%H:%M") < self.update_time:
            return None
        today = now.date().isoformat()
        if self.store.daily_update_run_on(today) is not None:
            return None
        return today

    def tick(self) -> bool:
        """Run today's update if it is due. Returns whether a run happened."""
        if not self._running.acquire(blocking=False):
            return False
        try:
            today = self.due()
            if today is None:
                return False
            run = self.store.start_daily_update_run(today, "SCHEDULE", datetime.now(UTC))
            try:
                outcome = self._run_jobs()
            except Exception as error:  # noqa: BLE001 - recorded, retried tomorrow
                logger.exception("Daily update failed.")
                outcome = {"error": f"The daily update failed unexpectedly: {error}"}
            self.store.finish_daily_update_run(run, datetime.now(UTC), outcome)
            return True
        finally:
            self._running.release()

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._loop, name="daily-update", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                self.tick()
            except Exception:  # noqa: BLE001 - keep the schedule alive
                logger.exception("Daily update check failed.")
            self._stop.wait(self._interval)
