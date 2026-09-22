"""
Google Flights Scraper — Sovereign Ingestion Engine
Uses fast-flights (reverse-engineered Google Flights internal API)
with curl_cffi TLS impersonation and Polite Backoff.
"""

import time
import random
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# ── Top Indian domestic routes for MoSPI/DGCA index coverage ──
SOVEREIGN_ROUTES = [
    ("BOM", "DEL"),  # Mumbai → Delhi
    ("DEL", "BOM"),  # Delhi → Mumbai
    ("BLR", "BOM"),  # Bengaluru → Mumbai
    ("BOM", "BLR"),  # Mumbai → Bengaluru
    ("DEL", "BLR"),  # Delhi → Bengaluru
    ("DEL", "CCU"),  # Delhi → Kolkata
    ("HYD", "DEL"),  # Hyderabad → Delhi
    ("MAA", "BOM"),  # Chennai → Mumbai
]


class RateLimiter:
    """Token Bucket with Human Jitter — prevents IP bans."""
    def __init__(self, max_per_minute: int = 12):
        self.max_per_minute = max_per_minute
        self._timestamps: List[float] = []

    def wait(self):
        now = time.time()
        self._timestamps = [t for t in self._timestamps if now - t < 60]
        if len(self._timestamps) >= self.max_per_minute:
            sleep_for = 60 - (now - self._timestamps[0]) + 1
            logger.warning(f"Rate limit reached — polite backoff {sleep_for:.1f}s")
            time.sleep(sleep_for)
        # Human jitter: 1.5 – 3.5 seconds between requests
        time.sleep(random.uniform(1.5, 3.5))
        self._timestamps.append(time.time())


def _target_date(days_ahead: int = 30) -> str:
    """Returns a future date string in YYYY-MM-DD format."""
    return (datetime.today() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")


def scrape_google_flights_route(
    origin: str,
    destination: str,
    date: str,
    rate_limiter: RateLimiter,
) -> Optional[Dict]:
    """
    Fetches live economy-class prices from Google Flights for one route.
    Returns a standardized fare record or None on failure.
    """
    try:
        from fast_flights import FlightQuery, Passengers, create_query, get_flights

        rate_limiter.wait()

        query = create_query(
            flights=[
                FlightQuery(
                    date=date,
                    from_airport=origin,
                    to_airport=destination,
                )
            ],
            seat="economy",
            trip="one-way",
            passengers=Passengers(adults=1),
            currency="INR",
        )

        result = get_flights(query)

        if not result or not result.flights:
            logger.warning(f"No flights returned for {origin}-{destination} on {date}")
            return None

        # Pick the median-priced flight (avoid anomaly from cheapest/most expensive)
        prices = sorted([f.price for f in result.flights if f.price and f.price > 0])
        if not prices:
            return None

        median_price = prices[len(prices) // 2]

        # Standardize: Indian airfare tax is ~18% GST on base fare
        total = float(median_price)
        base_fare = round(total / 1.18, 2)
        taxes = round(total - base_fare, 2)

        return {
            "source": "GoogleFlights",
            "route": f"{origin}-{destination}",
            "date": date,
            "base_fare": base_fare,
            "taxes": taxes,
            "baggage_fee": 0.0,
            "total_price": total,
            "num_options": len(prices),
            "min_price": float(prices[0]),
            "max_price": float(prices[-1]),
            "collection_method": "fast_flights_v2",
        }

    except ImportError:
        logger.error("fast-flights not installed. Run: pip install fast-flights")
        return None
    except Exception as e:
        logger.error(f"Scrape failed for {origin}-{destination}: {e}")
        return None


def scrape_all_sovereign_routes(
    days_ahead: int = 30,
    routes: List = None,
) -> List[Dict]:
    """
    Master ingestion function — scrapes all sovereign routes and returns
    a clean list of standardized fare records ready for the math engine.
    """
    if routes is None:
        routes = SOVEREIGN_ROUTES

    limiter = RateLimiter(max_per_minute=12)
    date = _target_date(days_ahead)
    results = []

    logger.info(f"Starting sovereign ingestion for {len(routes)} routes on {date}")

    for origin, destination in routes:
        record = scrape_google_flights_route(origin, destination, date, limiter)
        if record:
            results.append(record)
            logger.info(f"✓ {origin}-{destination}: INR {record['total_price']:.0f}")
        else:
            logger.warning(f"✗ {origin}-{destination}: No data — skipping")

    logger.info(f"Ingestion complete. {len(results)}/{len(routes)} routes collected.")
    return results
