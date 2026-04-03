"""
backend/analysis.py — Pure analysis library (no FastAPI).
Imported directly by frontend/app.py for single-process Streamlit Cloud deployment.
"""

import os
import base64
import json
import zipfile
from io import BytesIO

import numpy as np
import requests
import ee
import rasterio
from PIL import Image
from skimage.measure import label, regionprops, find_contours, approximate_polygon
from skimage.morphology import opening, footprint_rectangle

# ── GEE DOWNLOAD ──────────────────────────────────────────────────────────────

def get_geotiff_as_numpy(ee_image, roi):
    """Download a GEE image as a NumPy array via GeoTIFF.
    Returns (img_np, affine_transform, standard_bbox).
    standard_bbox: [[min_lat, min_lon], [max_lat, max_lon]]
    """
    url = ee_image.getDownloadURL({
        "region": roi,
        "scale": 10,
        "crs": "EPSG:4326",
        "format": "GEO_TIFF",
    })
    resp = requests.get(url, timeout=120)
    if resp.status_code != 200:
        raise RuntimeError(f"GEE download failed ({resp.status_code}): {resp.text[:200]}")

    def _parse(content):
        with rasterio.MemoryFile(content) as mf:
            with mf.open() as ds:
                arr = ds.read()
                tfm = ds.transform
                b   = ds.bounds
                img = np.transpose(arr, (1, 2, 0))
                bbox = [[b.bottom, b.left], [b.top, b.right]]
                return img, tfm, bbox

    try:
        with zipfile.ZipFile(BytesIO(resp.content)) as z:
            tif_name = next(n for n in z.namelist() if n.endswith(".tif"))
            with z.open(tif_name) as f:
                return _parse(f.read())
    except Exception:
        return _parse(resp.content)


def _to_base64_png(img_np: np.ndarray) -> str:
    img = Image.fromarray(img_np.astype(np.uint8))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


# ── CLASSIFICATION & GEOJSON ──────────────────────────────────────────────────

def _classify_and_build_geojson(binary_mask, change_map_np, dw_np, dw_built_np, transform):
    """Classify each change cluster and return (color_mask_rgba, geojson_dict)."""
    labeled = label(binary_mask)
    regions = regionprops(labeled)

    h, w = binary_mask.shape
    colored  = np.zeros((h, w, 4), dtype=np.uint8)
    features = []

    for props in regions:
        if props.area < 5:
            continue

        rmin, cmin, rmax, cmax = props.bbox
        cluster_mask  = (labeled[rmin:rmax, cmin:cmax] == props.label)
        cluster_dw    = dw_np[rmin:rmax, cmin:cmax]
        cluster_built = dw_built_np[rmin:rmax, cmin:cmax]

        built_probs = cluster_built[cluster_mask]
        if len(built_probs) == 0:
            continue

        # Rule 1: majority of changed pixels must have built_prob > 0.5
        majority_built = (np.sum(built_probs > 0.5) / len(built_probs)) > 0.5

        # Rule 2: modal DW label override for natural land covers
        labels_int = cluster_dw[cluster_mask].astype(int)
        bincounts  = np.bincount(labels_int) if len(labels_int) > 0 else np.array([0])
        modal_label = int(bincounts.argmax())

        change_type = "Human-made" if majority_built else "Natural"
        if modal_label in (4, 5):   # 4=Grass, 5=Bare Ground
            change_type = "Natural"

        # Color overlay
        fill = [255, 60, 60, 200] if change_type == "Human-made" else [60, 255, 60, 200]
        colored[rmin:rmax, cmin:cmax][cluster_mask] = fill

        # Confidence
        conf = np.mean(change_map_np[rmin:rmax, cmin:cmax][cluster_mask])
        conf_pct = max(0, min(100, round(float(conf) * 100)))

        # Contour polygon
        padded   = np.pad(cluster_mask, 1, mode="constant", constant_values=False)
        contours = find_contours(padded, 0.5)
        if not contours:
            continue
        contour  = max(contours, key=len) - 1 + np.array([rmin, cmin])
        simplified = approximate_polygon(contour, tolerance=1.0)

        coords = []
        for r, c in simplified:
            lon, lat = transform * (c, r)
            coords.append([lon, lat])
        if coords[0] != coords[-1]:
            coords.append(coords[0])

        features.append({
            "type": "Feature",
            "properties": {
                "type":        change_type,
                "confidence":  f"{conf_pct}%",
                "description": f"Detected {change_type} change ({conf_pct}% confidence).",
            },
            "geometry": {"type": "Polygon", "coordinates": [coords]},
        })

    geojson = {"type": "FeatureCollection", "features": features}
    return colored, geojson


