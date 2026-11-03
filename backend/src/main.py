from fastapi import FastAPI

from .api.open_review_cases import router as open_review_cases_router
from .api.source_release_ingestion import router as source_release_ingestion_router
from .config import ApplicationConfig

app = FastAPI(title="Medicine Change Care Loop")
app.state.open_review_cases = []
app.state.source_release_config = ApplicationConfig.from_environment()
app.include_router(open_review_cases_router)
app.include_router(source_release_ingestion_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
