# Tech Stack

## Ingestion / Scraping Layer
- **Python 3.11+**
- **Scrapy:** Core web automation framework for high-throughput crawling.
- **curl_cffi:** Advanced TLS fingerprinting to bypass anti-bot detections (Cloudflare, Akamai).
- **Fast-Flights:** Specifically utilized for interacting with Google Flights endpoints.

## Data Processing & Econometrics
- **Pandas:** Tabular data manipulation, cleaning, and time-series grouping.
- **NumPy:** Vectorized array mathematics for Jevons means and index calculations.
- **SciPy:** Advanced statistical anomaly detection (MAD Z-Scores, Trimmed Means).
- **Scikit-Learn:** Isolation Forests for algorithmic price-glitch detection.

## API & Gateway Layer
- **FastAPI:** High-performance asynchronous API framework.
- **Uvicorn:** ASGI server for serving the FastAPI application.
- **Pydantic:** Strict type validation for incoming data payloads to prevent injection attacks.
- **PyJWT:** Secure JSON Web Token generation for endpoint authorization.

## Presentation Layer
- **Streamlit:** Rapid analytical dashboarding framework.
- **Plotly / Altair:** For high-density, interactive dark-themed econometric charts.

## Database
- **PostgreSQL:** Primary relational data warehouse for storing millions of historical flight vectors.
- **SQLAlchemy:** Secure ORM preventing SQL Injection attacks.
