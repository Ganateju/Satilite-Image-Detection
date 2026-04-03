# 🛰️ Sat-Scan Terminal v3.0

### Geospatial AI Change Detection System

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python\&logoColor=white)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/AI-PyTorch-EE4C2C?logo=pytorch\&logoColor=white)](https://pytorch.org/)
[![Google Earth Engine](https://img.shields.io/badge/Engine-Google_Earth-4285F4?logo=google\&logoColor=white)](https://earthengine.google.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-00FF41.svg)](https://opensource.org/licenses/MIT)

---

## 📌 Overview

**Sat-Scan Terminal v3.0** is a full-stack geospatial AI system designed to detect and classify surface-level changes using Sentinel-2 satellite imagery.

It integrates deep learning, geospatial processing, and synchronized visualization to provide accurate and interpretable change detection results.

---

## 🚀 Key Features

* **Siamese Neural Network Architecture**
  Uses a ResNet-18 backbone to compare temporal satellite images (T1 vs T2) via feature distance.

* **Zero-Drift Visualization**
  Synchronized before/after satellite views using `folium.plugins.DualMap` at native 10m resolution.

* **Majority-Rule Classification Engine**
  Reduces noise and false positives by applying statistical mode analysis on Google Dynamic World probability bands.

* **Precise Contour Detection**
  Replaces bounding boxes with contour-based segmentation for more accurate region mapping.

---

## 🧠 System Architecture

```
Sentinel-2 Data (GEE)
        ↓
Preprocessing Pipeline
        ↓
Siamese ResNet-18 Model (PyTorch)
        ↓
Feature Distance Mapping
        ↓
Contour Extraction (Scikit-Image)
        ↓
Majority-Rule Classification (Dynamic World)
        ↓
Visualization (Streamlit + Folium)
```

---

## 🛠️ Tech Stack

| Component          | Technology                       |
| ------------------ | -------------------------------- |
| Inference Engine   | PyTorch (Siamese Neural Network) |
| Data Source        | Google Earth Engine (Sentinel-2) |
| Geospatial Math    | Rasterio + Affine Transform      |
| Image Processing   | Scikit-Image                     |
| Backend API        | FastAPI (Uvicorn)                |
| Frontend Interface | Streamlit + Folium               |

---

## ⚙️ Installation & Setup

### 1. Clone Repository

```bash
git clone https://github.com/Ganateju/Satilite-Image-Detection.git
cd Satilite-Image-Detection
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the root directory:

```
GEE_PROJECT_ID=your-google-project-id
```

> ⚠️ Do not commit `.env` files to version control.

---

## ▶️ Running the Application

Run the backend and frontend in separate terminals:

### Terminal A: Backend API

```bash
uvicorn backend.main:app --port 8000
```

### Terminal B: Frontend Interface

```bash
streamlit run frontend/app.py
```

---

## 📡 Classification Logic

```
IF (Cluster_Area > Threshold) AND (Mode(DynamicWorld_Class) == Built):
    LABEL = "HUMAN-MADE"
ELSE:
    LABEL = "NATURAL"
```

---

## 📊 Output

* Highlighted regions of detected change
* Classification labels:

  * **Human-Made** (Red)
  * **Natural** (Green)
* Synchronized before/after satellite comparison

---

## 🤝 Acknowledgments

* Smart India Hackathon — Problem inspiration
* Google Earth Engine — Satellite data infrastructure
* Open Source Community — Core libraries and tools

---

## 📄 License

This project is licensed under the MIT License.
See the [LICENSE](https://opensource.org/licenses/MIT) file for details.

---

## 📬 Contact

For queries or collaboration, feel free to open an issue or connect.
