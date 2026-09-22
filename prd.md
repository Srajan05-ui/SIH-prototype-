# Product Requirements Document (PRD)
**Project:** Sovereign Airfare Intelligence System (SIH PS 26056)
**Version:** 2.0.0 (Unified Build)

## 1. Problem Statement
The Directorate General of Civil Aviation (DGCA) and the Ministry of Statistics and Programme Implementation (MoSPI) require a cryptographically secure, fully automated sovereign intelligence system to ingest, verify, and mathematically standardize real-time airfare pricing across India. The current dependency on unverified OTA data and basic arithmetic indices creates severe upward biases in the national Consumer Price Index (CPI), leading to flawed monetary policy decisions.

## 2. Target Audience
- **Macroeconomists & Central Bankers (MoSPI/RBI):** Require extreme accuracy (Törnqvist/Fisher indices) and isolation from volatility (Trimmed Means).
- **Aviation Regulators (DGCA):** Require anomaly detection to monitor price gouging and algorithmic pricing manipulation.
- **Auditors:** Require strict Data Provenance, Audit Trails, and cryptographic verification of all scraped data.

## 3. Core Objectives
1. **Ethical Sovereign Ingestion:** Scrape flight prices dynamically from official tariffs (DGCA), aggregators (Google Flights), and airlines directly, completely bypassing anti-bot bans using Rate Limiting, IP Jitter, and Polite Backoff algorithms.
2. **Advanced Econometric Math:** Replace legacy calculation models with the UN COICOP 07.3.3 standard, employing Jevons Geometric Means and Superlative Matrices (Fisher, Törnqvist, Walsh).
3. **Volatility Insulation:** Build a Trimmed Mean Engine to isolate Core Inflation from seasonal Headline spikes by automatically dropping 10% tail variables.
4. **Data Security & Integrity:** Implement a Web Application Firewall (WAF), JWT Authentication, TLS Encryption, and centralized Secret Vaults.

## 4. In-Scope Features
- **Scraping Layer:** `Scrapy`, `curl_cffi`, TokenBucket Rate Limiting.
- **Mathematical Engine:** `index_chain_calc.py` utilizing Pandas and NumPy.
- **API Layer:** `FastAPI` with strict JWT endpoints and CORS.
- **Presentation Layer:** High-Density Dark-Themed `Streamlit` Dashboard (`dashboard.py`).

## 5. Out-of-Scope
- Direct flight bookings or transactional ticketing.
- B2C consumer-facing interfaces.
