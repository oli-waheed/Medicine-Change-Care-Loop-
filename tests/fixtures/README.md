# Test and demo data rules (T033)

All data in `tests/fixtures/` and `backend/seed/` is simulated. It contains no real
patient-identifiable information and no real medicine records.

| Data | Rule |
|---|---|
| Medication record files | Declare `"dataset": "SIMULATED …"`; every `record_id`, `person_reference`, `Pakkaustunnus` and `VNR-numero` starts with `SIM-`; every `medicine_display` starts with `Fictional`. |
| Fimea release fixtures (`fimea-basic-register/*.xml`) | `Pakkaustunnus`, `VNR-numero`, `CASnumero` and `Aineistoera` start with `SIM-`; code-table `id`/`listname` values and XML ID references start with `SIM-` or `SYN-`; trade names start with `Fictional`; descriptive values are labelled `synthetic` or `fictional`; `Ajopvm` dates are in 2090 or later. |
| All data files | No personal identity codes (henkilötunnus), e-mail addresses, phone numbers, real-format ATC codes or real-format CAS numbers. |

`tests/unit/test_simulated_data_guard.py` enforces these rules on every test run. Add new data files under
these folders so the guard checks them.

One deliberate exception lives in test code, not in these files:
`test_basic_register_to_snapshots.py` replaces a fictional `Pakkaustunnus` with the numeric string `000100`
inside an otherwise fictional record, to prove that leading zeroes are preserved.

Real Fimea downloads are stored only in `backend/data/` at run time. That folder, `Perusrekisteri.xml` and
the Fimea XSD files are git-ignored and must never be committed.
