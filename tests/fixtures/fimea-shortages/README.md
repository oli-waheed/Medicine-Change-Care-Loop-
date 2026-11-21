# Synthetic Fimea shortage files (feature 006)

Fictional files in the format of Fimea's open-data `Shortages.txt`
(semicolon-separated, double-quoted, CRLF, header
`NordicArticleNumber;Valid;UnavailableFrom;EndingDate;DateOfTheNotification;Updated;Company`).
The VNRs `SIM-VNR-…` match the synthetic Basic Register fixtures; `SIM-VNR-900`
matches no package on purpose. These are not Fimea data.

- `shortages.txt`: three shortages (two `K`, one `E`).
- `shortages-later.txt`: a later download with changed dates and one shortage gone.
- `shortages-wrong-columns.txt`: an unexpected header, which must be rejected.
