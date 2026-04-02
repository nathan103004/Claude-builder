# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

SantéNav — a Quebec health navigation web app. Users enter a postal code, select a care tier (primary / urgent / emergency), and the app finds nearby clinics from the MSSS data, then scrapes the RVSQ government portal for available appointment slots. An optional Claude-powered chatbot helps users choose the right tier. See `PRD.md` for full requirements and `README.md` for the executive summary.

## Planned Architecture

**Frontend:** Next.js (React) — multilingual UI (FR/EN), real-time appointment dashboard via WebSocket/SSE, device camera access for RAMQ card capture.

**Backend:** Python FastAPI — REST + WebSocket endpoints, Selenium orchestration, OCR processing, and Claude API calls for the optional chatbot.

**No application database.** All clinic and appointment data comes live from the RVSQ portal. The only persistent data is optional user accounts (language, postal code, past booking confirmations).

## RVSQ Portal Flow (Selenium)

All clinic matching and booking goes through https://www.rvsq.gouv.qc.ca/prendrerendezvous/Principale.aspx. The CSV files in the repo are reference data only and are **not used for clinic matching**.

**Step 1 — Login.** Selenium fills the identification form:
- Prénom, Nom
- Numéro d'assurance maladie (RAMQ number)
- Numéro séquentiel de la carte d'assurance maladie
- Date de naissance (jour / mois / année)
- Accepts consent checkbox → clicks "Continuer"

**Step 2 — Clinic search ("Prendre rendez-vous dans une clinique à proximité").** Selenium fills:
- Date (À partir de cette date)
- Votre code postal
- Périmètre de recherche (km) — default 50 km
- Moment de la journée (Avant-midi / Après-midi / Soir)
- Service dropdown — maps from our UI tier selection:
  - "Consultation urgente" → urgent care (prioritized, most availability)
  - "Consultation semi-urgente" → semi-urgent
  - "Suivi" / "Suivi pédiatrique" / "Suivi de grossesse" → primary/follow-up care
- Clicks "Rechercher" → scrapes resulting clinic cards

**Step 3 — Display & poll.** Scraped clinic cards are pushed to the user dashboard. A background job re-runs the search every 5 minutes and pushes updates via WebSocket/SSE.

**Step 4 — Booking.** User selects a slot → Selenium completes the booking on RVSQ → returns confirmation number to the dashboard.

## RAMQ Card Capture

User taps "Scan RAMQ card" → device camera opens (mobile) or file picker (desktop). Server-side OCR (pytesseract or Google Vision) extracts: card number, sequential number, first name, last name, date of birth. Image is deleted immediately after extraction; data lives in session memory only and is used to pre-fill the RVSQ login form.

## Optional AI Chatbot

Claude API (`claude-haiku-4-5`) powers a collapsible side panel that helps users choose a service type. It outputs `{ tier, explanation }` and pre-selects the RVSQ service dropdown in the main flow. The app must be fully functional without it.

## Key External Dependencies

- Anthropic Claude API (`ANTHROPIC_API_KEY`) — optional chatbot only
- Zipcodebase API (`ZIPCODEBASE_API_KEY`) — postal code → coordinates
- Selenium WebDriver + a compatible browser driver (Chromium recommended)
- pytesseract or Google Vision API — RAMQ OCR
