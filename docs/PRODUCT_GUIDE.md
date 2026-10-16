# AI autopilot update

AI autopilot is the default extraction mode. After one-time Gemini key setup in Account settings, dropping a file starts AI extraction and verification; the workbook is generated automatically and can auto-download when the browser permits. Partial/no-table results require review. Local OCR remains an explicit alternative. AI mode sends pages/text to Google Gemini. See AI_AUTOPILOT.md.

# Tableflow product edition

This edition turns the extraction application into an image-free product experience. All product visuals use type, CSS layouts, lines, grids and native controls. The document sample PNG exists only as an OCR input fixture; it is not a decorative website image.

## Pages and flow

- **Landing:** large editorial typography, a moving text strip, a four-stage sticky scroll narrative, feature reveals and a scroll-reactive statement. Reduced-motion preferences replace pinned transitions with a readable stacked flow.
- **Account:** sign in or create a local account with email, name and password. Passwords are salted and hashed with scrypt. Server sessions use random tokens with HttpOnly/SameSite cookies. There is no email verification or password recovery service.
- **Overview:** real counts from the current account's retained documents, processed pages, review flags and Excel requests, plus recent documents and a seven-day activity chart.
- **Extract:** upload a source, follow per-page progress, review/edit cells, inspect page text, download the original source, save, export or share.
- **Document library:** account-scoped history with reopen, retry and delete actions. The original source remains available for retry and comparison.
- **Shared exports:** inspect snapshot expiry and revoke links. Deleting a document revokes its associated snapshots.
- **Settings:** current account and local storage information.
- **Plans:** Starter, Pro and Team product concepts with monthly/yearly display, saved preferences and selected-plan styling. Pricing is illustrative. There is no checkout, payment collection, subscription or implemented team collaboration. Every implemented challenge feature is available on every preview plan.

## Sharing that works in a local application

**Share file** prepares the saved Excel workbook, then uses the browser's native file-share menu if supported. Otherwise the button downloads the workbook so the user can attach it in email or another app. The application does not send messages on its own.

**Create snapshot link** exports an immutable workbook, stores a random access token's hash, and sets a 1-hour, 24-hour or 7-day expiry. Anyone with the token link can download that snapshot without an account while it remains active. The owner's dashboard can revoke the link. Previously downloaded copies cannot be withdrawn.

The default server listens only on this machine. Consequently a `127.0.0.1` snapshot link is not an internet share URL. To send a workbook to someone elsewhere, share/download the file. Public link hosting would require a separate deployment with HTTPS, configured hosts and additional production operations. This ZIP does not claim to provide that hosting.

## Validation improvements

- Recognized Quantity/Qty and Price/Unit price/Rate columns can be checked against Amount/Total/Subtotal with Decimal arithmetic and a 0.01 tolerance.
- The multiplication check is skipped when a recognized nonzero tax/discount adjustment could explain a difference.
- Recognized summary labels are compared with preceding non-summary amount rows. Nested subtotal scopes, tax rules and arbitrary report semantics are not inferred universally; flags request review.
- Predominantly numeric columns can flag an unexpected text value as possible misalignment.
- Existing blank-cell, duplicate-row, suspicious-text, long-cell, OCR-confidence and borderless-alignment flags remain.

The invoice fixture deliberately contains a wrong line amount and grand total. The bank fixture checks preservation of leading-zero identifiers; it is not evidence of a universal bank reconciliation engine.

## Release boundaries

The implementation is suitable for a local demonstration and challenge submission. It has local account isolation but no public SaaS hosting, mail delivery, password recovery, payment integration, collaborative editing, team roles or multi-tenant production operations. Legacy jobs created before account support are not automatically assigned to new accounts; re-upload them into the desired account.

UI markup, JavaScript syntax and backend flows are checked automatically. Browser visual/interaction verification was unavailable in the build environment. The short demo is supplied as a recording script; record the real app for submission.
