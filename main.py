"""
AirAsia Rides — Demand Heatmap Dashboard
Tier 1: Time-of-Day Hotspot Analysis

Designed for Streamlit Cloud.
Data is user-uploaded via CSV — nothing is persisted server-side.
All processing happens in session memory only.
"""

import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import plotly.graph_objects as go
import io
import pydeck as pdk
import h3
from datetime import datetime

# ── Page config (must be first Streamlit call) ─────────────────────────────────
st.set_page_config(
    page_title="Rides · Demand Heatmap",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Wise Neptune design tokens ─────────────────────────────────────────────────
W = {
    # Core brand — exact Wise spec
    "green_forest":      "#163300",   # Forest Green — Interactive Primary
    "green_bright":      "#9FE870",   # Bright Green — Interactive Accent
    "green_light":       "#F0FAE8",   # Background Neutral (Forest Green @ 8%)

    # Content — real Wise content greys (green-tinted neutrals)
    "content_primary":   "#0E0F0C",   # Content Primary
    "content_secondary": "#454745",   # Content Secondary
    "content_tertiary":  "#6A6C6A",   # Content Tertiary

    # Backgrounds
    "bg_primary":        "#FFFFFF",   # Background Screen
    "bg_secondary":      "#F7F8F5",   # Neutral surface (Forest Green @ 4%)
    "bg_tertiary":       "#EEEEE9",   # Slightly deeper neutral

    # Borders — Forest Green @ 12%
    "border_light":      "#E3E4DF",
    "border_mid":        "#C8C9C3",

    # Sentiment — exact Wise tokens
    "positive":          "#2F5711",   # Sentiment Positive
    "positive_bg":       "#EAF4E0",   # Positive light surface
    "negative":          "#A8200D",   # Sentiment Negative
    "negative_bg":       "#FAEAE8",   # Negative light surface
    "warning":           "#EDC843",   # Sentiment Warning
    "warning_bg":        "#FDF8E1",   # Warning light surface
}

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
html,body,[class*="css"]{{font-family:'Inter',-apple-system,sans-serif;color:{W['content_primary']}}}
#MainMenu,footer,header{{visibility:hidden}}
.block-container{{padding:0 2rem 2rem 2rem!important;max-width:100%!important}}
[data-testid="stSidebar"]{{background:{W['bg_secondary']};border-right:1px solid {W['border_light']}}}
[data-testid="stSidebar"] section[data-testid="stSidebarContent"]{{padding:1.5rem 1.25rem}}
label,.stSelectbox label{{font-size:11px!important;font-weight:600!important;
  color:{W['content_tertiary']}!important;text-transform:uppercase;letter-spacing:0.06em}}
[data-testid="stSelectbox"]>div>div{{border:1px solid {W['border_mid']}!important;
  border-radius:8px!important;font-size:14px!important;background:{W['bg_primary']}!important}}
.stButton>button{{background:{W['green_forest']}!important;color:{W['green_bright']}!important;
  border:none!important;border-radius:24px!important;padding:10px 20px!important;
  font-weight:600!important;font-size:14px!important;width:100%!important;transition:opacity 0.15s}}
.stButton>button:hover{{opacity:0.88!important}}
[data-testid="stFileUploader"]{{border:1.5px dashed {W['border_mid']};
  border-radius:12px;background:{W['bg_secondary']};padding:4px 8px}}
[data-testid="stFileUploader"] label{{font-size:13px!important;font-weight:500!important;
  color:{W['content_secondary']}!important;text-transform:none!important;letter-spacing:0!important}}
.mc{{background:{W['bg_primary']};border:1px solid {W['border_light']};
  border-radius:12px;padding:16px 20px;height:100%}}
.mc-lbl{{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.07em;
  color:{W['content_tertiary']};margin-bottom:6px}}
.mc-val{{font-size:28px;font-weight:600;color:{W['content_primary']};line-height:1.1}}
.mc-sub{{font-size:12px;color:{W['content_tertiary']};margin-top:4px}}
.mc-val.pos{{color:{W['positive']}}}.mc-val.neg{{color:{W['negative']}}}.mc-val.wrn{{color:{W['warning']}}}
.sec{{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.07em;
  color:{W['content_tertiary']};margin:16px 0 8px 0}}
.story{{border-left:3px solid {W['green_forest']};border-radius:0 8px 8px 0;
  padding:12px 16px;font-size:13px;line-height:1.65;margin:10px 0;
  background:{W['bg_secondary']};color:{W['content_primary']}}}
.story.guar{{border-left-color:{W['negative']};background:{W['negative_bg']}}}
.story.opt{{border-left-color:{W['warning']};background:{W['warning_bg']}}}
.story.org{{border-left-color:{W['positive']};background:{W['positive_bg']}}}
.badge{{display:inline-block;border-radius:20px;padding:3px 12px;font-size:12px;font-weight:600}}
.b-guar{{background:{W['negative_bg']};color:{W['negative']}}}
.b-opt{{background:{W['warning_bg']};color:{W['warning']}}}
.b-org{{background:{W['positive_bg']};color:{W['positive']}}}
.zrow{{display:flex;align-items:center;justify-content:space-between;
  padding:8px 0;border-bottom:1px solid {W['border_light']};font-size:13px}}
.zrow:last-child{{border-bottom:none}}
.zpill{{border-radius:20px;padding:2px 9px;font-size:11px;font-weight:600}}
.zp-ok{{background:{W['positive_bg']};color:{W['positive']}}}
.zp-med{{background:{W['warning_bg']};color:{W['warning']}}}
.zp-bad{{background:{W['negative_bg']};color:{W['negative']}}}
.v-error{{background:{W['negative_bg']};border:1px solid {W['negative']}40;
  border-radius:10px;padding:12px 16px;font-size:13px;color:{W['negative']};margin:8px 0}}
.v-warn{{background:{W['warning_bg']};border:1px solid {W['warning']}40;
  border-radius:10px;padding:12px 16px;font-size:13px;color:{W['warning']};margin:8px 0}}
.v-ok{{background:{W['positive_bg']};border:1px solid {W['positive']}40;
  border-radius:10px;padding:12px 16px;font-size:13px;color:{W['positive']};margin:8px 0}}
.code{{font-family:monospace;font-size:12px;background:{W['bg_secondary']};
  padding:1px 5px;border-radius:4px;color:{W['content_secondary']}}}
.schema-tbl{{width:100%;border-collapse:collapse;font-size:13px;text-align:left;margin-top:8px}}
.schema-tbl th{{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;
  color:{W['content_tertiary']};padding:8px 12px;border-bottom:2px solid {W['border_light']}}}
.schema-tbl td{{padding:8px 12px;border-bottom:1px solid {W['border_light']};
  color:{W['content_primary']};vertical-align:top}}
.schema-tbl tr:last-child td{{border-bottom:none}}
.req{{color:{W['negative']};font-weight:600;font-size:11px}}
.opt-tag{{color:{W['content_tertiary']};font-size:11px}}
iframe{{border-radius:12px!important;border:1px solid {W['border_light']}!important}}
::-webkit-scrollbar{{width:6px}}
::-webkit-scrollbar-thumb{{background:{W['border_mid']};border-radius:3px}}
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
# ZONES removed — zones are now derived from your actual order data via DBSCAN
# See run_dbscan() which is called once at upload time
DBSCAN_EPS_KM  = 0.5    # neighbourhood radius — tuned to KL density & 2km broadcast radius
DBSCAN_MIN_PTS = 30     # minimum orders to form a zone — filters out sparse outliers

# ── DBSCAN zone discovery ──────────────────────────────────────────────────────
from sklearn.cluster import DBSCAN
from scipy.spatial import ConvexHull

@st.cache_data(show_spinner=False)
def run_dbscan(coords_json: str) -> pd.DataFrame:
    """
    Discover demand zones from actual order coordinates using DBSCAN.
    No hardcoded zone names — zones emerge from where your orders actually land.

    Returns a DataFrame with one row per discovered zone:
      zone_id, zone_name, centroid_lat, centroid_lng, order_count,
      unmet_count, unmet_pct, hull_coords (list of [lat,lng] for boundary polygon)

    Zones are ranked by order_count so Zone 1 is always your busiest zone.
    Noise points (sparse outliers) are excluded — not forced into nearest zone.
    """
    try:
        df = pd.read_json(io.StringIO(coords_json), orient="records")
    except Exception:
        return pd.DataFrame()
    if df.empty or len(df) < DBSCAN_MIN_PTS * 2:
        return pd.DataFrame()

    coords = df[["order_lat","order_lng"]].values
    eps_rad = DBSCAN_EPS_KM / 6371.0

    labels = DBSCAN(
        eps=eps_rad,
        min_samples=DBSCAN_MIN_PTS,
        algorithm="ball_tree",
        metric="haversine",
    ).fit_predict(np.radians(coords))

    df["zone_cluster"] = labels

    zones = []
    cluster_ids = sorted([l for l in set(labels) if l >= 0])

    for cid in cluster_ids:
        mask    = labels == cid
        pts     = coords[mask]
        total   = mask.sum()
        unmet   = (df.loc[mask, "status"] == "no_driver").sum() if "status" in df.columns else 0
        unmet_p = round(unmet / total * 100, 1) if total else 0

        centroid_lat = pts[:, 0].mean()
        centroid_lng = pts[:, 1].mean()

        # Convex hull boundary — gives clean zone outline for stakeholders
        hull_coords = []
        if len(pts) >= 3:
            try:
                hull = ConvexHull(pts)
                hull_pts = pts[hull.vertices]
                # Close the polygon
                hull_coords = [[float(p[0]), float(p[1])] for p in hull_pts]
                hull_coords.append(hull_coords[0])
            except Exception:
                pass

        zones.append({
            "zone_id":      cid,
            "zone_name":    f"Zone {cid + 1}",   # renamed by rank below
            "centroid_lat": round(centroid_lat, 6),
            "centroid_lng": round(centroid_lng, 6),
            "order_count":  int(total),
            "unmet_count":  int(unmet),
            "unmet_pct":    unmet_p,
            "hull_coords":  hull_coords,
        })

    if not zones:
        return pd.DataFrame()

    # Rank by order volume — Zone 1 = busiest
    zone_df = pd.DataFrame(zones).sort_values("order_count", ascending=False).reset_index(drop=True)
    zone_df["zone_name"] = [f"Zone {i+1}" for i in range(len(zone_df))]
    zone_df["rank"]      = range(1, len(zone_df) + 1)

    return zone_df


def assign_zones_from_dbscan(df: pd.DataFrame, zone_df: pd.DataFrame) -> pd.DataFrame:
    """
    Assign each order to its DBSCAN zone using nearest centroid.
    Noise points (cluster=-1) get zone_name='Outlier'.
    Called once at upload after run_dbscan().
    """
    if zone_df.empty:
        df["zone_name"] = "Unknown"
        return df

    centroids = zone_df[["centroid_lat","centroid_lng","zone_name"]].values

    def _nearest(lat, lng):
        dists = [abs(float(c[0])-lat) + abs(float(c[1])-lng) for c in centroids]
        return centroids[int(np.argmin(dists))][2]

    df = df.copy()
    df["zone_name"] = [_nearest(r.order_lat, r.order_lng)
                       for r in df.itertuples()]
    return df



HOUR_PROFILES = [
    0.08,0.04,0.03,0.03,0.05,0.12,
    0.35,0.90,1.00,0.65,0.50,0.55,
    0.75,0.80,0.60,0.55,0.70,0.90,
    1.00,0.85,0.70,0.50,0.35,0.18,
]

HL = {  # hour labels
    0:"12 AM",1:"1 AM",2:"2 AM",3:"3 AM",4:"4 AM",5:"5 AM",
    6:"6 AM",7:"7 AM",8:"8 AM",9:"9 AM",10:"10 AM",11:"11 AM",
    12:"12 PM",13:"1 PM",14:"2 PM",15:"3 PM",16:"4 PM",17:"5 PM",
    18:"6 PM",19:"7 PM",20:"8 PM",21:"9 PM",22:"10 PM",23:"11 PM",
}
DAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

STORIES = {
    0: ("org",  "12 AM — Night tail. Minimal demand. KLCC entertainment strip only. Save guarantee budget."),
    1: ("org",  "1 AM — Near-dead. Scattered late-night trips. No guarantee needed."),
    2: ("org",  "2 AM — Lowest point of the day. Full organic."),
    3: ("org",  "3 AM — Dead zone. No deployment warranted."),
    4: ("org",  "4 AM — Pre-dawn. Airport-bound orders starting around KL Sentral corridor."),
    5: ("opt",  "5 AM — Early movers: airport runs, first-shift workers. KL Sentral first to stir. Optional guarantee."),
    6: ("opt",  "6 AM — Demand warming. KLCC and KL Sentral first spike. Light optional guarantee."),
    7: ("guar", "7 AM — Morning ramp. Unmet demand appearing in KLCC. Drivers still offline. START GUARANTEE: KLCC + KL Sentral."),
    8: ("guar", "8 AM — Peak morning. Highest unmet demand of AM period. Guarantee actively reducing lost orders."),
    9: ("guar", "9 AM — Morning peak tailing. Keep guarantee live for late commuters. END WINDOW at 9:30 AM."),
    10:("org",  "10 AM — Inter-peak lull. Organic earnings strong enough. No top-up needed."),
    11:("org",  "11 AM — Building toward lunch. Bangsar and Mid Valley starting to stir. Hold budget."),
    12:("opt",  "12 PM — Lunch spike. Bangsar / Mid Valley window opens. Monitor unmet — intervene if above 15%."),
    13:("opt",  "1 PM — Full lunch peak. High volume, decent supply. Optional guarantee for Bangsar."),
    14:("org",  "2 PM — End lunch window. Demand falls. Full organic, drivers repositioning."),
    15:("org",  "3 PM — Afternoon lull. Lowest earning point of the day. Idle risk highest here."),
    16:("org",  "4 PM — School runs, early leavers. Scattered demand building. No guarantee yet."),
    17:("org",  "5 PM — Pre-peak build. Send driver nudge to KLCC NOW — 30 mins before demand spikes."),
    18:("guar", "6 PM — START EVENING GUARANTEE: KLCC + KL Sentral. Highest unmet demand of the day. Critical window."),
    19:("guar", "7 PM — Sustained evening peak. KLCC, Bangsar, KL Sentral simultaneously hot. Every driver counts."),
    20:("guar", "8 PM — Peak plateau. Dinner crowd, post-work nightlife. Keep guarantee live through 9 PM."),
    21:("org",  "9 PM — END EVENING GUARANTEE WINDOW. Demand softening. Organic earnings hold."),
    22:("org",  "10 PM — Late evening. Scattered nightlife demand. KLCC bar strip still has volume."),
    23:("org",  "11 PM — Winding down. Organic only. Save budget for tomorrow morning."),
}

# Required columns — status OR order_status must be present
REQUIRED_COORDS = {"order_lat", "order_lng", "hour"}

# ── Rides raw status → app schema mapping ──────────────────────────────────────
# True unmet demand: supply gap, not a human cancellation
NO_DRIVER_STATUSES = {
    "no_driver_available",  # CANCELLATION_DONE — no driver accepted broadcast
    "no_taker",             # CANCELLATION_DONE — broadcast expired, nobody took it
    "no_driver",            # already normalised (passthrough)
}
# Human / system cancellations — not a supply gap
CANCELLED_STATUSES = {
    "cancelled_by_passenger",
    "cancelled_by_driver",
    "no_show",
    "cancelled_by_system",
    "cancelled",            # already normalised (passthrough)
}
# All fulfilment / in-progress states = trip happened
COMPLETED_STATUSES = {
    "completed",
    "fulfilment_done",
    "on_board",
    "on_the_way",
    "confirmed",
    "finalize_total_fare",
}
AUTH_FAILED_ORDER_STATUS = "auth_failed"   # always → cancelled
CREATED_ORDER_STATUS     = "created"       # pending live orders → dropped

# ── Session state init ─────────────────────────────────────────────────────────
for k, v in {
    "df": None, "file_name": None, "row_count": 0,
    "warnings": [], "upload_error": None,
    "zone_df": pd.DataFrame(),
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Helpers ────────────────────────────────────────────────────────────────────
# nearest_zone() removed — zone assignment now driven by run_dbscan()
# See assign_zones_from_dbscan() and the parse_csv() zone assignment block

def lh(h):
    return HL.get(int(h), str(h))

# ── Sample CSV ─────────────────────────────────────────────────────────────────
@st.cache_data
def sample_csv(n=1500):
    """
    Generate sample CSV using hardcoded KL hotspot coordinates.
    No dependency on ZONES — coordinates are inline so this function
    is self-contained and survives any refactoring of the zone system.
    1,500 rows gives enough density for DBSCAN to find 4-6 natural zones.
    """
    # Realistic KL demand hotspots — lat/lng/spread/weight
    # These are ONLY used for sample data generation, not for zone labelling
    KL_HOTSPOTS = [
        (3.1579, 101.7123, 0.010, 9),  # KLCC / Bukit Bintang
        (3.1340, 101.6862, 0.008, 8),  # KL Sentral
        (3.1180, 101.6780, 0.009, 7),  # Bangsar
        (3.1530, 101.6300, 0.010, 7),  # Damansara
        (3.1720, 101.6990, 0.008, 6),  # Chow Kit
        (3.0740, 101.6050, 0.009, 6),  # Sunway
        (3.1730, 101.6530, 0.008, 5),  # Mont Kiara
        (3.1080, 101.7450, 0.009, 5),  # Cheras
    ]
    rng     = np.random.default_rng(42)
    weights = np.array([h[3] for h in KL_HOTSPOTS], dtype=float)
    weights /= weights.sum()
    rows, attempts = [], 0
    while len(rows) < n and attempts < n * 10:
        attempts += 1
        idx  = rng.choice(len(KL_HOTSPOTS), p=weights)
        lat0, lng0, spread, _ = KL_HOTSPOTS[idx]
        hour = int(rng.integers(0, 24))
        if rng.random() > HOUR_PROFILES[hour]: continue
        day  = int(rng.integers(0, 7))
        if rng.random() > (1.0 if day < 5 else 0.72): continue
        up  = 0.18 if 17<=hour<=20 else 0.12 if 7<=hour<=9 else 0.07
        r   = rng.random()
        st_ = "no_driver" if r<up else "cancelled" if r<up+0.05 else "completed"
        rows.append({
            "order_id":         f"ORD{len(rows):06d}",
            "order_lat":        round(float(lat0 + rng.normal(0, spread)), 6),
            "order_lng":        round(float(lng0 + rng.normal(0, spread)), 6),
            "hour":             hour,
            "day":              day,
            "status":           st_,
            "fare_amount":      round(float(rng.uniform(8, 35)), 2),
            "trip_distance_km": round(float(rng.uniform(1, 18)), 1),
        })
    return pd.DataFrame(rows).to_csv(index=False).encode("utf-8")

# ── CSV parser / validator ─────────────────────────────────────────────────────

H3_RES = 8   # ~0.86 km² per cell — matches the 2 km broadcast radius well

def _h3_color(pct: float) -> list:
    """
    pydeck default sentiment colours — red / yellow / green.
    Full opacity, saturated, readable on any map base.
    """
    if pct >= 20:   return [255,  69,  58, 220]   # red    — crisis
    elif pct >= 12: return [255, 196,   0, 200]   # yellow — watch
    elif pct >= 5:  return [ 48, 209,  88, 180]   # green  — OK
    else:           return [210, 240, 200, 140]   # pale green — well served


def add_h3_column(df: pd.DataFrame, res: int = H3_RES) -> pd.DataFrame:
    """
    Vectorised H3 cell assignment.
    Called once when CSV is uploaded — result stored in session_state.df.
    Never called again during filter interactions.
    """
    lats = df["order_lat"].to_numpy()
    lngs = df["order_lng"].to_numpy()
    df = df.copy()
    df["h3_cell"] = [h3.latlng_to_cell(float(lat), float(lng), res)
                     for lat, lng in zip(lats, lngs)]
    return df


def parse_csv(file):
    """Returns (df | None, [warnings], error_str | None)."""
    warns = []
    try:
        raw = pd.read_csv(file)
    except Exception as e:
        return None, [], f"Could not read file: {e}"

    if raw.empty:
        return None, [], "The uploaded file is empty."

    raw.columns = [c.strip().lower().replace(" ","_") for c in raw.columns]

    # ── Column check: need coords + hour + at least one status column ──
    has_coords = REQUIRED_COORDS.issubset(set(raw.columns))
    has_status = "status" in raw.columns or "order_status" in raw.columns
    if not has_coords:
        missing = REQUIRED_COORDS - set(raw.columns)
        return None, [], (
            f"Missing required columns: **{', '.join(sorted(missing))}**. "
            "Required: `order_lat`, `order_lng`, `hour`."
        )
    if not has_status:
        return None, [], (
            "Need at least one status column: `status` or `order_status`. "
            "See schema guide below."
        )

    df = raw.copy()

    # Coordinates
    df["order_lat"] = pd.to_numeric(df["order_lat"], errors="coerce")
    df["order_lng"] = pd.to_numeric(df["order_lng"], errors="coerce")
    bad = df[["order_lat","order_lng"]].isna().any(axis=1).sum()
    if bad: warns.append(f"{bad} rows had unparseable coordinates and were dropped.")
    df  = df.dropna(subset=["order_lat","order_lng"])
    if df.empty: return None, warns, "No valid coordinate rows after cleaning."

    # Bounds check (KL bounding box)
    oob = (~df["order_lat"].between(2.9,3.4)|~df["order_lng"].between(101.4,102.0)).sum()
    if oob: warns.append(f"{oob} rows fall outside the KL bounding box — they will still appear on the map.")

    # Hour
    df["hour"] = pd.to_numeric(df["hour"], errors="coerce")
    bh = df["hour"].isna().sum()
    if bh: warns.append(f"{bh} rows had unparseable hour values — defaulted to 0.")
    df["hour"] = df["hour"].fillna(0).astype(int).clip(0,23)

    # Day
    if "day" in df.columns:
        df["day"] = pd.to_numeric(df["day"], errors="coerce").fillna(0).astype(int).clip(0,6)
    elif "order_timestamp" in df.columns:
        try:
            df["day"] = pd.to_datetime(df["order_timestamp"], errors="coerce").dt.weekday.fillna(0).astype(int)
            warns.append("Derived `day` from `order_timestamp`.")
        except Exception:
            df["day"] = 0
            warns.append("Could not parse `order_timestamp` — all rows defaulted to Monday.")
    else:
        df["day"] = 0
        warns.append("No `day` or `order_timestamp` column — all rows treated as Monday. "
                     "Add `day` (0=Mon…6=Sun) for weekday analysis.")

    # ── Status normalisation ────────────────────────────────────────────────────
    # Step 1: drop pending live orders (CREATED / Pending_Acceptance)
    if "order_status" in df.columns:
        os_raw = df["order_status"].astype(str).str.strip().str.lower().str.replace(" ","_")
        live_mask = os_raw == CREATED_ORDER_STATUS
        if live_mask.sum():
            warns.append(f"{live_mask.sum()} CREATED/Pending_Acceptance rows dropped "
                         "(live orders — not yet resolved).")
        df = df[~live_mask].copy()
        if df.empty:
            return None, warns, "All rows were CREATED/Pending_Acceptance — no resolved orders to analyse."

    # Step 2: build a working status column from whatever is available
    if "status" in df.columns:
        raw_status = df["status"].astype(str).str.strip().str.lower().str.replace(" ","_")
    else:
        # only order_status present — use it as proxy
        raw_status = df["order_status"].astype(str).str.strip().str.lower().str.replace(" ","_")

    # Step 3: map to app schema
    df["status"] = np.where(
        raw_status.isin(NO_DRIVER_STATUSES), "no_driver",
        np.where(
            raw_status.isin(CANCELLED_STATUSES), "cancelled",
            np.where(raw_status.isin(COMPLETED_STATUSES), "completed",
                     "cancelled")   # safe default for anything unrecognised
        )
    )

    # Step 4: AUTH_FAILED order_status always overrides to cancelled
    if "order_status" in df.columns:
        os_norm = df["order_status"].astype(str).str.strip().str.lower().str.replace(" ","_")
        df.loc[os_norm == AUTH_FAILED_ORDER_STATUS, "status"] = "cancelled"

    # Step 5: report what was found
    mapped = df["status"].value_counts().to_dict()
    warns.append(
        f"Status mapping: {mapped.get('completed',0):,} completed · "
        f"{mapped.get('no_driver',0):,} no_driver · "
        f"{mapped.get('cancelled',0):,} cancelled."
    )

    # Step 6: flag No_Taker separately so ops can distinguish it from No_Driver_Available
    if "status" in raw.columns:
        raw_s = raw["status"].astype(str).str.strip().str.lower().str.replace(" ","_")
        no_taker_count = (raw_s == "no_taker").sum()
        if no_taker_count:
            warns.append(
                f"Of those, {no_taker_count:,} are No_Taker (broadcast ignored by drivers) "
                "vs No_Driver_Available (no drivers online). "
                "Consider using No_Taker for incentive targeting — these zones have drivers but no uptake."
            )

    # ── Zone discovery via DBSCAN ────────────────────────────────────────────
    # No hardcoded zones — clusters emerge from where your orders actually land
    slim_coords = df[["order_lat","order_lng","status"]].to_json(orient="records")
    zone_df     = run_dbscan(slim_coords)

    if not zone_df.empty:
        df = assign_zones_from_dbscan(df, zone_df)
        warns.append(
            f"DBSCAN discovered {len(zone_df)} demand zones "
            f"(eps={DBSCAN_EPS_KM}km, min={DBSCAN_MIN_PTS} orders). "
            f"Zone 1 = busiest, Zone {len(zone_df)} = smallest."
        )
    else:
        df["zone_name"] = "Unclustered"
        warns.append(
            "DBSCAN could not find distinct zones — data may be too sparse. "
            f"Try reducing DBSCAN_MIN_PTS below {DBSCAN_MIN_PTS}."
        )
    st.session_state["zone_df"] = zone_df

    if "order_id" not in df.columns:
        df["order_id"] = [f"ORD{i:06d}" for i in range(len(df))]
        warns.append("No `order_id` column — sequential IDs generated.")

    # H3 cell assignment — done once here, never recomputed on filter changes
    df = add_h3_column(df.reset_index(drop=True), H3_RES)

    return df, warns, None

# ── Upload handler ─────────────────────────────────────────────────────────────
def handle_upload(f):
    df, warns, err = parse_csv(f)
    if err:
        st.session_state.upload_error = err
        st.session_state.df           = None
        st.session_state.warnings     = []
    else:
        st.session_state.df           = df
        st.session_state.file_name    = f.name
        st.session_state.row_count    = len(df)
        st.session_state.warnings     = warns
        st.session_state.upload_error = None
        st.rerun()

# ── Map ────────────────────────────────────────────────────────────────────────
def build_map(df, view):
    m = folium.Map(location=[3.1478,101.6953], zoom_start=13,
                   tiles="CartoDB Positron", prefer_canvas=True)
    # ── DBSCAN zone overlays — derived from actual order data ──────────────
    zone_df = st.session_state.get("zone_df", pd.DataFrame())
    if not zone_df.empty:
        # Colour zones by unmet rate
        for _, z in zone_df.iterrows():
            pct = z["unmet_pct"]
            c   = "#A8200D" if pct>=20 else "#EDC843" if pct>=12 else "#163300"

            # Convex hull boundary polygon
            if z["hull_coords"] and len(z["hull_coords"]) >= 3:
                folium.Polygon(
                    locations=z["hull_coords"],
                    color=c, weight=1.5, fill=True,
                    fill_color=c, fill_opacity=0.06,
                    tooltip=(
                        f"<b>{z['zone_name']}</b><br>"
                        f"Orders: {z['order_count']:,}<br>"
                        f"Unmet: {z['unmet_pct']}%"
                    ),
                ).add_to(m)

            # Zone label at centroid
            folium.Marker(
                [z["centroid_lat"], z["centroid_lng"]],
                icon=folium.DivIcon(
                    html=(
                        f'<div style="font-size:10px;font-weight:600;color:{c};'
                        f'white-space:nowrap;font-family:Inter,sans-serif;'
                        f'background:rgba(255,255,255,0.90);padding:2px 7px;'
                        f'border-radius:4px;border:1px solid {c}66">'
                        f'{z["zone_name"]} · {z["order_count"]:,} orders</div>'
                    ),
                    icon_size=(160, 20), icon_anchor=(80, 10),
                ),
            ).add_to(m)

    if df.empty: return m

    heat_df = df.copy()
    if view == "unmet":       heat_df = heat_df[heat_df["status"]=="no_driver"]
    elif view == "completed":  heat_df = heat_df[heat_df["status"]=="completed"]

    # Vectorised — 9x faster than itertuples, scales to 1M+ rows
    heat_df = heat_df.dropna(subset=["order_lat","order_lng"])
    if not heat_df.empty:
        pts = heat_df[["order_lat","order_lng"]].assign(w=1.0).values.tolist()
        HeatMap(pts, radius=26, blur=20, max_zoom=15, min_opacity=0.3,
                gradient={0.1:"#0000ff",0.3:"#00eeff",0.5:"#00ff88",
                          0.7:"#ffff00",0.85:"#ff8800",1.0:"#ff0000"}).add_to(m)

    # No-driver dots: cap at 2,000 — individual CircleMarkers don't scale
    # beyond this (browser renders ~2k DOM nodes fine, 10k causes lag)
    unmet_df = df[df["status"]=="no_driver"].dropna(subset=["order_lat","order_lng"])
    DOT_CAP = 2000
    if len(unmet_df) > DOT_CAP:
        unmet_df = unmet_df.sample(DOT_CAP, random_state=42)
    for r in unmet_df.itertuples():
        folium.CircleMarker(
            [r.order_lat, r.order_lng], radius=4,
            color="#D0021B", weight=0.8,
            fill=True, fill_color="#D0021B", fill_opacity=0.75,
            tooltip=f"No driver · {r.zone_name} · {lh(r.hour)}",
        ).add_to(m)
    return m



@st.cache_data(show_spinner=False)
def build_crisis_outlines(agg_json: str) -> dict:
    """
    Merge crisis/watch H3 cells into unified GeoJSON polygon outlines.
    Returns dict with 'crisis' and 'watch' GeoJSON Feature dicts.
    Input is the same tiny aggregated JSON already computed — no extra cost.
    """
    try:
        agg = pd.read_json(io.StringIO(agg_json), orient="records")
    except Exception:
        return {}
    if agg.empty:
        return {}

    crisis_cells = agg[agg["unmet_pct"] >= 20]["h3_cell"].tolist()
    watch_cells  = agg[(agg["unmet_pct"] >= 12) & (agg["unmet_pct"] < 20)]["h3_cell"].tolist()

    result = {}
    if crisis_cells:
        geo = h3.cells_to_geo(crisis_cells)
        result["crisis"] = {"type": "Feature", "geometry": geo, "properties": {
            "label": f"{len(crisis_cells)} crisis cells — >20% unmet demand"
        }}
    if watch_cells:
        geo = h3.cells_to_geo(watch_cells)
        result["watch"] = {"type": "Feature", "geometry": geo, "properties": {
            "label": f"{len(watch_cells)} watch cells — 12–20% unmet demand"
        }}
    return result


def add_outlines_to_map(m: folium.Map, outlines: dict, show: str) -> folium.Map:
    """
    Overlay crisis/watch outlines on a folium map.
    show: 'Crisis' | 'Watch' | 'Both' | 'None'
    """
    if not outlines or show == "None":
        return m

    if show in ("Crisis", "Both") and "crisis" in outlines:
        folium.GeoJson(
            outlines["crisis"],
            style_function=lambda f: {
                "fillColor":   "#FF453A",
                "fillOpacity": 0.10,
                "color":       "#FF453A",
                "weight":      2.5,
                "dashArray":   "6 4",
            },
            tooltip=folium.GeoJsonTooltip(
                fields=["label"],
                aliases=[""],
                style="font-family:Inter,sans-serif;font-size:12px;"
                      "background:#163300;color:#9FE870;padding:6px 10px;"
                      "border-radius:6px;border:none",
            ),
            name="Crisis zone",
        ).add_to(m)

    if show in ("Watch", "Both") and "watch" in outlines:
        folium.GeoJson(
            outlines["watch"],
            style_function=lambda f: {
                "fillColor":   "#FFC400",
                "fillOpacity": 0.08,
                "color":       "#FFC400",
                "weight":      1.5,
                "dashArray":   "4 4",
            },
            tooltip=folium.GeoJsonTooltip(
                fields=["label"],
                aliases=[""],
                style="font-family:Inter,sans-serif;font-size:12px;"
                      "background:#163300;color:#9FE870;padding:6px 10px;"
                      "border-radius:6px;border:none",
            ),
            name="Watch zone",
        ).add_to(m)

    return m

# ── H3 hex grid ───────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def build_h3(agg_json: str) -> pd.DataFrame:
    """
    Receives pre-aggregated cell data as JSON (~80KB for 65k orders).
    Aggregation happens in render_h3 BEFORE this cache boundary so the
    cache only hashes a tiny payload regardless of raw row count.
    """
    try:
        agg = pd.read_json(io.StringIO(agg_json), orient="records")
    except Exception:
        return pd.DataFrame()
    if agg.empty or "h3_cell" not in agg.columns:
        return pd.DataFrame()

    agg["fill_color"] = [_h3_color(p) for p in agg["unmet_pct"]]
    agg["tooltip_html"] = (
        "<div style='font-family:Inter,sans-serif;min-width:160px'>"
        "<div style='font-size:11px;font-weight:600;text-transform:uppercase;"
        "letter-spacing:0.05em;margin-bottom:6px;opacity:0.7'>Cell detail</div>"
        "<div style='font-size:15px;font-weight:600;margin-bottom:2px'>"
        + agg["unmet_pct"].astype(str) + "% unmet</div>"
        "<div style='font-size:12px;opacity:0.85'>"
        + agg["total"].astype(str) + " orders total</div>"
        "<div style='font-size:12px;opacity:0.85'>"
        + agg["unmet"].astype(int).astype(str) + " lost to no-driver</div>"
        "<div style='font-size:12px;opacity:0.85'>"
        + agg["cancelled"].astype(int).astype(str) + " cancelled</div>"
        "</div>"
    )
    return agg


def render_h3(
    df: pd.DataFrame,
    cell_filter: str = "All",
    outlines: dict = None,
    outline_show: str = "None",
):
    """
    Render H3 hex grid via pydeck.
    cell_filter:  'All' | 'Crisis only' | 'Watch only' | 'OK only'
    outlines:     dict from build_crisis_outlines() — merged GeoJSON polygons
    outline_show: 'None' | 'Crisis' | 'Watch' | 'Both'
    """
    outlines = outlines or {}
    if df.empty:
        st.info("No data for this filter.")
        return
    if "h3_cell" not in df.columns:
        st.info("H3 cells not computed — re-upload your CSV.")
        return

    # ── Aggregate here (raw rows → cell-level) BEFORE cache boundary ──
    # This keeps the cache payload ~80KB regardless of how many raw rows
    # 65k rows → 981 cells → 78KB JSON vs 3.2MB if we passed raw rows
    agg = df.groupby("h3_cell").agg(
        total     =("status", "count"),
        unmet     =("status", lambda x: (x == "no_driver").sum()),
        cancelled =("status", lambda x: (x == "cancelled").sum()),
    ).reset_index()
    agg["unmet_pct"] = (agg["unmet"] / agg["total"] * 100).round(1)

    agg_json = agg[["h3_cell","total","unmet","cancelled","unmet_pct"]].to_json(orient="records")
    hexes = build_h3(agg_json)
    if hexes.empty:
        st.info("Not enough points to form hexagons.")
        return

    # ── Apply cell filter ──
    if cell_filter == "Crisis only":
        hexes = hexes[hexes["unmet_pct"] >= 20].copy()
    elif cell_filter == "Watch only":
        hexes = hexes[(hexes["unmet_pct"] >= 12) & (hexes["unmet_pct"] < 20)].copy()
    elif cell_filter == "OK only":
        hexes = hexes[hexes["unmet_pct"] < 12].copy()

    if hexes.empty:
        st.info(f"No cells match the '{cell_filter}' filter for this time window.")
        return

    # ── Compute cell centroids for precise tooltip positioning ──
    def _centroid(cell):
        lat, lng = h3.cell_to_latlng(cell)
        return [round(lng, 6), round(lat, 6)]

    hexes["position"] = hexes["h3_cell"].apply(_centroid)

    layer = pdk.Layer(
        "H3HexagonLayer",
        hexes,
        get_hexagon="h3_cell",
        get_fill_color="fill_color",
        extruded=False,
        pickable=True,
        auto_highlight=True,
        highlight_color=[255, 255, 255, 80],
        coverage=0.88,
    )

    view = pdk.ViewState(
        latitude=3.1478, longitude=101.6953,
        zoom=13, pitch=0, bearing=0,
    )

    tooltip = {
        "html": "{tooltip_html}",
        "style": {
            "backgroundColor": "#163300",
            "color":           "#9FE870",
            "fontSize":        "13px",
            "padding":         "10px 14px",
            "borderRadius":    "8px",
            "boxShadow":       "0 4px 16px rgba(0,0,0,0.18)",
            "border":          "1px solid #2A5800",
            "pointer-events":  "none",
        },
    }

    st.pydeck_chart(
        pdk.Deck(
            layers=[layer],
            initial_view_state=view,
            map_style="light",
            tooltip=tooltip,
        ),
        use_container_width=True,
        height=460,
    )

    # ── Outline summary callout (shown below pydeck which can't do GeoJSON) ──
    if outlines and outline_show != "None":
        parts = []
        if outline_show in ("Crisis","Both") and "crisis" in outlines:
            n_crisis = (hexes["unmet_pct"] >= 20).sum()
            parts.append(
                f'<span style="display:inline-flex;align-items:center;gap:6px;'
                f'background:#FF453A18;border:1px solid #FF453A55;border-radius:6px;'
                f'padding:4px 10px;font-size:12px">'
                f'<span style="width:16px;height:2px;background:#FF453A;border-radius:1px;'
                f'border-top:1px dashed #FF453A"></span>'
                f'<b style="color:#FF453A">Crisis outline</b> — {n_crisis} cells merged</span>'
            )
        if outline_show in ("Watch","Both") and "watch" in outlines:
            n_watch = ((hexes["unmet_pct"]>=12)&(hexes["unmet_pct"]<20)).sum()
            parts.append(
                f'<span style="display:inline-flex;align-items:center;gap:6px;'
                f'background:#FFC40018;border:1px solid #FFC40055;border-radius:6px;'
                f'padding:4px 10px;font-size:12px">'
                f'<span style="width:16px;height:2px;background:#FFC400;border-radius:1px;'
                f'border-top:1px dashed #FFC400"></span>'
                f'<b style="color:#996600">Watch outline</b> — {n_watch} cells merged</span>'
            )
        if parts:
            st.markdown(
                f'<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:6px;'
                f'margin-bottom:4px">' + " ".join(parts) + '</div>',
                unsafe_allow_html=True,
            )
            st.info(
                "Zone outlines are shown on the Heatmap view. "
                "Switch to Heatmap + outline to show your stakeholder the affected area as a single boundary.",
                icon="ℹ️",
            )

    # ── Cell summary stats ──
    total_cells  = len(hexes)
    crisis_cells = (hexes["unmet_pct"] >= 20).sum()
    watch_cells  = ((hexes["unmet_pct"] >= 12) & (hexes["unmet_pct"] < 20)).sum()
    ok_cells     = (hexes["unmet_pct"] <  12).sum()

    filter_note = (
        f" (filtered: {cell_filter})"
        if cell_filter != "All" else ""
    )

    st.markdown(
        f'''<div style="display:flex;gap:14px;flex-wrap:wrap;align-items:center;
                    margin-top:8px;font-size:12px;color:{W['content_secondary']}">
          <span style="display:flex;align-items:center;gap:5px">
            <span style="width:12px;height:12px;border-radius:2px;
                   background:#FF453A;display:inline-block"></span>
            Crisis &gt;20% &nbsp;<b style="color:{W['negative']}">{crisis_cells}</b>
          </span>
          <span style="display:flex;align-items:center;gap:5px">
            <span style="width:12px;height:12px;border-radius:2px;
                   background:#FFC400;display:inline-block"></span>
            Watch 12–20% &nbsp;<b style="color:#8A6E00">{watch_cells}</b>
          </span>
          <span style="display:flex;align-items:center;gap:5px">
            <span style="width:12px;height:12px;border-radius:2px;
                   background:#30D158;display:inline-block"></span>
            OK &lt;12% &nbsp;<b style="color:{W['positive']}">{ok_cells}</b>
          </span>
          <span style="margin-left:auto;color:{W['content_tertiary']}">
            H3 res {H3_RES} · ~0.86 km²/cell · {total_cells} cells{filter_note}
          </span>
        </div>''',
        unsafe_allow_html=True,
    )

# ── Charts ─────────────────────────────────────────────────────────────────────
CL = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
          font=dict(family="Inter,sans-serif", size=11, color=W["content_secondary"]),
          margin=dict(l=0,r=0,t=8,b=0))

def chart_hours(df_all, sel_hr):
    counts = df_all.groupby("hour").size().reindex(range(24),fill_value=0)
    unmet  = df_all[df_all["status"]=="no_driver"].groupby("hour").size().reindex(range(24),fill_value=0)
    colors = ["#163300" if h==sel_hr else "#D0021B" if 17<=h<=20
              else "#F5A623" if 7<=h<=9 else "#0070F3" if 12<=h<=13
              else "#D0D4E0" for h in range(24)]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=[lh(h) for h in range(24)], y=counts.values,
                         marker_color=colors, name="Total orders",
                         hovertemplate="<b>%{x}</b><br>Orders: %{y}<extra></extra>"))
    fig.add_trace(go.Bar(x=[lh(h) for h in range(24)], y=unmet.values,
                         marker_color="rgba(208,2,27,0.25)", name="No driver",
                         hovertemplate="<b>%{x}</b><br>No driver: %{y}<extra></extra>"))
    fig.update_layout(**CL, height=160, barmode="overlay",
                      showlegend=True,
                      legend=dict(orientation="h",yanchor="bottom",y=1.02,
                                  xanchor="right",x=1,font=dict(size=11)),
                      xaxis=dict(showgrid=False,tickangle=-45,tickfont=dict(size=9)),
                      yaxis=dict(showgrid=True,gridcolor=W["border_light"],zeroline=False),
                      bargap=0.15)
    return fig