# ── PUBLIC API ────────────────────────────────────────────────────────────────

def run_analysis(bbox: list, t1_date: str, t2_date: str, model_fn) -> dict:
    """
    Core analysis pipeline.

    Parameters
    ----------
    bbox      : [min_lon, min_lat, max_lon, max_lat]
    t1_date   : 'YYYY-MM-DD'
    t2_date   : 'YYYY-MM-DD'
    model_fn  : callable — detect_changes_zero_shot(img1_np, img2_np, threshold)

    Returns
    -------
    dict with keys: standard_bbox, geojson, t1_image, t2_image,
                    change_mask, stats
    """
    roi = ee.Geometry.Rectangle(bbox)
    s2  = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")

    def mask_clouds(img):
        qa  = img.select("QA60")
        cm  = (1 << 10)
        ci  = (1 << 11)
        mask = qa.bitwiseAnd(cm).eq(0).And(qa.bitwiseAnd(ci).eq(0))
        return img.updateMask(mask).divide(10000)

    def vis(img):
        return img.select(["B4", "B3", "B2"]).multiply(255 / 0.3).min(255).max(0).toByte()

    # T1
    t1s = ee.Date(t1_date).advance(-1, "month")
    t1e = ee.Date(t1_date).advance(1,  "month")
    col1 = s2.filterBounds(roi).filterDate(t1s, t1e).map(mask_clouds)
    if col1.size().getInfo() == 0:
        raise ValueError("No Sentinel-2 imagery for the Before date. Try a wider date range.")
    img1 = col1.median().clip(roi)

    # T2
    t2s = ee.Date(t2_date).advance(-1, "month")
    t2e = ee.Date(t2_date).advance(1,  "month")
    col2 = s2.filterBounds(roi).filterDate(t2s, t2e).map(mask_clouds)
    if col2.size().getInfo() == 0:
        raise ValueError("No Sentinel-2 imagery for the After date. Try a wider date range.")
    img2 = col2.median().clip(roi)

    # Dynamic World
    dw_col = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").filterBounds(roi).filterDate(t2s, t2e)
    if dw_col.size().getInfo() == 0:
        raise ValueError("No Dynamic World data for this area/date.")
    dw_label = dw_col.select("label").mode()
    dw_built  = dw_col.select("built").mean()

    # Download GeoTIFFs
    img1_np, tfm,  std_bbox = get_geotiff_as_numpy(vis(img1), roi)
    img2_np, _,    _        = get_geotiff_as_numpy(vis(img2), roi)
    dw_raw,  _,    _        = get_geotiff_as_numpy(dw_label, roi)
    dwb_raw, _,    _        = get_geotiff_as_numpy(dw_built, roi)

    dw_np    = dw_raw[:, :, 0]  if dw_raw.ndim  == 3 else dw_raw
    dw_built_np = dwb_raw[:, :, 0] if dwb_raw.ndim == 3 else dwb_raw

    # Align shapes
    mh = min(img1_np.shape[0], img2_np.shape[0], dw_np.shape[0], dw_built_np.shape[0])
    mw = min(img1_np.shape[1], img2_np.shape[1], dw_np.shape[1], dw_built_np.shape[1])
    img1_np    = img1_np[:mh, :mw]
    img2_np    = img2_np[:mh, :mw]
    dw_np      = dw_np[:mh, :mw]
    dw_built_np = dw_built_np[:mh, :mw]

    # AI inference
    binary_mask, change_map_np = model_fn(img1_np, img2_np, threshold=0.35)
    binary_mask = opening(binary_mask, footprint_rectangle((3, 3)))

    color_mask, geojson = _classify_and_build_geojson(
        binary_mask, change_map_np, dw_np, dw_built_np, tfm
    )

    # Stats
    total   = binary_mask.size
    changed = int(np.sum(binary_mask))
    human   = int(np.sum(binary_mask & (dw_np == 6)))
    natural = changed - human

    return {
        "standard_bbox": std_bbox,
        "geojson":       geojson,
        "t1_image":      _to_base64_png(img1_np),
        "t2_image":      _to_base64_png(img2_np),
        "change_mask":   _to_base64_png(color_mask),
        "stats": {
            "changed_pct": round(changed / total * 100, 2),
            "human_pct":   round(human   / total * 100, 2) if total > 0 else 0,
            "natural_pct": round(natural  / total * 100, 2) if total > 0 else 0,
        },
    }
