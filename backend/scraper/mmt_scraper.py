"""
Sovereign OTA Ingestion Engine — MakeMyTrip (MMT) Scraper
Ported directly from RacheetX/Web-scraper with adaptations for
the multi-route, multi-window sovereign index pipeline.

Techniques used (from Web-scraper repo):
  - Playwright persistent Chrome profile (bypasses automation detection)
  - CSS selector: .flightCard (discovered via inspect_dom.py)
  - URL template: makemytrip.com/flight/search?itinerary=ORIG-DEST-DATE
  - Regex parsing for airline, flight code, times, price
  - Advance window scraping (T+7, T+15, T+30)
  - Intraday Jevons geometric mean (from intraday_jevons.py)
  - Weighted APIx aggregation (from calculate_apix.py)
  - SQLite persistence (from apix_master.py)
"""

import re
import asyncio
import random
import sqlite3
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# ── Sovereign Route Coverage (top 12 Indian domestic routes) ──────
SOVEREIGN_ROUTES = [
    ("BOM", "DEL"), ("DEL", "BOM"),
    ("BLR", "BOM"), ("BOM", "BLR"),
    ("DEL", "BLR"), ("BLR", "DEL"),
    ("DEL", "CCU"), ("CCU", "DEL"),
    ("HYD", "DEL"), ("MAA", "BOM"),
    ("BOM", "MAA"), ("BLR", "HYD"),
]

# ── Advance windows (days ahead) for index construction ───────────
ADVANCE_WINDOWS = [7, 15, 30]

# ── Airline market weights (from init_weights.py pattern) ─────────
AIRLINE_WEIGHTS = {
    "IndiGo": 0.55,
    "Air India": 0.18,
    "Air India Express": 0.07,
    "SpiceJet": 0.08,
    "Akasa Air": 0.07,
    "Vistara": 0.05,
}

# ── Route traffic weights ──────────────────────────────────────────
ROUTE_WEIGHTS = {
    "BOM-DEL": 1.0, "DEL-BOM": 1.0,
    "DEL-BLR": 0.85, "BLR-DEL": 0.85,
    "BLR-BOM": 0.75, "BOM-BLR": 0.75,
    "DEL-CCU": 0.60, "CCU-DEL": 0.60,
    "HYD-DEL": 0.55, "MAA-BOM": 0.50,
    "BOM-MAA": 0.50, "BLR-HYD": 0.45,
}

# ── Booking window weights ─────────────────────────────────────────
WINDOW_WEIGHTS = {"T+7": 0.5, "T+15": 0.3, "T+30": 0.2}


# ─────────────────────────────────────────────────────────────────
# JEVONS GEOMETRIC MEAN (from intraday_jevons.py)
# ─────────────────────────────────────────────────────────────────
def calculate_jevons_mean(prices: List[float]) -> float:
    """
    Calculates the geometric mean (Jevons) of prices.
    Statistically dampens extreme intraday price spikes from
    dynamic airline pricing algorithms.
    """
    arr = np.array([p for p in prices if p and p > 0])
    if len(arr) == 0:
        return 0.0
    return round(float(np.exp(np.mean(np.log(arr)))), 2)


# ─────────────────────────────────────────────────────────────────
# MMT PLAYWRIGHT SCRAPER (from apix_master.py + extract_flights.py)
# ─────────────────────────────────────────────────────────────────
async def scrape_mmt_route(
    page,
    origin: str,
    destination: str,
    flight_date: str,
    days_ahead: int,
) -> List[Dict]:
    """
    Scrapes MakeMyTrip for a single route+date using Playwright.
    Uses the .flightCard CSS selector discovered by RacheetX/Web-scraper.
    """
    search_url = (
        f"https://www.makemytrip.com/flight/search?"
        f"itinerary={origin}-{destination}-{flight_date}"
        f"&tripType=O&paxType=A-1_C-0_I-0&intl=false&cabinClass=E"
    )

    max_retries = 2
    for attempt in range(max_retries):
        try:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(3500)
            await page.keyboard.press("Escape")

            # Remove blocking modals (from probe_mmt.py technique)
            await page.evaluate("""() => {
                const selectors = [
                    '[data-cy="CommonModal_2"]', '.commonModal',
                    '.modalMain', '.overlayCrossIcon', '.loginModal'
                ];
                selectors.forEach(sel =>
                    document.querySelectorAll(sel).forEach(el => el.remove())
                );
            }""")

            await page.wait_for_selector(".flightCard", timeout=25000)

            # Scroll to trigger lazy-loaded inventory
            for _ in range(8):
                await page.wait_for_timeout(700)
                await page.evaluate("window.scrollBy(0, 800)")

            cards = await page.locator(".flightCard").all()
            logger.info(f"  {origin}-{destination} T+{days_ahead}: {len(cards)} cards detected")

            parsed_flights = []
            for card in cards:
                text = await card.inner_text()

                # Regex parsing (from extract_flights.py)
                carrier_match = re.search(
                    r"(IndiGo|Air India Express|Air India|SpiceJet|Akasa Air|Vistara)",
                    text, re.IGNORECASE
                )
                code_match = re.search(r"([A-Z0-9]{2}-[0-9]{3,4})", text)
                times = re.findall(r"\b([0-2][0-9]:[0-5][0-9])\b", text)
                price_match = re.search(r"[₹Rs\.]\s*([\d,]+)", text)

                carrier = carrier_match.group(1) if carrier_match else "Unknown"
                flight_code = code_match.group(1) if code_match else "Unknown"
                dep_time = times[0] if len(times) >= 1 else None
                arr_time = times[1] if len(times) >= 2 else None
                price = int(price_match.group(1).replace(",", "")) if price_match else None
                stops = 0 if "non stop" in text.lower() else 1

                if price and carrier != "Unknown" and price > 500:
                    parsed_flights.append({
                        "scrape_date": datetime.today().strftime("%Y-%m-%d"),
                        "route": f"{origin}-{destination}",
                        "advance_window": f"T+{days_ahead}",
                        "flight_date": flight_date,
                        "airline": carrier,
                        "flight_code": flight_code,
                        "departure": dep_time,
                        "arrival": arr_time,
                        "stops": stops,
                        "total_fare_inr": price,
                        "source": "MMT_Playwright",
                    })

            return parsed_flights

        except Exception as e:
            logger.warning(f"  Attempt {attempt + 1} failed for {origin}-{destination}: {e}")
            if attempt < max_retries - 1:
                await page.wait_for_timeout(3000)

    return []


