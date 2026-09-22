# Security & Governance Specification

As an official system built for MoSPI and DGCA, the architecture adheres to absolute zero-trust security paradigms.

## 1. Secrets Management / Vault
All API keys, database URLs, and cryptographic tokens are strictly prohibited from being hard-coded in the source repository. The system utilizes environment variables (`.env`) linked to a secure secret manager (e.g., AWS Secrets Manager or HashiCorp Vault in production).

## 2. API Gateway & WAF (Web Application Firewall)
- **FastAPI Gateway:** Acts as the single controlled entry point. Direct database connections from the frontend or external clients are physically blocked.
- **WAF:** Inspects incoming traffic arrays for SQL Injection (SQLi) and Cross-Site Scripting (XSS).
- **Rate Limiting:** Protects against DDoS attacks by limiting requests per IP address using a Token Bucket algorithm.

## 3. RBAC (Role-Based Access Control) & Authentication
Access to the Streamlit Dashboard is strictly segregated:
- `Admin`: Full write access and configuration controls.
- `Analyst`: Access to underlying datasets, econometric engines, and reporting exports.
- `Viewer`: Read-only access to the final sovereign dashboard.
- **MFA:** Multi-Factor Authentication is enforced for all logins via JWT and secure session cookies.

## 4. Data Provenance & Audit Trails
- **Provenance:** Every airfare row in PostgreSQL contains metadata regarding its exact origin (e.g., `source=GoogleFlights`, `timestamp=16900021`), ensuring mathematical accountability.
- **Audit Logging (SIEM):** All API access attempts (authorized and unauthorized) are logged to a centralized stream for security auditing.

## 5. Ingestion Security (Polite Scraping)
- **Rate Limit Adherence:** The scraper dynamically throttles itself to prevent overloading airline servers.
- **TLS Fingerprinting:** Uses `curl_cffi` to construct legitimate TLS handshakes to avoid triggering automated bot-bans.
