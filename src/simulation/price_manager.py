"""
Electricity Price Management
Handles selection between "high" and "normal" price scenarios
"""

import pandas as pd
from typing import Literal
from datetime import datetime


class PriceManager:
    """
    Manages electricity price data with scenario selection

    Two scenarios available:
    - "high": Period of high variation and peak prices
    - "normal": Contemporary everyday situation

    Both are real price data from different time slots
    """

    def __init__(self, historical_data: pd.DataFrame):
        """
        Initialize with historical data

        Args:
            historical_data: DataFrame with 'Price_High' and 'Price_Normal' columns
        """
        self.data = historical_data
        self.scenario: Literal['high', 'normal'] = 'normal'  # Default scenario

    def set_scenario(self, scenario: Literal['high', 'normal']):
        """
        Select price scenario

        Args:
            scenario: Either 'high' or 'normal'
        """
        if scenario not in ['high', 'normal']:
            raise ValueError(f"Invalid scenario: {scenario}. Must be 'high' or 'normal'")

        self.scenario = scenario
        print(f"✓ Price scenario set to: {scenario.upper()}")

    def get_price(self, index: int) -> float:
        """
        Get electricity price for given data index

        Args:
            index: Index into historical data

        Returns:
            Price in EUR/kWh
        """
        if self.scenario == 'high':
            return self.data['Price_High'].iloc[index]
        else:
            return self.data['Price_Normal'].iloc[index]

    def get_price_forecast(self, current_index: int, horizon_steps: int = 96) -> pd.Series:
        """
        Get price forecast for next N timesteps

        Args:
            current_index: Current position in data
            horizon_steps: Number of future steps (default 96 = 24 hours)

        Returns:
            Series of future prices
        """
        end_index = min(current_index + horizon_steps, len(self.data))

        if self.scenario == 'high':
            return self.data['Price_High'].iloc[current_index:end_index]
        else:
            return self.data['Price_Normal'].iloc[current_index:end_index]

    def get_scenario_stats(self) -> dict:
        """Get statistics for both scenarios"""

        stats = {
            'high': {
                'min': self.data['Price_High'].min(),
                'max': self.data['Price_High'].max(),
                'mean': self.data['Price_High'].mean(),
                'std': self.data['Price_High'].std(),
            },
            'normal': {
                'min': self.data['Price_Normal'].min(),
                'max': self.data['Price_Normal'].max(),
                'mean': self.data['Price_Normal'].mean(),
                'std': self.data['Price_Normal'].std(),
            }
        }

        return stats

    def identify_cheap_windows(
        self,
        current_index: int,
        horizon_steps: int = 96,
        percentile: float = 25.0
    ) -> list:
        """
        Identify cheap electricity windows in forecast

        Args:
            current_index: Current position
            horizon_steps: Forecast horizon
            percentile: Price percentile to consider "cheap" (default 25th)

        Returns:
            List of (start_index, end_index, avg_price) for cheap periods
        """
        prices = self.get_price_forecast(current_index, horizon_steps)
        threshold = prices.quantile(percentile / 100.0)

        cheap_windows = []
        in_window = False
        window_start = None

        for i, price in enumerate(prices):
            if price <= threshold:
                if not in_window:
                    window_start = current_index + i
                    in_window = True
            else:
                if in_window:
                    window_end = current_index + i - 1
                    avg_price = prices.iloc[window_start - current_index:window_end - current_index + 1].mean()
                    cheap_windows.append((window_start, window_end, avg_price))
                    in_window = False

        # Handle case where cheap window extends to end
        if in_window:
            window_end = current_index + len(prices) - 1
            avg_price = prices.iloc[window_start - current_index:].mean()
            cheap_windows.append((window_start, window_end, avg_price))

        return cheap_windows


if __name__ == "__main__":
    """Test price manager"""

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))

    from data_loader import HSYDataLoader

    print("=== Testing Price Manager ===\n")

    # Load data
    loader = HSYDataLoader()
    loader.load_all_data()

    # Create price manager
    pm = PriceManager(loader.main_data)

    # Get statistics
    stats = pm.get_scenario_stats()

    print("Price Scenario Statistics:")
    print("\nHIGH scenario (high variation/peaks):")
    print(f"  Min:  {stats['high']['min']:.3f} EUR/kWh")
    print(f"  Max:  {stats['high']['max']:.3f} EUR/kWh")
    print(f"  Mean: {stats['high']['mean']:.3f} EUR/kWh")
    print(f"  Std:  {stats['high']['std']:.3f} EUR/kWh")
    print(f"  Range: {stats['high']['max'] - stats['high']['min']:.3f} EUR/kWh")

    print("\nNORMAL scenario (contemporary everyday):")
    print(f"  Min:  {stats['normal']['min']:.3f} EUR/kWh")
    print(f"  Max:  {stats['normal']['max']:.3f} EUR/kWh")
    print(f"  Mean: {stats['normal']['mean']:.3f} EUR/kWh")
    print(f"  Std:  {stats['normal']['std']:.3f} EUR/kWh")
    print(f"  Range: {stats['normal']['max'] - stats['normal']['min']:.3f} EUR/kWh")

    # Test scenario switching
    print("\n=== Testing Scenario Switching ===")
    pm.set_scenario('high')
    price_high = pm.get_price(100)
    print(f"Price at index 100 (HIGH scenario): {price_high:.3f} EUR/kWh")

    pm.set_scenario('normal')
    price_normal = pm.get_price(100)
    print(f"Price at index 100 (NORMAL scenario): {price_normal:.3f} EUR/kWh")

    # Test cheap windows identification
    print("\n=== Identifying Cheap Windows (next 24h) ===")
    pm.set_scenario('high')  # Use high scenario for dramatic differences
    cheap_windows = pm.identify_cheap_windows(current_index=0, horizon_steps=96, percentile=25)

    print(f"Found {len(cheap_windows)} cheap electricity windows:")
    for i, (start, end, avg_price) in enumerate(cheap_windows[:5]):  # Show first 5
        duration_hours = (end - start + 1) * 0.25
        print(f"  Window {i+1}: Steps {start}-{end} ({duration_hours:.1f}h), Avg: {avg_price:.3f} EUR/kWh")
