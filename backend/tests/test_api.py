from fastapi.testclient import TestClient

from backend.api.main import app


CAPESIZE_REQUEST = {
    "origin": "Australia",
    "destination": "Paradip",
    "vessel_class": "Capesize",
    "cargo_type": "Coal",
    "cargo_quantity_mt": 150000,
    "horizon_days": 7,
    "congestion_level": "Medium",
    "availability_level": "Medium",
}


def test_health_and_model_status() -> None:
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}
        status = client.get("/api/v1/models/status").json()

    assert status["lstm"]["loaded"] is True
    assert status["xgboost_port_risk"]["loaded"] is True


def test_pipeline_config_is_backend_owned_and_trained_only() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/pipeline/config")

    assert response.status_code == 200
    payload = response.json()
    assert payload["service_status"] == "ready"
    assert payload["default_requirement"]["origin"] == "Australia"
    assert payload["supported_scenarios"]
    assert all(
        scenario["model_kind"] == "trained_artifact"
        for scenario in payload["supported_scenarios"]
    )
    assert payload["input_constraints"]["cargo_quantity_mt"]["maximum"] == 250000


def test_pipeline_connects_ui_contract_to_trained_models() -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/pipeline/run", json=CAPESIZE_REQUEST)

    assert response.status_code == 200
    payload = response.json()
    assert payload["forecast"]["model"]["kind"] == "trained_artifact"
    assert payload["forecast"]["model"]["name"] == "PyTorch 2-layer LSTM"
    assert payload["risk"]["source"] == "trained XGBoost congestion model"
    assert payload["recommendation"]["reasons"]
    assert len(payload["recommendation"]["cost_options"]) == 3
    assert sum(
        option["is_lowest_modeled_cost"]
        for option in payload["recommendation"]["cost_options"]
    ) == 1


def test_pipeline_labels_statistical_fallback() -> None:
    request = {**CAPESIZE_REQUEST, "vessel_class": "Panamax", "cargo_quantity_mt": 72000}
    with TestClient(app) as client:
        response = client.post("/api/v1/pipeline/run", json=request)

    assert response.status_code == 200
    model = response.json()["forecast"]["model"]
    assert model["kind"] == "statistical_fallback"
    assert model["fallback_used"] is True
    assert model["fallback_reason"]
