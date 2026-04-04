# Security Policy

## RAMQ Data Handling

SantéNav processes Quebec health insurance card (RAMQ) data strictly in memory:

- **OCR**: The uploaded card image is written to a system temp file, processed by
  pytesseract, and deleted in a `finally` block (`routers/ocr.py`). Extracted fields
  are returned to the browser only — never logged or stored.
- **Session credentials**: RAMQ credentials used for RVSQ portal login are held in
  a RAM-only dict (`rvsq/session_store.py`) with a 30-minute inactivity TTL. All
  sessions are purged on server shutdown.
- **No database writes**: No RAMQ fields are written to `users.json` or any other
  persistent storage.

## Reporting a Vulnerability

Please open a private GitHub Security Advisory (Security → Advisories → New draft advisory).
