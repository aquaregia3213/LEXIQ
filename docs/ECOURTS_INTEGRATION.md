# Indian eCourts Case Intelligence Integration Guide

## 1. Verified Official Access Method & Portal Boundaries

**Official Starting Point:** [https://services.ecourts.gov.in/ecourtindia_v6/](https://services.ecourts.gov.in/ecourtindia_v6/)  
**Managing Authority:** eCommittee, Supreme Court of India & National Informatics Centre (NIC).

### Public Access Architecture
- **Visual CAPTCHA & Session Protection:** The public eCourts services portal (`services.ecourts.gov.in`) enforces visual CAPTCHAs, dynamic CSRF/session tokens, and rate limits on all search requests (CNR search, Case Number search, Party Name search, and Cause Lists).
- **No Unauthenticated REST API:** There is **no public, self-service unauthenticated REST API** for arbitrary individual case queries on `services.ecourts.gov.in`.
- **Anti-Scraping Compliance:** In accordance with official guidelines and terms of service, LEXIQ **strictly prohibits** automated CAPTCHA bypassing, headful session spoofing, or unauthorized scraping.
- **Implemented Mechanism:** LEXIQ implements a **Portal-Assisted Workflow** and **Lawful Record Intake Architecture**:
  1. Validates and normalizes 16-character CNR numbers and case identifiers.
  2. Generates pre-populated, authorized deep links directly to `services.ecourts.gov.in`.
  3. Allows legal practitioners and users to complete visual verification on the official portal and input/paste lawful case status responses, daily orders, or cause lists into LEXIQ.
  4. Parses, extracts, and normalizes court data into strongly-typed Pydantic schemas.
  5. Uses Google Gemini (`gemini-2.5-flash`) or Langflow to synthesize procedural posture and litigation risks while strictly isolating verified court facts from AI analysis.

---

## 2. Institutional Credentials & Approvals (Automated API Clearance)

To transition from the default **Portal-Assisted** mode to **Automated Lookup Verified**, the following institutional prerequisites are required:

1. **Central Project Coordinator (CPC) Clearance:**
   - Formal application and MoU with the Central Project Coordinator (CPC) of the relevant High Court or the eCommittee of the Supreme Court of India.
   - Typically granted to government departments, institutional litigants (banks, public sector undertakings, insurance carriers), and licensed legal research institutions.
2. **MeitY API Setu Registration:**
   - Onboarding via [API Setu](https://apisetu.gov.in) (Ministry of Electronics and Information Technology, Government of India).
   - Issuance of institutional Client ID, Client Secret, and HMAC IP-whitelisted endpoint credentials.
3. **Configuration in LEXIQ:**
   Once institutional credentials are granted, configure the following in your `.env`:
   ```env
   ECOURTS_INTEGRATION_MODE=authorized_api
   ECOURTS_API_URL=https://api.apisetu.gov.in/ecourts/v1
   ECOURTS_CLIENT_ID=your_institutional_client_id
   ECOURTS_CLIENT_SECRET=your_institutional_client_secret
   ```
   *Until an authorized endpoint is configured, LEXIQ safely defaults to `portal_assisted` or `mock` mode and clearly displays `Automated lookup verified: Pending official grant`.*

---

## 3. Supported Search Fields & Identifiers

| Parameter | Format / Constraints | Description |
| :--- | :--- | :--- |
| **CNR Number** | 16-character alphanumeric (e.g. `MHAU010012342023`) | State (2) + District (2) + Court Complex (2) + Case Number (6) + Filing Year (4). |
| **State** | Name or State Code | State or Union Territory jurisdiction (e.g. Maharashtra, Delhi, Karnataka). |
| **District** | Name or District Code | Specific District Court jurisdiction. |
| **Court Complex** | Complex Name / Code | Sub-district or specific court complex. |
| **Case Type** | Standard legal abbreviation | e.g., `COMM.S.` (Commercial Suit), `ARB.P.` (Arbitration Petition), `WP` (Writ Petition), `CS` (Civil Suit). |
| **Case Number** | Numerical string | Registration sequence number. |
| **Filing Year** | 4-digit integer (`1950` - `2100`) | Year of institution or registration. |
| **Party Name** | Plain text | Petitioner / Plaintiff or Respondent / Defendant. |

---

## 4. Implemented Features Matrix

- [x] **CNR Number Format Validation:** Strict 16-character alphanumeric regex validation (`[A-Z]{2}[A-Z0-9]{4}[0-9]{10}`).
- [x] **Authorized Deep-Linking:** Automatically generates structured portal search parameters for `services.ecourts.gov.in/ecourtindia_v6/`.
- [x] **Lawful Case Record Ingestion (`POST /api/v1/ecourts/ingest`):** Robust regex parsing of pasted or uploaded case status printouts, daily orders, and cause list excerpts.
- [x] **Procedural & Risk AI Analysis (`POST /api/v1/ecourts/analyze`):** Grounds procedural posture, pending applications, and listing dates with Google Gemini.
- [x] **Fact Isolation:** Separates unmodified court facts (`official_case_facts`) from AI procedural recommendations (`ai_summary`).
- [x] **Agent / Langflow Tool (`lookup_court_case`):** Registered tool accessible to both native `AgentOrchestrator` and Langflow workflows via `/api/v1/agent/tools/execute`.
- [x] **Next.js Interactive UI (`/ecourts`):** Tabbed interface with CNR lookup, portal launcher, sample data loaders, procedural history table, and status badges.
- [x] **Mock & Offline Provider:** Deterministic provider for unit testing, offline demonstrations, and local development.

---

## 5. Unavailable Features & Upstream Blockers

| Feature | Current Status | Blocker / Reason |
| :--- | :--- | :--- |
| **Direct Headless CAPTCHA Bypass** | Prohibited | Violates NIC terms of service; subject to IP bans and legal penalties. |
| **Real-time Cause List Push Notifications** | Pending | Requires institutional webhook feed from High Court CIS (Court Information System). |
| **Automated Certified Judgment Download** | Restricted | Certified copies require advocate portal login and digital stamp verification. |

---

## 6. How to Test with Sample Data

### Method 1: Interactive Frontend UI
1. Navigate to the frontend at `http://localhost:3000`.
2. Click **eCourts India** (`⚖️`) in the sidebar navigation.
3. In **Tab 2: Lawful Record Intake**, click:
   - **Load Sample: Bombay HC Commercial Suit** (`MHAU010012342023`)
   - Or **Load Sample: Delhi HC Arbitration Petition** (`DLHC010056782022`)
4. Click **Normalize & Inspect Case Record**.
5. Click **Run AI Procedural Risk Analysis** to see verified facts and AI analysis synthesized by Google Gemini.

### Method 2: Automated Pytest Suite
Run the dedicated offline unit tests:
```powershell
python -m pytest tests/unit/test_ecourts.py -v
```

### Method 3: REST API Test via curl
```powershell
# Lookup coordinates
curl -X POST "http://localhost:8000/api/v1/ecourts/lookup" `
  -H "Content-Type: application/json" `
  -d '{"cnr_number": "MHAU010012342023"}'

# Ingest and normalize case record
curl -X POST "http://localhost:8000/api/v1/ecourts/ingest" `
  -H "Content-Type: application/json" `
  -d '{"raw_text": "Case No: COMM.S. 1234 of 2023 Status: PENDING Next Date: 12/11/2026 Injunction Granted"}'
```