# ─────────────────────────────────────────────────────────────────
# MASTER INGESTION RUNNER (from apix_master.py)
# ─────────────────────────────────────────────────────────────────
async def run_sovereign_ingestion(
    routes: List = None,
    windows: List[int] = None,
    db_path: str = "airfare.db",
) -> pd.DataFrame:
    """
    Master async runner. Launches persistent Playwright Chrome context,
    iterates over all routes × advance windows, applies Jevons mean per
    route-window combination, and persists results to SQLite.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.error("Playwright not installed. Run: pip install playwright && playwright install chromium")
        return pd.DataFrame()

    routes = routes or SOVEREIGN_ROUTES
    windows = windows or ADVANCE_WINDOWS

    all_flights = []

    async with async_playwright() as p:
        import os
        user_data_dir = os.path.abspath("./chrome_profile")
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            channel="chromium",
            headless=True,  # headless=True for server deployment
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
            ignore_default_args=["--enable-automation"],
        )

        page = browser_context.pages[0] if browser_context.pages else await browser_context.new_page()

        for origin, destination in routes:
            for days_ahead in windows:
                flight_date = (datetime.today() + timedelta(days=days_ahead)).strftime("%d%m%Y")
                logger.info(f"Scraping {origin}-{destination} T+{days_ahead}...")

                flights = await scrape_mmt_route(page, origin, destination, flight_date, days_ahead)
                all_flights.extend(flights)

                # Polite delay between requests (from apix_master.py pattern)
                await page.wait_for_timeout(int(random.uniform(3000, 5500)))

        await browser_context.close()

    if not all_flights:
        logger.warning("No flights scraped from MMT.")
        return pd.DataFrame()

    df = pd.DataFrame(all_flights).drop_duplicates()

    # Apply Jevons geometric mean per route-window-airline (intraday compression)
    df["jevons_fare_inr"] = df.groupby(
        ["route", "advance_window", "airline"]
    )["total_fare_inr"].transform(lambda x: calculate_jevons_mean(x.tolist()))

    # Persist to SQLite (from apix_master.py pattern)
    conn = sqlite3.connect(db_path)
    df.to_sql("flight_prices", conn, if_exists="append", index=False, method="multi")
    conn.close()

    logger.info(f"Ingestion complete: {len(df)} records stored in {db_path}")
    return df


# ─────────────────────────────────────────────────────────────────
# APIX WEIGHTED AGGREGATION (from calculate_apix.py)
# Converts raw scraped fares → Sovereign APIx Index
# ─────────────────────────────────────────────────────────────────
def calculate_apix_weighted_fare(df: pd.DataFrame) -> float:
    """
    Reproduces the triple-weighted APIx formula from calculate_apix.py:
        APIx = Σ(fare × airline_weight × route_weight × window_weight)
               / Σ(airline_weight × route_weight × window_weight)
    """
    if df.empty:
        return 0.0

    numerator = 0.0
    denominator = 0.0

    for _, row in df.iterrows():
        aw = AIRLINE_WEIGHTS.get(row.get("airline", ""), 0.05)
        rw = ROUTE_WEIGHTS.get(row.get("route", ""), 0.5)
        ww = WINDOW_WEIGHTS.get(row.get("advance_window", "T+15"), 0.3)
        fare = row.get("jevons_fare_inr", row.get("total_fare_inr", 0))

        numerator   += fare * aw * rw * ww
        denominator += aw * rw * ww

    return round(numerator / denominator, 2) if denominator > 0 else 0.0


# ─────────────────────────────────────────────────────────────────
# SYNC WRAPPER — for use by FastAPI (runs async ingestion in thread)
# ─────────────────────────────────────────────────────────────────
def scrape_mmt_sync(
    routes: List = None,
    windows: List[int] = None,
    db_path: str = "airfare.db",
) -> pd.DataFrame:
    """Synchronous entry point for calling from FastAPI endpoints."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(
            run_sovereign_ingestion(routes, windows, db_path)
        )
    except Exception as e:
        logger.error(f"MMT sync scrape failed: {e}")
        return pd.DataFrame()
    finally:
        loop.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    df = asyncio.run(run_sovereign_ingestion(
        routes=[("DEL", "BOM"), ("BOM", "DEL")],
        windows=[7, 15],
    ))
    if not df.empty:
        apix = calculate_apix_weighted_fare(df)
        print(f"\n✅ APIx Weighted Fare: INR {apix}")
        print(df[["route", "advance_window", "airline", "total_fare_inr", "jevons_fare_inr"]].head(10))
