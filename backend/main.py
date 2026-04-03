import os
import base64
from io import BytesIO
import numpy as np
from PIL import Image
import requests
import ee
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from skimage.measure import label, regionprops
import zipfile
import rasterio
from dotenv import load_dotenv
from .model import detect_changes_zero_shot

load_dotenv()

# Initialize FastAPI
app = FastAPI(title="Satellite Change Detector API")

PROJECT_ID = os.getenv("GEE_PROJECT_ID", "")

@app.on_event("startup")
def startup_event():
    try:
        if not PROJECT_ID:
            raise ValueError("GEE_PROJECT_ID is not set. Add it to your .env file.")
        print("Initializing Earth Engine...")
        ee.Initialize(project=PROJECT_ID)
        print("Earth Engine initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize Earth Engine: {e}")

class AnalyzeRequest(BaseModel):
    bbox: List[float] # [min_lon, min_lat, max_lon, max_lat]
    t1_date: str # YYYY-MM-DD
    t2_date: str # YYYY-MM-DD

def get_geotiff_as_numpy(ee_image, roi):
    url = ee_image.getDownloadURL({
        'region': roi,
        'scale': 10,
        'crs': 'EPSG:4326',
        'format': 'GEO_TIFF'
    })
    response = requests.get(url)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to fetch GeoTIFF from Earth Engine")
    
    try:
        # Load from zip (EE usually zips GEO_TIFF downloads)
        with zipfile.ZipFile(BytesIO(response.content)) as z:
            tif_name = [n for n in z.namelist() if n.endswith('.tif')][0]
            with z.open(tif_name) as f:
                with rasterio.MemoryFile(f.read()) as memfile:
                    with memfile.open() as dataset:
                        img_arr = dataset.read()
                        transform = dataset.transform
                        bounds = dataset.bounds
                        img_np = np.transpose(img_arr, (1, 2, 0))
                        # format required visually: [[min_lat, min_lon], [max_lat, max_lon]]
                        s_bounds = [[bounds.bottom, bounds.left], [bounds.top, bounds.right]]
                        return img_np, transform, s_bounds
    except Exception as e:
        # Fallback if EE sends raw tif
        with rasterio.MemoryFile(response.content) as memfile:
            with memfile.open() as dataset:
                img_arr = dataset.read()
                transform = dataset.transform
                bounds = dataset.bounds
                img_np = np.transpose(img_arr, (1, 2, 0))
                s_bounds = [[bounds.bottom, bounds.left], [bounds.top, bounds.right]]
                return img_np, transform, s_bounds

def get_bw_to_base64(img_np):
    img = Image.fromarray(img_np.astype(np.uint8))
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()



def generate_geojson_and_color_mask(binary_mask, change_map_np, dw_np, dw_built_np, transform):
    labeled_mask = label(binary_mask)
    regions = regionprops(labeled_mask)
    
    h, w = binary_mask.shape
    colored = np.zeros((h, w, 4), dtype=np.uint8)
    features = []
    
    for props in regions:
        # Enforce strict < 5px filtering as requested
        if props.area < 5:
            continue
            
        rmin, cmin, rmax, cmax = props.bbox
        
        cluster_dw = dw_np[rmin:rmax, cmin:cmax]
        cluster_built = dw_built_np[rmin:rmax, cmin:cmax]
        cluster_mask = (labeled_mask[rmin:rmax, cmin:cmax] == props.label)
        
        built_probabilities = cluster_built[cluster_mask]
        if len(built_probabilities) == 0:
            continue
        
        # 1. Majority Override: Must be >0.5 probability natively
        majority_built = (np.sum(built_probabilities > 0.5) / len(built_probabilities)) > 0.5
        
        # 2. Modal Bare Soil Extractor natively computes most popular feature
        cluster_labels = cluster_dw[cluster_mask].astype(int)
        bincounts = np.bincount(cluster_labels)
        modal_label = bincounts.argmax() if len(bincounts) > 0 else 0
        
        change_type = "Human-made" if majority_built else "Natural"
        
        # Strict hard-override ignoring built logic natively
        if modal_label in [4, 5]: # 4: Grass, 5: Bare Ground
            change_type = "Natural"
            
        # Execute unified boolean coloring sequence rapidly overlaying Numpy properties
        color_fill = [255, 60, 60, 200] if change_type == "Human-made" else [60, 255, 60, 200]
        cluster_colored = colored[rmin:rmax, cmin:cmax]
        cluster_colored[cluster_mask] = color_fill
        
        cluster_conf = np.mean(change_map_np[rmin:rmax, cmin:cmax][cluster_mask])
        confidence_pct = max(0, min(100, round(float(cluster_conf) * 100)))
        
        from skimage.measure import find_contours, approximate_polygon
        # Isolate boolean array natively inside local crop
        padded_mask = np.pad(cluster_mask, pad_width=1, mode='constant', constant_values=False)
        contours = find_contours(padded_mask, 0.5)
        if not contours:
            continue
            
        # Extract longest boundary
        contour = max(contours, key=len)
        contour_global = contour - 1 + [rmin, cmin] # Remove pad, add structural offset
        
        # Downsample complex jagged matrices
        simplified = approximate_polygon(contour_global, tolerance=1.0)
        
        # Re-Project array natively onto absolute EPSG:4326 via Rasterio Affine Transform
        poly_coords = []
        for r, c in simplified:
            lon, lat = transform * (c, r)
            poly_coords.append([lon, lat])
            
        # Close vector
        if poly_coords[0] != poly_coords[-1]:
            poly_coords.append(poly_coords[0])
        
        poly = {
            "type": "Feature",
            "properties": {
                "type": change_type,
                "confidence": f"{confidence_pct}%",
                "description": f"Detected {change_type} change with {confidence_pct}% confidence."
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [poly_coords]
            }
        }
        features.append(poly)
        
    return colored, {
        "type": "FeatureCollection",
        "features": features
    }

