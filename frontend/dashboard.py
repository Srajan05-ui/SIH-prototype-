import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import requests

# ==========================================
# PAGE CONFIGURATION (High-Density Dark Theme)
# ==========================================
st.set_page_config(
    page_title="Sovereign Inflation Command Center",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark Theme CSS overrides
st.markdown("""
<style>
    .reportview-container {
        background: #0B0E14;
    }
    .sidebar .sidebar-content {
        background: #151A22;
    }
    h1, h2, h3, h4, h5, h6, p, span, div {
        color: #E2E8F0;
        font-family: 'Inter', 'Fira Code', monospace;
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #38BDF8;
    }
    @keyframes flash {
        0% { background-color: #F87171; color: #0B0E14; }
        50% { background-color: transparent; color: #F87171; }
        100% { background-color: #F87171; color: #0B0E14; }
    }
    .variance-alert {
        color: #F87171 !important;
        font-weight: bold;
        padding: 10px;
        border-radius: 5px;
        animation: flash 1s infinite;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# SIDEBAR: Sovereign Re-Basing Matrix
# ==========================================
st.sidebar.title("🦅 VayuSutra")
st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Sovereign Re-Basing Matrix")
base_year = st.sidebar.selectbox("Select Timeline Baseline", [2012, 2022, 2026], index=2)
st.sidebar.markdown(f"*All calculations dynamically chained to base year {base_year}*")

st.sidebar.markdown("---")
st.sidebar.subheader("System Modules")
page = st.sidebar.radio("Navigation", [
    "Inflation Command Center", 
    "Provenance & Anomaly Center",
    "API Security & Compliance"
])

# ==========================================
# API FETCH (To FastAPI Backend)
# ==========================================
def fetch_inflation_vectors(base_year):
    api_url = "http://localhost:8000/api/v1/inflation_vectors"
    
    try:
        response = requests.get(api_url, params={"base_year": base_year}, timeout=2)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data)
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    except requests.exceptions.RequestException as e:
        # Graceful fallback to mock data if backend is unreachable
        st.sidebar.warning("⚠️ Backend API Unreachable. Using Simulation Mode.")
        dates = pd.date_range(start="2026-01-01", periods=12, freq='MS')
        
        # Simulate the curves
        fisher_headline = np.linspace(100, 112, 12) + np.random.normal(0, 1.5, 12)
        trimmed_core = np.linspace(100, 108, 12) + np.random.normal(0, 0.5, 12) 
        # Adding a bit of drift if base_year is 2012 to show off the visual alert functionality
        drift = 0.1 if base_year == 2012 else 0.02
        tornqvist_val = fisher_headline + np.random.normal(0, drift, 12)
        
        # Rebase simulation logic
        multiplier = 1.0
        if base_year == 2012: multiplier = 1.8
        elif base_year == 2022: multiplier = 1.2
            
        return pd.DataFrame({
            'Date': dates,
            'Headline (Fisher)': fisher_headline * multiplier,
            'Core (Trimmed Mean)': trimmed_core * multiplier,
            'Törnqvist Validation': tornqvist_val * multiplier,
            'Historical Base': np.full(12, 100.0 * multiplier)
        })

# ==========================================
# MAIN DASHBOARD TAB: Command Center
# ==========================================
if page == "Inflation Command Center":
    st.title("Sovereign Inflation Command Center")
    st.markdown("Cryptographically Secure Macroeconomic Airfare Indices")
    
    # Fetch Data
    df = fetch_inflation_vectors(base_year)
    current_headline = df['Headline (Fisher)'].iloc[-1]
    current_core = df['Core (Trimmed Mean)'].iloc[-1]
    current_tornqvist = df['Törnqvist Validation'].iloc[-1]
    variance = abs(current_headline - current_tornqvist)
    
    # --- Top Row KPIs ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Headline CPI (Fisher)", f"{current_headline:.2f}", "+1.2%")
    with col2:
        st.metric("Core CPI (Trimmed Mean)", f"{current_core:.2f}", "+0.5%")
    with col3:
        st.metric("Törnqvist Variance", f"{variance:.4f} pts")
    with col4:
        if variance > 0.05:
            st.markdown('<div class="variance-alert">⚠️ WARNING: Index Drift Detected</div>', unsafe_allow_html=True)
        else:
            st.success("✓ Indices Aligned")

    st.markdown("---")
    
    # --- Multi-line Charting & COICOP Side Card ---
    col_chart, col_side = st.columns([3, 1])
    
    with col_chart:
        st.subheader("Temporal Inflation Matrix")
        fig = go.Figure()
        
        # Headline (Red/Orange)
        fig.add_trace(go.Scatter(x=df['Date'], y=df['Headline (Fisher)'], name="Headline (Fisher)", line=dict(color='#F87171', width=3)))
        # Core (Blue)
        fig.add_trace(go.Scatter(x=df['Date'], y=df['Core (Trimmed Mean)'], name="Core (Trimmed Mean)", line=dict(color='#38BDF8', width=3)))
        # Tornqvist (Green Dash)
        fig.add_trace(go.Scatter(x=df['Date'], y=df['Törnqvist Validation'], name="Törnqvist Validation", line=dict(color='#34D399', width=2, dash='dash')))
        # Base (Grey Dotted)
        fig.add_trace(go.Scatter(x=df['Date'], y=df['Historical Base'], name="Base Trajectory", line=dict(color='#94A3B8', width=1, dash='dot')))
        
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            hovermode="x unified",
            margin=dict(l=0, r=0, t=30, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_side:
        st.subheader("Transmission Metrics")
        st.markdown("**UN COICOP Code:** `07.3.3`")
        
        # Calculate Basis Points Impact
        inflation_rate = (current_headline - (100 * (1.8 if base_year==2012 else 1.2 if base_year==2022 else 1.0))) / 100.0
        cpi_impact_bps = inflation_rate * (0.12 * 0.085) * 10000
        
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = cpi_impact_bps,
            title = {'text': "National CPI Impact (bps)"},
            gauge = {
                'axis': {'range': [-50, 50]},
                'bar': {'color': "#38BDF8"},
                'steps': [
                    {'range': [-50, 0], 'color': "#1E293B"},
                    {'range': [0, 50], 'color': "#0F172A"}
                ],
            }
        ))
        fig_gauge.update_layout(
            template="plotly_dark", 
            paper_bgcolor='rgba(0,0,0,0)',
            height=250,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_gauge, use_container_width=True)
        st.info("Direct transmission vector to All-India Headline CPI via Transport Group weighting.")

elif page == "Provenance & Anomaly Center":
    st.title("Data Provenance & Anomaly Center")
    st.info("Under Construction - Scatter Plot & Source Consistency Matrix pending Phase 4.")

elif page == "API Security & Compliance":
    st.title("API Security & Compliance")
    st.info("Under Construction - Vault Status & SIEM Audit Logs pending Phase 4.")

