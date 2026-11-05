"""Validated HTTP contracts for model inference and the decision pipeline."""

from typing import Literal

from pydantic import BaseModel, Field


class PipelineRequest(BaseModel):
    """A procurement requirement used by both inference and orchestration."""

    origin: Literal[
        "Australia", "United States", "Mozambique", "Russia", "Indonesia"
    ] = "Australia"
    destination: Literal[
        "Paradip",
        "Visakhapatnam",
        "Gangavaram",
        "Gopalpur",
        "Dhamra",
        "Sagar/Sandheads",
        "Haldia",
    ] = "Paradip"
    vessel_class: Literal["Handysize", "Supramax", "Panamax", "Capesize"] = (
        "Capesize"
    )
    cargo_type: Literal["Coal"] = "Coal"
    cargo_quantity_mt: float = Field(default=150_000, gt=0, le=250_000)
    horizon_days: Literal[1, 7, 14, 30, 60] = 7
    congestion_level: Literal["Low", "Medium", "High"] = "Medium"
    availability_level: Literal["Low", "Medium", "High"] = "Medium"


class HealthResponse(BaseModel):
    status: Literal["ok"]

