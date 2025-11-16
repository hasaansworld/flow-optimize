#!/usr/bin/env python3
"""
Quick plotting script for AI evaluation results.

Usage (from project root):
    python plot_ai_results.py
or:
    python plot_ai_results.py ai_evaluation_normal_20steps.json
"""

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# --------- CONFIG ---------
# Default evaluation file name (can be overridden via CLI arg)
DEFAULT_EVAL_FILENAME = "ai_evaluation_normal_20steps.json"
# --------------------------


def load_constraints(project_root: Path):
    """
    Import CONSTRAINTS from config/constraints.py
    """
    sys.path.insert(0, str(project_root / "config"))
    try:
        from constraints import CONSTRAINTS  # type: ignore
        return CONSTRAINTS
    except Exception as e:
        print(f"⚠️ Could not import CONSTRAINTS from config/constraints.py: {e}")
        print("   Plots will be shown without min/max level bands.")
        return None


def load_ai_eval(path: Path) -> pd.DataFrame:
    """
    Load AI evaluation JSON and flatten into a pandas DataFrame.
    """
    with open(path, "r") as f:
        data = json.load(f)

    preds = data.get("predictions", [])
    if not preds:
        raise ValueError("No 'predictions' found in evaluation file.")

    # Flatten JSON into DataFrame
    df = pd.json_normalize(preds)

    # Parse timestamp to datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Convenience columns
    df["L1"] = df["system_state.L1_m"]
    df["V"] = df["system_state.V_m3"]
    df["price"] = df["system_state.electricity_price_eur_kwh"]
    df["power_kw"] = df["cost_calculation.total_power_kw"]
    df["flow_m3"] = df["cost_calculation.flow_pumped_m3"]

    return df


def plot_level(df: pd.DataFrame, constraints):
    """
    Plot tank level L1 over time, with constraint bands if available.
    """
    plt.figure(figsize=(12, 4))
    plt.plot(df["timestamp"], df["L1"], label="L1 (simulated level)")

    if constraints is not None:
        try:
            plt.axhline(constraints.L1_MIN, linestyle="--", label="L1_MIN")
            plt.axhline(constraints.L1_MAX, linestyle="--", label="L1_MAX")
        except Exception:
            # In case attributes are named differently or missing
            pass

    plt.title("Tank Level Over Time")
    plt.xlabel("Time")
    plt.ylabel("L1 [m]")
    plt.legend()
    plt.tight_layout()
    plt.show()


def plot_price_and_power(df: pd.DataFrame):
    """
    Plot electricity price and total pump power on a shared time axis.
    """
    fig, ax1 = plt.subplots(figsize=(12, 4))

    ax1.set_xlabel("Time")
    ax1.set_ylabel("Electricity price [€/kWh]")
    ax1.plot(df["timestamp"], df["price"], label="Price")
    ax1.tick_params(axis="y")

    ax2 = ax1.twinx()
    ax2.set_ylabel("Total pump power [kW]")
    ax2.plot(df["timestamp"], df["power_kw"], label="Pump power", alpha=0.7)
    ax2.tick_params(axis="y")

    plt.title("Electricity Price and Pump Power")
    fig.tight_layout()
    plt.show()


def main():
    project_root = Path(__file__).parent

    # Pick evaluation filename
    if len(sys.argv) > 1:
        eval_filename = sys.argv[1]
    else:
        eval_filename = DEFAULT_EVAL_FILENAME

    eval_path = project_root / eval_filename

    if not eval_path.exists():
        print(f"❌ Evaluation file not found: {eval_path}")
        print("   Pass a filename as argument or change DEFAULT_EVAL_FILENAME.")
        sys.exit(1)

    print(f"📂 Loading evaluation from: {eval_path}")
    df = load_ai_eval(eval_path)

    print(f"Loaded {len(df)} timesteps.")
    print("First few rows:")
    print(df[["timestamp", "L1", "price", "power_kw", "flow_m3"]].head())

    constraints = load_constraints(project_root)

    # Plots
    plot_level(df, constraints)
    plot_price_and_power(df)


if __name__ == "__main__":
    main()