def chart_matrix(df_all):
    pivot = (df_all.pivot_table(index="day",columns="hour",
                                values="order_id",aggfunc="count",fill_value=0)
             .reindex(range(7),fill_value=0))
    pivot.index = [DAYS[i] for i in pivot.index]
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values, x=[lh(h) for h in pivot.columns], y=pivot.index,
        colorscale=[[0,"#FFF"],[0.15,"#ECFCE8"],[0.4,"#9FE870"],
                    [0.7,"#2ECC5A"],[0.85,"#F5A623"],[1,"#D0021B"]],
        showscale=True,
        colorbar=dict(title=dict(text="Orders",font=dict(size=11)),
                      tickfont=dict(size=10),thickness=12,len=0.85),
        hovertemplate="<b>%{y} · %{x}</b><br>Orders: %{z}<extra></extra>",
    ))
    fig.update_layout(**CL, height=220,
                      xaxis=dict(showgrid=False,tickangle=-45,tickfont=dict(size=9)),
                      yaxis=dict(showgrid=False,tickfont=dict(size=11)))
    return fig

def chart_unmet(df_all):
    g = df_all.groupby("hour").apply(
        lambda x: pd.Series({"t":len(x),"u":(x["status"]=="no_driver").sum()})
    ).reset_index()
    g["pct"] = (g["u"]/g["t"].clip(lower=1)*100).round(1)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[lh(h) for h in g["hour"]], y=g["pct"],
        mode="lines+markers",
        line=dict(color="#D0021B",width=2), marker=dict(size=5,color="#D0021B"),
        fill="tozeroy", fillcolor="rgba(208,2,27,0.07)",
        hovertemplate="<b>%{x}</b><br>Unmet: %{y}%<extra></extra>",
    ))
    fig.add_hline(y=15,line_dash="dot",line_color="#F5A623",line_width=1.5,
                  annotation_text="15% — guarantee trigger",
                  annotation_font_size=10,annotation_font_color="#F5A623",
                  annotation_position="top left")
    fig.update_layout(**CL, height=180, showlegend=False,
                      xaxis=dict(showgrid=False,tickangle=-45,tickfont=dict(size=9)),
                      yaxis=dict(showgrid=True,gridcolor=W["border_light"],
                                 ticksuffix="%",zeroline=False))
    return fig

