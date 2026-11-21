# Contract: CSV exports (feature 011)

Both: `text/csv; charset=utf-8`, `Content-Disposition: attachment; filename="<name>-YYYY-MM-DD.csv"`, UTF-8 with BOM, `;` separator, CRLF, header row. Values starting with `= + - @` (or a tab or carriage return) get a leading `'`.

## `GET /api/exports/review-cases.csv`

Columns: Case ID; Case type (Release/Shortage); Status; Package ID (Pakkaustunnus); Simulated record; Simulated person; Medicine (record); Change; Changed fields; Clean-up label; Prior source; Current source; Source evidence (Available/Unavailable); Case created (UTC); Last review step (UTC); Last reviewer; Last note; Review steps.

## `GET /api/exports/review-history.csv`

One row per status event, oldest first. Columns: Case ID; Package ID (Pakkaustunnus); Medicine (record); Step time (UTC); From status; To status; Reviewer ("System" for the NEW event); Note.
