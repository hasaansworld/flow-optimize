"""
Data Loader for HSY Wastewater Pumping Station
Loads and preprocesses historical data from Excel files
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Tuple
from datetime import datetime


class HSYDataLoader:
    """Load and preprocess HSY historical data"""

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            # Auto-detect project root (2 levels up from this file)
            script_dir = Path(__file__).parent
            project_root = script_dir.parent.parent
            data_dir = project_root / "assets"

        self.data_dir = Path(data_dir)
        self.main_data = None
        self.volume_level_map = None

    def load_all_data(self) -> Dict:
        """Load all data files and return processed datasets"""

        print("Loading HSY historical data...")

        # Load main operational data
        self.main_data = self._load_main_data()

        # Load volume-level lookup table
        self.volume_level_map = self._load_volume_level_map()

        print(f"✓ Loaded {len(self.main_data)} records from {self.main_data['Time stamp'].min()} to {self.main_data['Time stamp'].max()}")
        print(f"✓ Loaded volume-level map with {len(self.volume_level_map)} entries")

        return {
            'operational_data': self.main_data,
            'volume_level_map': self.volume_level_map
        }

    def _load_main_data(self) -> pd.DataFrame:
        """Load main hackathon data file"""

        file_path = self.data_dir / "Hackathon_HSY_data.xlsx"

        # Read with header row
        df = pd.read_excel(file_path, sheet_name='Taul1', header=0)

        # Skip units row (first data row)
        df = df.iloc[1:].reset_index(drop=True)

        # Convert timestamp
        df['Time stamp'] = pd.to_datetime(df['Time stamp'])

        # Convert all numeric columns
        numeric_cols = df.columns[1:]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Rename columns for clarity
        df = df.rename(columns={
            'Water level in tunnel L2': 'L1',  # Note: This is actually L1 (tunnel level)
            'Water volume in tunnel V': 'V',
            'Sum of pumped flow to WWTP F2': 'F2',
            'Inflow to tunnel F1': 'F1',
            'Electricity price 1: high': 'Price_High',
            'Electricity price 2: normal': 'Price_Normal'
        })

        return df

    def _load_volume_level_map(self) -> pd.DataFrame:
        """Load volume vs level lookup table"""

        file_path = self.data_dir / "Volume of tunnel vs level Blominmäki.xlsx"

        df = pd.read_excel(file_path, sheet_name='Taul1')

        # Rename for clarity
        df = df.rename(columns={
            'Level L1 m': 'Level',
            'Volume V m³': 'Volume'
        })

        return df

    def get_pump_data_columns(self) -> Dict[str, list]:
        """Get lists of pump-related column names"""

        pump_ids = []
        for i in [1, 2]:
            for j in [1, 2, 3, 4]:
                pump_ids.append(f"{i}.{j}")

        return {
            'pump_ids': pump_ids,
            'flow_cols': [f'Pump flow {pid}' for pid in pump_ids],
            'efficiency_cols': [f'Pump efficiency {pid}' for pid in pump_ids],
            'frequency_cols': [f'Pump frequency {pid}' for pid in pump_ids]
        }

    def volume_to_level(self, volume: float) -> float:
        """Convert volume to level using lookup table with interpolation"""

        if self.volume_level_map is None:
            raise ValueError("Volume-level map not loaded. Call load_all_data() first.")

        # Linear interpolation
        return np.interp(
            volume,
            self.volume_level_map['Volume'].values,
            self.volume_level_map['Level'].values
        )

    def level_to_volume(self, level: float) -> float:
        """Convert level to volume using lookup table with interpolation"""

        if self.volume_level_map is None:
            raise ValueError("Volume-level map not loaded. Call load_all_data() first.")

        # Linear interpolation
        return np.interp(
            level,
            self.volume_level_map['Level'].values,
            self.volume_level_map['Volume'].values
        )

    def get_time_series(self, start_time: datetime = None, end_time: datetime = None) -> pd.DataFrame:
        """Get time series data for a specific period"""

        if self.main_data is None:
            raise ValueError("Data not loaded. Call load_all_data() first.")

        df = self.main_data.copy()

        if start_time:
            df = df[df['Time stamp'] >= start_time]
        if end_time:
            df = df[df['Time stamp'] <= end_time]

        return df


if __name__ == "__main__":
    # Test the data loader
    loader = HSYDataLoader()
    data = loader.load_all_data()

    print("\n=== Data Summary ===")
    print(f"Time range: {data['operational_data']['Time stamp'].min()} to {data['operational_data']['Time stamp'].max()}")
    print(f"Total records: {len(data['operational_data'])}")
    print(f"\nSample data:")
    print(data['operational_data'][['Time stamp', 'L1', 'V', 'F1', 'F2', 'Price_Normal']].head())

    print("\n=== Volume-Level Mapping ===")
    print(f"Level range: {data['volume_level_map']['Level'].min():.1f}m - {data['volume_level_map']['Level'].max():.1f}m")
    print(f"Volume range: {data['volume_level_map']['Volume'].min():.0f}m³ - {data['volume_level_map']['Volume'].max():.0f}m³")

    # Test conversions
    test_volume = 10000
    test_level = loader.volume_to_level(test_volume)
    print(f"\nTest conversion: {test_volume}m³ → {test_level:.2f}m")

    test_level = 5.0
    test_volume = loader.level_to_volume(test_level)
    print(f"Test conversion: {test_level}m → {test_volume:.0f}m³")
