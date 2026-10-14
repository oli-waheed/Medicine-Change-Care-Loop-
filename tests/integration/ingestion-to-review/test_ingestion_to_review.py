from datetime import UTC, datetime

from fastapi import FastAPI
from starlette.requests import Request

from src.api.open_review_cases import router
from src.domain.evidence import EvidenceClassification
from src.services.detect_relevant_changes import detect_relevant_changes
from src.workflows.ingestion_to_review import run_ingestion_to_review


def test_fixture_comparison_creates_case_visible_in_open_case_read_view(
    snapshot_pair, medication_record
):
    prior, current, order = snapshot_pair
    app = FastAPI()
    app.state.open_review_cases = []
    app.include_router(router)
    read_request = Request(
        {
            "type": "http",
            "app": app,
            "headers": [],
            "method": "GET",
            "path": "/api/open-review-cases",
            "query_string": b"",
        }
    )

    result = run_ingestion_to_review(
        (prior,),
        (current,),
        (medication_record,),
        order=order,
        open_cases=app.state.open_review_cases,
        created_at=datetime(2099, 1, 3, tzinfo=UTC),
    )
    payload = router.routes[0].endpoint(read_request)

    assert len(result.comparison.changes) == 1
    assert result.comparison.changes[0].medicine_key == "SIM-PKG-100"
    assert [case.status.value for case in result.created_cases] == ["NEW"]
    assert len(payload) == 1
    assert payload[0]["matchedRecord"]["recordId"] == "SIM-MED-100"
    assert payload[0]["change"]["field"] == "Laakevalmiste/Kauppanimi"
    assert payload[0]["change"]["before"][0]["value"] == "Fictional Alpha"
    assert payload[0]["change"]["after"][0]["value"] == "Fictional Alpha Updated"
    assert payload[0]["sources"]["prior"]["fileName"] == "prior.xml"
    assert payload[0]["sources"]["current"]["recordLocator"] == current.source_record_locator
    assert payload[0]["sourceOrder"]["evidenceClass"] == EvidenceClassification.VERIFIED
    assert payload[0]["initialStatusEvent"]["toStatus"] == "NEW"
    assert payload[0]["evidenceClass"] == "VERIFIED"


def test_workflow_does_not_create_cases_when_release_order_is_unknown(
    snapshot_pair, medication_record
):
    prior, current, order = snapshot_pair
    unknown_order = order.__class__(
        order.prior_release,
        order.current_release,
        order.prior_order,
        order.current_order,
        EvidenceClassification.UNKNOWN,
        "Source order is not established.",
    )
    open_cases = []

    result = run_ingestion_to_review(
        (prior,), (current,), (medication_record,), order=unknown_order, open_cases=open_cases
    )

    assert result.comparison.changes == ()
    assert result.comparison.classification is EvidenceClassification.UNKNOWN
    assert result.created_cases == ()
    assert open_cases == []


def test_workflow_uses_only_exact_pakkaustunnus_match(snapshot_pair, medication_record):
    prior, current, order = snapshot_pair
    wrong_package = medication_record.__class__(
        "SIM-MED-999",
        "SIM-PERSON-999",
        "Fictional unrelated medicine",
        package_identifier="SIM-VNR-100",
    )
    result = run_ingestion_to_review(
        (prior,), (current,), (wrong_package,), order=order, open_cases=[]
    )

    assert len(result.comparison.changes) == 1
    assert result.created_cases == ()


def test_replaying_fixture_does_not_duplicate_case_in_open_read_store(
    snapshot_pair, medication_record
):
    prior, current, order = snapshot_pair
    open_cases = []
    first = run_ingestion_to_review(
        (prior,), (current,), (medication_record,), order=order, open_cases=open_cases
    )
    replay = run_ingestion_to_review(
        (prior,), (current,), (medication_record,), order=order, open_cases=open_cases
    )

    assert len(first.created_cases) == 1
    assert replay.created_cases == ()
    assert len(open_cases) == 1
