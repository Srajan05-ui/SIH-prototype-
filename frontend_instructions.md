# Frontend Developer Instructions

**Primary Domain:** `frontend/`, `dashboard.py` (Streamlit)

## 1. Core Responsibilities
Your primary objective is to render the quantitative data into a highly dense, executive-level Sovereign Dashboard for policymakers, without doing any heavy mathematics on the client side.

### A. API Consumption
- **Rule #1:** You must NOT calculate inflation math (Fisher, Törnqvist, Trimmed Means) in the frontend.
- Use Python `requests` or `httpx` to ping the Backend Developer's FastAPI endpoints to fetch pre-calculated JSON vectors.
- Handle API connection failures gracefully.

### B. UI Implementation (`dashboard.py`)
- Maintain the High-Density Dark Theme as specified in `design_doc.md`. Use `#0B0E14` and `#151A22` hex codes for the primary UI canvas.
- Maintain the `⚙️ Sovereign Re-Basing Matrix` dropdown. When a user shifts the timeline (e.g., from 2026 to 2012), send the new base-year parameter to the backend API via query params (e.g., `?base_year=2012`).

### C. Charting & Visuals
- Map the returned JSON vectors into Plotly or Altair multi-line charts.
- **Critical Alerts:** If the backend JSON returns a Törnqvist `variance > 0.05`, you must trigger an explicit flashing red visual UI alert on the command center.

## 2. Collaboration Contract
- **DO NOT** write Pandas grouping logic or anomaly detection models in `dashboard.py`.
- If you need data grouped differently (e.g., by airline instead of by date), ask the Backend Developer to expose a new endpoint.
