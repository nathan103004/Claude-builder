# Product Requirements Document — SantéNav

**Version:** 0.3  
**Date:** 2026-04-02  
**Status:** Draft

---

## 1. Overview

### 1.1 Purpose
SantéNav is a web application that helps Quebec residents find and book appointments at the right tier of care. The core function is clinic matchmaking and appointment booking via the RVSQ government portal. An optional AI chatbot helps users who want guidance on which tier to choose, but it is not required to use the app.

### 1.2 Goals
- Route users to the appropriate Quebec health care tier (primary care, urgent care, emergency)
- Surface available appointments from the RVSQ portal and display them in a user dashboard
- Automate appointment booking using RAMQ card information captured via phone camera
- Eliminate language as a barrier to healthcare navigation
- Give patients an optional bilingual medical summary to hand to care providers

### 1.3 Quebec Health Care Tiers
| Tier | Description | Facility type in CSV |
|---|---|---|
| **Emergency** | Life-threatening — call 911 or go to ER | CHSGS flag |
| **Urgent care** | Semi-urgent, same-day or next-day — highest slot availability | CHSGS / CLSC |
| **Primary care** | Non-urgent, routine, family doctor equivalent | CLSC flag |

> **Booking priority:** Urgent care tier is searched first as it consistently has the most appointment availability on RVSQ.

### 1.4 What We Are Not Building
- A database — all clinic and appointment data comes live from RVSQ; nothing is stored server-side beyond the session
- Clinic matching from CSV data — the CSV files in the repo are reference material only
- Medical specialty matching
- Real-time wait time data
- EHR / dossier santé Québec integration
- Payment processing, telemedicine, or prescription management

---

## 2. User Flows

### 2.1 Onboarding
```
1. Language selection (FR / EN)
2. Guest mode OR create account (email + password)
3. Text size selection (small / medium / large / extra-large)
4. Enter postal code
5. RAMQ:
   a. Scan card (camera / file upload) → OCR fills fields automatically
   b. Enter manually → form with Prénom, Nom, Numéro d'assurance maladie,
      Numéro séquentiel, Date de naissance
   c. Skip → prompted again before booking
```

### 2.2 Core Flow — Clinic Matching & Appointment Booking
```
1. User enters postal code and selects service type (or chatbot pre-selects):
   - "Consultation urgente" ← default / recommended (most availability)
   - "Consultation semi-urgente"
   - "Suivi" / "Suivi pédiatrique" / "Suivi de grossesse"
   - "Emergency" → 911 prompt immediately
2. Selenium logs into RVSQ with user's RAMQ credentials
3. Navigates to "Prendre rendez-vous dans une clinique à proximité"
4. Fills: postal code, search radius (default 50 km), time of day, service type, date
5. Clicks "Rechercher" → scrapes returned clinic cards from RVSQ
6. Clinic cards displayed in our app's dashboard (name, address, available slots)
7. Background job polls RVSQ every 5 min; new availability triggers in-app notification
8. User selects a slot → Selenium confirms booking on RVSQ
9. Confirmation number shown; pre-appointment instructions displayed
```

### 2.3 Optional — AI Symptom Chatbot
```
- Accessible via "Not sure where to go?" button; renders as a side panel
- Claude (haiku) asks up to 3 follow-up questions
- Output: recommended care tier + plain-language explanation
- If urgent symptoms detected → 911 prompt
- Pre-selects tier in main flow; user can override at any time
```

---

## 3. Functional Requirements

### FR-01: Multilingual Interface
- UI in French and English; language selected at onboarding
- Optional chatbot accepts any language input; responds in chosen UI language
- All system messages localized

### FR-02: Service Type Selection
- Dropdown or button group mapping to RVSQ service options:
  - **Consultation urgente** (default / highlighted) — issue requiring care within 24–48 h; most availability
  - **Consultation semi-urgente** — less time-sensitive
  - **Suivi / Suivi pédiatrique / Suivi de grossesse** — follow-up care
- Emergency option → 911 prompt (FR-03), bypasses RVSQ entirely
- Optional chatbot can pre-select; user can always override

### FR-03: Emergency → 911 Prompt
- Triggered by: user selects "Emergency", or chatbot detects urgent symptoms
- Full-screen card: "Call 911 now" + dispatcher script in chosen language (name, location, chief complaint, RAMQ number placeholder)
- No clinic cards shown

### FR-04: Optional AI Symptom Chatbot (Claude API)
- Collapsible side panel; app is fully usable without it
- Model: `claude-haiku-4-5`
- Max 3 follow-up turns
- Output maps directly to RVSQ service dropdown: `{ service_type: "consultation_urgente|consultation_semi_urgente|suivi|emergency", explanation: string }`

