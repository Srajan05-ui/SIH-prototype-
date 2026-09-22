# UX/UI Design Document

The presentation layer of the Sovereign Airfare Intelligence System is designed specifically for high-level macroeconomists, policymakers, and auditors.

## 1. Global Aesthetic
- **Theme:** High-Density Dark Theme (Deep Navy / Carbon backgrounds with glowing cyber-metric accents).
- **Typography:** Professional, monospace-heavy for mathematical precision (e.g., `Inter`, `Fira Code` for numerical outputs).
- **Layout Strategy:** Matrix-style modular panels allowing maximum data density without scrolling.

## 2. Dashboard Structure (`dashboard.py`)

### Sidebar: Navigation & Configuration
- **Sovereign Re-Basing Matrix:** A dynamic dropdown panel labeled `⚙️ Shift Baseline Timeline` allowing users to instantly re-calculate the entire interface relative to a new base year (e.g., 2012 vs 2026).
- **Navigation Tabs:**
  1. Sovereign Inflation Command Center
  2. Data Provenance & Anomaly Center
  3. API Security & Compliance

### Tab 1: Sovereign Inflation Command Center
- **Top Row (Executive KPIs):**
  - Current Headline CPI (Fisher Index).
  - Current Core CPI (Trimmed Mean Index).
  - Törnqvist / Walsh Discrepancy Warnings (Flashing red if variance > 0.05 points).
- **Main Matrix Plot (Multi-line Charting):**
  - A dense, interactive graph mapping 4 distinct curves over time: 
    - The Chained Fisher (Headline)
    - Trimmed Mean (Core Inflation)
    - Törnqvist Validation Curve
    - The Historical Base Trajectory.
- **Side Card (COICOP 07.3.3 Transmission):**
  - Real-time gauge chart showing the exact basis-point transmission scale of current airfare inflation onto the broader national All-India CPI.

### Tab 2: Provenance & Anomaly Center
- **Anomaly Scatter Plot:** Displays `MAD Modified Z-Score` outliers (e.g., sudden Rs 15,000 spikes on a Rs 4,000 route) flagged and stripped from the index.
- **Source Consistency Matrix:** Compares Official Airline vs Google Flights vs OTA prices side-by-side to flag manipulation indicators.
