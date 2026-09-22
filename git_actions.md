# Git Actions & CI/CD Pipeline

To ensure a highly resilient and automated deployment cycle, we utilize GitHub Actions to manage testing, security scanning, and deployment across both the frontend and backend.

## 1. Continuous Integration (CI)
On every Pull Request to the `main` or `develop` branches, the following jobs are executed:

### A. Python Linter & Formatter (`black`, `flake8`)
Ensures PEP8 compliance across the mathematical engines and API.

### B. Security Scanning (`bandit`, `safety`)
- Scans `requirements.txt` for known vulnerable dependencies.
- Analyzes Python code (`bandit`) for hardcoded secrets, weak cryptographic hashes, and SQL injection vectors.

### C. Automated Testing (`pytest`)
- Executes strict mathematical validation tests on `index_chain_calc.py` to ensure the Trimmed Mean, Törnqvist, and Fisher calculations have exactly zero floating-point deviations from expected outputs.

## 2. Continuous Deployment (CD)
Upon merging into `main`, the pipeline triggers the deployment orchestration:

### A. Backend Deployment (Render / AWS ECS)
- Connects to the host using secure OIDC (OpenID Connect).
- Executes `render.yaml` instructions to pull the new image, run `pip install -r requirements.txt`, and gracefully restart `uvicorn` workers without downtime.

### B. Frontend Deployment (Streamlit Cloud / Vercel)
- Updates the Streamlit application cache and rebuilds the analytical matrices for immediate dashboard updates.
