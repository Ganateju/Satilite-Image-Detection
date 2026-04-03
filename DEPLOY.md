# Deployment Guide — Streamlit Cloud

## Overview

This app runs as a single-process Streamlit app (`app.py`).
There is **no separate FastAPI server** — analysis functions are imported directly.

---

## Step 1 — Fork & Push to GitHub

```bash
git clone https://github.com/your-username/sat-change-detector.git
cd sat-change-detector
git add .
git commit -m "Initial commit"
git push origin main
```

---

## Step 2 — Create a Google Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (same Project ID used for Earth Engine)
3. Navigate to **IAM & Admin → Service Accounts**
4. Click **Create Service Account**
5. Grant no roles at project level (EE manages its own permissions)
6. Click the new service account → **Keys → Add Key → JSON**
7. Download the `.json` file

**Register the service account with Earth Engine:**
```
https://code.earthengine.google.com/register
```
Choose "Unpaid usage" → "Service Account" → paste the `client_email` from the JSON.

---

## Step 3 — Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **New app**
3. Connect your GitHub repository
4. Set **Main file path** to: `app.py`
5. Click **Advanced settings → Secrets**

---

## Step 4 — Add the Secret

In the Streamlit Secrets panel, paste the **entire contents** of your downloaded
service account JSON file as the value of `GEE_JSON_KEY`:

```toml
GEE_JSON_KEY = """
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "...",
  "private_key": "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----\n",
  "client_email": "your-sa@your-project.iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  ...
}
"""
```

> ⚠️ **NEVER** commit the `.json` key file or paste it anywhere public.
> The `.gitignore` in this repo already excludes all `*.json` files.

---

## Step 5 — Deploy

Click **Deploy**. Streamlit Cloud will:
- Install all packages from `requirements.txt`
- Call `app.py` as the entry point
- Authenticate GEE via the service account on first run (cached for the session)

---

## Local Development

```bash
cp .env.example .env
# Edit .env: add GEE_PROJECT_ID=your-project-id
pip install -r requirements.txt
earthengine authenticate
streamlit run app.py
```

---

## Troubleshooting

| Error | Fix |
|---|---|
| `GEE not configured` | Add `GEE_JSON_KEY` to Streamlit Secrets |
| `No imagery found` | Widen date range (±2 months) or pick a less cloudy region |
| `GeoTIFF download failed` | AOI may be too large; redraw under 10 km × 10 km |
| `EE quota exceeded` | Wait 1 hour or request a higher quota in GCP Console |
