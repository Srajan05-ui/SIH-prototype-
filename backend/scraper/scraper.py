import time
import random
import logging
from fast_flights import FlightData, Result
from curl_cffi import requests
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class SovereignScrapingEngine:
    """
    Advanced scraping engine utilizing curl_cffi for TLS fingerprint impersonation
    to bypass strict anti-bot systems, specifically targeting Google Flights and Airlines.
    """
    
    def __init__(self, max_requests_per_minute: int = 15):
        self.max_requests = max_requests_per_minute
        self.request_timestamps = []
        
        # Base curl_cffi session masquerading as Chrome 110 to bypass TLS checks
        self.session = requests.Session(impersonate="chrome110")

    def _enforce_rate_limit(self):
        """
        Token Bucket Rate Limiting & Polite Backoff Algorithm.
        Ensures we never exceed the max requests per minute to avoid IP blacklisting.
        """
        now = time.time()
        # Remove timestamps older than 60 seconds
        self.request_timestamps = [t for t in self.request_timestamps if now - t < 60]
        
        if len(self.request_timestamps) >= self.max_requests:
            sleep_time = 60 - (now - self.request_timestamps[0])
            if sleep_time > 0:
                logger.warning(f"Rate limit approaching. Engaging polite backoff for {sleep_time:.2f}s...")
                time.sleep(sleep_time)
                
        # Add Jitter to simulate human variance (between 0.5 and 2.5 seconds)
        jitter = random.uniform(0.5, 2.5)
        time.sleep(jitter)
        self.request_timestamps.append(time.time())

    def fetch_google_flights_data(self, origin: str, destination: str, date: str) -> Optional[List[Dict]]:
        """
        Fetches pricing data from Google Flights.
        Returns a list of parsed pricing records containing Base Fare, Taxes, etc.
        """
        self._enforce_rate_limit()
        
        try:
            # Note: fast_flights is a wrapper, in a true production system, 
            # we inject the curl_cffi session into the wrapper to maintain the TLS disguise.
            result = FlightData(date=date, from_airport=origin, to_airport=destination).get_flights()
            
            parsed_fares = []
            for flight in result.flights:
                # Standardizing Fare Extraction (Assuming standard 12% tax breakdown for simulation)
                total = flight.price
                base = total * 0.88
                taxes = total * 0.12
                
                parsed_fares.append({
                    "source": "GoogleFlights",
                    "route": f"{origin}-{destination}",
                    "base_fare": base,
                    "taxes": taxes,
                    "baggage_fee": 0.0, # Assumes standard cabin class
                    "total_price": total,
                    "collection_method": "curl_cffi_fast_flights"
                })
            return parsed_fares
            
        except Exception as e:
            logger.error(f"Google Flights Escalation Failed for {origin}-{destination}: {e}")
            return None # Triggers Source Fallback in the main orchestrator

    def fetch_airline_direct_fallback(self, url: str) -> Optional[Dict]:
        """
        Source Fallback mechanism. If Google Flights blocks us, we hit the airline directly 
        using extreme TLS impersonation.
        """
        self._enforce_rate_limit()
        
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                # Custom HTML parsing would go here depending on the airline
                return {"status": "success", "raw_html": response.text[:500]} 
            else:
                logger.error(f"Direct Airline Scrape returned {response.status_code}")
                return None
        except requests.RequestsError as e:
            logger.error(f"Network error during direct fallback: {e}")
            return None
