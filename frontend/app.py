import streamlit as st
import folium
import folium.plugins
from folium.plugins import Draw, LocateControl, Geocoder
from streamlit_folium import st_folium
import streamlit.components.v1 as components
import requests
import datetime
import math

st.set_page_config(
    layout="wide",
    page_title="SAT-SCAN TERMINAL v3.1",
    page_icon="🛰️",
    initial_sidebar_state="collapsed",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
with open("frontend/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ── HELPERS ────────────────────────────────────────────────────────────────────
def haversine(lon1, lat1, lon2, lat2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def ts():
    return datetime.datetime.now().strftime("%H:%M:%S")

# ── LOG STATE ──────────────────────────────────────────────────────────────────
if "log_lines" not in st.session_state:
    st.session_state.log_lines = [
        ("system", "SYSTEM BOOT COMPLETE"),
        ("ok",     "SENTINEL-2 SENSOR ARRAY: ONLINE"),
        ("ok",     "PYTORCH SIAMESE MODEL: LOADED"),
        ("ok",     "AWAITING AOI COORDINATES..."),
    ]

def log(msg, kind="ok"):
    st.session_state.log_lines.append((kind, f"[{ts()}] {msg}"))

def build_log_html():
    rows = ""
    for kind, msg in st.session_state.log_lines[-60:]:  # keep last 60 lines
        css = {"system": "log-sys", "ok": "log-ok",
               "warn": "log-warn", "err": "log-err"}.get(kind, "log-ok")
        rows += f'<div class="{css}">&gt; {msg}</div>\n'
    rows += '<div><span class="cursor"></span></div>'
    return f'<div class="terminal-log">{rows}</div>'

# ── SYSTEM STATUS BAR ──────────────────────────────────────────────────────────
now_str = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
st.markdown(f"""
<div class="status-bar">
  <span class="status-item">MISSION: <span>SAT-SCAN TERMINAL v3.1</span></span>
  <span class="status-item">SENSOR: <span>COPERNICUS/SENTINEL-2</span></span>
  <span class="status-item">MODEL: <span>SIAMESE RESNET</span></span>
  <span class="status-item">CLASSIFIER: <span>DYNAMIC WORLD v1</span></span>
  <span class="status-item">TIMESTAMP: <span>{now_str}</span></span>
  <span class="status-item">STATUS: <span>ACTIVE</span></span>
</div>
""", unsafe_allow_html=True)

# ── THREE COLUMNS: AOI | RESULTS | LOG ────────────────────────────────────────
col1, col2, col3 = st.columns([1.1, 1.5, 0.65], gap="medium")

# ──────────────────────────────────────────────────────────────────────────────
# COL 1 — AOI SELECTOR + DATES
# ──────────────────────────────────────────────────────────────────────────────
with col1:
    st.markdown('<span class="term-header">// 01 — AREA OF INTEREST</span>', unsafe_allow_html=True)
    st.markdown(
        '<span style="font-size:0.65rem;color:#FFFFFF;letter-spacing:0.08em;">'
        'DRAW RECTANGLE › MAX 10 km × 10 km</span>',
        unsafe_allow_html=True
    )

    m = folium.Map(location=[37.7749, -122.4194], zoom_start=11, tiles=None)
    folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        attr="Google", name="Google Satellite", overlay=False,
    ).add_to(m)
    Geocoder(position="topleft").add_to(m)
    LocateControl(position="topleft", drawCircle=False, keepCurrentZoomLevel=False).add_to(m)
    Draw(
        export=False,
        draw_options={
            "rectangle": True, "polygon": False, "polyline": False,
            "circle": False, "marker": False, "circlemarker": False,
        },
    ).add_to(m)

    output = st_folium(m, width=None, height=400)

    st.markdown('<span class="term-header">// 02 — TEMPORAL WINDOW</span>', unsafe_allow_html=True)
    dcol1, dcol2 = st.columns(2)
    with dcol1:
        t1_date = st.date_input("T1 › BEFORE", datetime.date(2021, 1, 1))
    with dcol2:
        t2_date = st.date_input("T2 › AFTER",  datetime.date(2023, 1, 1))

# Decode bbox
bbox      = None
valid_box = False

if output and output.get("last_active_drawing"):
    geom   = output["last_active_drawing"]["geometry"]
    coords = geom["coordinates"][0]
    lons = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    bbox = [min(lons), min(lats), max(lons), max(lats)]

    w_km = haversine(min(lons), min(lats), max(lons), min(lats))
    h_km = haversine(min(lons), min(lats), min(lons), max(lats))

    with col1:
        if w_km > 10.0 or h_km > 10.0:
            st.warning(f"AOI EXCEEDS LIMIT: {w_km:.2f} × {h_km:.2f} km — REDRAW")
        else:
            st.info(f"AOI LOCKED: {w_km:.2f} km × {h_km:.2f} km")
            valid_box = True

# ──────────────────────────────────────────────────────────────────────────────
# COL 2 — ANALYSIS & RESULTS
# ──────────────────────────────────────────────────────────────────────────────
with col2:
    st.markdown('<span class="term-header">// 03 — EXECUTE SCAN</span>', unsafe_allow_html=True)

    if st.button("[ INITIATE CHANGE DETECTION ]", type="primary"):
        if not valid_box:
            st.error("NO VALID AOI — DRAW RECTANGLE FIRST")
            log("ERROR: INVALID AOI — SCAN ABORTED", "err")
        else:
            st.session_state.log_lines = []
            log("SAT-LINK INITIALIZING...", "system")
            log(f"AOI: [{bbox[0]:.5f}, {bbox[1]:.5f}, {bbox[2]:.5f}, {bbox[3]:.5f}]", "ok")
            log(f"T1={t1_date}  T2={t2_date}", "ok")
            log("AUTHENTICATING GEE CREDENTIALS...", "system")
            log("QUERYING COPERNICUS/S2_SR_HARMONIZED...", "system")
            log("FETCHING GEOTIFF AT scale=10m/px...", "system")

            with st.spinner("SCANNING... PLEASE WAIT"):
                try:
                    res = requests.post(
                        "http://127.0.0.1:8000/api/analyze",
                        json={"bbox": bbox, "t1_date": str(t1_date), "t2_date": str(t2_date)},
                        timeout=180,
                    )
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state.analysis_data  = data
                        st.session_state.run_t1_date    = t1_date
                        st.session_state.run_t2_date    = t2_date
                        st.session_state.run_bbox       = bbox

                        feats     = data.get("geojson", {}).get("features", [])
                        n_human   = sum(1 for f in feats if f["properties"]["type"] == "Human-made")
                        n_natural = sum(1 for f in feats if f["properties"]["type"] == "Natural")

                        log("GEOTIFF DOWNLOAD COMPLETE", "ok")
                        log("RUNNING SIAMESE RESNET INFERENCE...", "system")
                        log("MORPHOLOGICAL OPENING: square(3)", "system")
                        log("EXTRACTING CONTOUR POLYGONS...", "ok")
                        log("QUERYING DYNAMICWORLD/V1 built probability...", "system")
                        log("MAJORITY RULE CLASSIFIER (threshold=0.5) APPLIED", "ok")
                        log("BARE-SOIL MODAL OVERRIDE (Class 4/5) APPLIED", "ok")
                        log(f"HUMAN-MADE CHANGES: {n_human}", "warn" if n_human > 0 else "ok")
                        log(f"NATURAL CHANGES:    {n_natural}", "ok")
                        log(f"TOTAL AREA CHANGED: {data['stats']['changed_pct']}%", "ok")
                        log("CLASSIFICATION COMPLETE. RENDERING MAP...", "system")
                    else:
                        log(f"BACKEND ERR {res.status_code}: {res.text[:80]}", "err")
                        st.error(f"Backend Error: {res.text}")
                except Exception as e:
                    log(f"CONNECTION FAILURE: {str(e)[:80]}", "err")
                    st.error(f"Connection error: {e}")

    # ── RESULTS ───────────────────────────────────────────────────────────────
    if "analysis_data" in st.session_state:
        data   = st.session_state.analysis_data
        run_t1 = st.session_state.run_t1_date
        run_t2 = st.session_state.run_t2_date

        # Stats
        st.markdown("""
<div class="stats-card">
  <h4>[ CHANGE STATISTICS ]</h4>
  <p>TOTAL CHANGED &nbsp;&nbsp;: <b>{changed}%</b></p>
  <p style="color:#FF4444 !important;">HUMAN-MADE (BUILT): <b>{human}%</b></p>
  <p style="color:#00FF41 !important;">NATURAL CHANGE &nbsp;: <b>{natural}%</b></p>
</div>""".format(
            changed=data["stats"]["changed_pct"],
            human=data["stats"]["human_pct"],
            natural=data["stats"]["natural_pct"],
        ), unsafe_allow_html=True)

        # Before / After thumbnails — compact two-col
        st.markdown('<span class="term-header">// SENTINEL-2 IMAGERY</span>', unsafe_allow_html=True)
        ic1, ic2 = st.columns(2)
        with ic1:
            st.image(data["t1_image"], caption=f"T1 BEFORE › {run_t1}", width='stretch')
        with ic2:
            st.image(data["t2_image"], caption=f"T2 AFTER  › {run_t2}",  width='stretch')

        # ── DUAL MAP ──────────────────────────────────────────────────────────
        st.markdown('<span class="term-header">// SYNCHRONIZED CHANGE MAP</span>', unsafe_allow_html=True)

        std_bbox   = data["standard_bbox"]
        s_min_lat  = std_bbox[0][0];  s_min_lon = std_bbox[0][1]
        s_max_lat  = std_bbox[1][0];  s_max_lon = std_bbox[1][1]
        center     = [(s_min_lat + s_max_lat) / 2, (s_min_lon + s_max_lon) / 2]

        m_res = folium.plugins.DualMap(
            location=center,
            zoom_start=15,
            tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
            attr="Google",
            name="Google Satellite",
        )

        # Before image on left
        folium.raster_layers.ImageOverlay(
            image=data["t1_image"], bounds=std_bbox,
            opacity=1.0, interactive=False, cross_origin=False, zindex=2,
        ).add_to(m_res.m1)

        # After image on right
        folium.raster_layers.ImageOverlay(
            image=data["t2_image"], bounds=std_bbox,
            opacity=1.0, interactive=False, cross_origin=False, zindex=2,
        ).add_to(m_res.m2)

        # GeoJSON — vector outlines only on right (After) panel
        def style_fn(feat):
            is_human = feat["properties"]["type"] == "Human-made"
            return {
                "color":       "#FF0000" if is_human else "#00FF41",
                "fillColor":   "#FF0000" if is_human else "#00FF41",
                "weight":      1,
                "fillOpacity": 0.06,   # near-invisible fill → vector outline look
                "opacity":     0.9,
            }

        feats = data.get("geojson", {}).get("features", [])
        if feats:
            folium.GeoJson(
                data["geojson"],
                name="Detections",
                style_function=style_fn,
                popup=folium.GeoJsonPopup(fields=["type", "confidence", "description"]),
            ).add_to(m_res.m2)

        st.iframe(m_res.get_root().render(), height=560)

# ──────────────────────────────────────────────────────────────────────────────
# COL 3 — TERMINAL LOG
# ──────────────────────────────────────────────────────────────────────────────
with col3:
    st.markdown('<span class="term-header">// MISSION LOG</span>', unsafe_allow_html=True)
    log_ph = st.empty()
    log_ph.markdown(build_log_html(), unsafe_allow_html=True)
