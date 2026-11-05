"""End-to-end UI -> pipeline -> model orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from backend.api.schemas import PipelineRequest
from backend.backtest import run_backtest
from backend.feasibility import PORT_LIMITS, VESSEL_SPECS, check_all_vessel_classes
from backend.forecasting import build_forecast_from_series, holdout_errors
from backend.model_service import ModelRegistry
from backend.recommendation import build_recommendation, compare_vessel_costs
from backend.risk import compute_risk
from backend.synthetic_data import generate_synthetic_series

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REAL_DATA_PATH = PROJECT_ROOT / "data" / "freight_rates.csv"


def _resolve_series(request: PipelineRequest) -> tuple[pd.Series, str]:
    route = f"{request.origin}-{request.destination}"
    if REAL_DATA_PATH.exists():
        frame = pd.read_csv(REAL_DATA_PATH, parse_dates=["date"])
        mask = (
            (frame["route"] == route)
            & (frame["vessel_class"] == request.vessel_class)
            & (frame["cargo_type"] == request.cargo_type)
        )
        subset = frame.loc[mask].sort_values("date")
        if len(subset) >= 90:
            return (
                subset.set_index("date")["rate_usd_per_mt"].astype(float),
                "data/freight_rates.csv",
            )
    generated = generate_synthetic_series(
        request.origin,
        request.destination,
        request.vessel_class,
        request.cargo_type,
    )
    return (
        generated.set_index("date")["rate_usd_per_mt"].astype(float),
        "deterministic synthetic fallback",
    )


def _baseline_forecast(
    request: PipelineRequest, series: pd.Series, data_source: str
) -> dict[str, Any]:
    forecast = build_forecast_from_series(series, request.horizon_days)
    metrics = holdout_errors(series)
    output = ModelRegistry._forecast_payload(
        current=float(forecast["current_rate"]),
        prediction=float(forecast["point"][-1]),
        p10=float(forecast["p10"][-1]),
        p90=float(forecast["p90"][-1]),
        probability=float(forecast["prob_increase"]),
        horizon_days=request.horizon_days,
        history=series.tail(120),
        metrics={
            "mae": metrics["stat_mae"],
            "rmse": metrics["stat_rmse"],
            "naive_mae": metrics["naive_mae"],
            "naive_rmse": metrics["naive_rmse"],
        },
        model={
            "name": metrics["model_name"],
            "kind": "statistical_fallback",
            "artifact": None,
            "trained_scope": None,
            "fallback_used": True,
            "fallback_reason": (
                "No committed trained artifact covers this exact route, vessel class, "
                "and horizon."
            ),
            "data_cutoff": pd.Timestamp(series.index[-1]).date().isoformat(),
            "data_source": data_source,
            "data_provenance": (
                f"Backend demonstration series from {data_source}; not a live market quote."
            ),
            "interval_method": "holdout residual spread with sqrt(time) widening",
            "interval_calibrated": False,
            "known_limitations": [
                "Fallback data is synthetic unless an exact matching series exists in data/freight_rates.csv.",
                "The residual interval is indicative and has not been calibrated for coverage.",
            ],
        },
    )
    output["_legacy_forecast"] = forecast
    return output


def _selected_feasibility(request: PipelineRequest) -> tuple[dict[str, Any], dict[str, Any]]:
    all_checks = check_all_vessel_classes(request.destination)

    def summarize(checks: list[dict[str, Any]]) -> str:
        statuses = {check["status"] for check in checks}
        if "fail" in statuses:
            return "fail"
        if "unknown" in statuses:
            return "unknown"
        return "pass"

    candidates = []
    for vessel_class, checks in all_checks.items():
        candidates.append(
            {
                "vessel_class": vessel_class,
                "specs": VESSEL_SPECS[vessel_class],
                "checks": checks,
                "overall": summarize(checks),
            }
        )
    selected = next(
        candidate
        for candidate in candidates
        if candidate["vessel_class"] == request.vessel_class
    )
    return selected, {
        "port": request.destination,
        "port_limits": PORT_LIMITS[request.destination],
        "selected": selected,
        "candidates": candidates,
    }


def run_pipeline(request: PipelineRequest, registry: ModelRegistry) -> dict[str, Any]:
    """Run forecasting, feasibility, risk, recommendation, and backtesting."""

    trained_forecast = registry.predict_freight(
        request.origin,
        request.destination,
        request.vessel_class,
        request.horizon_days,
    )
    if trained_forecast is not None:
        forecast_payload = trained_forecast
        if request.vessel_class == "Capesize":
            series = registry.lstm_target_series()
        else:
            series, _ = _resolve_series(request)
        legacy_forecast = {
            "series": series,
            "current_rate": forecast_payload["current_rate_usd_per_mt"],
            "point": np.asarray(
                [item["p50"] for item in forecast_payload["series"]], dtype=float
            ),
            "p10": np.asarray(
                [item["p10"] for item in forecast_payload["series"]], dtype=float
            ),
            "p50": np.asarray(
                [item["p50"] for item in forecast_payload["series"]], dtype=float
            ),
            "p90": np.asarray(
                [item["p90"] for item in forecast_payload["series"]], dtype=float
            ),
            "prob_increase": forecast_payload["probability_increase"],
        }
    else:
        series, data_source = _resolve_series(request)
        forecast_payload = _baseline_forecast(request, series, data_source)
        legacy_forecast = forecast_payload.pop("_legacy_forecast")

    selected, feasibility = _selected_feasibility(request)
    port_prediction = registry.predict_port_risk(request.destination)
    if port_prediction is not None:
        congestion_index = float(port_prediction["congestion_index_0_100"])
        congestion_level = (
            "Low" if congestion_index < 35 else "Medium" if congestion_index < 65 else "High"
        )
        risk_source = "trained XGBoost congestion model"
    else:
        congestion_level = request.congestion_level
        risk_source = "user-provided congestion level (no trained port model for destination)"

    risk = compute_risk(
        series,
        congestion_level=congestion_level,
        availability_level=request.availability_level,
    )
    risk.update(
        {
            "source": risk_source,
            "port_model_prediction": port_prediction,
            "requested_congestion_level": request.congestion_level,
        }
    )

    recommendation = build_recommendation(
        legacy_forecast,
        risk,
        request.vessel_class,
        VESSEL_SPECS[request.vessel_class]["dwt_max"],
        request.cargo_quantity_mt,
    )
    vessel_costs = compare_vessel_costs(
        request.destination,
        forecast_payload["current_rate_usd_per_mt"],
        request.cargo_quantity_mt,
    )
    backtest = run_backtest(
        series,
        request.horizon_days,
        congestion_level,
        request.availability_level,
    )
    serializable_backtest = {
        "n_points": backtest["n_points"],
        "avg_savings_per_mt": backtest["avg_savings_per_mt"],
        "method": "Holt decision-rule walk-forward backtest",
        "note": (
            "Backtested/simulated estimate; this validates the decision rule and "
            "is not a guarantee or an LSTM walk-forward benchmark."
        ),
        "decisions": {
            "charter_now": sum(
                point["decision"] == "Charter Now" for point in backtest["points"]
            ),
            "wait_monitor": sum(
                point["decision"] != "Charter Now" for point in backtest["points"]
            ),
        },
    }

    return {
        "request": request.model_dump(),
        "forecast": forecast_payload,
        "feasibility": feasibility,
        "risk": risk,
        "recommendation": {
            **recommendation,
            "selected_feasibility": selected["overall"],
            "vessel_cost_comparison": vessel_costs,
        },
        "backtest": serializable_backtest,
    }
