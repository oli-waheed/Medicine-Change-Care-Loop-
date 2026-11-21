# Roadmap

Status: proposal for team discussion, revised 2026-11-21 (evening) after two
external reviews. Nothing here changes the constitution. Any item marked
**scope change** needs an explicit constitution amendment agreed by the team
(Alison, Cassiy, Oli) before work starts.

**Positioning.** Medicine Change Care Loop is a Finnish medicine-intelligence
layer: it explains what changed about a medicine, where the evidence comes
from, and what a pharmacy professional may want to review. It is not a
dispensing, inventory, prescribing or patient-record system, and it makes no
clinical decisions.

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
| 011 CSV exports | Cases and review history as CSV for reports and records | Waiting for approval (T006) |
| 012 New since your last visit | Marks new cases, shortages and source files per browser | Waiting for approval (T006) |
| 013 Package timeline | Each package's changes across compared releases, with values | Waiting for approval (T007) |
| 014 Completeness, structure and shortage coverage | Field-completeness and source-structure checks; "not listed is not available" on Medicine Shortages | Waiting for approval (T006) |
| 015 Medicine change impact explorer | Linked records of a package or product, each verified, possible or missing | Waiting for approval (T007) |

Decisions already taken: the backend's daily update is the only scheduler
(T016); a VNR change counts as a change (T018); CI runs on every push.

Real-data validation (`docs/validation/2026-11-21-real-release-comparison.md`):
one real pair (2026-10-06 → 2026-11-21) passes every automatic check. 2,050
packages changed; 957 of them carry a clean-up label (feature 008).

## 2. Next, inside the course scope (no constitution change)

### 2.1 Foundation (do first)

1. **Repeat the real-release check** on later Fimea releases as the daily
   update collects them (`backend/tools/compare_releases.py`, Source History),
   and update the validation report and the README's "remaining validation".
2. **Obtain the schema the XML declares** (`Perusrekisteri_Fimea_2022.xsd`).
   Only the 2021 XSD was available, and the XML uses at least one element it
   does not declare, so full XSD validation is not possible yet. Feature 014
   compares each release's element paths and declared schema with the previous
   release instead.
3. **Database migrations** (Alembic) before any pilot; the prototype adds new
   columns automatically, which is enough for a course prototype only.
4. **Pharmacist interviews** (5–8, exploratory): how they learn about medicine
   changes and shortages today, what takes time, what evidence they need. Ask
   about their work, not whether they like the app.

### 2.2 Direction A — medicine intelligence (recommended for the course)

| Proposed | Feature | Notes |
|---|---|---|
| ~~015~~ Built (2026-11-21) | **Medicine change impact explorer** | Links already in the data: package, product, VNR, active-substance code, strength, form, authorisation holder. Shows verified links, possible links and missing information separately. No graph database needed. |
| 016 | **Supply signals** | Facts side by side for a package or substance: shortage reported and since when, how long earlier shortages lasted, authorisation status, packages with the same VNR or substance. **No prediction and no "risk" score**: the clinical-scope guards forbid such wording, and an unvalidated indicator would look like a clinical assessment. |
| 017 | **Read-only medicine intelligence API** | Documented, versioned endpoints for changes, shortages and quality checks; the base for route B in §3.2. |
| 018 | **Portfolio release** | Architecture and data-flow diagrams, a guided demo, the limitations and safety statement, interview findings. |

### 2.3 Direction B — pharmacy stock impact (scope change)

**015B Pharmacy stock impact monitor, simulated only.** "Which products we sell
or keep in stock are affected by today's changes and shortages?" Uses a
simulated stock list in place of the simulated medication records; no patient
data. It needs a constitution amendment, because pharmacy inventory
integration is excluded. If chosen, keep three things separate and never merge
them into one status: national shortage report (Fimea), local stock, and
supplier deliveries.

The team should choose A or B (or A first, then B).

## 3. Pharmacy direction (after the course, or by amendment)

### 3.1 What does not work

A service that continuously checks every pharmacy customer's medicines against
Fimea changes is not possible through Kanta. A pharmacy may retrieve a
customer's prescriptions from the Prescription Centre only in the dispensing
situation, at the oral request of the customer or the person acting for them,
and customers can restrict sharing with consent denials.

### 3.2 Realistic routes

**A. Match against the pharmacy's own product range and stock** (scope change):
see §2.3.

**B. Check at the moment of dispensing** (scope change, later). The pharmacy
system already has the prescription open at the customer's request. It asks
this service about one package or VNR: "any recent change or shortage?".
Patient data stays inside the pharmacy system.

Since 1 January 2026, section 57 f of the Medicines Act lets a pharmacist depart
from a prescription in defined situations; a departure because of a national
shortage is recorded with its reason code. Fimea's shortage data is the
evidence behind that reason, so route B could show the shortage record, its
source and update date. It must never decide that the legal conditions are met
or choose a medicine. Validate with pharmacists and obtain legal review first.

HE 163/2026 (pharmacy services, online pharmacy, automated dose dispensing) is
a government proposal, mainly meant to take effect on 1 March 2027; treat it as
a proposal until enacted.

### 3.3 Foundation work both routes need

Proposed as a feature after 018 (numbers 001–015 are used):

- organisations and user accounts with role-based permissions;
- an audit log of who reviewed what and when (feature 007 records initials and
  notes; a pilot needs authenticated identities);
- a data adapter boundary so pharmacy data never mixes with Fimea source data.

### 3.4 Later ideas from the reviews (not planned)

Recall and safety-action manager (needs official recall sources and batch
data), expiry and lifecycle monitoring, multi-branch views, task orchestration,
service documentation workbench, business intelligence, cold-chain monitoring.
Each is a separate product phase. **Avoid**: AI choosing medicines, automatic
clinical scoring, unverified shortage prediction, collecting patient data
"for later", and building a full pharmacy management system.

## 4. Regulatory points to confirm with experts

Verified on 2026-11-21:

- Valvira's tasks moved to Lupa- ja valvontavirasto on 1.1.2026, including the
  register of social and health care information systems. Registration is a
  notification, not an approval.
- Act 703/2023 classifies systems as unclassified, B, A1, A2 or A3; classes A2
  and A3 need joint testing with Kela.
- Medicines Act section 57 f (in force 1.1.2026) and the DP recording with
  reason codes; HE 163/2026 submitted, mainly 1.3.2027 if enacted.
- Fimea received 2,783 shortage reports in 2025 (2,676 in 2024).

Not verified, to be confirmed by a lawyer or the agency before any pilot:

- which class routes A and B would fall into;
- whether any part counts as a medical device;
- GDPR basis and whether a data protection impact assessment is required.

None of the team are lawyers; this section lists questions, not answers.

## 5. Out of scope for the prototype

Unchanged from the constitution: real patient data, Kanta or EHR integration,
pharmacy inventory integration, automatic medicine substitution, autonomous
clinical decisions, and production deployment. AI summaries were also left out
of feature 007 on purpose.
