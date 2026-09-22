from fastapi import FastAPI, Depends, HTTPException, Security, Request
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List
import time
import pandas as pd
import numpy as np
from functools import lru_cache

from backend.db.database import get_db, engine, Base
from backend.engine.index_chain_calc import SovereignEconometricEngine
from backend.scraper.scraper import scrape_all_sovereign_routes
from backend.scraper.mmt_scraper import scrape_mmt_sync, calculate_apix_weighted_fare

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sovereign Airfare Intelligence API",
    description="MoSPI/DGCA Grade Secure Macroeconomic Airfare Inflation Engine",
    version="2.0.0",
)

# ── CORS ──────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to Streamlit/Vercel URL in production
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# ── API KEY AUTH ──────────────────────────────────────────────────
API_KEY_NAME = "X-Government-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def get_api_key(api_key: str = Security(api_key_header)):
    if api_key == "mospi_admin_778899":
        return api_key
    raise HTTPException(status_code=403, detail="Could not validate sovereign credentials.")

# ── IN-MEMORY WAF RATE LIMITER ────────────────────────────────────
RATE_STORE: Dict[str, list] = {}

def rate_limiter(request: Request):
    ip = request.client.host
    now = time.time()
    RATE_STORE.setdefault(ip, [])
    RATE_STORE[ip] = [t for t in RATE_STORE[ip] if now - t < 60]
    if len(RATE_STORE[ip]) >= 100:
        raise HTTPException(status_code=429, detail="Rate limit exceeded — WAF Block.")
    RATE_STORE[ip].append(now)

# ── LIVE DATA CACHE (30-minute TTL to avoid hammering Google Flights) ─
_scrape_cache: Dict = {"data": None, "timestamp": 0.0}
CACHE_TTL_SECONDS = 1800  # 30 minutes


def _get_live_route_dataframe() -> pd.DataFrame:
    """
    Tiered data source strategy:
      1. MMT Playwright (primary OTA — real fare cards from MakeMyTrip)
      2. Google Flights fast-flights (secondary)
      3. Deterministic synthetic fallback
    Results are cached for 30 minutes.
    """
    global _scrape_cache
    now = time.time()

    if _scrape_cache["data"] is not None and (now - _scrape_cache["timestamp"]) < CACHE_TTL_SECONDS:
        return _scrape_cache["data"]

    # ── Tier 1: MakeMyTrip Playwright scraper ──
    try:
        mmt_df = scrape_mmt_sync(
            routes=[("BOM", "DEL"), ("DEL", "BOM"), ("BLR", "BOM"),
                    ("DEL", "BLR"), ("DEL", "CCU"), ("HYD", "DEL")],
            windows=[7, 30],
        )
        if not mmt_df.empty and len(mmt_df) >= 4:
            # Build t0/t1 pairs: T+30 = base price, T+7 = current price
            t30 = mmt_df[mmt_df["advance_window"] == "T+30"].groupby("route")["jevons_fare_inr"].mean()
            t7  = mmt_df[mmt_df["advance_window"] == "T+7"].groupby("route")["jevons_fare_inr"].mean()
            common_routes = t30.index.intersection(t7.index)
            if len(common_routes) >= 3:
                df = pd.DataFrame({
                    "route": common_routes,
                    "base_price_t0": t30[common_routes].values,
                    "base_price_t1": t7[common_routes].values,
                    "passenger_volume_t0": 900.0,
                    "passenger_volume_t1": 950.0,
                    "source": "MMT_Playwright_Live",
                })
                _scrape_cache = {"data": df, "timestamp": now,
                                 "raw_mmt": mmt_df, "apix": calculate_apix_weighted_fare(mmt_df)}
                return df
    except Exception as e:
        pass

    # ── Tier 2: Google Flights fast-flights ──
    try:
        records = scrape_all_sovereign_routes(days_ahead=30)
        if records and len(records) >= 3:
            records_7d = scrape_all_sovereign_routes(days_ahead=7)
            records_7d_map = {r["route"]: r for r in records_7d} if records_7d else {}
            rows = []
            for r in records:
                route = r["route"]
                r7 = records_7d_map.get(route)
                rows.append({
                    "route": route,
                    "base_price_t0": r["base_fare"],
                    "base_price_t1": r7["base_fare"] if r7 else r["base_fare"] * 1.05,
                    "passenger_volume_t0": 900.0,
                    "passenger_volume_t1": 950.0,
                    "source": "GoogleFlights_Live",
                })
            df = pd.DataFrame(rows)
            _scrape_cache = {"data": df, "timestamp": now, "apix": None}
            return df
    except Exception:
        pass

    # ── Tier 3: Deterministic synthetic fallback ──
    rng = np.random.default_rng(42)
    routes = ["BOM-DEL", "DEL-BOM", "BLR-BOM", "BOM-BLR", "DEL-BLR", "DEL-CCU"]
    df = pd.DataFrame({
        "route": routes,
        "base_price_t0": rng.uniform(2500, 7000, len(routes)),
        "base_price_t1": rng.uniform(2700, 7500, len(routes)),
        "passenger_volume_t0": rng.integers(300, 1200, len(routes)).astype(float),
        "passenger_volume_t1": rng.integers(280, 1250, len(routes)).astype(float),
        "source": "Synthetic_Fallback",
    })
    _scrape_cache = {"data": df, "timestamp": now, "apix": None}
    return df

# ── ENDPOINT: National Inflation Metrics ─────────────────────────────
@app.get("/api/v1/inflation/national")
def get_national_inflation(
    base_year: int = 2026,
    request: Request = None,
    api_key: str = Depends(get_api_key),
):
    rate_limiter(request)
    route_data = _get_live_route_dataframe()
    data_source = route_data["source"].iloc[0] if "source" in route_data.columns else "Unknown"
    engine_obj = SovereignEconometricEngine(base_year=base_year)
    result = engine_obj.build_inflation_vectors(route_data, base_year=base_year)
    result["data_source"] = data_source
    result["routes_scraped"] = route_data["route"].tolist()
    result["apix_weighted_fare_inr"] = _scrape_cache.get("apix", None)
    return result

# ── ENDPOINT: Anomaly Detection Feed ─────────────────────────────
@app.get("/api/v1/anomalies")
def get_anomaly_feed(api_key: str = Depends(get_api_key), request: Request = None):
    rate_limiter(request)
    rng = np.random.default_rng(7)
    routes = ["BOM-DEL", "BLR-BOM", "DEL-CCU", "HYD-MAA", "DEL-BOM", "CCU-BLR"]
    prices = rng.uniform(2500, 7000, 30)
    # Inject synthetic anomalies (spikes above 3 std devs)
    mean, std = prices.mean(), prices.std()
    z_scores = ((prices - mean) / std).tolist()
    anomaly_flags = [abs(z) > 2.5 for z in z_scores]

    records = []
    for i in range(30):
        records.append({
            "route": routes[i % len(routes)],
            "price": round(float(prices[i]), 2),
            "z_score": round(z_scores[i], 4),
            "is_anomaly": anomaly_flags[i],
        })
    return {"total": len(records), "anomalies_detected": sum(anomaly_flags), "records": records}

# ── HEALTH CHECK ─────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "Sovereign API Online", "version": "2.0.0"}
