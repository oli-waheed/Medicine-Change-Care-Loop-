import logging

from fastapi import FastAPI

from .api.change_processing_outcomes import router as change_processing_outcomes_router
from .api.daily_updates import daily_update_lifespan
from .api.daily_updates import router as daily_updates_router
from .api.exports import router as exports_router
from .api.latest_release_check import router as latest_release_check_router
from .api.medicine_catalogue import router as medicine_catalogue_router
from .api.medicine_shortages import router as medicine_shortages_router
from .api.open_review_cases import router as open_review_cases_router
from .api.review_cases import router as review_cases_router
from .api.source_history import router as source_history_router
from .api.source_release_ingestion import router as source_release_ingestion_router
from .config import ApplicationConfig
from .services.pipeline_store import PipelineStore
from .services.simulated_medication_records import load_simulated_medication_records

logger = logging.getLogger(__name__)


def _load_records(config: ApplicationConfig):
    if not config.medication_records_path.is_file():
        logger.warning(
            "No simulated medication records at %s; no review cases can be created.",
            config.medication_records_path,
        )
        return ()
    return load_simulated_medication_records(config.medication_records_path)


_config = ApplicationConfig.from_environment()

# Feature 006: the lifespan starts the daily automatic update.
app = FastAPI(title="Medicine Change Care Loop", lifespan=daily_update_lifespan)
app.state.source_release_config = _config
# The database is opened lazily on first request, not at import time.
app.state.store = PipelineStore(_config.database_url)
app.state.medication_records = _load_records(_config)
app.include_router(open_review_cases_router)
app.include_router(change_processing_outcomes_router)
app.include_router(source_release_ingestion_router)
# Feature 004: read-only medicine catalogue over the active baseline.
app.include_router(medicine_catalogue_router)
# Feature 005: check Fimea for the latest release on request.
app.include_router(latest_release_check_router)
# Feature 006: Fimea shortage data and the daily automatic update.
app.include_router(medicine_shortages_router)
app.include_router(daily_updates_router)
# Feature 007: a pharmacist records a review step (the only operation that changes a case).
app.include_router(review_cases_router)
# Feature 010: read-only history of stored source files and release quality checks.
app.include_router(source_history_router)
# Feature 011: read-only CSV exports of review cases and their history.
app.include_router(exports_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
