# 🛰️ Sat-Scan Terminal v3.0

### Geospatial AI Change Detection System | SIH Re-Engineered Build

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://YOUR-APP-LINK.streamlit.app)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python\&logoColor=white)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/AI-PyTorch-EE4C2C?logo=pytorch\&logoColor=white)](https://pytorch.org/)
[![Google Earth Engine](https://img.shields.io/badge/Engine-Google_Earth-4285F4?logo=google\&logoColor=white)](https://earthengine.google.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-00FF41.svg)](https://opensource.org/licenses/MIT)

---
<img width="2752" height="1536" alt="Gemini_Generated_Image_2yo8o82yo8o82yo8" src="https://github.com/user-attachments/assets/93797dda-1598-42e4-a65e-32169cf40c18" />



> 🚀 **Live Demo:** https://satilite-image-detection.streamlit.app/


---

## 📌 Overview

**Sat-Scan Terminal v3.0** is a geospatial AI system designed to detect and classify surface-level changes using Sentinel-2 satellite imagery.

Originally developed for the **Smart India Hackathon (SIH)**, this version represents a **complete system-level rebuild**, focused on precision, synchronization, and noise-resistant classification.

---

## 📜 Engineering Journey (SIH Context)

The initial prototype failed due to:

* Coordinate desynchronization ("grey-screen drift")
* High false positives from seasonal/environmental changes
* Poor spatial interpretation using bounding boxes

Instead of abandoning the project, the system was **re-engineered from scratch**.

**v3.0 reflects a shift from failure → structured engineering recovery**, focusing on:

* root-cause debugging
* architectural redesign
* robustness over quick fixes

---

## 🎯 Engineering Objective

Design a **stable and interpretable change detection pipeline** that:

* Eliminates temporal misalignment
* Minimizes false positives
* Produces precise region-level outputs
* Scales across real-world geospatial data

---

## 🧠 Core Architecture

### 1. Siamese Feature Extraction

* ResNet-18 backbone for T1 vs T2 comparison
* Uses feature distance instead of raw pixel difference
* Improves robustness to lighting and seasonal variation

### 2. Majority-Rule Classification Engine

* Uses Google Dynamic World probability bands
* Applies statistical mode across regions
* Filters noise and “poison pixels”

### 3. Contour-Based Detection

* Replaces bounding boxes with precise contours
* Enables accurate spatial interpretation

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

| Component        | Technology                       |
| ---------------- | -------------------------------- |
| Inference Engine | PyTorch (Siamese Neural Network) |
| Data Pipeline    | Google Earth Engine (Sentinel-2) |
| Geospatial Math  | Rasterio + Affine Transform      |
| Image Processing | Scikit-Image                     |
| Visualization    | Streamlit + Folium DualMap       |

---

## 🚀 Usage

### 🌐 Live Application

1. Open the Streamlit app
2. Draw an Area of Interest (AOI)
3. Select T1 (Before) and T2 (After) dates
4. Run detection to visualize changes

### 💻 Local Setup

```bash
git clone https://github.com/Ganateju/Satilite-Image-Detection.git
cd Satilite-Image-Detection
pip install -r requirements.txt
```

Create a `.env` file:

```
GEE_PROJECT_ID=your-google-project-id
```

Run:

```bash
streamlit run frontend/app.py
```

---

## 📡 Classification Logic

```python
IF (Cluster_Area > Threshold) AND (Mode(DynamicWorld_Class) == Built):
    LABEL = "HUMAN-MADE"  # Red
ELSE:
    LABEL = "NATURAL"     # Green
```

---

## 📊 Output

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
| Stability        | Unreliable           | Consistent & Stable     |

---

## 🤝 Acknowledgments

* Smart India Hackathon — Problem statement
* Google Earth Engine — Data infrastructure
* Open-source community — Core tools

---

## 📄 License

This project is licensed under the MIT License.

---

## 🧩 Developer Note

This project demonstrates a key engineering principle:

> **Failure is acceptable. Not understanding the failure is not.**

The system was rebuilt by identifying core issues and redesigning the architecture instead of applying superficial fixes.

---
