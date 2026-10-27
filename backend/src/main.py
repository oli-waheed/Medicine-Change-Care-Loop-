from fastapi import FastAPI

from .api.open_review_cases import router as open_review_cases_router

app = FastAPI(title="Medicine Change Care Loop")
app.state.open_review_cases = []
app.include_router(open_review_cases_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
