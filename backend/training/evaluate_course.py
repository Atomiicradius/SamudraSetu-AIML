"""One comparison table: persistence vs Holt vs lstm (old) vs lstm_v2.

Run from the repository root AFTER train_lstm_v2.py:

    python backend/training/evaluate_course.py

All four models are scored on the SAME test windows (the lstm_v2 test split:
the last 20% of rows, after a 60-row purge gap). For each window the forecast
origin is row t and the target is rate[t+h] in raw USD/MT.

* persistence : rate[t]
* holt        : statsmodels damped-trend ExponentialSmoothing fitted on the
                trailing 365 rows up to and including t (no look-ahead)
* lstm (old)  : backend/artifacts/lstm_freight_model.pth with its ORIGINAL
                preprocessing (full-series ffill+bfill and full-series scaler
                from lstm_metadata.json). Caveat: that scaler/fill used future
                data, and the old model trained on rows up to ~2021-12, so it
                is evaluated exactly as it is served, not as a clean test.
* lstm_v2     : backend/artifacts/lstm_v2_freight_model.pth

Nothing here trains a model or modifies an existing file; it writes only
data/model/course_eval_results.json.
"""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from statsmodels.tsa.holtwinters import ExponentialSmoothing

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import train_lstm_v2 as v2  # noqa: E402  (same folder; reuses split + metrics code)

OUT_PATH = PROJECT_ROOT / "data" / "model" / "course_eval_results.json"
HOLT_HISTORY = 365


def holt_predictions(rate_series: np.ndarray, origin_positions: np.ndarray) -> np.ndarray:
    """(N, 4) Holt forecasts for each origin using only rows <= origin."""
    out = np.zeros((len(origin_positions), len(v2.HORIZONS)))
    for n, pos in enumerate(origin_positions):
        history = rate_series[max(0, pos - HOLT_HISTORY + 1): pos + 1]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            fit = ExponentialSmoothing(history, trend="add", damped_trend=True).fit(optimized=True)
            path = np.asarray(fit.forecast(v2.MAX_H))
        out[n] = [path[h - 1] for h in v2.HORIZONS]
    return out


def old_lstm_predictions(master: pd.DataFrame, end_dates: np.ndarray) -> np.ndarray:
    """(N, 4) USD/MT forecasts from the committed LSTM, as the API serves it."""
    meta = json.loads((PROJECT_ROOT / "data" / "model" / "lstm_metadata.json").read_text(encoding="utf-8"))
    cols, target = meta["num_cols"], meta["target_col"]
    mean = np.asarray(meta["scaler_mean"]); scale = np.asarray(meta["scaler_scale"])
    numeric = master[cols].ffill().bfill()  # old (leaky) preprocessing, on purpose
    scaled = ((numeric.to_numpy(dtype=np.float64) - mean) / scale).astype(np.float32)
    pos = master["date"].reset_index(drop=True)
    idx = pd.Index(pos).get_indexer(pd.to_datetime(end_dates))
    windows = np.stack([scaled[i - meta["lookback_days"] + 1: i + 1] for i in idx])

    model = v2.FreightLSTM(input_dim=len(cols))
    model.load_state_dict(torch.load(PROJECT_ROOT / "backend" / "artifacts" / "lstm_freight_model.pth",
                                     map_location="cpu", weights_only=True))
    model.eval()
    with torch.no_grad():
        out = model(torch.from_numpy(windows)).numpy().astype(np.float64)
    t = cols.index(target)
    return out * scale[t] + mean[t]  # columns are the 7/14/30/60-day forecasts


def main() -> None:
    meta_path = v2.META_PATH
    if not meta_path.exists() or not v2.ARTIFACT_PATH.exists():
        raise SystemExit("Run backend/training/train_lstm_v2.py first (artifact/metadata missing).")
    v2_meta = json.loads(meta_path.read_text(encoding="utf-8"))
    data = v2.prepare_data(drop_sparse_columns=bool(v2_meta["dropped_sparse_columns"]))
    test = data["splits"]["test"]

    master = pd.read_csv(v2.DATA_PATH, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    frame = data["frame"]
    rate_full = frame[data["target"]].to_numpy(dtype=np.float64)
    origin_pos = pd.Index(frame["date"]).get_indexer(pd.to_datetime(test["end_dates"]))

    # lstm_v2
    model = v2.FreightLSTM(input_dim=len(data["columns"]))
    model.load_state_dict(torch.load(v2.ARTIFACT_PATH, map_location="cpu", weights_only=True))
    model.eval()
    with torch.no_grad():
        v2_pred = test["rate_t"][:, None] * np.exp(model(torch.from_numpy(test["X"])).numpy().astype(np.float64))

    print(f"Scoring {len(origin_pos)} test windows "
          f"({str(test['end_dates'][0])[:10]} -> {str(test['end_dates'][-1])[:10]}); fitting Holt per window...")
    predictions = {
        "persistence": np.repeat(test["rate_t"][:, None], len(v2.HORIZONS), axis=1),
        "holt": holt_predictions(rate_full, origin_pos),
        "lstm (old)": old_lstm_predictions(master, test["end_dates"]),
        "lstm_v2": v2_pred,
    }

    results: dict = {"n_test_windows": int(len(origin_pos)), "horizons": {}}
    print("\n| Horizon | Model | MAE | RMSE | MAPE % | Dir. acc % |")
    print("|---|---|---|---|---|---|")
    for k, h in enumerate(v2.HORIZONS):
        actual = test["future_rate"][:, k]
        per_model = {name: v2.compute_metrics(test["rate_t"], actual, pred[:, k])
                     for name, pred in predictions.items()}
        results["horizons"][f"{h}-Day"] = per_model
        for name, m in per_model.items():
            da = "n/a" if m["directional_accuracy_pct"] is None else f"{m['directional_accuracy_pct']:.1f}"
            print(f"| {h}d | {name} | {m['mae']:.3f} | {m['rmse']:.3f} | {m['mape_pct']:.2f} | {da} |")

    print("\nVerdict vs persistence (needs lower MAE AND lower RMSE):")
    for h in v2.HORIZONS:
        per_model = results["horizons"][f"{h}-Day"]
        base = per_model["persistence"]
        for name in ("holt", "lstm (old)", "lstm_v2"):
            m = per_model[name]
            beats = m["mae"] < base["mae"] and m["rmse"] < base["rmse"]
            print(f"  {h:>2}d  {name:<11}: {'beats' if beats else 'does NOT beat'} persistence "
                  f"(MAE {m['mae']:.3f} vs {base['mae']:.3f})")
    anything = any(
        results["horizons"][f"{h}-Day"][n]["mae"] < results["horizons"][f"{h}-Day"]["persistence"]["mae"]
        and results["horizons"][f"{h}-Day"][n]["rmse"] < results["horizons"][f"{h}-Day"]["persistence"]["rmse"]
        for h in v2.HORIZONS for n in ("holt", "lstm (old)", "lstm_v2")
    )
    if not anything:
        print("\nHONEST SUMMARY: no model beats persistence at any horizon on this test set. "
              "The freight target is a simulated random walk, so none is expected to.")
    OUT_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nSaved: {OUT_PATH}")


if __name__ == "__main__":
    main()
