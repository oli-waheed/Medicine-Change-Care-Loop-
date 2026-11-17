from fastapi import FastAPI
from starlette.requests import Request

from src.api.open_review_cases import get_open_review_cases, router
from src.services.create_review_cases import create_review_cases
from src.services.pipeline_store import PipelineStore


def test_read_api_returns_only_new_cases_with_evidence(
    tmp_path, change_set, medication_record
):
    app = FastAPI()
    app.state.store = PipelineStore(f"sqlite:///{tmp_path / 'cases.sqlite3'}")
    app.state.store.add_cases(create_review_cases((change_set,), (medication_record,)))
    request = Request(
        {
            "type": "http",
            "app": app,
            "headers": [],
            "method": "GET",
            "path": "/api/open-review-cases",
            "query_string": b"",
        }
    )

    payload = get_open_review_cases(request)

    assert len(payload) == 1
    assert payload[0]["status"] == "NEW"
    assert payload[0]["matchedRecord"]["recordId"] == "SIM-MED-100"
    assert payload[0]["sources"]["prior"]["evidenceClass"] == "VERIFIED"
    assert payload[0]["sources"]["current"]["checksum"] == "new-checksum"
    assert any(route.path == "/api/open-review-cases" for route in router.routes)
