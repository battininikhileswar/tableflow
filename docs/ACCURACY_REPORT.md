# Local extraction accuracy and AI verification scope

**AI autopilot note:** these sample conversions use the local native/OCR engine. AI orchestration is separately tested with fake provider responses in `tests/test_ai_agent.py`; no live cloud-model accuracy is measured.

Measured on 2026-10-15 using Python 3.12.14, PyMuPDF 1.26.6, tesseract 5.3.4, and English OCR in Linux. The inputs are generated synthetic tables, not an independent public benchmark. The invoice deliberately contains incorrect amounts and totals so validation has errors to detect; exact-cell accuracy compares extraction with what is actually printed, not corrected business values. Timings are one warm local run, not performance guarantees.

## Measured LOCAL extraction (not Gemini AI accuracy)

| Input | Pages | Data rows | Columns | Exact data cells | Exact-cell match | Extraction time | Review flags |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| sample-inventory.pdf | 2 | 16 | 12 | 192/192 | 100.00% | 0.09s | 0 |
| sample-scan.png | 1 | 8 | 12 | 94/96 | 97.92% | 0.85s | 3 |
| sample-scanned.pdf | 2 | 16 | 12 | 187/192 | 97.40% | 1.45s | 13 |
| sample-50-pages.pdf | 50 | 50 | 12 | 600/600 | 100.00% | 0.84s | 34 |
| sample-invoice.pdf | 1 | 4 | 12 | 48/48 | 100.00% | 0.03s | 12 |
| sample-bank-statement.pdf | 1 | 5 | 12 | 60/60 | 100.00% | 0.04s | 0 |

All six fixtures retained 12 headers and the expected row count. Digital and scanned multi-page samples use the same schema and merge into one table. Each exported data row records its source page.

**Metric:** compare every expected data-cell string with the output at the same row/column. Missing cells count as wrong; extra data cells enlarge the denominator. Headers are checked separately. Ground truth is in `samples/ground-truth.json`; the 50-page fixture cycles through its 16 rows. This metric measures exact text on these fixtures, not visual similarity, numeric equivalence, or general document accuracy.

**Observed OCR limitation:** OCR can substitute the letter O for the digit 0 in SKU identifiers. Such substitutions can have high OCR confidence. They were left unchanged to avoid inventing corrections; source text, the original download and the editor support manual repair. Review flag count is not the count of actual extraction mistakes. Duplicate rows in the 50-page fixture are intentional repeated synthetic records and are flagged as review candidates.

## Automated verification

`python -m unittest discover -s tests -v` exercises the real engine and a temporary HTTP server. The captured final output is `docs/test-results.txt`.

Coverage includes:

- Native extraction against every known source cell, plus row-page provenance.
- Scanned two-page PDF and a PNG, with 12 columns and preserved row counts.
- A 50-page PDF accepted and a 51-page PDF rejected.
- Locked PDFs, blank images, invalid input, and corrupt PDFs.
- Upload, progress polling, table editing, validation refresh, preview, JSON report and Excel download.
- Workbook reopening, source page column, freeze panes, leading-zero preservation and literal formula-like values.
- Retry, deletion, saved-history recovery across a server restart.
- Account registration/sign-in/sign-out, cookie attributes, authentication gates and account isolation.
- Plan preferences, invalid JSON requests, Excel snapshot immutability, expiry, revocation and source download.
- Invoice quantity-times-price checks, grand total checks and likely numeric-column misalignment.
- An image-free UI markup check: no image or SVG visual elements.
- Same-origin/host enforcement, unknown routes, malformed edits and static assets.

JavaScript syntax is checked with `node --check web/app.js`. Python sources are compiled with `python -m compileall -q app`. These checks do not replace browser testing.

## Verification limits

- Browser automation was unavailable under the environment's preview policy. Layout, animation timing, mobile rendering, keyboard navigation and interactive browser downloads require a final manual browser pass. No screenshot-based UI verification is claimed.
- Tests ran in Linux, not Windows or macOS. Windows launcher and Docker configurations were not executed.
- Optional OpenAI calls were not made with live credentials. Core extraction is local and independent of that optional feature.
- Telugu/Hindi OCR requires additional language packs and was not benchmarked. Skewed, handwritten, faint, irregular, nested and merged-cell documents were not comprehensively benchmarked.
- There is no claim of universal accuracy or zero errors. Confirm important values against the source, particularly identifiers, totals and scanned text.

## Manual acceptance checklist

1. Run the app, create a local account, and click Try a sample; verify the animation and page progress.
2. Scroll through the page on desktop and mobile; enable reduced motion and repeat.
3. Open the 12-column table; scroll horizontally, edit one header and one data cell. Inspect source text and download the original if needed.
4. Save, switch to Validation, compare source text for pages 1 and 2, and export the workbook.
5. Reopen in Excel or LibreOffice and compare edits and Source page values.
6. Upload the scanned sample and verify OCR handling and any flags.
7. Restart the server; verify history, reopen a document, retry a failed input, delete a completed job.
8. Create an Excel snapshot, verify download without sign-in, then revoke it and verify it becomes unavailable.
9. Switch a preview plan and confirm no billing or checkout occurs.
10. With optional credentials, request header suggestions and inspect the confirmation flow.
