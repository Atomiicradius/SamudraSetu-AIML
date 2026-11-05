"""One comparison table: persistence vs Holt vs lstm (old) vs lstm_v2 vs TimesFM.

Run from the repository root AFTER train_lstm_v2.py. TimesFM needs its own
environment (timesfm package + internet on first run to download weights):

    .\\.venv-tfm\\Scripts\\python.exe backend/training/evaluate_course.py
    .\\.venv-tfm\\Scripts\\python.exe backend/training/evaluate_course.py --timesfm-stride 3
    python backend/training/evaluate_course.py --skip-timesfm   # no timesfm package

All models are scored on the SAME test windows (the lstm_v2 test split:
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
* timesfm     : zero-shot TimesFM 2.5 (200M, google/timesfm-2.5-200m-pytorch),
                context = trailing 512 rows of the raw freight target ending
                at t (no fine-tuning, no covariates), point = median output,
                band = 0.1/0.9 quantiles. If --timesfm-stride N > 1, TimesFM
                is run on every Nth window only and is compared with
                persistence re-scored on exactly those windows.

Nothing here trains a model or modifies an existing file; it writes only
data/model/course_eval_results.json.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
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
TIMESFM_REPO = "google/timesfm-2.5-200m-pytorch"
TIMESFM_CONTEXT = 512
TIMESFM_MAX_HORIZON = 128  # must be a multiple of the model's output patch (128)
TIMESFM_BATCH = 32
Q10_INDEX, Q90_INDEX = 1, 9  # quantile axis = [mean, q0.1 ... q0.9]


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


def timesfm_predictions(rate_full: np.ndarray, origin_pos: np.ndarray):
    """Zero-shot TimesFM 2.5 forecasts -> (point, q10, q90), each (N, 4) in USD/MT.

    API (read from timesfm 3.0.2 source, timesfm/timesfm_2p5/timesfm_2p5_torch.py):
      TimesFM_2p5_200M_torch.from_pretrained(repo_id, torch_compile=False)
      model.compile(ForecastConfig(...))
      point (N,H), quant (N,H,10) = model.forecast(horizon=H, inputs=[1-D arrays])
    quant's last axis is [mean, q0.1, ..., q0.9]; point is the median (q0.5).
    """
    import timesfm  # imported lazily so the other models run without it

    t0 = time.time()
    model = timesfm.TimesFM_2p5_200M_torch.from_pretrained(TIMESFM_REPO, torch_compile=False)
    model.compile(timesfm.ForecastConfig(
        max_context=TIMESFM_CONTEXT, max_horizon=TIMESFM_MAX_HORIZON,
        normalize_inputs=True, use_continuous_quantile_head=True,
        force_flip_invariance=True, infer_is_positive=True, fix_quantile_crossing=True,
        per_core_batch_size=TIMESFM_BATCH,
    ))
    print(f"TimesFM loaded from {TIMESFM_REPO} in {time.time() - t0:.0f}s; forecasting "
          f"{len(origin_pos)} windows (context {TIMESFM_CONTEXT} rows, horizon {v2.MAX_H})...")

    point = np.zeros((len(origin_pos), len(v2.HORIZONS)))
    q10 = np.zeros_like(point); q90 = np.zeros_like(point)
    h_idx = [h - 1 for h in v2.HORIZONS]
    t0 = time.time()
    for start in range(0, len(origin_pos), TIMESFM_BATCH):
        chunk = origin_pos[start:start + TIMESFM_BATCH]
        inputs = [rate_full[max(0, p - TIMESFM_CONTEXT + 1): p + 1].astype(np.float32) for p in chunk]
        pt, quant = model.forecast(horizon=v2.MAX_H, inputs=inputs)
        point[start:start + len(chunk)] = pt[:, h_idx]
        q10[start:start + len(chunk)] = quant[:, h_idx, Q10_INDEX]
        q90[start:start + len(chunk)] = quant[:, h_idx, Q90_INDEX]
        print(f"  {min(start + TIMESFM_BATCH, len(origin_pos))}/{len(origin_pos)} "
              f"({time.time() - t0:.0f}s)", flush=True)
    return point, q10, q90


def _fmt(m: dict, key: str, spec: str) -> str:
    value = m.get(key)
    return "n/a" if value is None else format(value, spec)


def _row(h: int, name: str, m: dict) -> str:
    return (f"| {h}d | {name} | {m['mae']:.3f} | {m['rmse']:.3f} | {m['mape_pct']:.2f} | "
            f"{_fmt(m, 'directional_accuracy_pct', '.1f')} | {_fmt(m, 'p10_p90_coverage_pct', '.1f')} |")


def _beats(m: dict, base: dict) -> bool:
    return m["mae"] < base["mae"] and m["rmse"] < base["rmse"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--timesfm-stride", type=int, default=1, choices=range(1, 6), metavar="N",
                        help="run TimesFM on every Nth test window (1-5, default 1 = all windows)")
    parser.add_argument("--skip-timesfm", action="store_true", help="skip TimesFM entirely")
    args = parser.parse_args()

    if not v2.META_PATH.exists() or not v2.ARTIFACT_PATH.exists():
        raise SystemExit("Run backend/training/train_lstm_v2.py first (artifact/metadata missing).")
    v2_meta = json.loads(v2.META_PATH.read_text(encoding="utf-8"))
    data = v2.prepare_data(drop_sparse_columns=bool(v2_meta["dropped_sparse_columns"]))
    test = data["splits"]["test"]

    master = pd.read_csv(v2.DATA_PATH, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    frame = data["frame"]
    rate_full = frame[data["target"]].to_numpy(dtype=np.float64)
    origin_pos = pd.Index(frame["date"]).get_indexer(pd.to_datetime(test["end_dates"]))

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
    bands: dict[str, tuple[np.ndarray, np.ndarray]] = {}

    # ---- TimesFM (zero-shot) ----
    stride = args.timesfm_stride
    sel = np.arange(0, len(origin_pos), stride)
    tfm = None
    tfm_note = None
    if not args.skip_timesfm:
        try:
            tfm = timesfm_predictions(rate_full, origin_pos[sel])
        except ImportError as exc:
            tfm_note = f"TimesFM skipped: package not importable in this Python ({exc}). Use .venv-tfm."
        except Exception as exc:  # download/offline/compile problems should not hide the other results
            tfm_note = f"TimesFM FAILED: {type(exc).__name__}: {exc}"
        if tfm_note:
            print("\n" + tfm_note)
    if tfm is not None and stride == 1:
        predictions["timesfm"] = tfm[0]
        bands["timesfm"] = (tfm[1], tfm[2])

    results: dict = {"n_test_windows": int(len(origin_pos)), "horizons": {}}
    print("\n| Horizon | Model | MAE | RMSE | MAPE % | Dir. acc % | P10-P90 cov % |")
    print("|---|---|---|---|---|---|---|")
    for k, h in enumerate(v2.HORIZONS):
        actual = test["future_rate"][:, k]
        per_model = {}
        for name, pred in predictions.items():
            m = v2.compute_metrics(test["rate_t"], actual, pred[:, k])
            if name in bands:
                lo, hi = bands[name]
                m["p10_p90_coverage_pct"] = float(np.mean((actual >= lo[:, k]) & (actual <= hi[:, k])) * 100.0)
            per_model[name] = m
        results["horizons"][f"{h}-Day"] = per_model
        for name, m in per_model.items():
            print(_row(h, name, m))

    # ---- TimesFM on a subset: rescore persistence on exactly those windows ----
    if tfm is not None and stride > 1:
        results["timesfm_subset"] = {"stride": stride, "n_windows": int(len(sel)), "horizons": {}}
        print(f"\nTimesFM was run on every {stride}th window only ({len(sel)} of {len(origin_pos)}); "
              f"persistence is re-scored on exactly those windows.")
        print("\n| Horizon | Model (subset) | MAE | RMSE | MAPE % | Dir. acc % | P10-P90 cov % |")
        print("|---|---|---|---|---|---|---|")
        for k, h in enumerate(v2.HORIZONS):
            actual, rate_t = test["future_rate"][sel, k], test["rate_t"][sel]
            m_t = v2.compute_metrics(rate_t, actual, tfm[0][:, k])
            m_t["p10_p90_coverage_pct"] = float(np.mean((actual >= tfm[1][:, k]) & (actual <= tfm[2][:, k])) * 100.0)
            m_p = v2.compute_metrics(rate_t, actual, rate_t)
            results["timesfm_subset"]["horizons"][f"{h}-Day"] = {"timesfm": m_t, "persistence": m_p}
            print(_row(h, "persistence", m_p)); print(_row(h, "timesfm", m_t))

    # ---- verdicts ----
    print("\nVerdict vs persistence (needs lower MAE AND lower RMSE):")
    any_beats = False
    for h in v2.HORIZONS:
        per_model = results["horizons"][f"{h}-Day"]
        base = per_model["persistence"]
        for name in [n for n in per_model if n != "persistence"]:
            ok = _beats(per_model[name], base); any_beats |= ok
            print(f"  {h:>2}d  {name:<11}: {'beats' if ok else 'does NOT beat'} persistence "
                  f"(MAE {per_model[name]['mae']:.3f} vs {base['mae']:.3f})")
    if tfm is not None and stride > 1:
        for h in v2.HORIZONS:
            sub = results["timesfm_subset"]["horizons"][f"{h}-Day"]
            ok = _beats(sub["timesfm"], sub["persistence"]); any_beats |= ok
            print(f"  {h:>2}d  timesfm (subset, stride {stride}): {'beats' if ok else 'does NOT beat'} persistence "
                  f"(MAE {sub['timesfm']['mae']:.3f} vs {sub['persistence']['mae']:.3f})")
    if not any_beats:
        print("\nHONEST SUMMARY: no model beats persistence at any horizon on this test set. "
              "The freight target is a simulated random walk, so none is expected to.")
    else:
        print("\nSUMMARY: at least one model beats persistence on both MAE and RMSE for some horizon; "
              "see the verdict lines above and check the margin before reading much into it.")
    OUT_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nSaved: {OUT_PATH}")


if __name__ == "__main__":
    main()
