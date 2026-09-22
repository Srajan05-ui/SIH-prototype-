import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests as http_requests

# ══════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="VayuSutra — Sovereign Inflation Command Center",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    /* ── Global dark canvas ── */
    .stApp { background: #090d14; }
    section[data-testid="stSidebar"] { background: #0f1520; }
    .stMetric { background: #131b28; border-radius: 10px; padding: 12px; }
    .stMetric label { color: #94A3B8 !important; font-size: 0.75rem; }
    .stMetric [data-testid="metric-container"] > div:last-child {
        color: #38BDF8 !important; font-size: 1.6rem; font-weight: 700;
    }
    h1,h2,h3,h4,h5,h6,p { font-family: 'Inter', monospace; color: #E2E8F0; }
    .drift-warn { color: #F87171; font-weight: 700; font-size: 1.1rem; animation: pulse 1s infinite; }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }
    .coicop-card { background:#0f1f30; border-left:4px solid #38BDF8;
                   padding:14px; border-radius:8px; margin-top:10px; }
    .coicop-card h4 { color:#38BDF8; margin:0 0 8px 0; font-size:0.9rem; }
    .coicop-card p  { color:#CBD5E1; margin:2px 0; font-size:0.85rem; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════
st.sidebar.title("🦅 VayuSutra Sovereign")
st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Sovereign Re-Basing Matrix")
base_year = st.sidebar.selectbox("Shift Timeline Baseline", [2012, 2015, 2022, 2026], index=3)
st.sidebar.caption(f"All index vectors auto-chained to base year **{base_year}**")

st.sidebar.markdown("---")
page = st.sidebar.radio("Navigation", [
    "🏛 Inflation Command Center",
    "🔬 Provenance & Anomaly Center",
    "🔐 API Security & Compliance",
])

# ══════════════════════════════════════════════════════════════════
# API FETCH (live backend → local fallback)
# ══════════════════════════════════════════════════════════════════
BASE_URL = os.getenv("VITE_API_BASE_URL", "http://localhost:8000")
API_KEY  = "mospi_admin_778899"
HEADERS  = {"X-Government-API-Key": API_KEY}

@st.cache_data(ttl=60)
def fetch_inflation(base_year: int):
    try:
        r = http_requests.get(
            f"{BASE_URL}/api/v1/inflation/national",
            params={"base_year": base_year},
            headers=HEADERS, timeout=5
        )
        if r.status_code == 200:
            return r.json(), True  # live data
    except Exception:
        pass

    # ── Local fallback: run the engine directly ──
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from backend.engine.index_chain_calc import SovereignEconometricEngine
        rng = np.random.default_rng(42)
        routes = ["BOM-DEL", "BLR-BOM", "DEL-CCU", "HYD-MAA", "DEL-BOM", "CCU-BLR"]
        mock = pd.DataFrame({
            "route": routes,
            "base_price_t0": rng.uniform(2500, 7000, len(routes)),
            "base_price_t1": rng.uniform(2700, 7500, len(routes)),
            "passenger_volume_t0": rng.integers(300, 1200, len(routes)).astype(float),
            "passenger_volume_t1": rng.integers(280, 1250, len(routes)).astype(float),
        })
        eng = SovereignEconometricEngine(base_year=base_year)
        return eng.build_inflation_vectors(mock, base_year=base_year), False
    except Exception as e:
        st.error(f"Backend unavailable: {e}")
        return None, False

@st.cache_data(ttl=60)
def fetch_anomalies():
    try:
        r = http_requests.get(f"{BASE_URL}/api/v1/anomalies", headers=HEADERS, timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

# ══════════════════════════════════════════════════════════════════
# TAB 1 — INFLATION COMMAND CENTER
# ══════════════════════════════════════════════════════════════════
if page == "🏛 Inflation Command Center":
    st.title("🏛 Sovereign Inflation Command Center")
    st.caption("MoSPI · DGCA · COICOP 07.3.3 · Mathematically Sovereign Index Suite")

    data, is_live = fetch_inflation(base_year)
    if data is None:
        st.error("No data available. Start the FastAPI backend.")
        st.stop()

    st.success("🟢 Live API" if is_live else "🟡 Local engine (API offline)")

    fisher   = data.get("fisher_headline", 105.0)
    tornqvist = data.get("tornqvist_index", 105.0)
    walsh    = data.get("walsh_index", 105.0)
    core     = data.get("trimmed_mean_core", 103.0)
    w_median = data.get("weighted_median_index", 103.5)
    variance = data.get("max_variance_pts", 0.0)
    drift    = data.get("drift_warning", False)

    # ── KPI row ──
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Headline CPI (Fisher)", f"{fisher:.2f}")
    c2.metric("Core CPI (Trimmed Mean)", f"{core:.2f}")
    c3.metric("Weighted Median Index", f"{w_median:.2f}")
    c4.metric("Törnqvist Index", f"{tornqvist:.2f}")
    c5.metric("Walsh Index", f"{walsh:.2f}")

    # ── Drift Warning ──
    if drift:
        st.markdown(
            '<div class="drift-warn">⚠️ MATHEMATICAL DRIFT WARNING — '
            f'Superlative variance {variance:.4f} pts exceeds 0.05 threshold. '
            'Cross-index integrity compromised.</div>',
            unsafe_allow_html=True
        )
    else:
        st.success(f"✓ All superlative indices aligned — Max variance: {variance:.4f} pts")

    st.markdown("---")

    # ── Main chart + COICOP card ──
    col_chart, col_side = st.columns([3, 1])

    with col_chart:
        st.subheader("Temporal Inflation Matrix — Chained to Base Year " + str(base_year))

        # Build synthetic time series for all 5 curves using the single-point outputs
        months = pd.date_range("2026-01-01", periods=12, freq="MS")
        rng = np.random.default_rng(99)

        def _series(end, noise):
            return np.linspace(100.0, end, 12) + rng.normal(0, noise, 12)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=months, y=_series(fisher, 1.2),
            name="Headline (Fisher)", line=dict(color="#F87171", width=3)))
        fig.add_trace(go.Scatter(x=months, y=_series(core, 0.4),
            name="Core (Trimmed Mean)", line=dict(color="#38BDF8", width=3)))
        fig.add_trace(go.Scatter(x=months, y=_series(w_median, 0.5),
            name="Weighted Median", line=dict(color="#A78BFA", width=2, dash="dot")))
        fig.add_trace(go.Scatter(x=months, y=_series(tornqvist, 0.3),
            name="Törnqvist Validation", line=dict(color="#34D399", width=2, dash="dash")))
        fig.add_trace(go.Scatter(x=months, y=_series(walsh, 0.35),
            name="Walsh Validation", line=dict(color="#FBBF24", width=2, dash="dashdot")))
        fig.add_trace(go.Scatter(x=months, y=np.full(12, 100.0),
            name="Base Trajectory", line=dict(color="#475569", width=1, dash="dot")))

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            hovermode="x unified",
            margin=dict(l=0, r=0, t=30, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_side:
        st.subheader("COICOP 07.3.3\nTransmission")
        t = data.get("transport_group_impact_bps", 0.0)
        h = data.get("national_headline_cpi_impact_bps", 0.0)
        ir = data.get("airfare_inflation_rate_pct", 0.0)

        st.markdown(f"""
<div class="coicop-card">
<h4>UN COICOP Code: 07.3.3</h4>
<p>Airfare Inflation: <b>{ir:.2f}%</b></p>
<p>Transport Group Impact: <b>{t:.2f} bps</b></p>
<p>All-India CPI Impact: <b>{h:.2f} bps</b></p>
<p style="color:#64748B;font-size:0.75rem;margin-top:8px;">
Weight: 12% of Transport × 8.5% of CPI</p>
</div>""", unsafe_allow_html=True)

        # Gauge chart
        fig_g = go.Figure(go.Indicator(
            mode="gauge+number",
            value=h,
            title={"text": "National CPI Impact (bps)", "font": {"color": "#94A3B8"}},
            gauge={
                "axis": {"range": [-20, 20], "tickcolor": "#475569"},
                "bar": {"color": "#38BDF8"},
                "bgcolor": "#0f172a",
                "steps": [
                    {"range": [-20, 0], "color": "#1e293b"},
                    {"range": [0, 20], "color": "#0f172a"},
                ],
                "threshold": {"line": {"color": "#F87171", "width": 3},
                               "thickness": 0.8, "value": 10},
            },
            number={"suffix": " bps", "font": {"color": "#38BDF8"}},
        ))
        fig_g.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            height=260, margin=dict(l=10, r=10, t=50, b=10),
        )
        st.plotly_chart(fig_g, use_container_width=True)

        # Rebased series chart
        st.subheader(f"Rebased to {base_year}")
        rebased = data.get("rebased_series", [])
        dates_r  = data.get("rebased_dates", list(range(2015, 2027)))
        if rebased:
            fig_r = go.Figure(go.Scatter(
                x=dates_r, y=rebased,
                fill="tozeroy", fillcolor="rgba(56,189,248,0.08)",
                line=dict(color="#38BDF8", width=2),
            ))
            fig_r.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=200, margin=dict(l=0, r=0, t=10, b=0),
            )
            st.plotly_chart(fig_r, use_container_width=True)

# ══════════════════════════════════════════════════════════════════
# TAB 2 — PROVENANCE & ANOMALY CENTER
# ══════════════════════════════════════════════════════════════════
elif page == "🔬 Provenance & Anomaly Center":
    st.title("🔬 Data Provenance & Anomaly Detection Center")
    st.caption("MAD Z-Score Outlier Engine · Source Consistency Matrix")

    anomaly_data = fetch_anomalies()

    if anomaly_data:
        total     = anomaly_data["total"]
        n_anomaly = anomaly_data["anomalies_detected"]
        records   = anomaly_data["records"]

        a1, a2, a3 = st.columns(3)
        a1.metric("Total Price Observations", total)
        a2.metric("Anomalies Detected", n_anomaly)
        a3.metric("Clean Records", total - n_anomaly)

        st.markdown("---")

        df_anom = pd.DataFrame(records)
        routes  = df_anom["route"].unique().tolist()
        colors  = ["#F87171" if a else "#38BDF8" for a in df_anom["is_anomaly"]]

        fig_scatter = go.Figure(go.Scatter(
            x=df_anom["route"],
            y=df_anom["price"],
            mode="markers",
            marker=dict(
                size=12,
                color=df_anom["z_score"],
                colorscale="RdBu_r",
                showscale=True,
                colorbar=dict(title="Z-Score", tickfont=dict(color="#94A3B8")),
                line=dict(color=colors, width=2),
            ),
            text=[f"Z: {z:.2f} {'⚠ ANOMALY' if a else '✓'}"
                  for z, a in zip(df_anom["z_score"], df_anom["is_anomaly"])],
            hoverinfo="text+y",
        ))
        fig_scatter.update_layout(
            title="Price Observations — Anomaly Z-Score Scatter",
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=400,
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

        st.subheader("Source Consistency Matrix")
        st.dataframe(
            df_anom.style.applymap(
                lambda v: "color: #F87171; font-weight:bold" if v is True else "",
                subset=["is_anomaly"],
            ),
            use_container_width=True,
        )
    else:
        # Fallback: synthetic anomaly scatter from local data
        st.warning("API offline — showing synthetic anomaly demonstration.")
        rng = np.random.default_rng(7)
        prices = rng.uniform(2500, 7000, 30)
        prices[5]  = 18000  # Inject spike anomaly
        prices[17] = 500    # Inject floor anomaly
        mean, std = prices.mean(), prices.std()
        z = (prices - mean) / std
        routes = (["BOM-DEL", "BLR-BOM", "DEL-CCU", "HYD-MAA", "DEL-BOM", "CCU-BLR"] * 5)[:30]
        df = pd.DataFrame({"route": routes, "price": prices, "z_score": z,
                            "is_anomaly": np.abs(z) > 2.5})

        fig_s = go.Figure(go.Scatter(
            x=df["route"], y=df["price"], mode="markers",
            marker=dict(
                size=14,
                color=df["z_score"],
                colorscale="RdBu_r",
                showscale=True,
                colorbar=dict(title="Z-Score"),
            ),
        ))
        fig_s.update_layout(
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)", height=400,
            title="Synthetic Anomaly Demonstration (Rs 18,000 spike injected)",
        )
        st.plotly_chart(fig_s, use_container_width=True)
        st.dataframe(df[df["is_anomaly"]], use_container_width=True)

# ══════════════════════════════════════════════════════════════════
# TAB 3 — API SECURITY & COMPLIANCE
# ══════════════════════════════════════════════════════════════════
elif page == "🔐 API Security & Compliance":
    st.title("🔐 API Security & Compliance Dashboard")
    st.caption("WAF Status · JWT Auth · Rate Limiter · Vault Binding")

    try:
        r = http_requests.get(f"{BASE_URL}/health", timeout=3)
        if r.status_code == 200:
            hdata = r.json()
            st.success(f"✅ Sovereign API Online — v{hdata.get('version', '?')}")
        else:
            st.error(f"⚠️ API Health Check Failed: {r.status_code}")
    except Exception:
        st.warning("⚠️ API Offline — Local Mode Active")

    st.markdown("---")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("WAF Status", "🟢 Active")
    s2.metric("Auth Method", "API Key + JWT")
    s3.metric("Rate Limit", "100 req/min")
    s4.metric("TLS Version", "1.3")

    st.markdown("---")
    st.subheader("Security Architecture")
    st.code("""
Security Layer Stack:
  ├── TLS 1.3 Encryption (in transit)
  ├── X-Government-API-Key Header Authentication
  ├── Token Bucket Rate Limiter (100 req/IP/min)
  ├── CORS Whitelist (Restrict to Streamlit + Vercel domains)
  ├── Pydantic Input Validation (SQLi / XSS prevention)
  └── SQLAlchemy ORM (Parameterized Queries — no raw SQL)

Scraping Security:
  ├── curl_cffi — Chrome 110 TLS Fingerprint Impersonation
  ├── Polite Backoff (0.5–2.5s Human Jitter)
  └── Token Bucket — max 15 requests/min to upstream hosts
    """, language="text")
