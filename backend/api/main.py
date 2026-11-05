"""FastAPI entrypoint for the unified model and decision-support service."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from backend.api.schemas import HealthResponse, PipelineRequest
from backend.model_service import ModelRegistry
from backend.pipeline import run_pipeline


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.model_registry = ModelRegistry()
    yield
    app.state.model_registry = None


app = FastAPI(
    title="SamudraSetu Unified API",
    version="1.0.0",
    summary="Freight model serving and decision-pipeline orchestration",
    lifespan=lifespan,
)

origins = [
    value.strip()
    for value in os.getenv(
        "SAMUDRA_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if value.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def _registry(request: Request) -> ModelRegistry:
    return request.app.state.model_registry


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/api/v1/models/status")
async def model_status(request: Request) -> dict[str, Any]:
    return _registry(request).status()

@app.get("/api/v1/pipeline/config")
async def pipeline_config(request: Request) -> dict[str, Any]:
    """Return backend-owned UI choices: ML scenarios + all supported options."""

    registry = _registry(request)
    ml_scenarios = registry.supported_freight_scenarios()
    request_schema = PipelineRequest.model_json_schema()["properties"]

    origins = request_schema["origin"]["enum"]
    destinations = request_schema["destination"]["enum"]
    vessel_classes = request_schema["vessel_class"]["enum"]
    horizons = request_schema["horizon_days"]["enum"]

    default_requirement = None
    if ml_scenarios:
        first = ml_scenarios[0]
        default_requirement = PipelineRequest(
            origin=first["origin"],
            destination=first["destination"],
            vessel_class=first["vessel_class"],
            cargo_type=first["cargo_type"],
            cargo_quantity_mt=150_000,
            horizon_days=first["horizons_days"][0],
        ).model_dump()
    else:
        default_requirement = PipelineRequest().model_dump()

    return {
        "service_status": "ready" if ml_scenarios else "degraded",
        "default_requirement": default_requirement,
        "supported_scenarios": ml_scenarios,
        "ml_scenarios": ml_scenarios,
        "available_origins": origins,
        "available_destinations": destinations,
        "available_vessels": vessel_classes,
        "available_horizons": horizons,
        "input_constraints": {
            "cargo_quantity_mt": {
                "exclusive_minimum": request_schema["cargo_quantity_mt"][
                    "exclusiveMinimum"
                ],
                "maximum": request_schema["cargo_quantity_mt"]["maximum"],
                "step": 1000,
                "default": 150_000,
            },
            "congestion_levels": request_schema["congestion_level"]["enum"],
            "availability_levels": request_schema["availability_level"]["enum"],
        },
        "models": registry.status(),
    }




@app.post("/api/v1/predict/freight")
async def predict_freight(
    payload: PipelineRequest, request: Request
) -> dict[str, Any]:
    prediction = _registry(request).predict_freight(
        payload.origin,
        payload.destination,
        payload.vessel_class,
        payload.horizon_days,
    )
    if prediction is not None:
        return {"supported": True, "forecast": prediction}
    return {
        "supported": False,
        "forecast": None,
        "reason": "No trained artifact covers the exact requested scope.",
        "available_models": _registry(request).status(),
    }


@app.post("/api/v1/pipeline/run")
async def pipeline(payload: PipelineRequest, request: Request) -> dict[str, Any]:
    return run_pipeline(payload, _registry(request))