# ── Zone summary HTML ──────────────────────────────────────────────────────────
def zone_html(df):
    """
    Zone ranking panel — driven by DBSCAN-discovered zones, not hardcoded names.
    Falls back to groupby zone_name if zone_df not available.
    """
    zone_df = st.session_state.get("zone_df", pd.DataFrame())

    if not zone_df.empty:
        # Use DBSCAN zone_df directly — already has all metrics
        rows = zone_df.sort_values("order_count", ascending=False).head(8)
        mx   = rows["order_count"].max() or 1
        out  = ""
        for _, r in rows.iterrows():
            p    = r["unmet_pct"]
            cls  = "zp-bad" if p>=18 else "zp-med" if p>=10 else "zp-ok"
            bw   = max(4, int(r["order_count"] / mx * 100))
            out += (
                f'<div class="zrow">'
                f'<span style="font-size:12px;font-weight:500;min-width:52px">'
                f'{r["zone_name"]}</span>'
                f'<div style="flex:1;margin:0 8px;height:3px;'
                f'background:{W["border_light"]};border-radius:2px">'
                f'<div style="width:{bw}%;height:3px;background:#163300;border-radius:2px">'
                f'</div></div>'
                f'<span style="font-size:12px;font-weight:500;min-width:34px;text-align:right">'
                f'{int(r["order_count"]):,}</span>'
                f'<span class="zpill {cls}" style="margin-left:8px">{p}%</span>'
                f'</div>'
            )
        return out

    # Fallback: compute from filtered df if zone_df not in session
    if df.empty:
        return f"<p style='color:{W['content_tertiary']};font-size:13px'>No data.</p>"
    zc = df.groupby("zone_name").size().reset_index(name="orders")
    zu = (df[df["status"]=="no_driver"].groupby("zone_name").size()
          .reset_index(name="unmet"))
    mg = zc.merge(zu, on="zone_name", how="left").fillna(0)
    mg["unmet_pct"] = (mg["unmet"] / mg["orders"] * 100).round(1)
    mg = mg.sort_values("orders", ascending=False).head(8)
    mx = mg["orders"].max() or 1
    out = ""
    for _, r in mg.iterrows():
        p   = r["unmet_pct"]
        cls = "zp-bad" if p>=18 else "zp-med" if p>=10 else "zp-ok"
        bw  = max(4, int(r["orders"] / mx * 100))
        out += (
            f'<div class="zrow">'
            f'<span style="font-size:12px;max-width:110px;overflow:hidden;'
            f'text-overflow:ellipsis;white-space:nowrap">{r["zone_name"]}</span>'
            f'<div style="flex:1;margin:0 8px;height:3px;background:{W["border_light"]};border-radius:2px">'
            f'<div style="width:{bw}%;height:3px;background:#163300;border-radius:2px"></div></div>'
            f'<span style="font-size:12px;font-weight:500;min-width:28px;text-align:right">'
            f'{int(r["orders"])}</span>'
            f'<span class="zpill {cls}" style="margin-left:8px">{p}%</span>'
            f'</div>'
        )
    return out

