# 🛰️ Sat-Scan Terminal v3.0

### Geospatial AI Change Detection System

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python\&logoColor=white)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/AI-PyTorch-EE4C2C?logo=pytorch\&logoColor=white)](https://pytorch.org/)
[![Google Earth Engine](https://img.shields.io/badge/Engine-Google_Earth-4285F4?logo=google\&logoColor=white)](https://earthengine.google.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-00FF41.svg)](https://opensource.org/licenses/MIT)

---

## 📌 Overview

**Sat-Scan Terminal v3.0** is a full-stack geospatial AI system designed to detect and classify surface-level changes using Sentinel-2 satellite imagery.

It combines deep learning, geospatial processing, and synchronized visualization to produce accurate, interpretable, and noise-resistant results.

---

## 📜 Project Background (SIH Context)

This project was originally developed for the **Smart India Hackathon (SIH)**.

The initial version failed due to:

* coordinate synchronization issues ("grey-screen drift")
* high false positives in change detection
* weak spatial interpretation using bounding boxes

Instead of abandoning the project, the system was **re-engineered from scratch**, focusing on root-cause fixes rather than surface-level patches.

**Version 3.0 represents a stable and production-oriented rebuild.**

---

## 🎯 Engineering Objective

Design a **robust and interpretable change detection pipeline** that:

* Eliminates temporal misalignment
* Reduces environmental and seasonal noise
* Produces precise region-level outputs
* Maintains consistency across large-scale geospatial data

---

## 🧠 Architectural Decisions

### 1. Siamese Feature Learning

* ResNet-18 backbone for temporal comparison (T1 vs T2)
* Euclidean feature distance instead of raw pixel differencing
* Improved robustness to lighting and seasonal variation

### 2. Majority-Rule Classification Engine

* Uses Google Dynamic World probability bands
* Applies statistical mode across regions
* Filters noise and “poison pixels”

### 3. Contour-Based Vectorization

* Replaces bounding boxes with precise contours
* Enables accurate region-level interpretation

### 4. Zero-Drift Visualization

* Implemented using `folium.plugins.DualMap`
* Ensures synchronized before/after comparison at 10m resolution

---

## 🏗️ System Architecture

```
Sentinel-2 Data (Google Earth Engine)
        ↓
Preprocessing Pipeline
        ↓
Siamese ResNet-18 (PyTorch)
        ↓
Feature Distance Map
        ↓
Thresholding + Clustering
        ↓
Contour Extraction (Scikit-Image)
        ↓
Majority-Rule Classification (Dynamic World)
        ↓
Visualization Layer (Streamlit + Folium)
```

---

## 🛠️ Tech Stack

| Component          | Technology                       |
| ------------------ | -------------------------------- |
| Inference Engine   | PyTorch (Siamese Neural Network) |
| Data Pipeline      | Google Earth Engine (Sentinel-2) |
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

Create a `.env` file:

```
GEE_PROJECT_ID=your-google-project-id
```

> Do not commit `.env` files.

---

## ▶️ Running the System

### Terminal A — Backend

```bash
uvicorn backend.main:app --port 8000
```

### Terminal B — Frontend

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

## 📊 Output Characteristics

* Contour-based detected regions
* Reduced false positives via probabilistic filtering
* Human-interpretable classification
* Synchronized temporal comparison

---

## 📈 Improvements Over Initial Version

| Aspect           | Initial Prototype    | v3.0 System             |
| ---------------- | -------------------- | ----------------------- |
| Map Alignment    | Drift Issues         | Fully Synchronized      |
| Noise Handling   | High False Positives | Majority-Rule Filtering |
| Region Detection | Bounding Boxes       | Precise Contours        |
| System Stability | Unreliable           | Stable & Consistent     |

---

## 🧪 Future Scope

* Multi-temporal analysis (T1, T2, T3…)
* Transformer-based geospatial models
* Real-time monitoring pipelines
* Integration with urban planning systems

---

## 🤝 Acknowledgments

* Smart India Hackathon — Problem statement
* Google Earth Engine — Data infrastructure
* Open-source community — Core libraries

---

## 📄 License

This project is licensed under the MIT License.
See the LICENSE file for details.

---

## 🧩 Developer Note

This project reflects a shift from **failure → structured engineering recovery**.

Instead of iterating blindly, the focus was on:

* identifying root causes
* redesigning system architecture
* prioritizing robustness over quick fixes

---
