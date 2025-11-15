"""
Calculate Baseline Cost from Historical HSY Data

This script analyzes the historical data to establish baseline metrics:
1. Total Energy Cost (EUR)
2. Specific Energy Consumption (kWh/m³)
3. Constraint violations

This serves as the benchmark that our multi-agent AI system must beat.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import json

sys.path.insert(0, str(Path(__file__).parent / 'src' / 'simulation'))
from data_loader import HSYDataLoader

def calculate_baseline_metrics(data: pd.DataFrame, price_scenario: str = 'normal'):
    """
    Calculate baseline metrics from historical data

    Args:
        data: Historical operational data
        price_scenario: 'normal' or 'high'

    Returns:
        Dictionary with baseline metrics
    """
    print("\n" + "="*60)
    print("BASELINE COST CALCULATION - Historical HSY Data")
    print("="*60)
    print(f"\nPrice Scenario: {price_scenario.upper()}")
    print(f"Duration: {data['Time stamp'].min()} to {data['Time stamp'].max()}")
    print(f"Timesteps: {len(data)} (every 15 minutes)")
    print()

    # Price column
    price_col = 'Price_High' if price_scenario == 'high' else 'Price_Normal'

    # Pump power columns (8 pumps: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4)
    pump_power_cols = [
        'Pump power 1.1', 'Pump power 1.2', 'Pump power 1.3', 'Pump power 1.4',
        'Pump power 2.1', 'Pump power 2.2', 'Pump power 2.3', 'Pump power 2.4'
    ]

    # Check which columns exist (some might be named differently)
    available_power_cols = []
    print("Checking for pump power columns...")
    for col in data.columns:
        if 'power' in col.lower() or 'efficiency' in col.lower():
            if any(f"{i}.{j}" in col for i in [1,2] for j in [1,2,3,4]):
                available_power_cols.append(col)
                print(f"  Found: {col}")

    if not available_power_cols:
        print("❌ No pump power columns found! Check column names.")
        print(f"\nAvailable columns: {list(data.columns)}")
        return None

    print(f"\n✓ Using {len(available_power_cols)} pump power columns")

    # Initialize accumulators
    total_cost = 0.0
    total_energy_kwh = 0.0
    total_flow_m3 = 0.0

    # Track violations
    L1_violations = 0
    F2_violations = 0
    L1_max_observed = 0
    F2_max_observed = 0

    # Timestep details (for per-timestep analysis)
    timestep_data = []

    # Process each timestep
    for idx, row in data.iterrows():
        # Sum power of all pumps
        total_power_kw = 0
        for col in available_power_cols:
            power = row[col]
            if pd.notna(power):
                total_power_kw += power

        # Energy consumed (kW × 0.25h = kWh)
        energy_kwh = total_power_kw * 0.25

        # Electricity price
        price = row[price_col]
        if pd.isna(price):
            price = 0.0  # Handle missing prices

        # Cost for this timestep
        cost_eur = energy_kwh * price

        # Flow pumped (m³/h × 0.25h = m³)
        F2 = row['F2']
        if pd.isna(F2):
            F2 = 0.0
        flow_m3 = F2 * 0.25

        # Accumulate
        total_cost += cost_eur
        total_energy_kwh += energy_kwh
        total_flow_m3 += flow_m3

        # Check constraints
        L1 = row['L1']
        if pd.notna(L1):
            if L1 > 8.0 or L1 < 0.0:
                L1_violations += 1
            L1_max_observed = max(L1_max_observed, L1)

        if pd.notna(F2):
            if F2 > 16000:
                F2_violations += 1
            F2_max_observed = max(F2_max_observed, F2)

        # Store timestep data
        timestep_data.append({
            'timestamp': row['Time stamp'],
            'L1': L1 if pd.notna(L1) else None,
            'F2': F2 if pd.notna(F2) else None,
            'total_power_kw': total_power_kw,
            'energy_kwh': energy_kwh,
            'price_eur_kwh': price,
            'cost_eur': cost_eur,
            'flow_m3': flow_m3
        })

    # Calculate specific energy
    specific_energy = total_energy_kwh / total_flow_m3 if total_flow_m3 > 0 else 0

    # Results
    results = {
        'metadata': {
            'duration_days': (data['Time stamp'].max() - data['Time stamp'].min()).days,
            'timesteps': len(data),
            'price_scenario': price_scenario,
            'start_date': str(data['Time stamp'].min()),
            'end_date': str(data['Time stamp'].max())
        },
        'baseline_metrics': {
            'total_cost_eur': round(total_cost, 2),
            'total_energy_kwh': round(total_energy_kwh, 2),
            'total_flow_m3': round(total_flow_m3, 2),
            'specific_energy_kwh_per_m3': round(specific_energy, 6),
            'average_cost_per_day_eur': round(total_cost / ((data['Time stamp'].max() - data['Time stamp'].min()).days), 2),
            'average_power_kw': round(total_energy_kwh / (len(data) * 0.25), 2)
        },
        'constraints': {
            'L1_min': round(data['L1'].min(), 2),
            'L1_max': round(L1_max_observed, 2),
            'L1_violations': L1_violations,
            'F2_max': round(F2_max_observed, 2),
            'F2_violations': F2_violations,
            'total_violations': L1_violations + F2_violations
        },
        'price_statistics': {
            'price_min': round(data[price_col].min(), 4),
            'price_max': round(data[price_col].max(), 4),
            'price_mean': round(data[price_col].mean(), 4),
            'price_median': round(data[price_col].median(), 4)
        }
    }

    return results, timestep_data


def print_baseline_report(results: dict):
    """Print formatted baseline report"""

    print("\n" + "="*60)
    print("BASELINE METRICS REPORT")
    print("="*60)

    meta = results['metadata']
    metrics = results['baseline_metrics']
    constraints = results['constraints']
    prices = results['price_statistics']

    print(f"\n📅 DURATION")
    print(f"  Start: {meta['start_date']}")
    print(f"  End:   {meta['end_date']}")
    print(f"  Days:  {meta['duration_days']}")
    print(f"  Timesteps: {meta['timesteps']} (15-min intervals)")

    print(f"\n💰 COST METRICS")
    print(f"  Total Cost:           €{metrics['total_cost_eur']:,.2f}")
    print(f"  Average Cost/Day:     €{metrics['average_cost_per_day_eur']:,.2f}")

    print(f"\n⚡ ENERGY METRICS")
    print(f"  Total Energy:         {metrics['total_energy_kwh']:,.2f} kWh")
    print(f"  Average Power:        {metrics['average_power_kw']:,.2f} kW")
    print(f"  Total Flow Pumped:    {metrics['total_flow_m3']:,.2f} m³")
    print(f"  Specific Energy:      {metrics['specific_energy_kwh_per_m3']:.6f} kWh/m³")

    print(f"\n🚨 CONSTRAINT COMPLIANCE")
    print(f"  L1 Range:             {constraints['L1_min']:.2f}m - {constraints['L1_max']:.2f}m")
    print(f"  L1 Limit:             0.0m - 8.0m (Alarm: 7.2m)")
    print(f"  L1 Violations:        {constraints['L1_violations']}")
    if constraints['L1_max'] > 7.2:
        print(f"    ⚠️  Max L1 exceeded alarm threshold!")

    print(f"\n  F2 Max Observed:      {constraints['F2_max']:,.0f} m³/h")
    print(f"  F2 Limit:             16,000 m³/h")
    print(f"  F2 Violations:        {constraints['F2_violations']}")

    print(f"\n  Total Violations:     {constraints['total_violations']}")
    if constraints['total_violations'] == 0:
        print(f"    ✅ No violations - baseline is compliant!")
    else:
        print(f"    ❌ {constraints['total_violations']} violations detected")

    print(f"\n💵 ELECTRICITY PRICES ({meta['price_scenario'].upper()} scenario)")
    print(f"  Min:    {prices['price_min']:.4f} EUR/kWh")
    print(f"  Max:    {prices['price_max']:.4f} EUR/kWh")
    print(f"  Mean:   {prices['price_mean']:.4f} EUR/kWh")
    print(f"  Median: {prices['price_median']:.4f} EUR/kWh")

    print("\n" + "="*60)
    print("✓ Baseline calculation complete!")
    print("="*60)


def main():
    """Main execution"""

    # Load data
    print("Loading HSY data...")
    loader = HSYDataLoader()
    data_dict = loader.load_all_data()
    data = data_dict['operational_data']

    print(f"\n✓ Loaded {len(data)} timesteps")

    # Calculate for both price scenarios
    for scenario in ['normal', 'high']:
        results, timestep_data = calculate_baseline_metrics(data, price_scenario=scenario)

        if results:
            print_baseline_report(results)

            # Save results
            output_file = Path(__file__).parent / f'baseline_metrics_{scenario}.json'
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n💾 Saved to: {output_file}")

            # Save timestep data
            df = pd.DataFrame(timestep_data)
            csv_file = Path(__file__).parent / f'baseline_timesteps_{scenario}.csv'
            df.to_csv(csv_file, index=False)
            print(f"💾 Saved timestep data to: {csv_file}")

        print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    main()
