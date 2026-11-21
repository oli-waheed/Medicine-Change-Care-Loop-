"""Feature 006: the daily automatic update (schedule and last run)."""

from contextlib import asynccontextmanager
from datetime import UTC

from fastapi import APIRouter, FastAPI, Request

from ..config import ApplicationConfig
from ..services.daily_updates import DailyUpdateScheduler, local_now
from ..services.latest_release_check import status_response
from ..services.medicine_shortages import update_status_response
from ..workflows.release_quality import backfill_release_pairs
from .latest_release_check import latest_release_check, start_latest_release_check
from .medicine_shortages import shortage_update, start_shortage_update

router = APIRouter(prefix="/api/daily-updates", tags=["daily-updates"])

# A real Basic Register check takes about 70 s; allow ample time before giving up waiting.
_WAIT_SECONDS = 30 * 60


def run_daily_jobs(app: FastAPI) -> dict:
    """Shortages first (small), then the Basic Register, then incomplete release pairs."""
    update = shortage_update(app)
    start_shortage_update(app, trigger="SCHEDULE")
    shortages = update_status_response(update.wait(_WAIT_SECONDS))

    start_latest_release_check(app)
    check = latest_release_check(app)
    check.wait(_WAIT_SECONDS)
    basic_register = status_response(check.status())
    # Features 010 and 013: complete release pairs without a check or history.
    added = backfill_release_pairs(app.state.store)
    return {
        "shortages": shortages,
        "basicRegister": basic_register,
        "qualityChecksAdded": added["qualityChecks"],
        "packageHistoriesAdded": added["packageHistories"],
    }


def utc_offset(moment) -> str:
    """The machine's offset as "UTC+02:00"; time-zone names differ between systems."""
    offset = moment.strftime("%z") or "+0000"
    return f"UTC{offset[:3]}:{offset[3:]}"


def _time(value):
    if value is None:
        return None
    return (value.replace(tzinfo=UTC) if value.tzinfo is None else value).isoformat()


@router.get("")
def get_daily_updates(request: Request) -> dict:
    config: ApplicationConfig = request.app.state.source_release_config
    run = request.app.state.store.latest_daily_update_run()
    return {
        "enabled": config.daily_update_time is not None,
        "time": config.daily_update_time,
        "timeZone": utc_offset(local_now()),
        "lastRun": (
            {
                "date": run.run_date,
                "trigger": run.trigger,
                "startedAt": _time(run.started_at),
                "finishedAt": _time(run.finished_at),
                "outcome": run.outcome,
            }
            if run is not None
            else None
        ),
    }


@asynccontextmanager
async def daily_update_lifespan(app: FastAPI):
    """Start the daily update when the backend starts (if DAILY_UPDATE_TIME is set)."""
    config: ApplicationConfig = app.state.source_release_config
    scheduler = None
    if config.daily_update_time is not None:
        scheduler = DailyUpdateScheduler(
            store=app.state.store,
            update_time=config.daily_update_time,
            run_jobs=lambda: run_daily_jobs(app),
        )
        scheduler.start()
    app.state.daily_update_scheduler = scheduler
    try:
        yield
    finally:
        if scheduler is not None:
            scheduler.stop()
