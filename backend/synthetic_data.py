"""
Synthetic placeholder data generator for the freight forecasting MVP.

*** THIS IS NOT REAL SAIL / MARKET DATA. ***
Generates ~2 years of daily "freight rate" history for ANY (origin,
destination, vessel_class, cargo_type) combination the procurement form can
produce, built from a trend + annual seasonal wobble + weekly wobble + noise
+ a small random-walk component (for realistic autocorrelation).

Reproducibility is the point of this module: the random generator is seeded
deterministically from a stable hash of the route+vessel identifiers, so
re-selecting the same combination during a live demo -- even across app
restarts -- always regenerates the exact same series and the exact same
downstream numbers. Python's built-in `hash()` is deliberately NOT used here
because it's salted per-process (PYTHONHASHSEED) and would silently change
on every restart; hashlib gives a stable digest instead.

Run directly to (re)write a small sample CSV (data/freight_rates.csv) for a
few example combinations -- purely optional. The app never requires this
file: it generates every combination on the fly. If the file *is* present
and contains rows matching the selected (route, vessel_class, cargo_type),
the app prefers that "real" data over synthetic generation.
"""

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

DAYS = 730  # ~2 years of daily history


def stable_seed(*parts: str) -> int:
    """Deterministic 32-bit seed from route+vessel identifiers, stable
    across processes and machines (unlike the salted builtin hash())."""
    key = "|".join(parts).encode("utf-8")
    digest = hashlib.sha256(key).hexdigest()
    return int(digest[:8], 16) % (2**32)


def generate_synthetic_series(origin: str, destination: str, vessel_class: str,
                               cargo_type: str = "Coal", days: int = DAYS, end_date=None) -> pd.DataFrame:
    """Generate one deterministic synthetic daily rate series for a single
    origin/destination/vessel/cargo combination."""
    seed = stable_seed(origin, destination, vessel_class, cargo_type)
    rng = np.random.default_rng(seed)

    if end_date is None:
        end_date = pd.Timestamp.today().normalize()
    dates = pd.date_range(end=end_date, periods=days, freq="D")
    t = np.arange(days)

    # Every parameter below is itself drawn from the same seeded rng, so the
    # single seed fully determines the whole series -- same combo, same
    # numbers, every time.
    base = rng.uniform(10.0, 30.0)
    trend_per_day = rng.uniform(-0.003, 0.003)
    seasonal_amp = rng.uniform(0.5, 2.5)
    weekly_amp = rng.uniform(0.2, 0.6)
    noise_std = rng.uniform(0.4, 0.9)

    trend = base + trend_per_day * t
    seasonal = seasonal_amp * np.sin(2 * np.pi * t / 365.25)
    weekly = weekly_amp * np.sin(2 * np.pi * t / 7)
    noise = rng.normal(0, noise_std, days)
    random_walk = np.cumsum(rng.normal(0, noise_std * 0.15, days))

    rate = trend + seasonal + weekly + noise + random_walk
    rate = np.clip(rate, 1.0, None)

    return pd.DataFrame({
        "date": dates,
        "route": f"{origin}-{destination}",
        "vessel_class": vessel_class,
        "cargo_type": cargo_type,
        "rate_usd_per_mt": rate.round(2),
    })


if __name__ == "__main__":
    # Optional: write a small sample CSV for a few example combinations.
    # Not required for the app to run -- it generates every combination
    # dynamically -- but useful as an offline data sample, and it also
    # demonstrates the "prefer real data if present" override path.
    example_combos = [
        ("Australia", "Paradip", "Supramax"),
        ("Indonesia", "Visakhapatnam", "Panamax"),
        ("Mozambique", "Dhamra", "Handysize"),
    ]
    frames = [generate_synthetic_series(o, d, v) for o, d, v in example_combos]
    df = pd.concat(frames, ignore_index=True)

    out_path = Path(__file__).parent / "freight_rates.csv"
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df)} rows to {out_path}")
