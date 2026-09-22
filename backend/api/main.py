from fastapi import FastAPI, Depends, HTTPException, Security, Request
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
import time
import pandas as pd
import numpy as np

from backend.db.database import get_db, engine, Base
from backend.engine.index_chain_calc import SovereignEconometricEngine

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

# ── HELPER: Generate synthetic multi-month route data ─────────────
def _make_route_dataframe(seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    routes = ["BOM-DEL", "BLR-BOM", "DEL-CCU", "HYD-MAA", "DEL-BOM", "CCU-BLR"]
    return pd.DataFrame({
        "route": routes,
        "base_price_t0": rng.uniform(2500, 7000, len(routes)),
        "base_price_t1": rng.uniform(2700, 7500, len(routes)),
        "passenger_volume_t0": rng.integers(300, 1200, len(routes)).astype(float),
        "passenger_volume_t1": rng.integers(280, 1250, len(routes)).astype(float),
    })

# ── ENDPOINT: National Inflation Metrics ─────────────────────────
@app.get("/api/v1/inflation/national")
def get_national_inflation(
    base_year: int = 2026,
    request: Request = None,
    api_key: str = Depends(get_api_key),
):
    rate_limiter(request)
    route_data = _make_route_dataframe()
    engine_obj = SovereignEconometricEngine(base_year=base_year)
    result = engine_obj.build_inflation_vectors(route_data, base_year=base_year)
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
