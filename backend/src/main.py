from fastapi import FastAPI

app = FastAPI(title="Medicine Change Care Loop")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
