# Developer Split Instructions
This repository is split between two engineers. Adhere strictly to these domain boundaries to prevent merge conflicts and API mismatch.

---

## BACKEND DEVELOPER (You)
**Primary Domain:** `ingestion/`, `processing/`, `api/`
**Responsibilities:**
1. **Mathematical Engines (`index_chain_calc.py`):**
   - Implement the `Trimmed Mean Engine` (drop top 10% / bottom 10%).
   - Implement Törnqvist & Walsh Superlative indices.
   - Implement the COICOP transmission logic.
   - Implement the Chained Base-Year Re-basing simulator.
2. **API Layer (`FastAPI`):**
   - Serve the outputs of `index_chain_calc.py` over secure HTTP GET endpoints.
   - Example Contract: `GET /api/v1/inflation/core` must return JSON: `{ "core_index": 105.4, "headline_index": 108.1, "variance": 0.02 }`
3. **Data Integrity:** Ensure all Pandas/NumPy logic returns clean, validated data arrays that never throw NaN errors to the frontend.

---

## FRONTEND DEVELOPER (Partner)
**Primary Domain:** `frontend/`, `dashboard.py` (Streamlit)
**Responsibilities:**
1. **API Consumption:**
   - You must NOT calculate inflation math in the frontend. 
   - Use Python `requests` or `httpx` to ping the Backend Developer's FastAPI endpoints to fetch the JSON vectors.
2. **UI Implementation (`dashboard.py`):**
   - Construct the High-Density Dark Theme as specified in `design_doc.md`.
   - Build the `⚙️ Sovereign Re-Basing Matrix` dropdown. When changed, send the new base-year parameter back to the backend API via query params (e.g., `?base_year=2022`).
3. **Charting:**
   - Map the returned JSON vectors into Plotly/Altair multi-line charts. Ensure the Törnqvist discrepancy warnings trigger visual UI alerts if the backend flags `variance > 0.05`.
