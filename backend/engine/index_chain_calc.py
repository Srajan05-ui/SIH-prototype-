import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from pydantic import BaseModel

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
        self.coicop_weight_in_transport = 0.12 # 12% of Transport Group
        self.transport_weight_in_cpi = 0.085 # 8.5% of All-India Headline CPI

    def calculate_trimmed_mean_core(self, prices_t0: np.ndarray, prices_t1: np.ndarray, trim_percent: float = 0.10) -> float:
        """
        Volatility Insulation: Isolates Core Inflation from Headline.
        Computes the symmetric trimmed mean of price relatives by dropping top and bottom tail extremes.
        """
        price_relatives = prices_t1 / prices_t0
        lower_bound = np.percentile(price_relatives, trim_percent * 100)
        upper_bound = np.percentile(price_relatives, (1 - trim_percent) * 100)
        
        trimmed_relatives = price_relatives[(price_relatives >= lower_bound) & (price_relatives <= upper_bound)]
        if len(trimmed_relatives) == 0:
            return 100.0 # Fallback if perfectly flat
            
        core_index = np.mean(trimmed_relatives) * 100
        return core_index

    def calculate_superlative_matrices(self, data: pd.DataFrame) -> Tuple[float, float, float]:
        """
        Cross-Validation: Törnqvist & Walsh Superlative Index Matrices against Fisher
        """
        # Calculate expenditure shares
        data['expenditure_t0'] = data['base_price_t0'] * data['passenger_volume_t0']
        data['expenditure_t1'] = data['base_price_t1'] * data['passenger_volume_t1']
        
        sum_exp_t0 = data['expenditure_t0'].sum()
        sum_exp_t1 = data['expenditure_t1'].sum()
        
        data['share_t0'] = data['expenditure_t0'] / sum_exp_t0
        data['share_t1'] = data['expenditure_t1'] / sum_exp_t1
        
        # Törnqvist Index
        data['tornqvist_weight'] = (data['share_t0'] + data['share_t1']) / 2.0
        tornqvist_index = np.exp(np.sum(data['tornqvist_weight'] * np.log(data['base_price_t1'] / data['base_price_t0']))) * 100
        
        # Walsh Index
        geom_volume = np.sqrt(data['passenger_volume_t0'] * data['passenger_volume_t1'])
        walsh_numerator = np.sum(data['base_price_t1'] * geom_volume)
        walsh_denominator = np.sum(data['base_price_t0'] * geom_volume)
        walsh_index = (walsh_numerator / walsh_denominator) * 100
        
        # Laspeyres & Paasche -> Fisher
        laspeyres = np.sum(data['base_price_t1'] * data['passenger_volume_t0']) / np.sum(data['base_price_t0'] * data['passenger_volume_t0'])
        paasche = np.sum(data['base_price_t1'] * data['passenger_volume_t1']) / np.sum(data['base_price_t0'] * data['passenger_volume_t1'])
        fisher_index = np.sqrt(laspeyres * paasche) * 100
        
        return tornqvist_index, walsh_index, fisher_index

    def calculate_coicop_transmission(self, airfare_inflation_rate: float) -> Dict[str, float]:
        """
        Standardization: Official COICOP Structure & Headline CPI Transmission
        """
        # Calculate the basis point contribution
        transport_impact_bps = airfare_inflation_rate * self.coicop_weight_in_transport * 100
        headline_cpi_impact_bps = airfare_inflation_rate * (self.coicop_weight_in_transport * self.transport_weight_in_cpi) * 100
        
        return {
            "coicop_code": self.coicop_code,
            "airfare_inflation_rate": airfare_inflation_rate,
            "transport_group_impact_bps": transport_impact_bps,
            "national_cpi_impact_bps": headline_cpi_impact_bps
        }

    def temporal_rebasing_simulator(self, historical_series: pd.Series, new_base_year: int, link_factor_override: float = None) -> pd.Series:
        """
        Temporal Flexibility: Chained Base-Year Re-basing Simulator
        """
        if new_base_year not in historical_series.index:
            raise ValueError(f"Base year {new_base_year} not found in historical series.")
            
        old_base_value = historical_series[new_base_year]
        link_factor = link_factor_override if link_factor_override else (100.0 / old_base_value)
        
        rebased_series = historical_series * link_factor
        return rebased_series

if __name__ == "__main__":
    # Smoke Test
    engine = SovereignEconometricEngine(base_year=2026)
    
    # Mock route data for test
    mock_data = pd.DataFrame({
        'route': ['BOM-DEL', 'BLR-BOM', 'DEL-CCU', 'HYD-MAA'],
        'base_price_t0': [5000, 4000, 6000, 3000],
        'base_price_t1': [5500, 4100, 6500, 3100],
        'passenger_volume_t0': [1000, 800, 500, 400],
        'passenger_volume_t1': [1050, 750, 520, 410]
    })
    
    t_idx, w_idx, f_idx = engine.calculate_superlative_matrices(mock_data)
    print(f"Fisher (Headline): {f_idx:.2f}")
    print(f"Tornqvist (Validation): {t_idx:.2f}")
    print(f"Walsh (Validation): {w_idx:.2f}")
    
    core = engine.calculate_trimmed_mean_core(mock_data['base_price_t0'].values, mock_data['base_price_t1'].values, trim_percent=0.1)
    print(f"Trimmed Mean (Core): {core:.2f}")
    
    transmission = engine.calculate_coicop_transmission(airfare_inflation_rate=(f_idx - 100)/100.0)
    print(f"Transmission to National CPI (Basis Points): {transmission['national_cpi_impact_bps']:.2f} bps")
