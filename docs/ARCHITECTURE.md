# AI-first release update

The default job mode is now AI autopilot, documented in AI_AUTOPILOT.md. It renders pages, requests vision extraction and a second AI verification pass, validates/merges structured output, and automatically writes Excel. The native/OCR decisions below describe the **explicit local alternative**, not the default AI path. Authenticated `/api/ai/settings` supplies key/model setup; credentials are never stored in job JSON.

# Architecture

Tableflow is a local Python application with account-scoped workspaces with a browser frontend. Its extraction agent inspects each page, chooses a strategy, validates the result, and retains source evidence for review. It does not call a cloud LLM to reconstruct arbitrary document values.

## Agent decisions

1. Verify upload signature, byte limit and job capacity; persist the source.
2. Inspect PDF encryption and page count, or decode a supported image.
3. For text-rich PDF pages, try native line-based table recognition, then text-based alignment.
4. If no native table is found, render the page at bounded resolution and OCR it. Image uploads go directly to OCR.
5. For a strongly ruled page, detect grid boundaries, remove ruling lines for OCR, and map word centers back into cells. Otherwise infer rows and columns from whitespace and flag alignment for review.
6. Assume the first detected row is the header, retaining the assumption and original row in JSON. Normalize empty and duplicate labels. User review can correct labels.
7. Merge only identical case-normalized schemas with the same strategy. Retain a page reference for each data row. Different strategies or schemas stay in separate tables.
8. Validate cells and rows, retain per-page errors and raw text, then mark the job ready for review. Page failures do not discard successful pages.
9. Optionally ask a cloud LLM for header-label suggestions; validate its response and require the user to apply it. Table values are unchanged.
10. Save edits, run validation again, and build Excel sheets with literal source text and page references.

The agent's recovery is bounded: native → text → OCR; individual page exceptions become visible notes; failed jobs can be retried. It does not repeatedly call tools or hide failed pages behind a success score.

## Runtime

- Python standard-library threaded HTTP server bound to loopback by default.
- One extraction worker thread, with at most eight queued/processing jobs. PDF analysis and source rendering share a lock to avoid concurrent PyMuPDF table-state access.
- `data/<random-job-id>/source` and atomic `job.json` writes; no database setup.
- On restart, in-progress jobs become failed with a retry message; completed jobs remain available.
- Frontend uses native browser APIs, no CDN, no framework, no build, and no telemetry. Product visuals use CSS/type only.
- SQLite stores local accounts, scrypt password hashes, hashed session tokens, plan preferences and hashed share tokens. Documents are filtered by account on every private API access.
- Shared Excel snapshots are immutable files with random bearer tokens, expiry and revocation. The public token route exposes only the snapshot. Deleting a source job revokes associated shares.
- Reduced-motion support, semantic controls, scroll reveals, illustrated document flow, source review and 100-row table pagination.

## Job model

```json
{
  "id": "random 32-character hexadecimal identifier",
  "filename": "source.pdf",
  "status": "queued | processing | complete | failed",
  "progress": 100,
  "result": {
    "filename": "source.pdf",
    "page_count": 2,
    "tables": [{
      "id": "table-1",
      "headers": ["SKU", "Quantity"],
      "rows": [["00123", "5"]],
      "row_pages": [1],
      "pages": [1, 2],
      "method": "pdf-native",
      "confidence": [],
      "header_assumption": "First detected row; editable in review"
    }],
    "pages": [{"page": 1, "method": "pdf-native", "text": "source text", "error": null}],
    "issues": [],
    "notes": []
  }
}
```

Data-cell indices in validation JSON are zero-based. The UI and Excel Validation sheet display one-based positions. OCR confidence is mean Tesseract word confidence per cell; `-1` indicates no recognized words. PDF-native cells have no OCR confidence. No confidence value is presented as measured accuracy.

## HTTP API

| Method | Route | Behavior |
| --- | --- | --- |
| POST | `/api/auth/register`, `/api/auth/login` | Create a local account or begin a cookie session |
| GET | `/api/auth/me` | Current account, or null |
| POST | `/api/auth/logout` | Revoke the current session |
| PUT | `/api/plan` | Save a Starter/Pro/Team preview preference; no billing |
| GET | `/api/shares` | Account-owned snapshot metadata, without token secrets |
| DELETE | `/api/shares/{id}` | Revoke a snapshot owned by this account |
| POST | `/api/jobs/{id}/share` | Export a snapshot with a 1/24/168-hour expiry |
| GET | `/share/{token}` | Download an active snapshot without sign-in |
| GET | `/api/jobs/{id}/source` | Download the original source document |
| GET | `/api/health` | OCR and optional AI availability |
| GET | `/api/jobs` | Document history without extraction payloads |
| POST | `/api/jobs?name=...&language=eng&ocr=0` | Raw document bytes; responds 202 with job ID |
| GET | `/api/jobs/{id}` | Job status, progress, result and error |
| PUT | `/api/jobs/{id}/tables` | JSON `{tables: [...]}` with matching IDs/shapes; save and validate |
| POST | `/api/jobs/{id}/retry` | Create a fresh job from the retained source |
| DELETE | `/api/jobs/{id}` | Delete a terminal job and all local artifacts |
| GET | `/api/jobs/{id}/page/{number}.png` | Bounded-resolution source preview |
| GET | `/api/jobs/{id}/export` | Excel workbook download |
| GET | `/api/jobs/{id}/report` | JSON extraction and validation report |
| POST | `/api/jobs/{id}/suggest` | Optional LLM request with `{table: "table-1"}` |

The UI sends raw bytes to avoid multipart parsing dependencies. Editing changes cell/header text, not row or column counts. Export requires a completed job and always reflects the server's saved data. The UI saves dirty edits before download.

## Reliability and scope

Uploads are checked by signature and then parsed by the document/image libraries. The server returns specific validation errors and limits page/image/render sizes. OCR subprocesses have a 100-second timeout per page. The app sets same-origin/host checks, a restrictive content policy and literal Excel string cells. It provides local accounts, but does not provide public hosting, email verification/recovery, billing, team collaboration, universal business-rule reconciliation, arbitrary-layout guarantees or production multi-tenant hardening. API endpoints for jobs, shares and plan preferences require a valid local account session; health, sample files, static assets and token-share downloads are public on the local server.

The optional LLM key remains in the server environment. Headers and up to three rows leave the device only after the user requests suggestions. Network/model failures are returned to the dialog; source data and current headers remain available.


## Product motion and accessibility

The landing page uses a four-stage sticky scroll sequence with CSS card transforms, a text marquee, scroll reveals and a progress line. Updates run through requestAnimationFrame; inactive workflow cards are hidden from assistive technology. Reduced-motion preferences stack all four cards and disable animation. Dashboard metrics and activity derive from actual retained account jobs, not sample statistics. The interface has keyboard-focus styles, labeled forms and editable grid cells. Browser QA is still required; these implementation choices are not evidence of audited accessibility compliance.
