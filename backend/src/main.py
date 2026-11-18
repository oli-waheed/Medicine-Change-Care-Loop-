import logging

from fastapi import FastAPI

from .api.change_processing_outcomes import router as change_processing_outcomes_router
from .api.open_review_cases import router as open_review_cases_router
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

app = FastAPI(title="Medicine Change Care Loop")
app.state.source_release_config = _config
# The database is opened lazily on first request, not at import time.
app.state.store = PipelineStore(_config.database_url)
app.state.medication_records = _load_records(_config)
app.include_router(open_review_cases_router)
app.include_router(change_processing_outcomes_router)
app.include_router(source_release_ingestion_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
