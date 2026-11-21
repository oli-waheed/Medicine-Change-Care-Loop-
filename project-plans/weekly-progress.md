# Weekly Progress

Team: Alison, Cassiy, Oli

Entries from week 42 onward were written on 2026-11-21 from the git history (commit dates and authors). The team should check them and add anything that is not in the commits, such as meetings and decisions made outside the repository.

## Week 41 (2026-10-05 – 2026-10-11)

Date: 2026-10-07

### Completed This Week

- The team created the GitHub repository and agreed to use feature branches and Pull Requests.
- Oli created the repository, Constitution v1.1.0, the first Specification and the implementation Plan for `001-ingestion-case-pipeline`.
- Cassiy created `feature/cassiy` with an initial use case, data model and synthetic patient and medication data.
- Alison created `feature/alison` and documented the team progress and workflow.

### Current Status

- `main` contains the course template, Constitution v1.1.0, and the first feature Specification and Plan.
- Cassiy's data-model branch has not been merged yet.
- No GitHub Issues or Pull Requests have been created yet.
- No `tasks.md`, application code, n8n workflow, API or automated tests exist yet.

### Next Steps

1. Review Cassiy's branch and connect it with the first feature specification.
2. Create implementation tasks with `/speckit-tasks`.
3. Create GitHub Issues for the agreed tasks.
4. Implement and test the first small feature slice.
5. Add evidence and update the project documentation.

## Week 42 (2026-10-12 – 2026-10-18)

- **Cassiy** (13 Oct): merged `main` into `feature/cassiy` and removed the preliminary files that the main implementation replaced. Implemented T011–T015 of feature 001: review-case creation tests, case-list contract tests, review-case domain types, ordered snapshot comparison, and exact matching with NEW case creation.
- **Alison** (14 Oct): implemented T016–T020: the read operation for open cases, the first open-case list and evidence view, the end-to-end slice from fixture to review page, and the first parser and ingestion contract tests.
- The weekly-progress "next steps" 1, 2 and 4 were done: Cassiy's work was connected to the specification, `tasks.md` existed, and the first slice was implemented and tested.

## Week 43 (2026-10-19 – 2026-10-25)

- No commits this week.

## Week 44 (2026-10-26 – 2026-11-01)

- **Alison** (28 Oct): implemented T021–T022, normalisation of the Fimea XML with integration tests; merged her T016–T020 and documentation work into `main`; updated the meeting memo template.
- **Cassiy** (28 Oct): implemented T023–T024, capture and validation of source releases; merged `feature/cassiy` (31 Oct).

## Week 45 (2026-11-02 – 2026-11-08)

- **Oli** (3 Nov): implemented T025, the scheduled n8n workflow that downloads Fimea's Basic Register and sends it to the backend.
- **Oli** (4 Nov): clarified the constitution's completion and convergence requirements; updated and reorganised the README and documentation.
- **Oli** (8 Nov): completed T026, the path from release ingestion to review cases (Pull Request #26).

## Week 46 (2026-11-09 – 2026-11-15)

- **Cassiy**: T027 matching unit tests (10 Nov) and T029 explicit matching outcomes (13 Nov).
- **Alison**: T028 integration test for repeated ingestion evidence (10 Nov) and T030 review-case uniqueness when a release is processed again (13 Nov).

## Week 47 (2026-11-16 – 2026-11-22)

Status on 2026-11-21.

### Completed This Week

- **Feature 001 finished** (18 Nov, Oli): integrated T027–T030 (Pull Requests #27 and #30); one case per package update and for packages no longer in the register; active substances paired by substance code instead of list position; unavailable evidence reported and identical downloads stored once; Fimea CC BY 4.0 licence and attribution; T031–T036: unmatched and ambiguous outcomes, quickstart with real results, guards that all test data is simulated and that the app makes no clinical decisions, and spec documents aligned with the code.
- **Features 002, 003 and 004** (20 Nov, Oli; Pull Requests #33–#38): easier-to-read case review, the application shell with About the Data and case search, and the interactive Medicine Catalogue, tested with a real Fimea release.
- **Features 005 and 006** (21 Nov, Oli): "Check for new Fimea release" on About the Data; the Medicine Shortages page with Fimea's shortage file and a daily automatic update. Both passed convergence reviews and were approved.
- **Validation** (21 Nov): two real Fimea releases (2026-10-06 and 2026-11-21) were compared. Change detection was correct (1,915 changed and 21 removed packages); 44 % of the changes were Fimea's own data clean-ups, and VNR changes were not detected. Report: `docs/validation/2026-11-21-real-release-comparison.md`.
- **Feature 007** (21 Nov): pharmacists can record a review on a case (in progress, two reviewed outcomes, reopen) with initials and a note; changes in shortage data create review cases. Approved.
- **Decisions** (21 Nov): T016, the backend's daily update is the only scheduler and the n8n workflow is switched off; T018, a VNR change now counts as a change.
- **Feature 008** (21 Nov): labels for likely source clean-ups ("Spacing or letter case only", "Active-substance fields only") and an optional switch to set them aside. Approved after checking it on the real-data demo.
- **Features 009–014** (21 Nov, evening): a faster, lighter catalogue (a real release now reads in about 12 s and 400 MB instead of 33 s and 2.3 GB); Source History with automatic quality checks of each new release; CSV exports of cases and review history; marks for what is new since the last visit; each package's change history in the catalogue; and field-completeness and source-structure checks. The roadmap was revised after two external reviews (direction A: medicine intelligence; direction B: simulated stock impact, needs a constitution amendment). Waiting for approval.
- **Other**: navy and green colour palette; a comparison helper (`backend/tools/compare_releases.py`) for later real releases; new gold logo; a fix for the error when a new database's first requests arrive together; GitHub Actions CI on every push; `docs/roadmap.md`, covering the course plan and a possible pharmacy direction.

### Current Status

- Features 001–008 are done and approved; 009–014 wait for approval.
- 308 backend and 96 frontend tests pass; every push is checked by CI.
- The app runs on simulated records. Real Fimea data is kept in a separate database that is not committed.

### Next Steps

1. Check the CI run on GitHub after the next push.
2. When Fimea publishes the next release, run `backend/tools/compare_releases.py` and add the result to the validation report and the README's "remaining validation".
3. Try features 009–014 with the real-data demo and approve them.
4. Choose direction A or B in `docs/roadmap.md` §2 as a team, and plan 5–8 pharmacist interviews.
5. Keep this log updated every week.
