from backend.model_service import ModelRegistry


def test_lstm_artifact_loads_and_serves_exact_scope() -> None:
    registry = ModelRegistry()

    prediction = registry.predict_freight(
        "Australia", "Paradip", "Capesize", 7
    )

    assert prediction is not None
    assert prediction["model"]["kind"] == "trained_artifact"
    assert prediction["model"]["name"] == "PyTorch 2-layer LSTM"
    assert prediction["horizon_days"] == 7
    assert len(prediction["series"]) == 7


def test_trained_artifact_is_not_used_outside_its_scope() -> None:
    registry = ModelRegistry()

    prediction = registry.predict_freight(
        "Australia", "Paradip", "Panamax", 7
    )

    assert prediction is None


def test_xgboost_port_models_load() -> None:
    registry = ModelRegistry()

    prediction = registry.predict_port_risk("Paradip")

    assert prediction is not None
    assert 0 <= prediction["congestion_index_0_100"] <= 100
    assert prediction["wait_hours"] >= 0

