import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import requests

# ==========================================
# PAGE CONFIGURATION (Bright & Colorful)
# ==========================================
st.set_page_config(
    page_title="Sovereign Inflation Command Center",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Colorful CSS overrides (No Black/Gray)
st.markdown("""
<style>
    .reportview-container { background: #FFFFFF; }
    .sidebar .sidebar-content { background: #F5F3FF; }
    h1, h2, h3, h4, h5, h6, p, span, div {
        font-family: 'Inter', sans-serif;
        color: #1E1B4B;
    }
    .metric-value { font-size: 2.5rem; font-weight: 700; color: #0D6EFD; }
    
    @keyframes flash {
        0% { background-color: #DC3545; color: #FFFFFF; }
        50% { background-color: transparent; color: #DC3545; }
        100% { background-color: #DC3545; color: #FFFFFF; }
    }
    .variance-alert {
        color: #DC3545 !important;
        font-weight: bold;
        padding: 10px;
        border-radius: 5px;
        animation: flash 1s infinite;
        text-align: center;
        border: 2px solid #DC3545;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# SIDEBAR
# ==========================================
st.sidebar.title("🦅 VayuSutra")
st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Sovereign Re-Basing")
base_year = st.sidebar.selectbox("Select Timeline Baseline", [2012, 2022, 2026], index=2)

st.sidebar.markdown("---")
st.sidebar.subheader("System Modules")
page = st.sidebar.radio("Navigation", [
    "Inflation Command Center", 
    "Provenance & Anomaly Center",
    "API Security & Compliance"
])

# ==========================================
# DATA FETCHING
# ==========================================
@st.cache_data(ttl=60)
def fetch_inflation_vectors(base_year):
    api_url = "http://localhost:8000/api/v1/inflation_vectors"
    try:
        response = requests.get(api_url, params={"base_year": base_year}, timeout=2)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data)
        df['Date'] = pd.to_datetime(df['Date'])
        return df, True
    except requests.exceptions.RequestException:
        # Graceful fallback mock
        dates = pd.date_range(start="2026-01-01", periods=12, freq='ME')
        fisher_headline = np.linspace(100, 112, 12) + np.random.normal(0, 1.5, 12)
        trimmed_core = np.linspace(100, 108, 12) + np.random.normal(0, 0.5, 12) 
        drift = 0.1 if base_year == 2012 else 0.02
        tornqvist_val = fisher_headline + np.random.normal(0, drift, 12)
        
        multiplier = 1.8 if base_year == 2012 else 1.2 if base_year == 2022 else 1.0
            
        df = pd.DataFrame({
            'Date': dates,
            'Headline (Fisher)': fisher_headline * multiplier,
            'Core (Trimmed Mean)': trimmed_core * multiplier,
            'Törnqvist Validation': tornqvist_val * multiplier,
            'Historical Base': np.full(12, 100.0 * multiplier)
        })
        return df, False

df, is_live = fetch_inflation_vectors(base_year)
if not is_live:
    st.sidebar.warning("⚠️ Backend API Unreachable. Using Simulation Mode.")
else:
    st.sidebar.success("🟢 Live API Connected")

# ==========================================
# PAGE 1: COMMAND CENTER
# ==========================================
if page == "Inflation Command Center":
    st.title("Sovereign Inflation Command Center")
    
    current_headline = df['Headline (Fisher)'].iloc[-1]
    current_core = df['Core (Trimmed Mean)'].iloc[-1]
    current_tornqvist = df['Törnqvist Validation'].iloc[-1]
    variance = abs(current_headline - current_tornqvist)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Headline CPI (Fisher)", f"{current_headline:.2f}", "+1.2%")
    col2.metric("Core CPI (Trimmed)", f"{current_core:.2f}", "+0.5%")
    col3.metric("Törnqvist Variance", f"{variance:.4f} pts")
    
    with col4:
        if variance > 0.05:
            st.markdown('<div class="variance-alert">⚠️ WARNING: Index Drift Detected</div>', unsafe_allow_html=True)
        else:
            st.success("✓ Indices Aligned")

    st.markdown("---")
    
    col_chart, col_side = st.columns([3, 1])
    with col_chart:
        st.subheader("Temporal Inflation Matrix")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['Date'], y=df['Headline (Fisher)'], name="Headline", line=dict(color='#0D6EFD', width=3)))
        fig.add_trace(go.Scatter(x=df['Date'], y=df['Core (Trimmed Mean)'], name="Core", line=dict(color='#6F42C1', width=3)))
        fig.add_trace(go.Scatter(x=df['Date'], y=df['Törnqvist Validation'], name="Törnqvist", line=dict(color='#20C997', width=2, dash='dash')))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

    with col_side:
        st.subheader("Transmission")
        cpi_impact_bps = ((current_headline - 100) / 100.0) * (0.12 * 0.085) * 10000
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number", value = cpi_impact_bps, title = {'text': "CPI Impact (bps)"},
            gauge = {'axis': {'range': [-50, 50]}, 'bar': {'color': "#FFB703"}}
        ))
        st.plotly_chart(fig_gauge, use_container_width=True)

# ==========================================
# PAGE 2: PROVENANCE & ANOMALIES
# ==========================================
elif page == "Provenance & Anomaly Center":
    st.title("Data Provenance & Anomaly Center")
    st.markdown("Monitor real-time scraped prices and algorithmic outlier detection.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("MAD Z-Score Outlier Detection")
        # Colorful Scatter Plot
        np.random.seed(42)
        anomaly_df = pd.DataFrame({
            'Route': ['DEL-BOM', 'BLR-DEL', 'BOM-BLR', 'HYD-MAA', 'CCU-DEL'] * 10,
            'Price': np.random.normal(5000, 1000, 50),
            'Z-Score': np.random.normal(1, 1.5, 50),
            'Volume': np.random.randint(100, 1000, 50)
        })
        anomaly_df.loc[0:4, 'Price'] += 8000 # Create huge spikes
        anomaly_df.loc[0:4, 'Z-Score'] += 4.0
        
        # Color based on severity
        anomaly_df['Status'] = np.where(anomaly_df['Z-Score'] > 3, 'Severe Anomaly', 
                               np.where(anomaly_df['Z-Score'] > 2, 'Warning', 'Normal'))
        
        fig = px.scatter(
            anomaly_df, x="Route", y="Price", size="Volume", color="Status",
            color_discrete_map={"Severe Anomaly": "#DC3545", "Warning": "#FFB703", "Normal": "#20C997"},
            hover_data=['Z-Score']
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.subheader("Ingestion Consistency Matrix")
        # Attractive Table
        table_data = pd.DataFrame({
            "Time": ["07:30", "07:32", "07:45", "08:00"],
            "Route": ["BOM-DEL", "DEL-BLR", "HYD-MAA", "CCU-DEL"],
            "DGCA Base": ["₹4,500", "₹6,200", "₹3,100", "₹5,500"],
            "OTA Scraped": ["₹14,500", "₹6,350", "₹3,100", "₹7,200"],
            "Variance": ["+222%", "+2.4%", "0.0%", "+30.9%"],
            "System Action": ["STRIPPED 🔴", "VALIDATED 🟢", "VALIDATED 🟢", "AUDIT 🟡"]
        })
        st.dataframe(table_data, use_container_width=True, hide_index=True)

# ==========================================
# PAGE 3: API SECURITY
# ==========================================
elif page == "API Security & Compliance":
    st.title("API Security & Compliance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("JWT Validation Origins")
        # Colorful Doughnut Chart
        fig = px.pie(
            values=[85, 10, 5], names=['Valid Tokens', 'Expired', 'Malformed/Attack'],
            hole=0.5, color_discrete_sequence=['#20C997', '#FFB703', '#DC3545']
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.subheader("Threat Vector Radar")
        # Radar Chart
        categories = ['Rate Limits', 'SQLi Attempts', 'Bot Traffic', 'Geo-Blocks', 'JWT Forgeries']
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=[12, 1, 45, 8, 2], theta=categories, fill='toself',
            marker=dict(color='#6F42C1')
        ))
        st.plotly_chart(fig, use_container_width=True)
        
    st.subheader("SIEM Audit Logs")
    logs = pd.DataFrame({
        "Timestamp": ["2026-09-23 01:12:44", "2026-09-23 01:14:02", "2026-09-23 01:18:11"],
        "IP Address": ["192.168.1.105", "10.0.0.52", "192.168.1.200"],
        "Endpoint": ["/api/inflation", "/api/trigger", "/api/simulate"],
        "HTTP Status": ["200 OK 🟢", "403 Forbidden 🔴", "429 Rate Limit 🟡"]
    })
    st.dataframe(logs, use_container_width=True, hide_index=True)
