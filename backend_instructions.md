# Backend Developer Instructions

**Primary Domain:** `backend/ingestion/`, `backend/processing/`, `backend/api/`

## 1. Core Responsibilities
Your primary objective is to maintain the mathematical integrity and security of the Sovereign Econometric Engine and serve it securely via FastAPI.

### A. Mathematical Engines (`index_chain_calc.py`)
- **Maintain Trimmed Mean Engine:** Ensure the 10% outlier trimming logic perfectly drops extreme anomalies to isolate Core Inflation.
- **Maintain Superlative Matrices:** Cross-validate Törnqvist and Walsh equations against Fisher indexing outputs dynamically.
- **Maintain COICOP Transmission:** Ensure airfare basis point transmission scales strictly adhere to the UN COICOP 07.3.3 categorization (12% of Transport, 8.5% of National CPI).
- **Maintain Rebasing Simulator:** Ensure the dynamic link-factors don't break timeline continuity when the Base Year shifts.

### B. API Layer (`FastAPI`)
- Expose all mathematical vectors via strict HTTP GET endpoints.
- **Data Integrity:** You must ensure all Pandas/NumPy logic returns clean JSON arrays. The API must NEVER throw `NaN` or unhandled exceptions to the frontend.
- **Security:** Ensure JWT validation is active on all non-public endpoints.

## 2. Collaboration Contract
- **DO NOT** write UI code or touch Streamlit styling.
- If the frontend developer requests a new data cut, expose a new query parameter in FastAPI (e.g., `?base_year=2022`).
- Inform the frontend developer immediately if you alter the JSON schema of the API responses.
