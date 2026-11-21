# Roadmap

Status: proposal for team discussion, 2026-11-21. Nothing here changes the
constitution. Any item marked **scope change** needs an explicit constitution
amendment agreed by the team (Alison, Cassiy, Oli) before work starts.

## 1. Where the prototype is now

| Feature | What it does | State |
|---|---|---|
| 001 Ingestion and case pipeline | Captures Fimea Basic Register releases, compares them, creates review cases against simulated records | Done |
| 002 Case review readability | Readable change summaries for reviewers | Done |
| 003 App shell and themes | Navigation, layout, light theme | Done |
| 004 Interactive medicine catalogue | Search, substance explorer, product comparison over a real release | Done |
| 005 Fimea release check | Button and service that downloads and ingests the newest release | Approved |
| 006 Medicine shortages | Daily download of Fimea's shortage file, Shortages page, update button | Approved |
| 007 Care loop review and shortage cases | Recorded human review (three outcomes, initials, notes, reopen) and review cases from shortage changes | Approved |
| 008 Labels for likely source clean-ups | Labels for spacing/case-only and active-substance-only changes, optional set-aside switch | Approved |
| 009 Faster, lighter catalogue | Reading a real release in about 12 s and 400 MB instead of 33 s and 2.3 GB | Waiting for approval (T006) |
| 010 Source History and release quality checks | Page of stored source files; automatic check of each new release pair | Waiting for approval (T009) |

Real-data validation (`docs/validation/2026-11-21-real-release-comparison.md`)
compared the 2026-10-06 and 2026-11-21 releases. Detection was correct, but:

- 848 of 1,915 changed packages (44%) changed only because Fimea restructured
  the substance fields, and a further 113 only in whitespace or letter case.
- 269 packages changed their VNR, which is not a compared field.

## 2. Next, inside the course scope

These fit the current constitution and use simulated records only.

1. ~~Decide T016~~ Decided 2026-11-21: the backend's daily update is the only
   scheduler; the n8n workflow is switched off.
2. ~~Decide T018~~ Decided 2026-11-21: a VNR change counts as a change.
3. ~~Label source noise~~ Done as feature 008 (2026-11-21).
   **Label source noise**: mark changes that come only from Fimea's own data
   clean-ups (field restructuring, whitespace, case) so reviewers can set them
   aside. This must come before any pilot, or pharmacists get flooded.
4. ~~Update the weekly progress log~~ Brought up to date on 2026-11-21.
   **Keep the weekly progress log current** (`project-plans/weekly-progress.md`).
5. ~~Continuous integration~~ Done: `.github/workflows/ci.yml` (2026-11-21).
   **Continuous integration**: run backend and frontend tests and linters on
   every push.

## 3. Pharmacy direction (after the course, or by amendment)

### 3.1 What does not work

A service that continuously checks every pharmacy customer's medicines against
Fimea changes is not possible through Kanta. A pharmacy may retrieve a
customer's prescriptions from the Prescription Centre only in the dispensing
situation, at the oral request of the customer or the person acting for them,
and customers can restrict sharing with consent denials.

### 3.2 Realistic routes

**A. Match against the pharmacy's own product range and stock** (scope change)

"Which products we sell or keep in stock are affected by today's release
changes and shortages?" No patient data is involved. It reuses the existing
comparison, shortage and review-case pipeline, with the stock list replacing
the simulated patient records. A simulated stock list could be prototyped in
the current stack. The constitution currently excludes pharmacy inventory
integration, so even a simulated version needs a team amendment.

**B. Check at the moment of dispensing** (scope change, later)

The pharmacy system already has the prescription open at the customer's
request. It asks this service about one package or VNR: "any recent change or
shortage?". Patient data stays inside the pharmacy system; this service
answers only about the medicine. Needs a stable read API and an agreement with
a pharmacy system vendor.

### 3.3 Foundation work both routes need

Proposed as feature **008 Pharmacy integration foundation** (number 007 is
taken):

- organisations and user accounts with role-based permissions;
- an audit log of who reviewed what and when (feature 007 already records
  reviewer initials and notes);
- a data adapter boundary so pharmacy data never mixes with Fimea source data.

Real sign-in and permissions are the first production-like work in the
project. The team should decide whether this belongs in the Xamk course.

## 4. Regulatory points to confirm with experts

Verified on 2026-11-21:

- Valvira's tasks moved to Lupa- ja valvontavirasto on 1.1.2026, including the
  register of social and health care information systems. Registration is a
  notification, not an approval.
- Act 703/2023 classifies systems as unclassified, B, A1, A2 or A3; classes A2
  and A3 need joint testing with Kela.

Not verified, to be confirmed by a lawyer or the agency before any pilot:

- which class routes A and B would fall into;
- whether any part counts as a medical device;
- GDPR basis and whether a data protection impact assessment is required;
- the specific legal sections cited in the earlier pharmacy roadmap draft.

None of the team are lawyers; this section lists questions, not answers.

## 5. Out of scope for the prototype

Unchanged from the constitution: real patient data, Kanta or EHR integration,
pharmacy inventory integration, automatic medicine substitution, autonomous
clinical decisions, and production deployment. AI summaries were also left out
of feature 007 on purpose.
