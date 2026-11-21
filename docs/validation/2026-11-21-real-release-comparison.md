# Validation: comparison of two real Fimea releases

**Date:** 2026-11-21
**Question:** Does change detection work correctly on two successive real Basic Register releases? (README "remaining validation"; review comment of 2026-11-21.)
**Answer:** Yes for chronology, package identity and the detected differences. Two gaps and one usability risk were found (sections 5–6).

## 1. Material

| | Prior release | Current release |
|---|---|---|
| Ajopvm / Aineistoera | 2026-10-06 / 2026-41 | 2026-11-21 / 2026-47 ("marraskuun 2. erä") |
| File | `Perusrekisteri.xml`, 199,465,476 bytes | `Perusrekisteri.xml`, 200,598,770 bytes |
| SHA-256 | `bb77de82…3fb8678` | `c7ac7fa9…f5201bd3` |
| Packages | 146,042 | 146,868 |
| Captured | uploaded 2026-11-20 | downloaded by the app 2026-11-21 12:22 (Helsinki), real-data database `backend/data/real/` |

Both files are real Fimea open data and are not stored in the repository. No patient data was involved; the simulated records use `SIM-` package IDs.

## 2. Method

1. The app's own result: `GET /api/change-processing-outcomes` on the real-data backend (1,936 outcomes, saved to a file).
2. An independent recomputation: both files normalised with `normalize_basic_register_release()`, every package projected with `project_snapshot_fields()` and compared field by field, keeping the before and after values (which the outcomes do not include).
3. A separate count of packages and VNRs read directly from the XML.

## 3. Results

| Check | Result |
|---|---|
| Release order | Read from each file's Ajopvm; 2026-10-06 → 2026-11-21, evidence `VERIFIED`. Correct. |
| Same releases on every outcome | All 1,936 outcomes name the same prior and current checksums. |
| Changed packages | App: 1,915 `FIELDS_CHANGED`; recomputation: 1,915. Identical. |
| Packages no longer present | App: 21 `NO_LONGER_PRESENT`; recomputation: 21. Identical. |
| New packages | 847 new package IDs; by design no case (only a note). |
| Package ID stability | 146,021 package IDs are in both releases; each appears once in each. All 1,936 changed or removed IDs exist in the prior file. |
| Matching | All 1,936 `NO_MATCH` / `NO_SIMULATED_RECORD`, as expected: no simulated record uses a real package ID. |
| Duplicate download | The daily update at 13:03 found the release already captured and did not store it again. |

## 4. What changed (before → after values checked)

| Group | Packages | Examples of the values |
|---|---|---|
| Active-substance fields only | 848 | Strength text split up: "10.82 mg (resp 10mg)" → "10.82 mg", with a new amount "6.94" and unit "mg" where none existed. Also substance renamed or recoded (Tacrolimus → Tacrolimus monohydrate). |
| Marketing authorisation ended | 440 | Status "Myyntilupa myönnetty" → "Myyntilupa peruuntunut", with an end date (mostly 2026-11-17 and 2026-10-30). E.g. 166122 Cinacalcet Accord. |
| Market status and dates | 370 | "On the market" 1 → 0 for 143 packages and 0 → 1 for 98; withdrawal and launch dates. E.g. 124752 Dicuno. |
| Other | 257 | Trade name (133; e.g. Larofec → Acapery, 214959), package size text and size fields, ATC code labels (36: the code's text label added), public clarification, special-permit end dates. |

These are genuine differences between the two files; none was produced by the comparison itself.

## 5. Findings

1. **Detection is correct.** The independent recomputation reproduces the app's 1,915 changed and 21 removed packages exactly, with plausible before and after values.
2. **Gap: VNR changes are not detected.** `project_snapshot_fields()` does not include `VNR-numero`. Between the releases 269 packages changed VNR: 160 gained one, 92 lost one, and 17 changed to a different VNR (e.g. 224957: 072811 → 192152). Since feature 006 links shortages by VNR, this is worth a decision. *(Decided 2026-11-21, T018: VNR is now a compared field.)*
3. **Risk: review noise from source clean-ups.** 848 packages (44 % of the changes) differ only because Fimea restructured active-substance strength fields, and 113 packages only in spaces or letter case (e.g. "Firekol " → "Firekol", "Ibuprofen Stada" → "Ibuprofen STADA"). With real package IDs in the simulated records, each would become a review case. The differences are real and must stay visible, but a deterministic label such as "spacing or letter case only" could help reviewers. This needs a team decision; it must not hide or close anything automatically.
4. **One pair is not yet "several daily downloads".** This validates one real pair, six weeks apart. The daily update now captures every real release, so further pairs will accumulate in the real-data database.

## 6. Recommended next steps

- Decide whether VNR should be a compared field (finding 2).
- Decide how to present formatting-only and source-restructuring differences (finding 3).
- Repeat this check on later daily pairs (finding 4), then update the README's "remaining validation".
- To see real changes as review cases, add a few fictional records with real package IDs from this comparison (for example 166122, 124752, 214959), as the README allows.

## 7. Repeating this check

`backend/tools/compare_releases.py` repeats sections 3 and 4 on any captured releases, using the app's current rules (VNR compared since T018, clean-up labels of feature 008). On the two releases above it reports, on 2026-11-21:

| Check | Result |
|---|---|
| Release order (Ajopvm) | strictly increasing |
| Pakkaustunnus repeated within a release | 0 |
| Pakkaustunnus in both releases | 146,021 |
| Changed packages | 2,050 (the 1,915 above plus 135 with only a VNR change) |
| No longer present / new | 21 / 847 |
| VNR gained / lost / changed | 160 / 92 / 17 |
| Label: spacing or letter case only / active-substance fields only / none | 109 / 848 / 1,093 |

The 113 formatting-only packages of finding 3 are 109 here, because four of them also changed VNR. Later pairs will be added as new reports when the daily update has collected them.
