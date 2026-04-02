# SantéNav — Quebec Health Navigation Assistant

> Find the right clinic, fast. AI-powered symptom triage and clinic matchmaking for Quebec residents.

---

## Problem

Quebec's health system is fragmented and hard to navigate. Residents struggle to know which clinic handles their condition, whether it accepts walk-ins, how far it is, and how to book an appointment — especially in a second language or during a health emergency.

---

## What It Does

SantéNav guides users from "I don't feel well" to a booked appointment in minutes:

1. **Symptom interview** — Chat in any language; Claude asks follow-up questions to build a clinical picture
2. **Urgency detection** — If symptoms are serious, the app stops and tells you exactly what to say when you call 911
3. **Medical summary PDF** — A clean bilingual (EN/FR) document you can hand to a nurse or doctor
4. **Clinic matchmaking** — Shows the 3–5 closest suitable clinics ranked by availability, distance, and cost
5. **Appointment booking** — Upload your RAMQ card photo; the app books your appointment automatically via Selenium
6. **Pre-appointment instructions** — What to do (and not do) before you arrive

---

## Key Features

- Multilingual chat input (any language → EN/FR output for medical staff)
- AI-driven triage using Claude API
- 911 emergency prompt with responder script
- Bilingual PDF symptom summary
- Clinic cards: public/private, accessibility, walk-in vs. appointment, distance, booking link
- RAMQ card OCR + automated booking
- Guest mode (no account required)
- Accessible UI: adjustable text size, WCAG 2.1 AA compliant

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React / Next.js |
| Backend | Python FastAPI |
| AI | Claude API (claude-sonnet-4-6 / claude-haiku-4-5) |
| Clinic data | MSSS CSV exports + live MSSS endpoint |
| Geolocation | Zipcodebase API (postal code → coordinates, distance) |
| Booking automation | Selenium WebDriver |
| PDF generation | reportlab / pdfkit |
| Maps | Leaflet.js |
| Auth | Optional — JWT, guest mode supported |

---

## Data Sources

- `etablissementscsv.csv` — 126 Quebec health establishments (MSSS, updated 2026-03-23)
- `installationscsv.csv` — 1,591 individual facilities with coordinates and service flags (MSSS, updated 2026-03-23)
- MSSS live directory: https://m02.pub.msss.rtss.qc.ca/M02ListeEtab.asp

---

## Quick Start

```bash
# Clone the repo
git clone <repo-url>
cd "Claude builder"

# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

> Requires: `ANTHROPIC_API_KEY`, `ZIPCODEBASE_API_KEY` in `.env`

---

## Privacy

User health data is never stored beyond the session unless the user creates an account. The app complies with Quebec's Law 25 (Act respecting the protection of personal information in the private sector) and PIPEDA.
