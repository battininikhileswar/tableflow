# AI autopilot

The default workflow is now AI-driven document reading and verification. Excel packaging, cryptography and arithmetic are deterministic software operations; a model is not used to write arbitrary code or execute document instructions.

## Modules

- `app/ai_agent.py`: schema, vision API client, bounded retries, extraction and verification passes, continuation checks, uncertainty and audit.
- `app/ai_config.py`: optional non-executing `.env` loader, environment key, account-scoped in-memory settings, redacted status.
- `app/server.py`: authenticated settings API, AI/local dispatch, job state and automatic workbook creation.
- `app/engine.py`: shared rule validation and safe Excel export, plus the explicit local extraction alternative.

## API

| Endpoint | Meaning |
| --- | --- |
| `GET /api/ai/settings` | Authenticated configured/model/provider status; never returns key |
| `PUT /api/ai/settings` | Accepts `api_key`, `model`; keys remain in account-scoped RAM |
| `PUT /api/ai/settings` with `{"clear":true}` | Clears the personal key/model preference; an environment key can remain |
| `POST /api/jobs?mode=ai&name=...` | AI is default; queues only after key configuration |
| `POST /api/jobs?mode=local&name=...` | Explicit local pipeline |

Job JSON stores mode and result metadata, never credentials. The queued worker receives a settings snapshot in memory. After process restart, interrupted work is marked failed; retry requires available credentials again. Saved complete jobs and Excel results survive restarts.

## Verification boundaries

The second pass receives both the page image and the draft, and is instructed to check source evidence. It is another request to the configured model, not an independent ground-truth oracle. AI can repeat a mistake, miss rows, or infer incorrect structure in both passes. JSON validity and matching column counts cannot prove transcription accuracy.

A page draft is rejected if its verification fails. If some pages succeeded, the workbook explicitly reports failed pages and partial status. If every page failed, the job fails. AI output that reports no tables stays available for review with a clear note; it is not advertised as a successful structured conversion.

Continuation is proposed by AI but accepted only for an existing adjacent-page table with exactly matching normalized headers/order. Schema mismatches remain separate. Row duplicates are flagged, not silently removed. Printed incorrect totals remain source values; numeric checks produce review flags.

The JSON report retains changed verification drafts and verified versions as audit evidence. The workbook's AI audit summarizes those changes. AI uncertainties remain source evidence after manual edits. No output reports a fabricated accuracy score.

## Data and cost

AI mode sends rendered pages and available embedded text to Google Gemini. Verification also sends the extracted draft and preceding-page schemas. Sensitive/private records should not be used for the challenge. Provider terms, quota and pricing apply to the account used; no credits or unlimited usage are included.

The client uses the documented `generateContent` REST endpoint with inline PNG data, a system instruction and a JSON response schema. The API is documented as legacy but supported. The default model was selected from Google's current model documentation; the model ID remains configurable. There are normally two calls per page and bounded retries. Do not assume a 50-page file completes in seconds or fits a small quota.

## Evidence in this build

- Contract tests construct and inspect a real-shaped REST request using fake network responses.
- Tests cover invalid JSON shapes, misaligned columns, numeric JSON values, truncated responses, rate limits, credential failures, verification rejection, page continuation, partial results, uncertainty, totals and workbook export.
- A worker orchestration test confirms an AI-mode job automatically writes Excel and does not persist its key in job JSON.
- Existing HTTP/account/share/local extraction tests remain.
- Live Gemini requests and live AI accuracy were not tested without credentials. Included sample Excel files and accuracy percentages come from the local engine and must not be presented as Gemini results.

Before the demonstration: configure a key, run `sample-invoice.pdf` in AI mode, check `result.ai.provider/model/requests`, open the exported workbook and verify its source values and flags. Record this real run, including visible progress and final workbook.