### FR-05: RAMQ Card Capture & RVSQ Login
- **Capture:** "Scan RAMQ card" → device camera (mobile) or file picker (desktop)
- **OCR extraction:** server reads Prénom, Nom, Numéro d'assurance maladie, Numéro séquentiel de la carte, Date de naissance
- **RVSQ login (Selenium):**
  1. Navigate to https://www.rvsq.gouv.qc.ca/prendrerendezvous/Principale.aspx
  2. Fill identification form with extracted data + accept consent checkbox → click "Continuer"
- RAMQ image deleted from server immediately after OCR; extracted fields held in session memory only
- If no RAMQ card available: user can manually type Prénom, Nom, Numéro d'assurance maladie, Numéro séquentiel, and Date de naissance into a form in the app; Selenium uses this to fill the RVSQ login form identically to the OCR path

### FR-06: Clinic Search via RVSQ (Selenium)
- After RVSQ login, Selenium navigates to "Prendre rendez-vous dans une clinique à proximité"
- Fills search form: postal code, radius (default 50 km), time of day (all checked), service type, date
- Clicks "Rechercher" → scrapes returned clinic cards (name, address, available slots)
- **No CSV data used for clinic matching** — RVSQ is the sole source

### FR-07: Appointment Dashboard
- Displays clinic cards scraped from RVSQ: clinic name, address, available slot times
- Background polling job re-runs RVSQ search every 5 min; pushes updates via WebSocket/SSE
- New availability → in-app notification (+ email if account holder)

### FR-08: Appointment Booking
- User selects a slot in the dashboard
- Selenium selects that slot on RVSQ and confirms booking
- Returns confirmation number to the dashboard

### FR-09: Pre-Appointment Instructions
- Shown after booking confirmation
- Tier-based generic instructions: "bring RAMQ card", "bring medication list", etc.
- Displayed in chosen UI language

### FR-10: Account System
- Optional — guest mode works throughout
- Account persists: language, text size, postal code, watched clinics, past booking confirmations
- Auth: email + password, JWT sessions
- No health or RAMQ data stored in account

---

## 4. Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-01 | Clinic cards rendered within 3 seconds of postal code entry |
| NFR-02 | WCAG 2.1 AA compliance |
| NFR-03 | Adjustable text size (4 levels), persisted in session |
| NFR-04 | Quebec Law 25 + PIPEDA compliant — no health data retained beyond session without consent |
| NFR-05 | HTTPS only; RAMQ image deleted immediately after OCR |
| NFR-06 | Mobile-first; camera capture works on iOS and Android browsers |
| NFR-07 | App fully usable without Claude API (chatbot gracefully hidden if unavailable) |
| NFR-08 | RVSQ polling uses exponential backoff on failure; respects site rate limits |

---

## 5. Data Sources

| Source | Description | Usage |
|---|---|---|
| RVSQ portal | https://www.rvsq.gouv.qc.ca/prendrerendezvous/Principale.aspx | All clinic matching, appointment availability, and booking — live only |
| `installationscsv.csv` | 1,591 Quebec facilities (MSSS reference data) | Reference only — not used for clinic matching |
| `etablissementscsv.csv` | 126 parent establishments (MSSS reference data) | Reference only |

---

## 6. Tech Stack

| Component | Technology |
|---|---|
| Frontend | Next.js (React) |
| Backend | Python FastAPI |
| Real-time updates | WebSocket (FastAPI) or Server-Sent Events |
| AI chatbot (optional) | Anthropic Claude API — `claude-haiku-4-5` |
| Appointment automation | Selenium WebDriver |
| RAMQ OCR | pytesseract or Google Vision API |
| Geolocation | Zipcodebase API |
| Maps | Leaflet.js |
| Auth | JWT + bcrypt |

---

## 7. Claude API — Chatbot Prompt

```
Model: claude-haiku-4-5

System: You are a Quebec health navigation assistant. 
        Based on the user's description, recommend one of three care tiers: 
        primary_care, urgent_care, or emergency.
        Never diagnose. Ask at most 3 follow-up questions.
        Respond in {language}. Output JSON at the end of the conversation.

Output: { "tier": "primary_care|urgent_care|emergency", "explanation": "<plain language, 1-2 sentences>" }

Immediate emergency triggers (output tier=emergency with no follow-up):
  chest pain, difficulty breathing, stroke symptoms, severe allergic reaction,
  loss of consciousness, uncontrolled bleeding, suicidal ideation
```
