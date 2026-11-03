# T011–T015 implementation notes

Implemented against the uploaded main ZIP baseline (latest visible commit 7b99ed8).
AI-assisted implementation prepared for user review; no GitHub push has been made.

## Behavior
- T011: exact package match and supported NEW-case creation tests.
- T012: serialization contract tests for status, fictional record, before/after values,
  both source releases, raw file references, record locators and source ordering evidence.
- T013: DetectedChange, ReviewCase, CaseStatusEvent and simulated-record domain types.
- T014: deterministic comparison of the T005 fields in existing MedicineSnapshot types.
  SourceOrderEvidence must explicitly establish source order; retrieval time is never used.
  Missing/ambiguous package pairs are skipped with diagnostic notes; baseline creates no changes.
  Repeated occurrences and source attributes are preserved. Identifiers are not trigger fields.
- T015: exact Pakkaustunnus matching, unique supported match only, initial NEW status event.
  Unknown/conflicting/inferred change evidence creates no case. VNR is never a fallback.
  Duplicate pairs in one call are suppressed and pair IDs are deterministic.

## Boundaries
No API endpoint, database persistence, UI, XML normalizer or scheduled ingestion was added.
T016–T018 and T022 onward remain pending. The contract serializer is the boundary for a later API.
Retrieval metadata is explicitly null because existing source types do not yet capture it (T023).
Source order keys come from the caller's established source evidence, not guessed date semantics.
Fixtures establish their own fictional ordering; this does not verify real Fimea cross-release keys.
Persistent replay deduplication belongs to T030; deterministic IDs alone are not database enforcement.
No diagnosis, treatment, substitution, urgency or automatic closure is implemented.

## Verification
Python 3.13.16 / pytest 9.1.1: all 54 tests passed (existing and new).
Ruff 0.16.10: lint and format checks pass using backend/pyproject.toml explicitly.
Three existing unit tests received import-format-only cleanup; their assertions are unchanged.

From the project root (with pytest and ruff installed):
```powershell
python -m pytest tests -q
python -m ruff check --config backend/pyproject.toml backend/src tests
python -m ruff format --config backend/pyproject.toml --check backend/src tests
```

## Files and integration
Copy the patch ZIP contents into the existing repository root only after fetching/merging
Oli's baseline into feature/cassiy and checking for local changes. The patch adds domain types,
services, a serialization schema, shared test fixtures and focused tests. It updates the task
checkboxes and includes this note. It contains no .git, credentials or virtual environment.
Review git diff, rerun the commands, then commit/push feature/cassiy. Never replace the .git folder.
