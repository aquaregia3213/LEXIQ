# LEXIQ Production Deployment Guide

A reliable, student-friendly step-by-step deployment guide for **LEXIQ: Agentic AI-Powered Legal Contract Intelligence Platform**.

---

## 1. Target Architecture & Free-Tier Budget

This architecture is optimized for high reliability, zero operational complexity, and **$0/month** total cost on standard student/hobby tiers.

```mermaid
graph LR
    User([User Browser]) -->|HTTPS| Vercel[Vercel<br/>Next.js 15 Frontend<br/>Free Hobby Tier]
    Vercel -->|REST API calls| Render[Render Web Service<br/>FastAPI Backend<br/>Free / Starter Tier]
    Render -->|SQL & pgvector queries| Neon[(Neon / Supabase<br/>Managed PostgreSQL 16<br/>Free Tier with pgvector)]
    Render -->|API Requests| Gemini[Google AI Studio<br/>Gemini 2.5 Flash & Embeddings<br/>Free Tier]
    Render -.->|Optional Orchestration| Langflow[Langflow Service<br/>Container / Cloud]
```

### Estimated Monthly Cost Breakdown

| Service | Hosting Provider | Plan | Monthly Cost | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Frontend** | **Vercel** | Hobby | **$0.00** | Automatic CI/CD on git push, global CDN edge network, free SSL. |
| **Backend API** | **Render** | Free | **$0.00** | Spins down after 15 min inactivity; wakes automatically on HTTP request. |
| **Database** | **Neon** or **Supabase** | Free Tier | **$0.00** | Dedicated PostgreSQL 16 with pre-installed `pgvector`. |
| **AI LLM & Embeddings** | **Google AI Studio** | Free Tier | **$0.00** | 15 RPM, 1,500 RPD on `gemini-2.5-flash`; free embeddings. |
| **Total** | | | **$0.00 / month** | 100% free for student evaluation, coursework, and portfolio demos. |

---

## 2. Prerequisites Checklist

