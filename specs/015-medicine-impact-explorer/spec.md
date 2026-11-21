# Feature 015: Medicine Change Impact Explorer (Linked Records)

**Status:** Approved specification (requested by Oli on 2026-11-21: roadmap direction A, first feature)
**Branch:** feature/medicine-impact-explorer

## 1. Objective

For any package or product in the Medicine Catalogue, show everything linked to it in Fimea's data, so a reviewer can see the wider impact of a change: other packages of the same product, packages with the same VNR, products with the same active substances (other strengths and forms) or sharing one, the same authorisation holder, the same trade name, and Fimea shortage rows. Each link says how certain it is.

## 2. Scope

### In scope
- Links from the active release and the active shortage file only.
- Three certainty levels: verified (exact shared identifier or reference), possible (only a name, or text differing in spaces or letter case), missing (the anchor lacks the identifier, or no shortage file is stored).
- Reading the holder (`Haltija`) of each authorisation or registration, for links only.

### Out of scope
- Any statement that products are interchangeable, comparable in effect, or alternatives; any ranking.
- Making the holder a compared field (a team decision, like T018).
- Links across releases (the package timeline of feature 013 covers history).
- A graph database.

## 3. Requirements

- **FR-001** `GET /api/medicine-catalogue/packages/{pakkaustunnus}/links` and `GET /api/medicine-catalogue/products/{product_reference}/links` MUST return link groups for the package, or for all packages of the product; 404 for unknown records; 503 as other catalogue endpoints when no release is available. Read-only.
- **FR-002** Groups and certainty:
  - `SAME_PRODUCT` other packages of the product — verified;
  - `SAME_VNR` packages with exactly the same VNR — verified; missing without a VNR;
  - `SAME_SUBSTANCES` products with exactly the same set of active-substance codes (other strengths and forms) — verified;
  - `SHARES_SUBSTANCE` products with at least one code in common — verified;
  - `SUBSTANCE_BY_NAME` for substances without a code, products with a substance of the same name — possible;
  - missing when no substance is listed;
  - `SAME_HOLDER` exactly the same holder text — verified; `SIMILAR_HOLDER` same except spaces or letter case — possible; missing without a holder;
  - `SAME_NAME` other product records with the same trade name — possible;
  - `SHORTAGES` rows of the active shortage file with the same VNR, as published — verified; missing without a VNR or without a stored file; with a VNR but no row: an empty group with the note that this does not show availability.
- **FR-003** Each group MUST state its basis in words, its total, and at most 50 items (packages, products or shortage rows).
- **FR-004** The response and the page MUST state that links show shared identifiers and values only and say nothing about whether one product can be used in place of another. Wording MUST pass the clinical-wording guards.
- **FR-005** The holder MUST be read into the authorisation record but excluded from change detection.
- **FR-006** The package and product pages MUST show a "Linked records" section: each group with its certainty, count, basis and items; linked packages and products open in the catalogue; groups longer than five items fold, with "Show more" and "Show fewer".

## 4. Acceptance criteria

1. With the synthetic links release and shortage file, every group of FR-002 gives the expected records and certainty, including missing and possible cases.
2. A holder appears in the record but never as a detected change.
3. On the real 2026-11-21 release, the index builds once (about 1 s) and later requests answer in under 0.1 s; e.g. package 148768 links 2 other packages, 104 products with the same substance and 10 sharing one.
4. All tests, lint, format, type check and build pass; no contrast failures or horizontal overflow at 320–1440 px.

## 5. Decisions (2026-11-21)

- D1 Product links group by active-substance code set, because codes are Fimea's identifiers; names only give possible links.
- D2 Holder is read but not compared until the team decides (as T018 did for VNR).
