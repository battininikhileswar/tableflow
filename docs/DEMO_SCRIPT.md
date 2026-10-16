# AI autopilot recording instructions

Before following the product walkthrough below, configure a real Gemini key in Account settings and run a dummy document in the default AI autopilot mode. Show the “AI is reading” and “AI is verifying” stages, then the automatically generated Excel workbook. The browser may require a click to download. Show the provider/model metadata in the JSON report or workbook. Do not use the included local sample outputs as evidence of a live AI conversion. AI credentials, live model response quality, usage costs and browser recording were not tested in this build.

The underlying product screens in the walkthrough remain, but local-mode text below should be described only when demonstrating the explicit Local OCR option. No prerecorded video is bundled.

# 3-minute 40-second demonstration

This is a screen-recording guide, not a prerecorded video. Start the app before recording. Use dummy documents only. Keep the browser around 1440 × 900 where possible. Create a throwaway local account before recording if you want to avoid typing a password on camera.

| Time | Screen/action | What to explain |
| --- | --- | --- |
| 0:00–0:20 | Show the landing title, scroll into the pinned four-step workflow. | “Tableflow converts PDFs and scanned tables into structured Excel. The product interface uses typography, CSS and motion without decorative images.” |
| 0:20–0:40 | Show sign-in or create-account page, then enter the dashboard. | “Accounts are stored locally with hashed passwords. The dashboard shows my own saved documents and actual extraction activity.” |
| 0:40–1:00 | Choose a new extraction and run the included sample. | “This PDF spans two pages and twelve columns. The agent selects native PDF analysis or OCR for each page and records processing progress.” |
| 1:00–1:25 | Show the merged table, horizontal scrolling, source text, and original-download control. Edit one cell, then save. | “Matching table schemas merge across pages. Each row retains source-page provenance. I can inspect the source and correct cells before export.” |
| 1:25–1:50 | Upload `sample-invoice.pdf`; open Validation. | “This dummy invoice intentionally has a wrong line amount and wrong grand total. Quantity-times-price and summary checks flag them for review. The system does not silently replace source values.” |
| 1:50–2:10 | Download Excel and open the workbook. Show the table and Validation sheet. | “The workbook keeps the structured data, review flags and source text. Leading-zero identifiers and formula-like source values remain literal text.” |
| 2:10–2:35 | Open Share Excel. Create a 1-hour snapshot link, copy it, and open it in another tab to download. Then revoke it in Shared exports. | “Sharing creates a saved Excel snapshot with expiry and revocation. Later edits do not change that copy. These local links require this server; for another device I share or attach the workbook file.” |
| 2:35–2:55 | Upload `sample-scanned.pdf` and show the extracted 12-column result. | “The scanned PDF uses OCR and grid geometry. OCR can confuse similar characters, so source review is part of the workflow. Confidence is not the same as accuracy.” |
| 2:55–3:15 | Open Plans & usage, toggle yearly/monthly, select a preview plan. | “The product includes Starter, Pro and Team concepts. Pricing is illustrative, no payment is taken, and all implemented features stay available for the challenge.” |
| 3:15–3:40 | Show the document library and the accuracy report/test results. | “The source includes five sample PDFs, converted workbooks, reproducible tests and a transparent accuracy report. The agent accepts up to fifty pages, and interrupted or failed documents can be retried.” |

If time is short, spend more of the recording on extraction, validation and Excel output than on product plans. For the 50-page requirement, open the included `sample-50-pages.pdf` and show a completed extraction if the recording remains under five minutes.

Optional AI header suggestions require your own API credentials and explicitly send headers plus three rows to the configured service. They are not required for the OCR demonstration.

Before submission, record the real browser flow, verify the downloaded workbook opens, and include the source ZIP or repository link. The announcement did not supply an actual submission URL; obtain it from the organizer. Announced deadline: **16 October 2026, 7:00 PM India time**.
