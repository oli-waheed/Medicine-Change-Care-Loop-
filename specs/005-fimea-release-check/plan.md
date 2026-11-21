# Feature 005: Implementation Plan

## Architecture

- **Shared ingestion** (`backend/src/workflows/ingest_release_file.py`): the body of `POST /api/source-releases/ingest` after the upload is on disk (metadata validation, duplicate check, capture, comparison, one-transaction write) moves into `ingest_release_file()`. The upload endpoint and the new check both call it, so FR-004 holds by construction. The endpoint's responses are unchanged.
- **Check service** (`backend/src/services/latest_release_check.py`): `LatestReleaseCheck` runs one check at a time in a daemon thread under a lock (FR-005): stream the download to a temporary file with the size limit, hash it, ingest it, prepare the catalogue (`MedicineCatalogueService.get_baseline()`), and record the phase, result or error. The download function is injectable so tests use fixture files.
- **API** (`backend/src/api/latest_release_check.py`): `POST` and `GET /api/source-releases/latest-check` (contract in `contracts/latest-release-check-api.md`). The ingestion metadata matches the n8n workflow (FR-003). `catalogue_service(app)` is shared with the catalogue API so the prepared cache is the one the catalogue uses.
- **Configuration**: `FIMEA_RELEASE_URL` (default the n8n address).
- **Frontend**: `LatestReleaseCheck` section on About the Data; POST on press, then GET every 2 s while running (FR-002, FR-008).

## Decisions

- A background thread with polling rather than a long request: a real check takes about 70 s (download, 33 s reconstruction, catalogue preparation), longer than is reasonable to hold a request open.
- In-memory status: the check's outcome is also recorded durably as a capture and retrieval in the database; only the progress display resets on restart.
- No status request on page load, so pages that do not use the check make no extra requests.

## Risks

- Reconstruction of a real release uses about 2.3 GB of memory (feature 004 T005); a check and a catalogue load can overlap only through the catalogue's lock, so the release is reconstructed once.
- An upload through `POST /ingest` and a check at the same moment are not serialised against each other; both use the existing duplicate and transaction rules.
