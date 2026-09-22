import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from pydantic import BaseModel
from scipy import stats

class PriceData(BaseModel):
    date: str
    route: str
    base_price_t0: float
    base_price_t1: float
    passenger_volume_t0: float
    passenger_volume_t1: float

class SovereignEconometricEngine:
    def __init__(self, base_year: int = 2026):
        self.base_year = base_year
        self.coicop_code = "07.3.3"
        self.coicop_weight_in_transport = 0.12  # 12% of Transport Group
        self.transport_weight_in_cpi = 0.085    # 8.5% of All-India Headline CPI

    # ─────────────────────────────────────────────────────────────
    # FEATURE 1: VOLATILITY INSULATION — Trimmed Mean & Weighted Median
    # ─────────────────────────────────────────────────────────────
    def calculate_trimmed_mean_core(
        self,
        prices_t0: np.ndarray,
        prices_t1: np.ndarray,
        trim_percent: float = 0.10
    ) -> Dict[str, float]:
        """
        Computes the symmetric trimmed mean by eliminating the top 10% and
        bottom 10% extreme price tail variables. Also computes a weighted
        median index alongside it so both curves can be output simultaneously.
        """
        price_relatives = prices_t1 / prices_t0

        # Symmetric trimmed mean (drop top & bottom 10%)
        lower_bound = np.percentile(price_relatives, trim_percent * 100)
        upper_bound = np.percentile(price_relatives, (1 - trim_percent) * 100)
        trimmed = price_relatives[
            (price_relatives >= lower_bound) & (price_relatives <= upper_bound)
        ]
        trimmed_mean_index = float(np.mean(trimmed) * 100) if len(trimmed) > 0 else 100.0

        # Weighted median — weights proportional to the base-period prices
        weights = prices_t0 / prices_t0.sum()
        sorted_idx = np.argsort(price_relatives)
        sorted_rel = price_relatives[sorted_idx]
        sorted_wts = weights[sorted_idx]
        cumulative_wt = np.cumsum(sorted_wts)
        median_idx = np.searchsorted(cumulative_wt, 0.5)
        weighted_median_index = float(sorted_rel[median_idx] * 100)

        return {
            "trimmed_mean_core": trimmed_mean_index,
            "weighted_median_index": weighted_median_index,
        }

    # ─────────────────────────────────────────────────────────────
    # FEATURE 2: SUPERLATIVE CROSS-VALIDATION — Törnqvist, Walsh, Fisher
    # ─────────────────────────────────────────────────────────────
    def calculate_superlative_matrices(
        self, data: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Parallel calculation of Törnqvist (log price ratios weighted by avg
        expenditure shares) and Walsh (geometric passenger volumes) indices.
        Cross-checks against Chained Fisher Index and flags if variance > 0.05.
        """
        df = data.copy()
        df["exp_t0"] = df["base_price_t0"] * df["passenger_volume_t0"]
        df["exp_t1"] = df["base_price_t1"] * df["passenger_volume_t1"]
        df["share_t0"] = df["exp_t0"] / df["exp_t0"].sum()
        df["share_t1"] = df["exp_t1"] / df["exp_t1"].sum()

        # Törnqvist Index: log price ratios weighted by arithmetic avg of shares
        df["tornqvist_wt"] = (df["share_t0"] + df["share_t1"]) / 2.0
        tornqvist = float(
            np.exp(
                np.sum(
                    df["tornqvist_wt"]
                    * np.log(df["base_price_t1"] / df["base_price_t0"])
                )
            ) * 100
        )

        # Walsh Index: geometric average of passenger volumes as weights
        geom_vol = np.sqrt(df["passenger_volume_t0"] * df["passenger_volume_t1"])
        walsh = float(
            (np.sum(df["base_price_t1"] * geom_vol) /
             np.sum(df["base_price_t0"] * geom_vol)) * 100
        )

        # Fisher (Headline): geometric mean of Laspeyres & Paasche
        laspeyres = (
            np.sum(df["base_price_t1"] * df["passenger_volume_t0"]) /
            np.sum(df["base_price_t0"] * df["passenger_volume_t0"])
        )
        paasche = (
            np.sum(df["base_price_t1"] * df["passenger_volume_t1"]) /
            np.sum(df["base_price_t0"] * df["passenger_volume_t1"])
        )
        fisher = float(np.sqrt(laspeyres * paasche) * 100)

        # Discrepancy flag
        max_variance = max(abs(tornqvist - fisher), abs(walsh - fisher)) / 100.0
        drift_warning = max_variance > 0.05

        return {
            "tornqvist_index": tornqvist,
            "walsh_index": walsh,
            "fisher_headline": fisher,
            "max_variance_pts": round(max_variance, 6),
            "drift_warning": drift_warning,
        }

    # ─────────────────────────────────────────────────────────────
    # FEATURE 3: COICOP 07.3.3 TRANSMISSION
    # ─────────────────────────────────────────────────────────────
    def calculate_coicop_transmission(
        self, airfare_inflation_rate: float
    ) -> Dict[str, float]:
        """
        Maps airfare inflation directly to UN COICOP code 07.3.3 and computes
        downstream basis-point transmission onto the Transport Group and the
        All-India Headline CPI.
        """
        transport_bps = airfare_inflation_rate * self.coicop_weight_in_transport * 10_000
        headline_bps = (
            airfare_inflation_rate
            * self.coicop_weight_in_transport
            * self.transport_weight_in_cpi
            * 10_000
        )
        return {
            "coicop_code": self.coicop_code,
            "airfare_inflation_rate_pct": round(airfare_inflation_rate * 100, 4),
            "transport_group_impact_bps": round(transport_bps, 4),
            "national_headline_cpi_impact_bps": round(headline_bps, 4),
        }

    # ─────────────────────────────────────────────────────────────
    # FEATURE 4: TEMPORAL BASE-YEAR RE-BASING SIMULATOR
    # ─────────────────────────────────────────────────────────────
    def temporal_rebasing_simulator(
        self,
        historical_series: pd.Series,
        new_base_year: int,
        link_factor_override: Optional[float] = None,
    ) -> pd.Series:
        """
        Shifts the indexing baseline to any new_base_year on demand.
        Automatically calculates arithmetic slicing link factors so the full
        historical timeline adjusts without breaking continuity.
        """
        if new_base_year not in historical_series.index:
            raise ValueError(
                f"Base year {new_base_year} not found in historical series index."
            )
        old_base_value = historical_series[new_base_year]
        link_factor = link_factor_override if link_factor_override else (100.0 / old_base_value)
        return (historical_series * link_factor).round(4)

    # ─────────────────────────────────────────────────────────────
    # COMBINED VECTOR — produces the full output for the API endpoint
    # ─────────────────────────────────────────────────────────────
    def build_inflation_vectors(
        self, route_data: pd.DataFrame, base_year: int = 2026
    ) -> Dict:
        """
        Single call that runs all 4 engines and returns a fully merged
        JSON-serializable dict ready to be served by FastAPI.
        """
        superlative = self.calculate_superlative_matrices(route_data)
        core_metrics = self.calculate_trimmed_mean_core(
            route_data["base_price_t0"].values,
            route_data["base_price_t1"].values,
        )
        airfare_inflation_rate = (superlative["fisher_headline"] - 100) / 100.0
        transmission = self.calculate_coicop_transmission(airfare_inflation_rate)

        # Build a synthetic 12-month historical series and rebase it
        base_fisher = superlative["fisher_headline"]
        historical = pd.Series(
            np.linspace(100, base_fisher, 12),
            index=range(2015, 2027),
        )
        rebased = self.temporal_rebasing_simulator(historical, new_base_year=base_year)

        return {
            **superlative,
            **core_metrics,
            **transmission,
            "rebased_series": rebased.tolist(),
            "rebased_dates": list(range(2015, 2027)),
            "base_year": base_year,
        }


# ─── Smoke test ───────────────────────────────────────────────────
if __name__ == "__main__":
    engine = SovereignEconometricEngine(base_year=2026)
    mock = pd.DataFrame({
        "route": ["BOM-DEL", "BLR-BOM", "DEL-CCU", "HYD-MAA", "DEL-BOM"],
        "base_price_t0": [5000, 4000, 6000, 3000, 4500],
        "base_price_t1": [5500, 4100, 6500, 3100, 4800],
        "passenger_volume_t0": [1000, 800, 500, 400, 700],
        "passenger_volume_t1": [1050, 750, 520, 410, 720],
    })
    result = engine.build_inflation_vectors(mock, base_year=2026)
    for k, v in result.items():
        if not isinstance(v, list):
            print(f"{k}: {v}")
