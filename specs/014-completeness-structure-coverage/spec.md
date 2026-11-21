# Feature 014: Field Completeness, Source Structure and Shortage Coverage

**Status:** Approved specification (requested by Oli on 2026-11-21 after the second external review: "foundation patch")
**Branch:** feature/completeness-structure-coverage

**Supersedes in part:**
- `specs/010-source-history-and-quality-checks` FR-002: two more checks per release pair; checks carry a version and older checks are made again.

## 1. Objective

Close the foundation gaps the reviews found, as far as the available evidence allows:

- The Fimea XML declares `Perusrekisteri_Fimea_2022.xsd`, which the project does not have (`specs/001-ingestion-case-pipeline/research.md`). Full XSD validation is therefore not possible; instead, detect when a release's structure or declared schema changes.
- Detect when a release suddenly lacks values that earlier releases had.
- Never let the Shortages page suggest that a medicine absent from Fimea's list is available.

## 2. Requirements

- **FR-001** The normaliser MUST record each release's declared schema location and every element path with its count, without changing release identity or snapshots.
- **FR-002** Each release check MUST include `SOURCE_STRUCTURE`: ATTENTION when element paths appear or disappear or the declared schema changes, naming them; PASSED otherwise.
- **FR-003** Each release check MUST include `FIELD_COMPLETENESS` for VNR, trade name, strength, form, ATC code, package size text, on-the-market flag, active substance and authorisation or registration: ATTENTION when any share of packages with a value drops by more than 2 percentage points, naming the field; PASSED otherwise. The shares are part of the check.
- **FR-004** Checks MUST carry a version (2). The daily update's backfill MUST make older checks again; the page MUST mark a check made by an earlier version until then.
- **FR-005** Medicine Shortages MUST state that a medicine not listed is not shown to be available, that the file holds only shortages reported by marketing authorisation holders by VNR, and that it says nothing about local stock or wholesaler deliveries.
- **FR-006** Wording MUST stay non-clinical.

## 3. Acceptance criteria

1. An unchanged synthetic pair passes both checks with 100 % VNR completeness; a pair with a new element and lost VNRs gets ATTENTION on both, naming the element and the field.
2. A stored version-1 check is shown as made by an earlier version and is replaced once by the backfill.
3. On the real pair (2026-10-06 → 2026-11-21) both checks pass: 113 element paths, same schema declared (`Perusrekisteri_Fimea_2022.xsd`), largest completeness drop 0.03 points (Vahvuus); VNR is present for 12.56 % of packages in both.
4. All tests, lint, format, type check and build pass; no contrast failures or horizontal overflow at 320–1440 px.

## 4. Open

- Obtain `Perusrekisteri_Fimea_2022.xsd` from Fimea for full schema validation (roadmap §2.1).
