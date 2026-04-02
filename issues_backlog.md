# Issues Backlog — SantéNav

Issues are grouped by epic. Each issue includes a short description and acceptance criteria.

---

## Epic 1: Project Setup

### #1 Initialize Next.js frontend
Set up Next.js app with FR/EN i18n, Tailwind CSS, and mobile-first layout scaffold.
- `next-intl` or `next-i18next` configured with FR as default locale
- Base layout renders correctly on mobile and desktop

### #2 Initialize FastAPI backend
Scaffold Python FastAPI project with CORS, `.env` config, and health-check endpoint.
- `GET /health` returns `{ status: "ok" }`
- `ANTHROPIC_API_KEY` and other secrets loaded from `.env`, never hardcoded

### #3 Configure Selenium runner
Set up headless Chromium + Selenium WebDriver as a backend service.
- Can navigate to https://www.rvsq.gouv.qc.ca/prendrerendezvous/Principale.aspx
- Runs headless in both local dev and production environments

---

## Epic 2: Onboarding

### #4 Language selection screen
First screen: FR / EN toggle. Persists choice in session (and account if logged in).
- All subsequent UI renders in chosen language
- Default: FR

### #5 Guest mode vs. account creation
After language selection, user chooses guest or creates account (email + password).
- Guest: session data only, cleared on browser close
- Account: JWT auth, bcrypt password hashing
- Both paths proceed identically after this screen

### #6 Text size selector
Onboarding step offering 4 text size options (small / medium / large / extra-large).
- Applied globally via CSS custom property
- Persisted in session; saved to account if logged in

### #7 Postal code entry
Input field for Quebec postal code with basic format validation (A1A 1A1).
- Stored in session for use in RVSQ search form
- Editable later from the dashboard

