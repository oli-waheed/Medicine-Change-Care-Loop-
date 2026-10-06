# Research: Medicine Change Ingestion-to-Case Pipeline

**Date**: 2026-10-06

## Fimea source selection

**Decision**: Use Fimea's Basic Register XML variant for the prototype's initial scheduled source snapshots.

**Rationale**: The team selected the official XML variant at [Fimea's Basic Register (XML) page](https://fimea.fi/en/databases_and_registers/basic-register-xml). Fimea states that the register is XML and has an XSD schema with field labels, and that information is transferred to the XML file once per day. This remains the Basic Register source; the selected representation is the XML variant, not the separate ASCII release bundle.

**Alternatives considered**:

- **FimeaWeb**: Provides search and access to product leaflets and summaries of product characteristics (SPCs), but it is an interactive service and no documented public API or stable automated retrieval contract was found. Dates shown in document titles are document revision dates, not verified record synchronization timestamps. Treat as a possible future/manual source, not this feature's ingestion feed.
- **Undocumented FimeaWeb requests**: Rejected because relying on private implementation details is brittle and source terms, rate limits, and automated reuse permission need confirmation.

**Evidence**:

- Fimea, [Basic Register (XML)](https://fimea.fi/en/databases_and_registers/basic-register-xml): official description of the XML representation, accompanying XSD, daily transfer of information to the XML file, excluded availability-shortage information, and Fimea's data-quality caveat.
- Fimea, [Perusrekisteri XML](https://fimea.fi/laakehaut_ja_luettelot/perusrekisteri-xml): Finnish-language counterpart with the same XML and daily-transfer description.
- Fimea, [Basic register for medicinal products (ASCII)](https://fimea.fi/en/databases_and_registers/basic-register): a distinct representation; it describes multiple ASCII files, twice-monthly updates, and package-level change markings. These ASCII-specific characteristics are not assumed for the selected XML variant.
- Fimea, [FimeaWeb](https://fimea.fi/en/databases_and_registers/fimeaweb): official description of searchable medicine and product information.
- Fimea, [Lääkehaku information](https://fimea.fi/laakehaut_ja_luettelot/laakehaku): Fimea's caveat that online information may contain errors and is not guaranteed complete, exact, or current.

## Current XML source inspection (T004)

**Files inspected in the repository root**:

- `Perusrekisteri.xml` — 199,465,476 bytes; UTF-8 XML. Its root is `Perusrekisteri`, has no default namespace, and declares `xsi:noNamespaceSchemaLocation="Perusrekisteri_Fimea_2022.xsd"`.
- `Perusrekisteri_Fimea_2021.xsd` — 34,748 bytes; XSD schema with Finnish `xs:documentation` annotations. This is the schema file present locally.

**Schema mismatch**: the XML references `Perusrekisteri_Fimea_2022.xsd`, but that file is not present; the local schema is named `Perusrekisteri_Fimea_2021.xsd`. A product record in the XML includes `RinnakkaisKauppa`, which is not declared in the local 2021 XSD. Do not assume the 2021 schema is interchangeable with the referenced 2022 schema. The XML and available schema were inspected, but validation against the schema version referenced by the XML could not be established. Obtain the matching 2022 XSD or confirmation of compatibility before relying on schema validation.

**XML structure and parsing facts**:

- The XSD declares a no-namespace `Perusrekisteri` root with a sequence: one `Versiotiedot`, zero or more `Pakkaus` records, zero or more `Laakevalmiste` records, then zero or more `Laakeaine` records.
- Package/product/substance relationships use XML IDs and IDREFs: `Pakkaus/@Laakevalmiste-ref` refers to a `Laakevalmiste/@id`; each `Pakkaus_Laakeaine/@Laakeaine-ref` refers to a `Laakeaine/@id`. A package refers to one product and may refer to one or more active-substance records.
- The actual file contains 146,042 `Pakkaus`, 30,329 `Laakevalmiste`, and 31,617 `Laakeaine` elements. These are observed counts for this file, not guaranteed future totals.
- `Kattavuus` is an integer which the XSD documentation says is always `1`; this file has `1`. This is evidence that the represented run is complete according to the schema annotation, not evidence that every field is error-free.
- Some optional code-table elements are present but empty in the XML (for example `Annostelulaite` and `Suljin` in the first package). Distinguish an empty element from an absent optional element and do not invent a code or display value.
- The first package is `Pakkaustunnus=1`, has `VNR-numero=033118`, `Pakkauskokoteksti=2 x 500 ml`, and references product `REL1`. Product `REL1` is `Mixobar Oesophagus`, strength `1 g/ml`, dosage form value `oraalisuspensio`; its record shows authorization status `Myyntilupa peruuntunut` and its linked package has `Kaupan=0`. This is an observed example only, not an assertion that it is a current marketed medicine.
- Parsing must preserve leading zeroes and treat identifiers as strings (`Pakkaustunnus` and `VNR-numero` are `xs:string` in the available XSD). Resolve product and substance IDREFs only within the same source document unless cross-release stability is separately verified. Preserve optional/missing fields as missing rather than fabricating values.

**Available fields relevant to the project (candidate inventory, not the team's approved change-field list)**:

- Package identity and display: `Pakkaustunnus` (schema annotation: immutable technical identifier in Fimea's marketing-authorisation register), optional `VNR-numero` (schema annotation: package-identifying Nordic product number; present for most marketed packages), `VanhaVNR`, `Pakkauskokoteksti`, `Pakkauskoko`, `Pakkauskokokerroin`, `Pakkauskokoyksikko`, and `JulkinenTarkenne`.
- Product identity and display: XML `Laakevalmiste/@id` (referenced from packages within the document), `Kauppanimi`, optional `Vahvuus`, `Laakemuoto`, `ATC-koodi`, and `Antoreitti`.
- Active-substance evidence: XML `Laakeaine/@id`, `VaikuttavaAine/Aine`, `CASnumero`, `Maara`, `Maarayksikko`, `JakamatonVahvuus`, and the package-to-substance references.
- Package availability/status fields also exist, including `Kaupanolo/Kaupan` and dates; marketing authorisation/registration status and dates are nested under the product. Their presence does not make them clinical urgency or treatment advice.
- `Substituutioryhma` exists in the schema but is outside this feature's use: it must not be used to select or recommend a medicine substitution.
- T005 remains responsible for the team's explicit choice of which fields are relevant to create a review case and which same-granularity key is used to match simulated records. This inventory alone does not make those decisions.

**Release/source ordering evidence**:

- `Versiotiedot` appears first in the XML. The XSD annotation says it uniquely identifies the delivered data batch.
- This file contains `Ajopvm=2026-10-06`; the XSD defines it as an `xs:date` and documents it as the dataset run date.
- It also contains `Aineistoera=2026-41`; the XSD describes this string as the dataset-batch identifier and says it consists of the year and current day. The one observed value's exact encoding/ordering semantics are not demonstrated by this single file.
- Optional `Kkera=lokakuun 1. erä`; the XSD calls this a batch qualifier for the first or second half of a month. `Kattavuus=1` denotes full coverage according to the XSD annotation.
- `Ajopvm` is the strongest documented candidate for chronological comparison of captured snapshots, with `Aineistoera`/`Kkera` retained as source batch identity/evidence. Only one snapshot is present, so monotonicity, uniqueness, corrections/reissues, and ordering across actual successive files are not empirically verified. No per-product/per-package last-modified timestamp or explicit XML change marker was found in the available schema. Do not infer change chronology from local retrieval time or record dates such as marketing-authorisation dates.
- Fimea's XML page states the XML file is populated from its internal database once per day. This describes transfer cadence, not proof that every daily file is a distinct ordered release or that a medicine record changed that day.

**Access, reuse, and source limitations**:

- Fimea says the register is intended primarily for organisations responsible for medicine acquisition, distribution, and sales, and that users need IT expertise to process the files.
- The official XML page warns that individual errors may occur and that online data is not guaranteed to be comprehensive, complete, precise, or current. It says availability-shortage information is not included in the XML at present. This conflicts with the local XML and XSD, which contain `SaatavuushairioTiedot` and related fields; the first package in the XML has `Saatavuushairio=0`. Treat availability-shortage completeness as unknown and do not rely on these fields without Fimea clarification.
- The pages and files reviewed do not state an explicit license, automated download permission, redistribution permission, stable download endpoint, or retrieval protocol. Do not infer those permissions. Confirm the applicable terms and supported retrieval method with Fimea before enabling scheduled production-like retrieval.

**T004 status**: complete as an inspection/documentation task. The schema filename mismatch and missing access/reuse terms remain explicit limitations; resolve them before relying on XSD validation or live scheduled ingestion. Synthetic fixtures remain appropriate for the prototype until then.

## Source identity and ordering

**Decision**: Retain each raw release bundle and its file names/checksums, source identity, source-provided release/order metadata where available, and retrieval time. Use source release metadata to establish chronology; retrieval time records when the prototype fetched the files and is not evidence of when Fimea changed a record.

**Rationale**: The reviewed public description confirms a twice-monthly release cadence and release comparisons but does not document a per-record last-modified timestamp or full file schema. Honest provenance must preserve the distinction between source chronology and local retrieval time.

**Alternatives considered**:

- **Use retrieval time as the medicine update date**: Rejected because it would falsely imply source update chronology.
- **Assume an undocumented stable record identifier or API**: Rejected because no public commitment to such an interface was found.

**Validation required before live ingestion**: Verify direct availability and reuse/automation terms; obtain and inspect the current file layout; identify source-provided release identity/order fields; confirm stable product/package identifiers; confirm which fields can support this feature's relevant-change definition. If order cannot be established, keep chronology unknown and do not create verified changes.

## Change and matching semantics

**Decision**: Compare only explicitly selected fields present in the Basic Register, and use deterministic exact identifier matching at the same product/package granularity. Do not turn an identifier mismatch, missing identifier, or multiple plausible matches into a case.

**Rationale**: Exact deterministic matching is auditable and avoids implying a clinical inference. Fimea identifies MA-number at authorization level and Nordic article number at package level; these are distinct granularities and must not be conflated.

**Alternatives considered**:

- **Fuzzy or AI-based matching**: Excluded from this feature; unclear matches must remain unmatched for human awareness rather than autonomously creating a case.
- **Treat all source-file differences as clinically relevant**: Rejected because catalog changes are not equivalent to clinical significance. Relevant fields require team/stakeholder confirmation before implementation.

**Open prerequisite**: After inspecting the selected XML and XSD, the team must select the exact catalog fields, stable key, and product/package granularity. This is a domain configuration decision; this plan deliberately does not invent clinical relevance criteria.

## Architecture and workflow boundaries

**Decision**: Model the workflow as source acquisition/orchestration, evidence-preserving snapshot and comparison, deterministic matching/case creation, and a pharmacist-facing read-only open-case view. Use n8n for the scheduled orchestration because the feature request explicitly specifies it.

**Rationale**: This structure follows the required end-to-end vertical slice while maintaining clear evidence boundaries and avoiding extra clinical workflow or deployment scope.

**Alternatives considered**:

- **Separate infrastructure services per processing stage**: Rejected for the prototype absent demonstrated scale or isolation needs.
- **Autonomous case status or clinical decisioning**: Prohibited by the project constitution.

**Technology decision**: The team selected Python/FastAPI, SQLite/SQLAlchemy, React/TypeScript/Vite, local n8n, pytest, and Vitest with React Testing Library. The exact versions, portable ORM constraints, commands, and naming conventions are recorded in [plan.md](plan.md#t001-stack-decision-record) and [quickstart.md](quickstart.md). Initial project skeletons and tool configuration exist; feature business logic remains unimplemented.