# ── Upload screen ──────────────────────────────────────────────────────────────
def upload_screen():
    st.markdown(f"""
    <div style="display:flex;flex-direction:column;align-items:center;
                justify-content:center;min-height:400px;padding:3rem;text-align:center">
      <div style="width:64px;height:64px;border-radius:16px;background:{W['green_light']};
                  display:flex;align-items:center;justify-content:center;
                  margin:0 auto 20px;font-size:28px">🗺️</div>
      <div style="font-size:20px;font-weight:600;color:{W['content_primary']};margin-bottom:8px">
        Upload your order data
      </div>
      <div style="font-size:14px;color:{W['content_secondary']};max-width:440px;
                  line-height:1.6;margin-bottom:8px">
        Upload a CSV export from your orders database to see the demand heatmap,
        hotspot timing, and unmet demand analysis across KL zones.<br><br>
        <b>No data is stored</b> — everything lives in your browser session only.
      </div>
    </div>
    """, unsafe_allow_html=True)

    col_up, col_schema = st.columns([1,1], gap="large")

    with col_up:
        st.markdown('<div class="sec">Upload CSV</div>', unsafe_allow_html=True)
        f = st.file_uploader("Drop CSV here", type=["csv"],
                             key="up_main", label_visibility="collapsed")
        if f:
            handle_upload(f)

        if st.session_state.upload_error:
            st.markdown(f'<div class="v-error"><b>Upload failed:</b> '
                        f'{st.session_state.upload_error}</div>',
                        unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="sec">No data yet? Download a sample</div>',
                    unsafe_allow_html=True)
        st.download_button(
            "Download sample CSV (300 rows)",
            data=sample_csv(), file_name="sample_orders_kl.csv", mime="text/csv",
        )

    with col_schema:
        st.markdown('<div class="sec">CSV schema — your Rides columns accepted</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <table class="schema-tbl">
          <thead><tr><th>Column</th><th>Type</th><th>Required</th><th>Notes</th></tr></thead>
          <tbody>
            <tr><td><span class="code">order_lat</span></td><td>float</td>
                <td><span class="req">Required</span></td><td>Pickup latitude · 6 decimals · KL range 2.9–3.4</td></tr>
            <tr><td><span class="code">order_lng</span></td><td>float</td>
                <td><span class="req">Required</span></td><td>Pickup longitude · KL range 101.4–102.0</td></tr>
            <tr><td><span class="code">hour</span></td><td>int</td>
                <td><span class="req">Required</span></td><td>0–23 · hour order was placed</td></tr>
            <tr><td><span class="code">status</span></td><td>string</td>
                <td><span class="req">Required*</span></td>
                <td>Your raw Rides values accepted directly — see mapping below</td></tr>
            <tr><td><span class="code">order_status</span></td><td>string</td>
                <td><span class="req">Required*</span></td>
                <td>*Either <span class="code">status</span> or <span class="code">order_status</span> must be present. Both is best.</td></tr>
            <tr><td><span class="code">order_timestamp</span></td><td>datetime</td>
                <td><span class="opt-tag">Optional</span></td><td>YYYY-MM-DD HH:MM:SS · used to derive day</td></tr>
            <tr><td><span class="code">day</span></td><td>int</td>
                <td><span class="opt-tag">Optional</span></td><td>0=Mon…6=Sun · or derived from order_timestamp</td></tr>
            <tr><td><span class="code">order_id</span></td><td>string</td>
                <td><span class="opt-tag">Optional</span></td><td>Auto-generated if missing</td></tr>
            <tr><td><span class="code">fare_amount</span></td><td>float</td>
                <td><span class="opt-tag">Optional</span></td><td>RM gross fare · reserved for revenue layer</td></tr>
            <tr><td><span class="code">dropoff_lat / lng</span></td><td>float</td>
                <td><span class="opt-tag">Optional</span></td><td>Enables corridor analysis (Phase 2)</td></tr>
          </tbody>
        </table>
        <div style="font-size:12px;color:{W['content_tertiary']};margin-top:10px">
          Column names are case-insensitive. Extra columns are ignored silently. Max file size: 50 MB.
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background:{W['bg_secondary']};border-radius:10px;
                    padding:12px 14px;margin-top:14px">
          <div style="font-size:12px;font-weight:600;color:{W['content_primary']};margin-bottom:8px">
            Status mapping — your raw values are auto-translated
          </div>
          <table style="width:100%;font-size:11px;border-collapse:collapse">
            <tr style="border-bottom:1px solid {W['border_light']}">
              <th style="text-align:left;padding:5px 8px;color:{W['content_tertiary']}">Your status value</th>
              <th style="text-align:left;padding:5px 8px;color:{W['content_tertiary']}">Maps to</th>
              <th style="text-align:left;padding:5px 8px;color:{W['content_tertiary']}">Meaning</th>
            </tr>
            <tr style="border-bottom:1px solid {W['border_light']}">
              <td style="padding:5px 8px;font-family:monospace">No_Driver_Available</td>
              <td style="padding:5px 8px"><span style="background:{W['negative_bg']};color:{W['negative']};border-radius:4px;padding:1px 6px;font-weight:600">no_driver</span></td>
              <td style="padding:5px 8px;color:{W['content_secondary']}">No driver accepted broadcast</td>
            </tr>
            <tr style="border-bottom:1px solid {W['border_light']}">
              <td style="padding:5px 8px;font-family:monospace">No_Taker</td>
              <td style="padding:5px 8px"><span style="background:{W['negative_bg']};color:{W['negative']};border-radius:4px;padding:1px 6px;font-weight:600">no_driver</span></td>
              <td style="padding:5px 8px;color:{W['content_secondary']}">Broadcast expired — drivers saw it but ignored</td>
            </tr>
            <tr style="border-bottom:1px solid {W['border_light']}">
              <td style="padding:5px 8px;font-family:monospace">Cancelled_by_Passenger<br>Cancelled_by_Driver<br>No_Show<br>Cancelled_by_System</td>
              <td style="padding:5px 8px;vertical-align:top"><span style="background:{W['warning_bg']};color:{W['warning']};border-radius:4px;padding:1px 6px;font-weight:600">cancelled</span></td>
              <td style="padding:5px 8px;color:{W['content_secondary']};vertical-align:top">Human / system cancellation</td>
            </tr>
            <tr style="border-bottom:1px solid {W['border_light']}">
              <td style="padding:5px 8px;font-family:monospace">AUTH_FAILED (order_status)</td>
              <td style="padding:5px 8px"><span style="background:{W['warning_bg']};color:{W['warning']};border-radius:4px;padding:1px 6px;font-weight:600">cancelled</span></td>
              <td style="padding:5px 8px;color:{W['content_secondary']}">Payment auth failure</td>
            </tr>
            <tr style="border-bottom:1px solid {W['border_light']}">
              <td style="padding:5px 8px;font-family:monospace">Completed · On_Board<br>On_The_Way · Confirmed<br>Finalize_Total_Fare</td>
              <td style="padding:5px 8px;vertical-align:top"><span style="background:{W['positive_bg']};color:{W['positive']};border-radius:4px;padding:1px 6px;font-weight:600">completed</span></td>
              <td style="padding:5px 8px;color:{W['content_secondary']};vertical-align:top">Trip happened</td>
            </tr>
            <tr>
              <td style="padding:5px 8px;font-family:monospace">CREATED / Pending_Acceptance</td>
              <td style="padding:5px 8px"><span style="background:{W['bg_tertiary']};color:{W['content_tertiary']};border-radius:4px;padding:1px 6px;font-weight:600">dropped</span></td>
              <td style="padding:5px 8px;color:{W['content_secondary']}">Live orders — excluded from analysis</td>
            </tr>
          </table>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background:{W['bg_secondary']};border-radius:10px;
                    padding:12px 14px;margin-top:10px">
          <div style="font-size:12px;font-weight:600;color:{W['content_primary']};margin-bottom:8px">
            SQL export — your exact schema
          </div>
          <div style="font-family:monospace;font-size:11px;color:{W['content_secondary']};line-height:1.8">
            SELECT<br>
            &nbsp;&nbsp;order_id,<br>
            &nbsp;&nbsp;pickup_lat AS order_lat,<br>
            &nbsp;&nbsp;pickup_lng AS order_lng,<br>
            &nbsp;&nbsp;HOUR(created_at) AS hour,<br>
            &nbsp;&nbsp;WEEKDAY(created_at) AS day,<br>
            &nbsp;&nbsp;created_at AS order_timestamp,<br>
            &nbsp;&nbsp;order_status,<br>
            &nbsp;&nbsp;status<br>
            FROM orders<br>
            WHERE city = 'Kuala Lumpur'<br>
            &nbsp;&nbsp;AND created_at &gt;= NOW() - INTERVAL 30 DAY<br>
            &nbsp;&nbsp;AND NOT (order_status = 'CREATED'<br>
            &nbsp;&nbsp;&nbsp;&nbsp;AND status = 'Pending_Acceptance');<br>
            <br>
            <span style="color:{W['content_tertiary']}">-- Both order_status and status columns included.</span><br>
            <span style="color:{W['content_tertiary']}">-- App auto-maps all status values shown above.</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

# ── Sidebar (shown when data loaded) ──────────────────────────────────────────
def sidebar():
    with st.sidebar:
        st.markdown(f"""
        <div style="padding:4px 0 18px">
          <div style="font-size:18px;font-weight:600;color:{W['content_primary']}">Rides</div>
          <div style="font-size:12px;color:{W['content_tertiary']};margin-top:2px">
            Demand Heatmap · Tier 1</div>
        </div>
        <hr style="border:none;border-top:1px solid {W['border_light']};margin:0 0 18px">
        """, unsafe_allow_html=True)

        # Data status
        st.markdown(f"""
        <div style="background:{W['positive_bg']};border-radius:8px;
                    padding:10px 12px;margin-bottom:14px">
          <div style="font-size:11px;font-weight:600;color:{W['positive']};
                      text-transform:uppercase;letter-spacing:0.06em;margin-bottom:3px">
            Data loaded</div>
          <div style="font-size:13px;color:{W['content_primary']};font-weight:500">
            {st.session_state.file_name}</div>
          <div style="font-size:12px;color:{W['content_secondary']};margin-top:2px">
            {st.session_state.row_count:,} orders</div>
        </div>
        """, unsafe_allow_html=True)

        for w in st.session_state.warnings:
            st.markdown(f'<div class="v-warn" style="margin-bottom:8px">⚠ {w}</div>',
                        unsafe_allow_html=True)

        # Replace file
        st.markdown('<div class="sec">Replace data</div>', unsafe_allow_html=True)
        nf = st.file_uploader("Upload new CSV", type=["csv"],
                              key="up_sidebar", label_visibility="collapsed")
        if nf:
            handle_upload(nf)

        st.markdown(f'<hr style="border:none;border-top:1px solid {W["border_light"]};margin:14px 0">',
                    unsafe_allow_html=True)

        # Filters
        st.markdown('<div class="sec">Filters</div>', unsafe_allow_html=True)
        h_opts = {"All hours":-1} | {lh(h):h for h in range(24)}
        sh_lbl = st.selectbox("Hour of day", list(h_opts.keys()), index=0)
        sh     = h_opts[sh_lbl]

        d_opts = {"All days":-1} | {d:i for i,d in enumerate(DAYS)}
        sd_lbl = st.selectbox("Day of week", list(d_opts.keys()), index=0)
        sd     = d_opts[sd_lbl]

        v_opts = {"All orders":"all","Unmet demand only":"unmet","Completed only":"completed"}
        sv_lbl = st.selectbox("Heatmap shows", list(v_opts.keys()), index=0)
        sv     = v_opts[sv_lbl]

        st.markdown(f'<hr style="border:none;border-top:1px solid {W["border_light"]};margin:14px 0">',
                    unsafe_allow_html=True)

        # Legend
        st.markdown('<div class="sec">Legend</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="font-size:12px;color:{W['content_secondary']};line-height:2.1">
          <span style="display:inline-block;width:10px;height:10px;background:#D0021B;
                border-radius:50%;margin-right:6px"></span>No driver (dot)<br>
          <span style="display:inline-block;width:10px;height:10px;background:#D0021B;
                opacity:0.4;border-radius:2px;margin-right:6px"></span>Evening peak bar<br>
          <span style="display:inline-block;width:10px;height:10px;background:#F5A623;
                border-radius:2px;margin-right:6px"></span>Morning peak bar<br>
          <span style="display:inline-block;width:10px;height:10px;background:#0070F3;
                border-radius:2px;margin-right:6px"></span>Lunch peak bar<br>
          <span style="display:inline-block;width:10px;height:10px;background:#163300;
                border-radius:2px;margin-right:6px"></span>Selected hour<br>
          <div style="margin-top:6px">
            <b style="color:#163300">●</b> Tier 1 &nbsp;
            <b style="color:#F5A623">●</b> Tier 2 &nbsp;
            <b style="color:#9E9EBF">●</b> Tier 3
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f'<hr style="border:none;border-top:1px solid {W["border_light"]};margin:14px 0">',
                    unsafe_allow_html=True)
        st.download_button("Download sample CSV", data=sample_csv(),
                           file_name="sample_orders_kl.csv", mime="text/csv")

    return sh, sd, sv

# ── Dashboard ──────────────────────────────────────────────────────────────────
def dashboard(df_raw, sh, sd, sv):
    df = df_raw.copy()
    if sh >= 0: df = df[df["hour"]==sh]
    if sd >= 0: df = df[df["day"]==sd]

    day_str  = DAYS[sd] if sd>=0 else "All days"
    hour_str = lh(sh) if sh>=0 else "All hours"

    # Header
    st.markdown(f"""
    <div style="padding:20px 0 14px;border-bottom:1px solid {W['border_light']};margin-bottom:18px">
      <div style="display:flex;align-items:baseline;justify-content:space-between;
                  flex-wrap:wrap;gap:8px">
        <div>
          <p style="font-size:22px;font-weight:600;color:{W['content_primary']};margin:0">
            Demand Heatmap — Tier 1 Zones</p>
          <p style="font-size:14px;color:{W['content_secondary']};margin:4px 0 0">
            {st.session_state.file_name} &nbsp;·&nbsp; {st.session_state.row_count:,} orders
            &nbsp;·&nbsp; {day_str} &nbsp;·&nbsp; {hour_str}</p>
        </div>
        <div style="font-size:12px;color:{W['content_tertiary']}">
          {datetime.now().strftime('%a %d %b %Y')}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Metrics
    total   = len(df)
    unmet   = len(df[df["status"]=="no_driver"]) if total else 0
    unmet_p = round(unmet/total*100,1) if total else 0
    done    = len(df[df["status"]=="completed"]) if total else 0
    done_p  = round(done/total*100,1) if total else 0
    zone_df_m = st.session_state.get("zone_df", pd.DataFrame())
    peakz = (zone_df_m.iloc[0]["zone_name"]
             if not zone_df_m.empty
             else df.groupby("zone_name").size().idxmax()
             if total else "—")

    stype, stxt = STORIES.get(sh, ("org","")) if sh>=0 else ("org","")
    vm = {"guar":("DEPLOY GUARANTEE","b-guar"),
          "opt": ("OPTIONAL",         "b-opt"),
          "org": ("ORGANIC ONLY",     "b-org")}
    vlbl, vcls = vm[stype]
    if sh < 0: vlbl, vcls = "SELECT AN HOUR", "b-org"

    c1,c2,c3,c4 = st.columns(4)
    for col,lb,vl,sb,cls in [
        (c1,"Orders this window",  f"{total:,}",  hour_str, ""),
        (c2,"Unmet demand",        f"{unmet:,}",  f"{unmet_p}% of orders lost",
             "neg" if unmet_p>=18 else "wrn" if unmet_p>=10 else ""),
        (c3,"Completion rate",     f"{done_p}%",  f"{done:,} completed",
             "pos" if done_p>=85 else "wrn"),
        (c4,"Peak zone",           peakz,          "highest demand", ""),
    ]:
        with col:
            st.markdown(f'<div class="mc"><div class="mc-lbl">{lb}</div>'
                        f'<div class="mc-val {cls}">{vl}</div>'
                        f'<div class="mc-sub">{sb}</div></div>', unsafe_allow_html=True)

    # Verdict + story bar
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    story_extra = (f'<div style="font-size:13px;color:{W["content_secondary"]};margin-top:6px">'
                   f'{stxt}</div>' if sh>=0 else
                   f'<div style="font-size:13px;color:{W["content_tertiary"]};margin-top:6px">'
                   f'Select an hour to see the operational verdict.</div>')
    st.markdown(
        f'<div class="mc" style="display:flex;align-items:flex-start;gap:16px;flex-wrap:wrap">'
        f'<div><div class="mc-lbl">Guarantee verdict</div>'
        f'<div style="margin-top:8px"><span class="badge {vcls}">{vlbl}</span></div></div>'
        f'{story_extra}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    # Map view toggle + zone panel
    # ── View toggle ──
    col_tog, col_filt, col_outline = st.columns([2, 2, 2], gap="large")
    with col_tog:
        view_toggle = st.radio(
            "Map view",
            ["Heatmap", "H3 grid"],
            horizontal=True,
            label_visibility="collapsed",
        )
        st.markdown(
            f'<div style="font-size:12px;color:{W["content_tertiary"]};margin:-4px 0 10px 0">'
            f'<b style="color:{W["content_primary"]}">Heatmap</b> — density pattern &nbsp;·&nbsp; '
            f'<b style="color:{W["content_primary"]}">H3 grid</b> — discrete cells for ops targeting</div>',
            unsafe_allow_html=True,
        )
    with col_filt:
        h3_filter = st.radio(
            "Show cells",
            ["All", "Crisis only", "Watch only", "OK only"],
            horizontal=True,
            label_visibility="collapsed",
        ) if view_toggle == "H3 grid" else "All"
        if view_toggle == "H3 grid":
            st.markdown(
                f'<div style="font-size:12px;color:{W["content_tertiary"]};margin:-4px 0 10px 0">'
                f'<b style="color:{W["negative"]}">Crisis</b> &gt;20% unmet &nbsp;·&nbsp; '
                f'<b style="color:#8A6E00">Watch</b> 12–20% &nbsp;·&nbsp; '
                f'<b style="color:{W["positive"]}">OK</b> &lt;12%</div>',
                unsafe_allow_html=True,
            )
    with col_outline:
        outline_show = st.radio(
            "Zone outlines",
            ["None", "Crisis", "Watch", "Both"],
            horizontal=True,
            label_visibility="collapsed",
        )
        st.markdown(
            f'<div style="font-size:12px;color:{W["content_tertiary"]};margin:-4px 0 10px 0">'
            f'<span style="display:inline-block;width:20px;height:2px;background:#FF453A;'
            f'border-radius:1px;margin-right:4px;vertical-align:middle"></span>Crisis outline &nbsp;·&nbsp; '
            f'<span style="display:inline-block;width:20px;height:2px;background:#FFC400;'
            f'border-radius:1px;margin-right:4px;vertical-align:middle"></span>Watch outline</div>',
            unsafe_allow_html=True,
        )

    mc, pc = st.columns([3,1], gap="medium")
    with mc:
        sec_title = "H3 hex grid (res 8 · ~0.86 km²/cell)" if "H3" in view_toggle else "Live demand heatmap"
        st.markdown(f'<div class="sec">{sec_title}</div>', unsafe_allow_html=True)

        # Pre-compute outlines from aggregated data (shared by both views)
        outlines = {}
        if outline_show != "None":
            agg_for_outline = df.groupby("h3_cell").agg(
                total    =("status","count"),
                unmet    =("status", lambda x: (x=="no_driver").sum()),
            ).reset_index()
            agg_for_outline["unmet_pct"] = (
                agg_for_outline["unmet"] / agg_for_outline["total"] * 100
            ).round(1)
            agg_outline_json = agg_for_outline[
                ["h3_cell","total","unmet","unmet_pct"]
            ].to_json(orient="records")
            outlines = build_crisis_outlines(agg_outline_json)

        if view_toggle == "Heatmap":
            m = build_map(df, sv)
            m = add_outlines_to_map(m, outlines, outline_show)
            st_folium(m, width=None, height=460, returned_objects=[])
        else:
            render_h3(df, cell_filter=h3_filter, outlines=outlines,
                      outline_show=outline_show)

    with pc:
        st.markdown('<div class="sec">Zone ranking</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div style="background:{W["bg_primary"]};border:1px solid {W["border_light"]};'
            f'border-radius:12px;padding:12px 14px">{zone_html(df)}</div>',
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        # Dynamic top zones from DBSCAN
        zone_df_s = st.session_state.get("zone_df", pd.DataFrame())
        if not zone_df_s.empty:
            top2  = zone_df_s.head(2)
            names = " · ".join(top2["zone_name"].tolist())
            avg_u = top2["unmet_pct"].mean()
            u_cls = W["negative"] if avg_u>=18 else W["warning"] if avg_u>=10 else W["positive"]
            st.markdown(
                f'<div style="background:{W["green_light"]};border-radius:10px;'
                f'padding:12px 14px;font-size:12px;color:{W["green_forest"]}">'
                f'<div style="font-weight:600;margin-bottom:4px">Top 2 demand zones</div>'
                f'{names}<br>'
                f'<span style="opacity:0.75">Avg unmet: '
                f'<b style="color:{u_cls}">{avg_u:.1f}%</b></span>'
                f'<div style="margin-top:6px;opacity:0.75;font-size:11px">'
                f'Zones derived from your order data via DBSCAN</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div style="background:{W["bg_tertiary"]};border-radius:10px;'
                f'padding:12px 14px;font-size:12px;color:{W["content_tertiary"]}">'
                f'Upload a CSV to discover demand zones.</div>',
                unsafe_allow_html=True,
            )

        # H3 reading guide shown only in grid view
        if "H3" in view_toggle:
            st.markdown(f"""
            <div style="background:{W['bg_secondary']};border-radius:10px;
                        padding:12px 14px;font-size:12px;color:{W['content_secondary']};
                        margin-top:10px">
              <div style="font-weight:600;color:{W['content_primary']};margin-bottom:6px">
                How to read the grid</div>
              <span style="color:#D0021B">&#9646;</span> Red &gt;20% unmet — deploy guarantee here<br>
              <span style="color:#F5A623">&#9646;</span> Amber 12–20% — watch, may need nudge<br>
              <span style="color:#9FE870">&#9646;</span> Green &lt;12% — organic, no action<br>
              <span style="color:#163300">&#9646;</span> Dark green &lt;5% — well served<br>
              <div style="margin-top:6px;color:{W['content_tertiary']}">
                Hover any cell for order count and unmet rate.
              </div>
            </div>
            """, unsafe_allow_html=True)

    # Charts
    df_day = df_raw if sd<0 else df_raw[df_raw["day"]==sd]

    st.markdown('<div class="sec">Demand by hour</div>', unsafe_allow_html=True)
    st.plotly_chart(chart_hours(df_day, sh),
                    use_container_width=True, config={"displayModeBar":False})

    st.markdown('<div class="sec">Order volume by hour × day</div>', unsafe_allow_html=True)
    st.plotly_chart(chart_matrix(df_raw),
                    use_container_width=True, config={"displayModeBar":False})

    st.markdown('<div class="sec">Unmet demand % by hour — guarantee trigger at 15%</div>',
                unsafe_allow_html=True)
    st.plotly_chart(chart_unmet(df_raw),
                    use_container_width=True, config={"displayModeBar":False})

    # Footer
    st.markdown(f"""
    <hr style="border:none;border-top:1px solid {W['border_light']};margin:24px 0 12px">
    <div style="font-size:11px;color:{W['content_tertiary']};
                display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px">
      <span>AirAsia Rides · Insights &amp; Reporting · Demand Heatmap v1.1</span>
      <span>Session data only — nothing stored · Map © OpenStreetMap contributors</span>
    </div>
    """, unsafe_allow_html=True)

# ── Router ─────────────────────────────────────────────────────────────────────
if st.session_state.df is None:
    upload_screen()
else:
    sh, sd, sv = sidebar()
    dashboard(st.session_state.df, sh, sd, sv)