Before beginning, ensure you have:
- [x] A GitHub account with the LEXIQ repository pushed.
- [x] A free [Vercel](https://vercel.com) account (sign in with GitHub).
- [x] A free [Render](https://render.com) account (sign in with GitHub).
- [x] A free [Neon](https://neon.tech) or [Supabase](https://supabase.com) account for managed PostgreSQL.
- [x] A Google Gemini API key from [Google AI Studio](https://aistudio.google.com/).

---

## 3. Step 1: Setup Managed PostgreSQL with pgvector (5 minutes)

We recommend **Neon** or **Supabase** because both provide managed PostgreSQL 16 with `pgvector` enabled out of the box.

### Option A: Using Neon (Recommended)
1. Sign in to [console.neon.tech](https://console.neon.tech).
2. Click **Create Project** $\rightarrow$ Name it `lexiq-db` $\rightarrow$ Select Region closest to you (e.g. `US East` or `Frankfurt`).
3. In the Neon dashboard, click on **SQL Editor** and run:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
4. On the project dashboard, copy the **Connection string** (select **Pooled connection** or direct connection). It looks like:
   ```text
   postgresql://lexiq_owner:AbC123XyZ@ep-cool-dawn-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
   *Save this connection string for Step 2.*

### Option B: Using Supabase
1. Sign in to [supabase.com](https://supabase.com) $\rightarrow$ **New Project**.
2. Go to **Database** $\rightarrow$ **Extensions** $\rightarrow$ search `vector` $\rightarrow$ Toggle **Enable**.
3. Under **Project Settings** $\rightarrow$ **Database**, copy the **URI connection string**.

---

## 4. Step 2: Deploy FastAPI Backend on Render (10 minutes)

### 2.1 Create New Web Service
1. Sign in to [dashboard.render.com](https://dashboard.render.com).
2. Click **New +** $\rightarrow$ Select **Web Service**.
3. Select **Build and deploy from a Git repository** $\rightarrow$ Choose your `LEXIQ` repository.

### 2.2 Configure Build & Runtime Settings
Fill in the following fields:

| Setting | Value |
| :--- | :--- |
| **Name** | `lexiq-backend` (or a name of your choice) |
| **Region** | Same or close to your database region (e.g. `Oregon` or `Ohio`) |
| **Branch** | `main` |
| **Root Directory** | *(leave empty — root of repo)* |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt && python database/init_db.py` |
| **Start Command** | `gunicorn -w 2 -k uvicorn.workers.UvicornWorker backend.app.main:app -b 0.0.0.0:$PORT` |
| **Plan Type** | `Free` |

> **Note on Build Command:** `python database/init_db.py` automatically runs before the server boots. It connects to PostgreSQL, creates all tables, and configures pgvector indexes.

### 2.3 Configure Backend Environment Variables
Under the **Environment Variables** section on Render, add the following key-value pairs:

```env
ENVIRONMENT=production
DATABASE_URL=postgresql://your_user:your_password@your_neon_host.neon.tech/neondb?sslmode=require
AI_PROVIDER=gemini
GEMINI_API_KEY=your_real_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
GEMINI_EMBEDDING_DIMENSION=768
AGENT_ORCHESTRATOR=native
LANGFLOW_FALLBACK_TO_NATIVE=true
LEXIQ_INTERNAL_API_KEY=generate_a_random_32_char_secret_here
CORS_ORIGINS=http://localhost:3000
```
*(We will update `CORS_ORIGINS` with your actual Vercel domain in Step 4).*

### 2.4 Set Health Check Path
Under **Advanced Settings**:
- **Health Check Path**: `/health`

Click **Create Web Service**. Render will now clone the repo, install dependencies, run migrations, and start Uvicorn. Once deployed, note your public URL:
`https://lexiq-backend.onrender.com`

---

## 5. Step 3: Deploy Next.js Frontend on Vercel (5 minutes)

### 3.1 Import Project
1. Go to [vercel.com/new](https://vercel.com/new).
2. Under **Import Git Repository**, choose your `LEXIQ` repo.

### 3.2 Configure Build & Root Directory
- **Project Name:** `lexiq-frontend`
- **Framework Preset:** `Next.js` (automatically detected)
- **Root Directory:** Click **Edit** $\rightarrow$ select `frontend` $\rightarrow$ click **Continue**.

### 3.3 Set Frontend Environment Variables
Add only the public backend URL (**never put secrets or database URLs here**):

| Key | Value |
| :--- | :--- |
| `NEXT_PUBLIC_API_BASE_URL` | `https://lexiq-backend.onrender.com` |

*(Replace with your actual Render URL from Step 2).*

### 3.4 Deploy
Click **Deploy**. Vercel will build the Next.js production bundle and publish your site at:
`https://lexiq-frontend.vercel.app`

---

## 6. Step 4: Wire CORS & Final Verification

1. Go back to your **Render Dashboard** $\rightarrow$ Select `lexiq-backend` $\rightarrow$ **Environment**.
2. Update `CORS_ORIGINS` to include your new Vercel domain:
   ```env
   CORS_ORIGINS=https://lexiq-frontend.vercel.app,http://localhost:3000
   ```
3. Click **Save Changes**. Render will automatically restart with the new CORS policy.

---

## 7. Operational Health Checks & Diagnostics

Verify your deployment using these built-in diagnostic endpoints:

### 1. Liveness Probe: `GET /health`
```bash
curl https://lexiq-backend.onrender.com/health
```
**Expected Response:**
```json
{
  "status": "ok",
  "service": "Legal AI Contract Intelligence API",
  "version": "1.0.0",
  "environment": "production",
  "database": {
    "status": "connected",
    "dialect": "postgresql"
  },
  "ai_provider": {
    "provider": "gemini",
    "llm_model": "gemini-2.5-flash",
    "embedding_dimension": 768,
    "is_configured": true
  }
}
```

### 2. Readiness Probe: `GET /health/ready`
```bash
curl https://lexiq-backend.onrender.com/health/ready
```
Returns `200 OK` with `{"status": "ready"}` when PostgreSQL is reachable. Returns `503 Service Unavailable` if the database is offline.

### 3. Sanitized Config Diagnostic: `GET /health/config`
```bash
curl https://lexiq-backend.onrender.com/health/config
```
Inspects active runtime parameters with all API keys and database credentials strictly masked.

---

## 8. Persistent Document Storage Considerations

### How Document Data is Stored
When a user uploads a contract:
1. **Text, Chunks, Embeddings & Clauses:** Extracted and permanently saved into PostgreSQL tables (`chunks`, `clauses`, `entities`, `obligations`). **This data survives all server restarts and redeploys.**
2. **Raw PDF Files:** Saved to `uploads/contracts/`. On Render's free tier, the local container disk is ephemeral (wiped on restart).
   - If a student relies on the free tier, contract search, RAG, and AI analysis continue to function seamlessly because chunk embeddings reside in PostgreSQL.
   - For 100% persistent raw PDF downloads across container restarts, you can attach a persistent disk on Render:
     - In Render dashboard $\rightarrow$ **Disks** $\rightarrow$ **Add Disk** $\rightarrow$ Name: `uploads-data`, Mount Path: `/var/data/uploads`, Size: `1 GB`.
     - Update environment variable: `UPLOAD_DIR=/var/data/uploads`.

---

## 9. Rollback & Maintenance Procedures

### Frontend Rollback on Vercel
1. Open your project on Vercel $\rightarrow$ Go to the **Deployments** tab.
2. Find the last known working deployment.
3. Click the three dots (`...`) $\rightarrow$ Select **Instant Rollback**.
4. Traffic is shifted to the previous build in under 5 seconds.

### Backend Rollback on Render
1. Open `lexiq-backend` on Render $\rightarrow$ Click **Events** or **Deploys**.
2. Select the previous successful deploy $\rightarrow$ Click **Rollback to this deploy**.

### Database Reset or Clean Remigration
If you ever need to recreate or clear tables:
```bash
# Connect to your remote PostgreSQL database and re-run migration:
python database/init_db.py
```
*(On Render, you can trigger this from the **Shell** tab in the dashboard).*

---

## 10. Common Deployment Gotchas & Solutions

| Symptom | Cause | Solution |
| :--- | :--- | :--- |
| **CORS Network Error in Browser** | `CORS_ORIGINS` in Render doesn't match Vercel URL. | Update `CORS_ORIGINS` on Render to match `https://lexiq-frontend.vercel.app` (do not include a trailing slash). |
| **`postgres://` Dialect Error** | Legacy connection URI. | LEXIQ automatically normalizes `postgres://` to `postgresql://` in `backend/app/config.py`. |
| **Vector Dimension Mismatch** | DB column set to 1536 but Gemini generates 768. | `database/init_db.py` automatically migrates `chunks.embedding` to `vector(768)` on startup. |
| **First Request Takes 30-50s** | Render free tier spin-down after 15 min. | Expected behavior on free tier. Upgrading to the $7/mo Starter plan eliminates spin-down. |
| **Gemini 404 on text-embedding-004** | Deprecated model ID on v1beta API. | Keep `GEMINI_EMBEDDING_MODEL=gemini-embedding-001` in your `.env`. |
