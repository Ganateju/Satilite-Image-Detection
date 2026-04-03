```
███████╗ █████╗ ████████╗      ███████╗ ██████╗ █████╗ ███╗  ██╗
██╔════╝██╔══██╗╚══██╔══╝      ██╔════╝██╔════╝██╔══██╗████╗ ██║
███████╗███████║   ██║         ███████╗██║     ███████║██╔██╗██║
╚════██║██╔══██║   ██║         ╚════██║██║     ██╔══██║██║╚████║
███████║██║  ██║   ██║    ██╗  ███████║╚██████╗██║  ██║██║ ╚███║
╚══════╝╚═╝  ╚═╝   ╚═╝    ╚═╝  ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚══╝
```

# Satellite Change Detector

> **STATUS: ACTIVE** | Sentinel-2 × PyTorch Siamese ResNet × Google Dynamic World

A full-stack geospatial AI application that detects and classifies land-cover changes
between two time periods using Sentinel-2 satellite imagery. Changes are categorized as
**Human-made (Built)** or **Natural** using a Siamese ResNet deep learning model and
Google Dynamic World land cover probabilities.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Satellite Data** | Google Earth Engine — `COPERNICUS/S2_SR_HARMONIZED` |
| **Land Cover** | Google Dynamic World v1 — continuous `built` probability |
| **AI Model** | PyTorch Siamese ResNet-18 (zero-shot change detection) |
| **Coordinate Math** | Rasterio — Affine transform, pixel-to-EPSG:4326 projection |
| **Change Clustering** | scikit-image — `find_contours`, `approximate_polygon`, `opening` |
| **Backend API** | FastAPI + Uvicorn |
| **Frontend** | Streamlit + Folium DualMap |
| **Map Viz** | Folium Leaflet + Google Satellite tiles |

---

## Features

- **Synchronized Dual Map** — Before (T1) and After (T2) Sentinel-2 imagery side-by-side
  with pixel-perfect pan/zoom sync via `folium.plugins.DualMap`
- **Precise Shape Detection** — contour-based polygon extraction (not bounding boxes)
  that hugs the exact footprint of each changed region
- **Smart Classification**
  - `Human-made` (Red) — majority of changed pixels exceed `>0.5` Dynamic World built probability
  - `Natural` (Green) — Class 4 (Grass) or Class 5 (Bare Ground) modal override enforced
- **10m Native Resolution** — pulls Sentinel-2 at `scale=10` for building-level detail
- **Terminal UI** — clean monospace professional interface with live mission log

---

## Setup

### 1. Prerequisites

- Python 3.10+
- A [Google Earth Engine](https://earthengine.google.com/) account
- A [Google Cloud Project](https://console.cloud.google.com/) with the Earth Engine API enabled

### 2. Clone & Install

```bash
git clone https://github.com/your-username/sat-change-detector.git
cd sat-change-detector

python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS

pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your Google Cloud Project ID:

```env
GEE_PROJECT_ID=your-project-id-here
```

### 4. Authenticate with Google Earth Engine

```bash
earthengine authenticate
```

Follow the browser prompt to authorize your account.

### 5. Run the Application

Open **two terminals** in the project root:

**Terminal 1 — Backend API:**
```bash
uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```bash
streamlit run frontend/app.py
```

Open `http://localhost:8501` in your browser.

---

## Usage

1. **Draw** a rectangle on the AOI map (max 10 km × 10 km)
2. **Set dates** — T1 (Before) and T2 (After)
3. **Click** `[ INITIATE CHANGE DETECTION ]`
4. Wait ~15–30 seconds for GEE + model inference
5. **Inspect** the synchronized dual map with Red/Green detection contours

---

## Project Structure

```
sat-change-detector/
├── backend/
│   ├── main.py           # FastAPI app — GEE queries, Rasterio, classification
│   └── model.py          # Siamese ResNet-18 change detection model
├── frontend/
│   ├── app.py            # Streamlit UI — maps, log, layout
│   └── style.css         # Terminal CSS theme
├── .env.example          # Required environment variable template
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Classification Logic

```
For each detected change cluster:

  1. Extract Dynamic World 'built' probability for all pixels in cluster
  2. If majority (>50%) of pixels have built_prob > 0.5:
       → Human-made (Red)
  3. Elif modal land cover label is Class 4 (Grass) or Class 5 (Bare Ground):
       → Natural (Green)  [Hard override — no exceptions]
  4. Else:
       → Natural (Green)
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GEE_PROJECT_ID` | **Yes** | Your Google Cloud Project ID with EE API enabled |
| `GEE_SERVICE_ACCOUNT_KEY_PATH` | No | Path to service account JSON (if not using `earthengine authenticate`) |

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

> *Built with Google Earth Engine, PyTorch, and Streamlit.*