### #8 RAMQ capture — camera / file upload
"Scan RAMQ card" button opens device camera on mobile or file picker on desktop.
- Uses `<input type="file" accept="image/*" capture="environment">` for mobile camera
- Image sent to backend OCR endpoint
- Extracted fields (Prénom, Nom, Numéro d'assurance maladie, Numéro séquentiel, Date de naissance) pre-fill the RAMQ form

### #9 RAMQ capture — manual entry form
"Enter manually" option shows a form: Prénom, Nom, Numéro d'assurance maladie, Numéro séquentiel, Date de naissance.
- Same field structure as OCR output — both paths feed Selenium identically
- Basic format validation on RAMQ number field

### #10 RAMQ skip / defer
"Skip for now" option at onboarding; user is prompted again immediately before booking.
- Skip does not block access to clinic search
- Prompt shown inline before booking step, not as a blocking modal

---

## Epic 3: RAMQ OCR

### #11 Backend OCR endpoint
`POST /ocr/ramq` — accepts image, returns extracted RAMQ fields.
- Tries pytesseract first; falls back to Google Vision API if confidence is low
- Returns `{ prenom, nom, numero_assurance_maladie, numero_sequentiel, date_naissance }`
- Image deleted from server immediately after extraction
- Returns clear error if extraction fails (user falls back to manual entry)

### #12 OCR result review screen
After OCR, display extracted fields for user to confirm or correct before proceeding.
- Pre-filled from OCR output
- All fields editable
- "Confirm" saves to session memory

---

## Epic 4: RVSQ Selenium Integration

### #13 RVSQ login automation
Selenium fills the RVSQ identification form and submits.
- Inputs: Prénom, Nom, Numéro d'assurance maladie, Numéro séquentiel, Date de naissance
- Checks consent checkbox
- Clicks "Continuer"
- Returns session/cookie state for subsequent navigation
- Handles login failure (wrong credentials) and surfaces error to user

### #14 RVSQ clinic search automation
Selenium navigates to "Prendre rendez-vous dans une clinique à proximité" and submits the search form.
- Inputs: postal code, radius (default 50 km), time of day (all checked), service type, date
- Clicks "Rechercher"
- Returns raw scraped clinic card data (name, address, available slots)

### #15 Clinic card scraper
Parse RVSQ search results page into structured data.
- Each card: `{ clinic_name, address, slots: [{ date, time }] }`
- Handles "no results" state gracefully

### #16 Appointment booking automation
Selenium selects a specific slot on RVSQ and completes the booking.
- Input: slot identifier from scrape
- Confirms booking, returns confirmation number
- Handles booking failure (slot taken, session expired) and surfaces error to user

### #17 RVSQ session management
Manage RVSQ session cookies across polling cycles.
- Re-authenticate if session expires mid-poll
- One Selenium instance per active user session (not shared)

---

## Epic 5: Appointment Dashboard

### #18 Clinic cards UI
Display scraped clinic cards in the dashboard.
- Shows: clinic name, address, available slot count, list of slot times
- "Book" button per slot

### #19 Background polling job
Backend job re-runs RVSQ search every 5 minutes for active sessions.
- Uses exponential backoff on RVSQ errors (max 30 min interval)
- Stops polling when user books or closes session

### #20 Real-time dashboard updates (WebSocket / SSE)
Push new slot data to the frontend as the polling job finds updates.
- Frontend updates clinic cards without full page reload
- Connection drops gracefully if backend is unreachable

### #21 New slot notification
In-app notification when a new slot appears.
- Toast / banner in chosen language
- Email notification if user has an account and opted in

---

## Epic 6: Service Type & Emergency Flow

### #22 Service type selector UI
Button group or dropdown on main screen with RVSQ service options.
- Options: Consultation urgente (default), Consultation semi-urgente, Suivi, Suivi pédiatrique, Suivi de grossesse, Emergency
- "Consultation urgente" visually highlighted
- Selection passed to RVSQ search (FR-06)

### #23 Emergency 911 prompt
Full-screen card shown when user selects "Emergency" or chatbot returns `emergency`.
- Displays "Call 911 now" in chosen language
- Pre-written dispatcher script with placeholder fields (name, location, RAMQ number)
- No clinic cards or RVSQ interaction triggered

---

## Epic 7: Optional AI Chatbot

### #24 Chatbot UI panel
Collapsible side panel accessible via "Not sure where to go?" button.
- Does not block main flow
- Hidden / disabled gracefully if Claude API is unavailable

### #25 Chatbot backend endpoint
`POST /chat` — streams Claude haiku-4-5 response, returns service type recommendation.
- System prompt: Quebec health navigation assistant, max 3 follow-up turns, output JSON
- Output: `{ service_type, explanation }`
- Emergency triggers bypass follow-up questions and return `emergency` immediately

### #26 Chatbot → service type pre-selection
Chatbot output pre-selects the service type dropdown in the main flow.
- User can override at any time
- If chatbot returns `emergency`, 911 prompt (issue #23) is shown immediately

---

## Epic 8: Pre-Appointment Instructions

### #27 Post-booking instructions screen
After booking confirmation, display tier-appropriate instructions.
- Content keyed by service type (e.g., urgent: "bring RAMQ card and medication list")
- Displayed in chosen UI language
- Dismissable; confirmation number shown above instructions

---

## Epic 9: Account System

### #28 Account registration & login
Email + password account creation and login.
- bcrypt password hashing
- JWT session tokens
- No health or RAMQ data stored in account

### #29 Account persistence
Persist user preferences to account: language, text size, postal code, past booking confirmation numbers.
- Loaded on login, applied immediately
- No RAMQ fields stored

---

## Epic 10: Accessibility & Polish

### #30 WCAG 2.1 AA audit
Audit all screens for keyboard navigation, contrast ratios, focus management, and ARIA labels.
- Run axe or Lighthouse accessibility audit
- All critical violations resolved before launch

### #31 FR/EN copy review
Review all UI strings in both languages with a native French speaker.
- All RVSQ service type labels match the portal exactly (e.g., "Consultation urgente")
- Emergency instructions reviewed for clarity

### #32 Mobile camera flow QA
Test RAMQ camera capture on iOS Safari and Android Chrome.
- Camera opens correctly on both platforms
- OCR accuracy tested with sample RAMQ card images

---

## Epic 11: Infrastructure & Security

### #33 HTTPS and environment config
Ensure all traffic is HTTPS; all secrets in environment variables.
- No API keys in source code or git history
- `.env.example` committed with placeholder values

### #34 RAMQ data handling audit
Verify RAMQ image is deleted immediately after OCR and no fields are logged or persisted beyond session.
- Code review of OCR endpoint and session storage
- No RAMQ fields written to any log file
