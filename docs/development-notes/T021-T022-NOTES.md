# T021-T022: XML file to normalized snapshots

The local-file reader and byte-content normalizer are implemented in
`backend/src/services/normalize_basic_register_release.py`.

The parser resolves package/product/substance links within one no-namespace XML
document. It preserves source text, attributes, missing versus empty fields,
leading zeroes, repeated routes/substances, authorization branches, release
metadata and package record locators. It returns snapshots only after the whole
document has been parsed and validated. Invalid XML, incomplete coverage,
duplicate identities and unresolved links raise errors without returning partial results.

T021 integration tests exercise file reading, normalization and comparison with
explicit synthetic ordering evidence. Failures cover unavailable files, malformed
and truncated XML, unresolved links, duplicate package identities and incomplete
coverage. Tests also cover repeated fields and raw identifier/text preservation.
The previous unit tests were corrected to use `pakkauskoko_yksikko` and inspect
code-table display values as XML attributes rather than element text.

## Verification

Local environment: Python 3.14.5, pytest 9.1.1, FastAPI 0.142.2.
The project target remains Python 3.13; this run does not certify that environment.

- All 17 T021/T022 integration and normalization tests pass.
- Full backend suite: 76 passed, six failed because pending T024's
  `src.services.ingest_source_release` does not exist.
- Ruff 0.16.10 lint and format checks pass for the three changed Python files.

```powershell
python -m pytest tests/integration/basic-register-to-snapshots tests/unit/basic-register-normalization -q
python -m pytest tests -q
```

## Remaining boundaries

T023 immutable capture and T024 ingestion/status orchestration remain pending.
The supplied checksum is retained as provenance, not independently verified.
This layer does not persist raw files or record retrieval metadata, infer source
chronology, or introduce clinical interpretation. Real-source XSD compatibility
and release ordering remain unresolved as documented in research.md.
The parser builds an in-memory XML tree; large live releases require memory
profiling before scheduled ingestion is enabled.
