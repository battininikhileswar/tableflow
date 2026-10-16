# AI-first release update

Default extraction now uses Gemini vision plus a second AI verification pass, with Python schema/continuation/total checks and automatic Excel generation. AI mode requires the user’s API key. Local OCR is explicit. Included sample workbooks/accuracy metrics are local-engine results; AI contract/orchestration tests use fake responses. Live AI quality remains unverified. See AI_AUTOPILOT.md.

# Challenge deliverable mapping

| Requirement | Implementation and evidence |
| --- | --- |
| Up to 50 PDF pages | Enforced limit, included 50-page fixture, accepted/rejected boundary tests |
| 10+ columns per page | 12-column native PDFs, scanned PDF and scan image |
| OCR on scanned PDFs and images | Tesseract TSV, grid-line removal, word geometry and flagged borderless fallback |
| Automatic tables and headers | Native line/text detection or OCR alignment; visible/editable first-row header assumption |
| Continued multi-page tables | Identical normalized schemas and strategy merge; per-row page provenance; duplicate data retained and flagged rather than blindly removed |
| Wrong totals | Recognized quantity × unit price checks and summary comparisons with 0.01 tolerance; intentional-error invoice fixture |
| Empty or misaligned columns | Blank-cell flags and unexpected text in predominantly numeric columns; alignment-fallback warnings |
| Working app and complete source | Python backend, account/share storage and framework-free browser UI |
| Setup and README | Windows/POSIX launchers, pinned Python dependencies, Docker option, troubleshooting |
| At least 3 PDFs and converted Excel | Five PDFs: two-page inventory, scanned inventory, 50-page inventory, invoice with errors, dummy bank statement. Each has an exported workbook and JSON report. A PNG scan is also included. |
| Accuracy/validation report | Synthetic exact-cell measurements, captured test log and limitations |
| 2–5-minute demo | Detailed 3:40 recording script included; record the real app. No prerecorded video is bundled. |
| User-requested image-free product UI | CSS/type landing motion, sticky narrative, account page, overview dashboard, document library, source text and settings |
| Excel sharing | Native file-share/download fallback and expiring, revocable snapshots. Local token links are not public internet URLs. |
| Product plans | Starter/Pro/Team concepts, period toggle and persisted preview selection; no charges or feature blocking |

The report describes the tested scope. Hidden documents can expose unsupported layouts or OCR mistakes; universal accuracy is not claimed. Team collaboration, billing, email delivery/recovery and public SaaS deployment are not part of this local release.
