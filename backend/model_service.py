"""Load and serve the trained artifacts contributed by the model repository.

The artifact scopes are intentionally explicit. The LSTM is trained only for
Australia -> Paradip / Capesize at 7, 14, 30, and 60 days. The freight
XGBoost model is trained only for Australia -> Paradip / Supramax at one day.
Unsupported requests return ``None`` so the caller can use a documented
baseline instead of misrepresenting model coverage.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import xgboost as xgb

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = PROJECT_ROOT / "backend" / "artifacts"
MODEL_DATA_DIR = PROJECT_ROOT / "data" / "model"
Z_10_90 = 1.2816


class FreightLSTM(nn.Module):
    """Architecture matching the committed two-layer PyTorch state dict."""

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 64,
        num_layers: int = 2,
        output_dim: int = 4,
        dropout: float = 0.2,
    ) -> None:
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, output_dim),
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        output, _ = self.lstm(features)
        return self.fc(output[:, -1, :])


class ModelRegistry:
    """Own loaded model objects and expose scope-aware inference methods."""

    LSTM_HORIZONS = (7, 14, 30, 60)
    LSTM_SCOPE = {
        "origin": "Australia",
        "destination": "Paradip",
        "vessel_class": "Capesize",
    }
    XGB_FREIGHT_SCOPE = {
        "origin": "Australia",
        "destination": "Paradip",
        "vessel_class": "Supramax",
        "horizon_days": 1,
    }

    def __init__(self) -> None:
        self.errors: dict[str, str] = {}
        self.lstm_model: FreightLSTM | None = None
        self.lstm_metadata: dict[str, Any] = {}
        self.lstm_results: dict[str, Any] = {}
        self.macro_data: pd.DataFrame | None = None
        self.xgb_data: pd.DataFrame | None = None
        self.xgb_models: dict[str, xgb.XGBRegressor] = {}
        self.xgb_results: dict[str, Any] = {}
        self._load_all()

    def _load_all(self) -> None:
        self._load_lstm()
        self._load_xgboost()

    def _load_lstm(self) -> None:
        try:
            self.lstm_metadata = json.loads(
                (MODEL_DATA_DIR / "lstm_metadata.json").read_text(encoding="utf-8")
            )
            self.lstm_results = json.loads(
                (MODEL_DATA_DIR / "lstm_results.json").read_text(encoding="utf-8")
            )
            self.macro_data = pd.read_csv(
                MODEL_DATA_DIR / "master_macro_freight_daily.csv",
                parse_dates=["date"],
            ).sort_values("date")
            model = FreightLSTM(input_dim=len(self.lstm_metadata["num_cols"]))
            state = torch.load(
                ARTIFACT_DIR / "lstm_freight_model.pth",
                map_location="cpu",
                weights_only=True,
            )
            model.load_state_dict(state)
            model.eval()
            self.lstm_model = model
        except (OSError, KeyError, ValueError, RuntimeError) as exc:
            self.errors["lstm"] = str(exc)

    def _load_xgboost(self) -> None:
        try:
            self.xgb_data = pd.read_csv(
                MODEL_DATA_DIR / "dataset_xgboost_master.csv",
                parse_dates=["date"],
            ).sort_values(["date", "port_code"])
            self.xgb_results = json.loads(
                (MODEL_DATA_DIR / "xgboost_results.json").read_text(encoding="utf-8")
            )
            artifact_names = {
                "freight": "xgboost_model_freight_australia_paradip_supramax_usd_per_mt.json",
                "congestion": "xgboost_model_congestion_index_0_100.json",
                "wait_hours": "xgboost_model_sim_wait_hours.json",
            }
            for key, filename in artifact_names.items():
                model = xgb.XGBRegressor()
                model.load_model(ARTIFACT_DIR / filename)
                self.xgb_models[key] = model
        except (OSError, KeyError, ValueError, xgb.core.XGBoostError) as exc:
            self.errors["xgboost"] = str(exc)

    def status(self) -> dict[str, Any]:
        """Return artifact availability plus the exact serving scopes."""

        return {
            "lstm": {
                "loaded": self.lstm_model is not None,
                "scope": self.LSTM_SCOPE,
                "horizons_days": list(self.LSTM_HORIZONS),
                "artifact": "backend/artifacts/lstm_freight_model.pth",
                "data_cutoff": self._date_string(self.macro_data),
                "error": self.errors.get("lstm"),
            },
            "xgboost_freight": {
                "loaded": "freight" in self.xgb_models,
                "scope": self.XGB_FREIGHT_SCOPE,
                "artifact": (
                    "backend/artifacts/"
                    "xgboost_model_freight_australia_paradip_supramax_usd_per_mt.json"
                ),
                "data_cutoff": self._date_string(self.xgb_data),
                "error": self.errors.get("xgboost"),
            },
            "xgboost_port_risk": {
                "loaded": {"congestion", "wait_hours"}.issubset(self.xgb_models),
                "scope": {"destination": "Paradip"},
                "data_cutoff": self._date_string(self.xgb_data),
                "error": self.errors.get("xgboost"),
            },
        }

    def supported_freight_scenarios(self) -> list[dict[str, Any]]:
        """Return only scopes currently backed by loaded trained artifacts."""

        scenarios: list[dict[str, Any]] = []
        if self.lstm_model is not None:
            scenarios.append(
                {
                    **self.LSTM_SCOPE,
                    "cargo_type": "Coal",
                    "horizons_days": list(self.LSTM_HORIZONS),
                    "model": "PyTorch 2-layer LSTM",
                    "model_kind": "trained_artifact",
                }
            )
        if "freight" in self.xgb_models:
            scope = self.XGB_FREIGHT_SCOPE
            scenarios.append(
                {
                    "origin": scope["origin"],
                    "destination": scope["destination"],
                    "vessel_class": scope["vessel_class"],
                    "cargo_type": "Coal",
                    "horizons_days": [scope["horizon_days"]],
                    "model": "XGBoost freight regressor",
                    "model_kind": "trained_artifact",
                }
            )
        return scenarios

    @staticmethod
    def _date_string(frame: pd.DataFrame | None) -> str | None:
        if frame is None or frame.empty:
            return None
        return pd.Timestamp(frame["date"].max()).date().isoformat()

    def predict_freight(
        self,
        origin: str,
        destination: str,
        vessel_class: str,
        horizon_days: int,
    ) -> dict[str, Any] | None:
        """Predict within a trained scope, or return ``None`` if unsupported."""

        requested_scope = {
            "origin": origin,
            "destination": destination,
            "vessel_class": vessel_class,
        }
        if (
            requested_scope == self.LSTM_SCOPE
            and horizon_days in self.LSTM_HORIZONS
            and self.lstm_model is not None
        ):
            return self._predict_lstm(horizon_days)

        xgb_scope = {**requested_scope, "horizon_days": horizon_days}
        if xgb_scope == self.XGB_FREIGHT_SCOPE and "freight" in self.xgb_models:
            return self._predict_xgboost_freight()
        return None

    def lstm_target_series(self) -> pd.Series:
        """Return the exact unscaled target series consumed by LSTM inference."""

        if self.macro_data is None:
            raise RuntimeError("LSTM source data is unavailable")
        target = self.lstm_metadata["target_col"]
        frame = self.macro_data[["date", target]].dropna().copy()
        return frame.set_index("date")[target].astype(float)

    def _predict_lstm(self, horizon_days: int) -> dict[str, Any]:
        assert self.macro_data is not None
        assert self.lstm_model is not None
        columns = self.lstm_metadata["num_cols"]
        lookback = int(self.lstm_metadata["lookback_days"])
        numeric = self.macro_data[columns].ffill().bfill()
        values = numeric.iloc[-lookback:].to_numpy(dtype=np.float32)
        mean = np.asarray(self.lstm_metadata["scaler_mean"], dtype=np.float32)
        scale = np.asarray(self.lstm_metadata["scaler_scale"], dtype=np.float32)
        scaled = (values - mean) / scale

        with torch.inference_mode():
            output = self.lstm_model(
                torch.tensor(scaled, dtype=torch.float32).unsqueeze(0)
            )[0].cpu().numpy()

        target_index = columns.index(self.lstm_metadata["target_col"])
        horizon_index = self.LSTM_HORIZONS.index(horizon_days)
        prediction = float(output[horizon_index] * scale[target_index] + mean[target_index])
        current = float(values[-1, target_index])
        metrics = self.lstm_results[f"{horizon_days}-Day"]
        sigma = float(metrics["rmse_usd_per_mt"])
        p10 = max(0.0, prediction - Z_10_90 * sigma)
        p90 = prediction + Z_10_90 * sigma
        probability = self._normal_cdf((prediction - current) / max(sigma, 1e-8))
        history = self.lstm_target_series().tail(120)
        return self._forecast_payload(
            current=current,
            prediction=prediction,
            p10=p10,
            p90=p90,
            probability=probability,
            horizon_days=horizon_days,
            history=history,
            metrics={
                "mae": metrics["mae_usd_per_mt"],
                "rmse": metrics["rmse_usd_per_mt"],
                "smape_pct": metrics["smape_pct"],
                "directional_accuracy_pct": metrics["directional_accuracy_pct"],
            },
            model={
                "name": "PyTorch 2-layer LSTM",
                "kind": "trained_artifact",
                "artifact": "backend/artifacts/lstm_freight_model.pth",
                "trained_scope": self.LSTM_SCOPE,
                "fallback_used": False,
                "fallback_reason": None,
                "data_cutoff": self._date_string(self.macro_data),
                "data_provenance": (
                    "Committed model dataset with a proxy/simulated freight target; "
                    "not a live market quote."
                ),
                "interval_method": "holdout RMSE normal approximation (uncalibrated)",
                "interval_calibrated": False,
                "known_limitations": [
                    "The committed LSTM targets only Australia-Paradip Capesize freight.",
                    "The committed freight target is a proxy/simulated series rather than a live market quote.",
                    "Its preprocessing fitted StandardScaler on the full series and used backfill; retraining with train-only scaling and strict point-in-time handling is required before production use.",
                    "Published test metrics were observed during training and are not an untouched final holdout.",
                ],
            },
        )

    def _paradip_xgb_row(self) -> pd.DataFrame:
        if self.xgb_data is None:
            raise RuntimeError("XGBoost source data is unavailable")
        rows = self.xgb_data
        if "port_name_Paradip" in rows.columns:
            rows = rows.loc[rows["port_name_Paradip"].astype(bool)]
        return rows.tail(1)

    def _xgb_predict(self, model_key: str) -> float:
        model = self.xgb_models[model_key]
        row = self._paradip_xgb_row()
        feature_names = model.get_booster().feature_names
        if not feature_names:
            raise RuntimeError(f"XGBoost artifact {model_key} has no feature metadata")
        return float(model.predict(row[feature_names])[0])

    def _predict_xgboost_freight(self) -> dict[str, Any]:
        target = "freight_australia_paradip_supramax_usd_per_mt"
        row = self._paradip_xgb_row()
        raw_prediction = self._xgb_predict("freight")
        prediction = max(0.0, raw_prediction)
        current = float(row[target].iloc[0])
        metrics = self.xgb_results[target]
        sigma = float(metrics["rmse"])
        history_frame = self.xgb_data
        assert history_frame is not None
        history = history_frame.loc[
            history_frame["port_name_Paradip"].astype(bool), ["date", target]
        ].set_index("date")[target].tail(120)
        return self._forecast_payload(
            current=current,
            prediction=prediction,
            p10=max(0.0, prediction - Z_10_90 * sigma),
            p90=prediction + Z_10_90 * sigma,
            probability=self._normal_cdf((prediction - current) / max(sigma, 1e-8)),
            horizon_days=1,
            history=history,
            metrics={
                "mae": metrics["mae"],
                "rmse": metrics["rmse"],
                "r2": metrics["r2"],
                "directional_accuracy_pct": metrics["directional_accuracy_pct"],
            },
            model={
                "name": "XGBoost freight regressor",
                "kind": "trained_artifact",
                "artifact": (
                    "backend/artifacts/"
                    "xgboost_model_freight_australia_paradip_supramax_usd_per_mt.json"
                ),
                "trained_scope": self.XGB_FREIGHT_SCOPE,
                "fallback_used": False,
                "fallback_reason": None,
                "data_cutoff": self._date_string(self.xgb_data),
                "data_provenance": (
                    "Committed proxy/simulated model dataset; not a live market quote."
                ),
                "interval_method": "holdout RMSE normal approximation (uncalibrated)",
                "interval_calibrated": False,
                "known_limitations": [
                    "The committed XGBoost freight artifact covers only a one-day Australia-Paradip Supramax target.",
                    "The underlying repository describes proxy/simulated inputs; predictions are demonstration outputs, not live market quotes.",
                ],
                "raw_model_output": raw_prediction,
            },
        )

    def predict_port_risk(self, destination: str) -> dict[str, Any] | None:
        """Serve trained congestion/wait predictions for Paradip only."""

        if destination != "Paradip" or not {
            "congestion",
            "wait_hours",
        }.issubset(self.xgb_models):
            return None
        raw_congestion = self._xgb_predict("congestion")
        raw_wait_hours = self._xgb_predict("wait_hours")
        return {
            "congestion_index_0_100": min(100.0, max(0.0, raw_congestion)),
            "wait_hours": max(0.0, raw_wait_hours),
            "raw_model_outputs": {
                "congestion_index_0_100": raw_congestion,
                "wait_hours": raw_wait_hours,
            },
            "postprocessing": "Congestion clipped to [0, 100]; wait hours clipped to >= 0.",
            "model": "XGBoost port regressors",
            "data_cutoff": self._date_string(self.xgb_data),
            "scope": {"destination": "Paradip"},
        }

    @staticmethod
    def _normal_cdf(value: float) -> float:
        return float(0.5 * (1.0 + math.erf(value / math.sqrt(2.0))))

    @staticmethod
    def _forecast_payload(
        *,
        current: float,
        prediction: float,
        p10: float,
        p90: float,
        probability: float,
        horizon_days: int,
        history: pd.Series,
        metrics: dict[str, Any],
        model: dict[str, Any],
    ) -> dict[str, Any]:
        start = pd.Timestamp(history.index[-1])
        dates = pd.date_range(start + pd.Timedelta(days=1), periods=horizon_days, freq="D")
        points = np.linspace(current, prediction, horizon_days + 1)[1:]
        low_width = prediction - p10
        high_width = p90 - prediction
        series = []
        for day, (date, point) in enumerate(zip(dates, points, strict=True), start=1):
            growth = math.sqrt(day / horizon_days)
            series.append(
                {
                    "date": date.date().isoformat(),
                    "p10": float(max(0.0, point - low_width * growth)),
                    "p50": float(point),
                    "p90": float(point + high_width * growth),
                }
            )
        return {
            "horizon_days": horizon_days,
            "current_rate_usd_per_mt": current,
            "point_forecast_usd_per_mt": prediction,
            "p10_usd_per_mt": p10,
            "p50_usd_per_mt": prediction,
            "p90_usd_per_mt": p90,
            "probability_increase": probability,
            "expected_pct_change": ((prediction / current) - 1.0) * 100.0,
            "series": series,
            "historical": [
                {"date": pd.Timestamp(date).date().isoformat(), "value": float(value)}
                for date, value in history.items()
            ],
            "metrics": metrics,
            "model": model,
        }