@app.post("/api/analyze")
def analyze_area(req: AnalyzeRequest):
    try:
        roi = ee.Geometry.Rectangle(req.bbox)
        
        s2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        
        def mask_s2_clouds(image):
            qa = image.select('QA60')
            cloudBitMask = 1 << 10
            cirrusBitMask = 1 << 11
            mask = qa.bitwiseAnd(cloudBitMask).eq(0).And(qa.bitwiseAnd(cirrusBitMask).eq(0))
            return image.updateMask(mask).divide(10000)
            
        t1_start = ee.Date(req.t1_date).advance(-1, 'month')
        t1_end = ee.Date(req.t1_date).advance(1, 'month')
        col1 = s2.filterBounds(roi).filterDate(t1_start, t1_end).map(mask_s2_clouds)
        if col1.size().getInfo() == 0:
            raise HTTPException(status_code=400, detail="No Sentinel-2 imagery found for the Before Date. Try a different date or location.")
        img1 = col1.median().clip(roi)
        img1_vis = img1.select(['B4', 'B3', 'B2']).multiply(255 / 0.3).min(255).max(0).toByte()
        
        t2_start = ee.Date(req.t2_date).advance(-1, 'month')
        t2_end = ee.Date(req.t2_date).advance(1, 'month')
        col2 = s2.filterBounds(roi).filterDate(t2_start, t2_end).map(mask_s2_clouds)
        if col2.size().getInfo() == 0:
            raise HTTPException(status_code=400, detail="No Sentinel-2 imagery found for the After Date. Try a different date or location.")
        img2 = col2.median().clip(roi)
        img2_vis = img2.select(['B4', 'B3', 'B2']).multiply(255 / 0.3).min(255).max(0).toByte()
        
        dw = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
        dw_col = dw.filterBounds(roi).filterDate(t2_start, t2_end)
        if dw_col.size().getInfo() == 0:
            raise HTTPException(status_code=400, detail="No Dynamic World classification found for this area/date.")
        dw_t2 = dw_col.select('label').mode()
        dw_built = dw_col.select('built').mean()
        
        img1_np, transform1, standard_bbox = get_geotiff_as_numpy(img1_vis, roi)
        img2_np, _, _ = get_geotiff_as_numpy(img2_vis, roi)
        dw_np_raw, _, _ = get_geotiff_as_numpy(dw_t2, roi)
        dw_built_raw, _, _ = get_geotiff_as_numpy(dw_built, roi)
        
        if len(dw_np_raw.shape) == 3:
            dw_np = dw_np_raw[:, :, 0]
        else:
            dw_np = dw_np_raw
            
        if len(dw_built_raw.shape) == 3:
            dw_built_np = dw_built_raw[:, :, 0]
        else:
            dw_built_np = dw_built_raw
            
        min_h = min(img1_np.shape[0], img2_np.shape[0], dw_np.shape[0], dw_built_np.shape[0])
        min_w = min(img1_np.shape[1], img2_np.shape[1], dw_np.shape[1], dw_built_np.shape[1])
        
        img1_np = img1_np[:min_h, :min_w]
        img2_np = img2_np[:min_h, :min_w]
        dw_np = dw_np[:min_h, :min_w]
        dw_built_np = dw_built_np[:min_h, :min_w]
        
        from skimage.morphology import opening, footprint_rectangle
        binary_mask, change_map_np = detect_changes_zero_shot(img1_np, img2_np, threshold=0.35)
        binary_mask = opening(binary_mask, footprint_rectangle((3, 3)))
        
        color_mask, geojson_data = generate_geojson_and_color_mask(binary_mask, change_map_np, dw_np, dw_built_np, transform1)
        
        t1_b64 = get_bw_to_base64(img1_np)
        t2_b64 = get_bw_to_base64(img2_np)
        mask_b64 = get_bw_to_base64(color_mask)
        
        total_pixels = binary_mask.size
        changed_pixels = np.sum(binary_mask)
        human_pixels = np.sum(binary_mask & (dw_np == 6))
        natural_pixels = changed_pixels - human_pixels
        
        return {
            "status": "success",
            "standard_bbox": standard_bbox,
            "geojson": geojson_data,
            "t1_image": f"data:image/png;base64,{t1_b64}",
            "t2_image": f"data:image/png;base64,{t2_b64}",
            "change_mask": f"data:image/png;base64,{mask_b64}",
            "stats": {
                "changed_pct": round(float(changed_pixels / total_pixels) * 100, 2),
                "human_pct": round(float(human_pixels / total_pixels) * 100, 2) if total_pixels > 0 else 0,
                "natural_pct": round(float(natural_pixels / total_pixels) * 100, 2) if total_pixels > 0 else 0
            }
        }
    except Exception as e:
        print(f"Error during analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))
