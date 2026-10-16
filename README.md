# Tableflow — AI Autopilot

**Upload a document. AI reads its tables, checks them against the source, and automatically prepares Excel.**

The image-free product includes login, a personal dashboard, document history, editable review, Excel sharing and preview plans. AI autopilot is now the default extraction engine. Local OCR remains an explicitly selected alternative.

## Quick start on Windows

1. Install **Python 3.12** with the Python launcher and pip.
2. Extract the ZIP into a writable folder and double-click **start.bat**. First-run Python dependency installation requires internet access.
3. Open **http://127.0.0.1:8000** and create a local account.
4. Open **Account settings → AI engine**. Paste your Gemini API key, keep or change the model ID, and save.
5. Choose **New extraction** and drop a PDF or image. In the default AI mode, uploading starts processing immediately. Excel is generated automatically; auto-download is enabled by default. If your browser blocks the download, click **Download Excel**.

**AI needs your API key and an internet connection.** The project does not include credentials or AI credits. Provider quota, model access and usage charges depend on your account. The default model is `gemini-3.8-flash`, configurable in settings. Get/manage your key through [Google AI Studio](https://aistudio.google.com/apikey).

Tesseract is **not required for AI vision mode**. Install it only for Local OCR mode.

## Persistent AI setup

Keys entered in the UI stay in account-scoped server memory until restart. To configure the server persistently, create a local `.env` next to `run.py`:

```text
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.8-flash
```

Restart the app after changing the file. Existing process environment variables take precedence. `.env` is ignored by Git and must never be submitted with credentials. Keys are not included in job JSON, exported workbooks or API responses. Do not put keys in frontend code.

## Manual start

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
```

Linux/macOS with Python 3.12:

```bash
bash start.sh
# Open http://127.0.0.1:8000
```

Docker is also supplied with `docker compose up --build`. Configure AI in the browser after starting, or provide environment variables to the container. The Docker recipe installs English Tesseract for optional Local OCR; Docker execution was not verified in this build environment.

## What AI autopilot does

1. Validates upload signature, size, PDF encryption and page count.
2. Renders each page into a bounded-resolution image and reads embedded text when present.
3. Asks Gemini vision to transcribe all detected tables into a strict JSON schema, retaining values as text.
4. Runs a **second model request** against the original page and draft. Only a complete, schema-valid verified page is accepted.
5. Checks AI continuation references against adjacent pages and matching schemas before merging rows. Incompatible continuations stay separate with a note. Identical data rows are not blindly removed; only exact repeated header rows are removed with an audit entry.
6. Combines AI uncertainty flags with blank/duplicate/column-alignment checks and supported Decimal arithmetic/total checks.
7. Automatically creates the Excel workbook with tables, source-page references, Validation, Page text and relevant AI audit information.
8. Downloads it automatically when requested by the upload settings and permitted by the browser. Partial results and no-table results stay available for review and are not auto-downloaded as a successful conversion.

Two model passes are not independent proof of correctness. Important amounts, identifiers and uncertain cells still deserve review. The agent preserves incorrect totals that are actually printed; it flags them instead of silently replacing source values.

## Reliability and failure handling

- Maximum **50 PDF pages**, **30 MB** per upload, **40 megapixels** per input image.
- Accepted inputs: PDF, PNG, JPEG and single-frame TIFF.
- AI response shape, string values, column alignment and uncertainty coordinates are checked in Python. Truncated/blocked responses are not accepted as partial tables.
- Transient network, rate-limit and selected server errors get bounded retries. Each AI request has a 120-second timeout and at most three attempts.
- Missing keys fail before the job is queued. Credentials/model access errors stop unnecessary further requests.
- If a page’s verification fails, its extraction draft is not exported as verified data. Successful pages remain available as a clearly marked partial result.
- A document normally needs **two AI calls per page** before retries: a 50-page file can require 100 calls or more with retries. Completion time and quota needs depend on the provider and document density.
- Page images/embedded text are sent to Google Gemini only when AI mode is selected. AI credentials are sent in request headers, not URLs.
- AI settings and job ownership are account-scoped. Job files, account hashes, sessions and snapshot metadata remain in this local installation.

## Local OCR alternative

Select **Local OCR · no cloud extraction** before uploading, then click **Run local extraction**. This mode uses PyMuPDF native line/text table detection and Tesseract fallback. It does not pretend to be the AI pipeline.

For scans, install Tesseract with English data and ensure `tesseract --version` works in the terminal launching the app. Set `TESSERACT_CMD` when it is outside PATH. Telugu/Hindi need additional language packs. Digital native tables can work without Tesseract. Local OCR has its own measured synthetic benchmark; those numbers are not AI-model accuracy measurements.

## Review, sharing and plans

Completed workbooks can be downloaded immediately or reviewed and edited. Saving edits recalculates rule checks while retaining AI uncertainty as source review evidence.

**Share Excel** supports the browser’s native file-sharing menu or a download fallback. Snapshot links have 1-hour, 24-hour or 7-day expiry, remain unchanged by later edits, and can be revoked. The default server is local: its snapshot links are not internet URLs. To send a workbook to another machine, share/download the actual file. Previously downloaded copies cannot be revoked.

Starter, Pro and Team are **preview plan concepts**. Selection is saved, pricing is illustrative, and no payment or subscription is created. All implemented features are available on every preview plan. Team collaboration, public cloud hosting and billing are not implemented.

## Tests and evidence

```bash
python -m unittest discover -s tests -v
node --check web/app.js
node --check web/product.js
```

Node is optional and only used for syntax checks. Tests use temporary data. AI tests use deterministic fake provider responses and inspect the actual HTTP request contract; they do not make paid live calls and are not AI accuracy benchmarks.

Included inputs: five synthetic PDFs (inventory, scanned inventory, 50-page inventory, intentionally incorrect invoice, dummy bank statement) and one scan image, with ground truth and converted workbooks. **Included converted samples were produced by Local OCR/native extraction, not by a live cloud AI run.**

- `docs/AI_AUTOPILOT.md`: AI configuration, architecture, data handling and limits.
- `docs/ACCURACY_REPORT.md`: local extraction benchmark, separately labeled from AI contract tests.
- `docs/test-results.txt`: captured complete test output.
- `docs/PRODUCT_GUIDE.md`: login, dashboard, sharing and plans.
- `docs/DEMO_SCRIPT.md`: 2–5 minute recording guide.

Recreate inputs with `python tests/make_samples.py` and `python tests/make_business_samples.py`. Run `python tests/benchmark.py` to recreate the **local-mode** exports and benchmark.

## Submission and remaining verification

Submit the source ZIP/repository, the sample outputs, report, and a **real 2–5 minute screen recording**. The recording script is supplied; no prerecorded video is bundled. Use only dummy/public documents. The provided announcement had no actual submission URL. Deadline supplied by the organizer: **16 October 2026, 7:00 PM India time**.

All automated tests passed in Linux. **No live Gemini key was supplied, so live model access, response quality, cost, latency and hidden-PDF AI accuracy are unverified.** Browser visual/interaction tests, Windows launcher execution and Docker execution were also unavailable. Configure your key, run the dummy sample, inspect the workbook, and record that real flow before submitting.

This is a local application, not a publicly hardened SaaS service. Do not expose its loopback server publicly. Email verification/recovery, collaborative roles and online billing are not connected.

## Credits and implementation

Original orchestration, prompts, UI, validation and account/share workflows are included in source. Google Gemini provides vision extraction/verification; optional legacy OpenAI assistance suggests headers only. PyMuPDF handles PDF analysis/rendering, Pillow image handling, NumPy local grid analysis, Tesseract local OCR, openpyxl Excel output and ReportLab dummy PDFs. Python's standard library provides HTTP, SQLite, sessions and password hashing. Dependencies retain their licenses.

Provider implementation references, checked 15 October 2026:

- [Gemini structured outputs and REST request schema](https://ai.google.dev/gemini-api/docs/generate-content/structured-output)
- [Gemini image understanding](https://ai.google.dev/gemini-api/docs/generate-content/image-understanding)
- [Gemini model IDs](https://ai.google.dev/gemini-api/docs/models)
