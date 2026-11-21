"""A new database opened by several requests at once creates its schema once.

Reproduces the error seen on 2026-11-21 when the browser loaded a page against a
new database: "table source_release_captures already exists".
"""

import threading

from src.services.pipeline_store import PipelineStore


def test_concurrent_first_requests_on_a_new_database(tmp_path):
    for attempt in range(5):
        store = PipelineStore(f"sqlite:///{tmp_path / f'new-{attempt}.sqlite3'}")
        start = threading.Barrier(8)
        errors: list[Exception] = []

        def first_request(store=store, start=start, errors=errors):
            start.wait()
            try:
                store.latest_daily_update_run()
                store.active_shortage_capture()
                store.open_case_payloads()
            except Exception as error:  # noqa: BLE001 - collected for the assertion
                errors.append(error)

        threads = [threading.Thread(target=first_request) for _ in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(30)
        store.dispose()
        assert errors == []
