"""Leakage-safe retrain of the Australia->Paradip Capesize freight LSTM (v2).

Run from the repository root:

    python backend/training/train_lstm_v2.py --drop-sparse-columns

What differs from the old ``train_lstm.py`` / ``build_master_datasets.py``:

* Missing values are filled with a causal forward-fill only (no backfill);
  rows that are still NaN at the start are dropped.
* The chronological split (70% train / 10% val / 20% test) happens BEFORE
  any scaling, with a PURGE_ROWS gap between segments. Windows are built
  inside each segment, so no label window crosses a boundary.
* StandardScaler statistics come from TRAIN rows only.
* Targets are log(rate[t+h] / rate[t]) on RAW USD/MT, for h = 7, 14, 30, 60.
* Early stopping uses VAL loss. The test set is touched exactly once, at
  the end, for reporting.

UNITS: data/model/master_macro_freight_daily.csv contains business days only
(no weekends). "Days" below (lookback, horizons, purge gap) are therefore
ROWS, exactly as in the old pipeline.

COLUMNS: the brief asks for the same 10 input columns as lstm_metadata.json.
Three of them (Supramax, Indonesia-Panamax, Mozambique-Handysize freight) are
empty before 2024-09-02. A forward-fill-only pipeline that drops leading NaN
rows would then keep just 526 rows, too few for val/test windows. By default
this script therefore stops with an explanation; pass --drop-sparse-columns to
train on the 7 dense columns instead (4,100+ rows from 2010-12-17).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "data" / "model" / "master_macro_freight_daily.csv"
OLD_META_PATH = PROJECT_ROOT / "data" / "model" / "lstm_metadata.json"
ARTIFACT_PATH = PROJECT_ROOT / "backend" / "artifacts" / "lstm_v2_freight_model.pth"
META_PATH = PROJECT_ROOT / "data" / "model" / "lstm_v2_metadata.json"
RESULTS_PATH = PROJECT_ROOT / "data" / "model" / "lstm_v2_results.json"

LOOKBACK = 30
HORIZONS = (7, 14, 30, 60)
MAX_H = max(HORIZONS)
PURGE_ROWS = 60
TRAIN_FRAC, VAL_FRAC = 0.70, 0.10  # remaining 0.20 is test
SEED = 42
MAX_EPOCHS = 60
PATIENCE = 8
BATCH_SIZE = 64
LEARNING_RATE = 1e-3
SPARSE_COVERAGE = 0.5  # columns with less raw coverage than this are "sparse"


class FreightLSTM(nn.Module):
    """Same architecture as the existing model: 2 layers, hidden 64, fc 64->32->4."""

    def __init__(self, input_dim: int, hidden_dim: int = 64, num_layers: int = 2,
                 output_dim: int = 4, dropout: float = 0.2) -> None:
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True,
                            dropout=dropout if num_layers > 1 else 0.0)
        self.fc = nn.Sequential(nn.Linear(hidden_dim, 32), nn.ReLU(),
                                nn.Dropout(dropout), nn.Linear(32, output_dim))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :])


# --------------------------------------------------------------------------
# Data preparation (shared with evaluate_course.py)
# --------------------------------------------------------------------------
def _windows(values: np.ndarray, rate: np.ndarray, dates: np.ndarray,
             start: int, end: int):
    """Build windows whose inputs AND labels lie entirely in rows [start, end)."""
    xs, rate_t, future, ends = [], [], [], []
    for i in range(start + LOOKBACK - 1, end - MAX_H):
        xs.append(values[i - LOOKBACK + 1: i + 1])
        rate_t.append(rate[i])
        future.append([rate[i + h] for h in HORIZONS])
        ends.append(dates[i])
    if not xs:
        raise SystemExit(f"Segment rows [{start}, {end}) is too short for one window "
                         f"(needs >= {LOOKBACK + MAX_H} rows).")
    rate_t = np.asarray(rate_t, dtype=np.float64)
    future = np.asarray(future, dtype=np.float64)
    return {
        "X_raw": np.asarray(xs, dtype=np.float32),
        "rate_t": rate_t,
        "future_rate": future,
        "y_log": np.log(future / rate_t[:, None]).astype(np.float32),
        "end_dates": np.asarray(ends),
    }


def prepare_data(drop_sparse_columns: bool = False) -> dict:
    meta = json.loads(OLD_META_PATH.read_text(encoding="utf-8"))
    columns = list(meta["num_cols"])
    target = meta["target_col"]

    raw = pd.read_csv(DATA_PATH, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    dropped = []
    if drop_sparse_columns:
        dropped = [c for c in columns if raw[c].notna().mean() < SPARSE_COVERAGE and c != target]
        columns = [c for c in columns if c not in dropped]

    filled = raw[["date"] + columns].copy()
    filled[columns] = filled[columns].ffill()  # causal fill ONLY, never bfill
    filled = filled.dropna().reset_index(drop=True)  # leading rows that are still NaN
    n = len(filled)

    train_end = int(n * TRAIN_FRAC)
    val_end = int(n * (TRAIN_FRAC + VAL_FRAC))
    ranges = {
        "train": (0, train_end),
        "val": (train_end + PURGE_ROWS, val_end),
        "test": (val_end + PURGE_ROWS, n),
    }
    min_rows = LOOKBACK + MAX_H
    for name, (a, b) in ranges.items():
        if b - a < min_rows + 1:
            raise SystemExit(
                f"STOP: after causal fill, {n} rows remain (from {filled['date'].iloc[0].date()}); "
                f"the {name} segment would have {b - a} rows but needs > {min_rows}.\n"
                f"Sparse columns: {[c for c in meta['num_cols'] if raw[c].notna().mean() < SPARSE_COVERAGE]}.\n"
                "Re-run with --drop-sparse-columns to train on the dense columns only."
            )

    values = filled[columns].to_numpy(dtype=np.float64)
    rate = filled[target].to_numpy(dtype=np.float64)
    dates = filled["date"].to_numpy()

    # Scaler: TRAIN rows only.
    tr_a, tr_b = ranges["train"]
    mean = values[tr_a:tr_b].mean(axis=0)
    scale = values[tr_a:tr_b].std(axis=0)
    scale[scale == 0] = 1.0

    splits = {}
    for name, (a, b) in ranges.items():
        w = _windows(values, rate, dates, a, b)
        w["X"] = ((w["X_raw"] - mean) / scale).astype(np.float32)
        splits[name] = w

    return {
        "columns": columns, "target": target, "dropped_columns": dropped,
        "mean": mean, "scale": scale, "ranges": ranges, "n_rows": n,
        "frame": filled, "splits": splits,
    }


# --------------------------------------------------------------------------
# Metrics (shared)
# --------------------------------------------------------------------------
def compute_metrics(rate_t: np.ndarray, actual: np.ndarray, pred: np.ndarray) -> dict:
    """Per-horizon MAE/RMSE/MAPE/directional accuracy. Arrays are (N,) in USD/MT.

    Directional accuracy compares sign(pred - rate_t) with sign(actual - rate_t),
    skipping windows where the actual rate did not move. A forecast that never
    moves from rate_t (persistence) has no direction, so it returns None.
    """
    err = pred - actual
    out = {
        "mae": float(np.mean(np.abs(err))),
        "rmse": float(np.sqrt(np.mean(err ** 2))),
        "mape_pct": float(np.mean(np.abs(err) / np.abs(actual)) * 100.0),
    }
    moved = actual != rate_t
    if np.all(pred == rate_t) or not moved.any():
        out["directional_accuracy_pct"] = None
    else:
        out["directional_accuracy_pct"] = float(
            np.mean(np.sign(pred[moved] - rate_t[moved]) == np.sign(actual[moved] - rate_t[moved])) * 100.0
        )
    return out


# --------------------------------------------------------------------------
# Training
# --------------------------------------------------------------------------
def _loss_over(model: nn.Module, loader: DataLoader, criterion) -> float:
    model.eval()
    total, count = 0.0, 0
    with torch.no_grad():
        for bx, by in loader:
            total += criterion(model(bx), by).item() * len(bx)
            count += len(bx)
    return total / count


def train(drop_sparse_columns: bool) -> None:
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    data = prepare_data(drop_sparse_columns)
    sp = data["splits"]

    def loader(name: str, shuffle: bool) -> DataLoader:
        ds = TensorDataset(torch.from_numpy(sp[name]["X"]), torch.from_numpy(sp[name]["y_log"]))
        return DataLoader(ds, batch_size=BATCH_SIZE, shuffle=shuffle)

    train_loader, val_loader = loader("train", True), loader("val", False)
    model = FreightLSTM(input_dim=len(data["columns"]))
    criterion = nn.SmoothL1Loss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)

    print(f"Rows after causal fill: {data['n_rows']}  | columns: {len(data['columns'])}  "
          f"| dropped: {data['dropped_columns']}")
    for name in ("train", "val", "test"):
        a, b = data["ranges"][name]
        print(f"  {name:5s} rows [{a},{b}) windows={len(sp[name]['X'])} "
              f"window-ends {sp[name]['end_dates'][0].astype('datetime64[D]')} -> "
              f"{sp[name]['end_dates'][-1].astype('datetime64[D]')}")

    best_val, best_epoch, best_state, stale = float("inf"), 0, None, 0
    for epoch in range(1, MAX_EPOCHS + 1):
        model.train()
        run, cnt = 0.0, 0
        for bx, by in train_loader:
            optimizer.zero_grad()
            loss = criterion(model(bx), by)
            loss.backward()
            optimizer.step()
            run += loss.item() * len(bx)
            cnt += len(bx)
        val_loss = _loss_over(model, val_loader, criterion)
        print(f"Epoch {epoch:02d} | train {run / cnt:.6f} | val {val_loss:.6f}")
        if val_loss < best_val - 1e-9:
            best_val, best_epoch, stale = val_loss, epoch, 0
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        else:
            stale += 1
            if stale >= PATIENCE:
                print(f"Early stopping at epoch {epoch} (best epoch {best_epoch}).")
                break
    model.load_state_dict(best_state)
    model.eval()

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), ARTIFACT_PATH)

    # ---- single, final look at the test set ----
    test = sp["test"]
    with torch.no_grad():
        pred_log = model(torch.from_numpy(test["X"])).numpy().astype(np.float64)
    pred_rate = test["rate_t"][:, None] * np.exp(pred_log)
    results = {"n_test_windows": int(len(test["X"])), "horizons": {}}
    rows = []
    for k, h in enumerate(HORIZONS):
        actual = test["future_rate"][:, k]
        m_model = compute_metrics(test["rate_t"], actual, pred_rate[:, k])
        m_pers = compute_metrics(test["rate_t"], actual, test["rate_t"])
        beats = m_model["mae"] < m_pers["mae"] and m_model["rmse"] < m_pers["rmse"]
        results["horizons"][f"{h}-Day"] = {"lstm_v2": m_model, "persistence": m_pers,
                                           "beats_persistence": bool(beats)}
        rows.append((h, "lstm_v2", m_model)); rows.append((h, "persistence", m_pers))
    RESULTS_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")

    meta = {
        "model": "lstm_v2", "artifact": "backend/artifacts/lstm_v2_freight_model.pth",
        "num_cols": data["columns"], "dropped_sparse_columns": data["dropped_columns"],
        "target_col": data["target"], "lookback_rows": LOOKBACK, "horizons_rows": list(HORIZONS),
        "target_definition": "log(rate[t+h] / rate[t]) on raw USD/MT; rate = last input row",
        "units_note": "master CSV is business-days only; 'days' are rows",
        "fill_policy": "forward-fill only, leading NaN rows dropped",
        "purge_rows": PURGE_ROWS, "split_fractions": {"train": TRAIN_FRAC, "val": VAL_FRAC, "test": 1 - TRAIN_FRAC - VAL_FRAC},
        "scaler_fit_on": "train rows only",
        "scaler_mean": data["mean"].tolist(), "scaler_scale": data["scale"].tolist(),
        "split_dates": {
            name: {
                "first_row_date": str(data["frame"]["date"].iloc[a].date()),
                "last_row_date": str(data["frame"]["date"].iloc[b - 1].date()),
                "n_windows": int(len(sp[name]["X"])),
            } for name, (a, b) in data["ranges"].items()
        },
        "seed": SEED, "best_epoch": best_epoch, "best_val_loss": best_val,
        "optimizer": {"name": "Adam", "lr": LEARNING_RATE, "loss": "SmoothL1", "batch": BATCH_SIZE,
                      "max_epochs": MAX_EPOCHS, "patience": PATIENCE, "scheduler": None},
    }
    META_PATH.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"\n### lstm_v2 vs persistence, test set ({results['n_test_windows']} windows, USD/MT)\n")
    print("| Horizon | Model | MAE | RMSE | MAPE % | Dir. acc % |")
    print("|---|---|---|---|---|---|")
    for h, name, m in rows:
        da = "n/a" if m["directional_accuracy_pct"] is None else f"{m['directional_accuracy_pct']:.1f}"
        print(f"| {h}d | {name} | {m['mae']:.3f} | {m['rmse']:.3f} | {m['mape_pct']:.2f} | {da} |")
    print()
    for h in HORIZONS:
        r = results["horizons"][f"{h}-Day"]
        verdict = "BEATS" if r["beats_persistence"] else "does NOT beat"
        print(f"{h}d: lstm_v2 {verdict} persistence "
              f"(MAE {r['lstm_v2']['mae']:.3f} vs {r['persistence']['mae']:.3f}, "
              f"RMSE {r['lstm_v2']['rmse']:.3f} vs {r['persistence']['rmse']:.3f}).")
    if not any(r["beats_persistence"] for r in results["horizons"].values()):
        print("\nHONEST SUMMARY: lstm_v2 does not beat persistence at any horizon. "
              "That is expected if the freight target is a simulated random walk "
              "(see generate_freight_routes.py): there is no signal beyond the last value.")
    print(f"\nSaved: {ARTIFACT_PATH}\n       {META_PATH}\n       {RESULTS_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--drop-sparse-columns", action="store_true",
                        help="drop input columns with <50%% raw coverage (needed for enough rows)")
    train(parser.parse_args().drop_sparse_columns)
