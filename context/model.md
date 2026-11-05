# Model Context

## Modeling Objective

The forecasting problem is: predict `freight_rate` (USD per MT, or the canonical unit present in the actual dataset) for a given combination of:

- Origin
- Destination
- Vessel class
- Cargo type
- Commercial basis (spot / contract, where distinguishable)

for future points in time, at the following initial forecast horizons:

- 7 days
- 14 days
- 30 days
- 60 days

(90 days may be added later; it is not part of the initial required scope — see `project-overview.md`.)

The forecast must be produced **as of a specific decision timestamp**, using only information that would genuinely have been available at that timestamp (see Data Leakage & Point-in-Time Rules below). This applies both to live inference and to historical backtesting.

The forecasting layer is the central intelligence layer of the system (per `project-overview.md` and `architecture.md`). It does not know about vessel constraints, contract strategies, risk scoring, the API, or the UI. Its sole responsibility is to turn point-in-time-safe features into a forecast distribution plus supporting metadata that downstream decision-support modules consume.

No single model family is assumed to be correct upfront. Model choice must be determined empirically through out-of-sample, chronological benchmarking against the actual available dataset, per the project's model strategy.

---

## Model Benchmark

Models must be evaluated in the following hierarchy, from simplest to most complex. Each tier exists to answer a specific question: "does the added complexity earn its keep on out-of-sample data?" A more complex model is only adopted if it demonstrably outperforms the simpler tier below it on the metrics defined in Evaluation.

### 1. Baselines
- **Naive** (last observed value carried forward)
- **Seasonal Naive**, where seasonality is identified in the actual freight data

Purpose: establishes the floor. If no other model beats these by a meaningful, out-of-sample margin, that is a valid and reportable finding — not a failure to hide.

### 2. Statistical
- **ARIMA / SARIMA**
- **Exponential Smoothing**, where appropriate for the observed series characteristics

Purpose: captures linear temporal structure without requiring large training data or exogenous features.

### 3. Gradient Boosting
- **XGBoost** (primary candidate)
- **LightGBM**, where useful as a comparison or for speed

Purpose: captures non-linear relationships and exogenous/covariate effects using engineered tabular features (see Data & Features).

### 4. Neural
- **LSTM or GRU**

Sequence lengths to be tested: 30, 60, 90, 180. No sequence length is assumed optimal in advance — it must be selected via validation.

### 5. Foundation Models
- **TimesFM / TimesFM 2.5**
- **Chronos-2**

Both zero-shot usage and domain adaptation/fine-tuning should be evaluated where practical given available data and compute. Chronos-2 should specifically be evaluated for probabilistic and covariate-informed forecasting, given its support for exogenous inputs.

### 6. Ensemble
An ensemble across multiple models may be used **only if multiple models independently perform well** on out-of-sample validation. Ensemble weights must be **learned from validation/backtesting results**, not manually assigned. An ensemble is not a default — it is adopted only if it beats the best single model on the metrics in Evaluation.

### Selection principle

The final model (or ensemble) must be selected based on **rolling/chronological backtesting performance and business usefulness**, not because it is:
- neural,
- a foundation model,
- more complex, or
- more popular/fashionable.

Prefer the simplest model that demonstrates strong, stable out-of-sample performance. If a Naive or ARIMA baseline is competitive with XGBoost or a foundation model on the actual dataset, that must be reported honestly rather than obscured in favor of a more sophisticated-looking system.

---

## Data & Features

### Canonical target

`freight_rate` — units and exact definition (e.g., USD/MT) must match the actual ingested dataset; do not assume a unit that hasn't been confirmed against real data.

### Historical (endogenous) features
- Lagged freight rate: lags such as 1, 3, 7, 14, 30, 60 days (adapt to actual data frequency/availability)
- Rolling statistics: mean, std, min, max over relevant windows
- Trend indicators
- Rate-of-change / period-over-period changes

### Exogenous features (potential — subject to actual data availability)
- Bunker/fuel price
- Commodity price (e.g., coal price)
- Shipping/freight indices (e.g., Baltic-related indices)
- Vessel availability
- Port congestion (origin and destination)
- FX rates
- Demand proxies (e.g., steel production, industrial production)
- Macro indicators
- Weather/disruption indicators

### Static/context features
- Origin
- Destination
- Vessel class
- Cargo type
- Route distance (if derivable)
- Parcel size / vessel capacity

The exact feature set actually implemented depends on real data availability. Do not fabricate features for variables that are not actually present in the ingested dataset — see `architecture.md`'s ingestion/preprocessing boundaries for where real data enters the system.

### Canonical dataset structure

Adapt the following structure to the actual dataset rather than inventing unavailable fields:

```
timestamp
origin
destination
vessel_class
cargo_type
parcel_size_mt
freight_rate
bunker_price
commodity_price
shipping_index
vessel_availability
port_congestion_origin
port_congestion_destination
weather_features
macro_features
```

### Feature documentation requirement

For every feature actually used, the implementing agent must document:

1. Timestamp (what date/time it represents)
2. Availability timestamp, if different from the represented timestamp (when it was actually knowable)
3. Frequency (daily, monthly, hourly, etc.)
4. Alignment method (how it is resampled/joined to the canonical daily frequency — see `architecture.md`'s `preprocessing/frequency_alignment.py`)
5. Missing-value treatment
6. Leakage risk assessment

This documentation lives alongside the feature-building code (e.g., in `backend/features/`), not only in this file.

---

## Data Leakage & Point-in-Time Rules

This is a **non-negotiable rule**, enforced at every stage: dataset construction, feature engineering, training, inference, and backtesting.

**Rule:** At prediction time, a model may only use information that would genuinely have been available at that timestamp.

Example: forecasting on 1 September —
- Information available on or before 1 September → allowed.
- The actual observed value from 15 September → forbidden, even if it exists in the historical database at training time.

This applies to every feature category without exception:
- Freight rates
- Bunker prices
- Commodity prices
- Port congestion
- Vessel availability
- Weather
- Macro indicators
- Any other external feature, present or future

**Forecasted (not yet realized) values of an exogenous variable may only be used as a feature if that forecast itself would genuinely have existed and been available at the prediction timestamp.** Do not substitute a realized future value where a forecast would have had to be used historically.

### Enforcement

- Every raw observation (freight and market data) is stored with an `available_as_of` timestamp, per the `freight_observations` and `market_observations` tables in `architecture.md`.
- Feature construction must filter all inputs to `available_as_of <= decision_timestamp` before building any feature. This is the responsibility of `backend/features/point_in_time.py` as defined in `architecture.md`, and every model implementation must consume features only through that gate — models must never query raw observation tables directly.
- Backtesting (`backend/backtesting/rolling_backtest.py`) must simulate each historical decision date using this same point-in-time filter, not the fully realized historical dataset.
- Any feature engineering shortcut (e.g., blind forward-filling of monthly macro data to daily frequency) that would implicitly leak future information is forbidden. Forward-filling is only valid when the value being filled forward is genuinely still the most recent known value as of each date being filled — not when it silently borrows a later publication.

---

## Training & Validation

Random train/test splitting must **never** be used as the primary evaluation method for this project. Time-series structure must be respected.

### Required approach

- **Chronological train/validation/test splits.**
- **Preferably rolling-origin (walk-forward) backtesting**, where the model is repeatedly retrained or re-evaluated as the origin date advances, simulating how the system would actually have operated over time.

Example structure (illustrative only — actual periods must be adapted to the real dataset's date range):

```
Train 2018–2021 → test 2022
Train 2018–2022 → test 2023
Train 2018–2023 → test 2024
Train 2018–2024 → test 2025
```

### Requirements

- Evaluation must represent how the system would genuinely have operated historically, respecting the point-in-time rules above at every simulated decision date.
- Hyperparameter selection must be done via the validation split(s), not the final test/backtest period — the test/backtest period is reserved for reporting out-of-sample performance, not for tuning.
- Random seeds must be fixed and recorded for reproducibility.
- Every training run must record: training data period, feature configuration used, forecast horizon(s) evaluated, hyperparameters, and resulting validation/backtest metrics (see Model Configuration & Artifacts).

---

## Probabilistic Forecasting

Where practical for the model family, the system should produce a distribution or interval, not only a point estimate.

Example (30-day forecast):

```
P10 = $29.5
P50 = $34.2
P90 = $40.0
```

### Required/supported outputs where applicable
- Point/median forecast
- Prediction intervals (e.g., P10/P50/P90)
- Probability of rate increase
- Probability of rate decrease
- Expected percentage change
- Forecast uncertainty/volatility measure

### Calibration requirement

Interval quality must be evaluated using appropriate coverage/calibration metrics (e.g., empirical coverage of the P10–P90 interval against realized outcomes in backtesting). **Uncertainty must never be presented as statistically reliable unless it has actually been evaluated for calibration on out-of-sample data.** If a model does not natively support probabilistic outputs (e.g., a plain point-forecasting configuration of a gradient-boosting model), its uncertainty must be derived through a documented method (e.g., quantile regression, residual-based intervals, or ensemble spread) and that method must be stated wherever the interval is surfaced downstream.

---

## Evaluation

The objective is not simply to minimize prediction error — it is to determine whether the forecast improves chartering decisions.

### Statistical metrics (required for every model in the benchmark)
- MAE
- RMSE
- sMAPE
- Directional accuracy
- Prediction interval coverage, where the model produces intervals

### Business/economic metrics
- Turning-point detection, where meaningful for the data
- Charter timing simulation (would the system's recommended timing have outperformed a baseline?)
- Contract strategy comparison outcomes
- Estimated freight expenditure under the system's recommendations
- Estimated savings versus baseline strategies

### Baseline strategies for comparison
- Spot-only
- Simple fixed strategy (e.g., always charter immediately, or a fixed-interval strategy)
- Forecast-based (uses the model's point/median forecast only)
- Forecast + risk-aware (uses the full recommendation logic, including uncertainty and risk)

### Labeling requirement

All economic results produced by this evaluation, and any economic figures surfaced anywhere in the product, must be labeled **"backtested/simulated estimated savings"** (or equivalent explicit wording). The system must never claim guaranteed future savings, in this file, in model outputs, or in any downstream UI text.

### Model-selection criteria

A candidate model or ensemble is promoted to active use only if it:
1. Outperforms the relevant baseline tier on out-of-sample statistical metrics, AND
2. Demonstrates business usefulness in the economic simulation (i.e., following its recommendations would historically have compared favorably to a reasonable baseline), AND
3. Has been evaluated using chronological/rolling backtesting, not a single random split.

Model selection results, including cases where a simpler model wins, must be recorded via `model_versions.benchmark_metrics` (see `architecture.md`) and are not to be overwritten or hidden by later, more complex candidates unless those candidates are actually shown to perform better.

---

## Model-Specific Requirements

### Naive / Seasonal Naive
- Implemented as the mandatory floor comparison for every horizon and every route/vessel-class combination evaluated.
- Must be run under the same chronological backtesting protocol as every other model — no special-casing.

### ARIMA / SARIMA
- Applied per relevant series (route/vessel-class/cargo-type combination) where enough historical data exists.
- Order selection (p, d, q / seasonal terms) must be determined through validation, not fixed a priori.
- Exponential Smoothing variants may be evaluated alongside ARIMA where the series characteristics suggest it (e.g., strong trend/seasonality without complex autocorrelation).

### XGBoost / LightGBM
- Consumes the full engineered feature set (historical + exogenous + static/context) from `backend/features/`.
- Hyperparameters (n_estimators, max_depth, learning_rate, etc.) must be tuned via the validation split and recorded in `model_versions.config_snapshot`.
- SHAP may be used for explainability (see Explainability section) since this is a tree-based model family where SHAP attributions are meaningful.

### LSTM / GRU
- Sequence length is a hyperparameter to be selected via validation from the candidate set {30, 60, 90, 180} (or the range actually justified by data volume) — never assumed.
- Must respect the same point-in-time feature construction as all other models; sequence windows must not extend into information unavailable at the decision timestamp.
- Dropout, hidden size, and number of layers must be tuned via validation and recorded.

### TimesFM
- Evaluated first in zero-shot mode against the actual freight series.
- Domain adaptation/fine-tuning is evaluated only where practical given available compute and data volume, and must be explicitly compared against the zero-shot variant — fine-tuning is not assumed to be worth its cost by default.
- Any covariates supported by the specific TimesFM version in use should be constructed under the same point-in-time constraints as covariates used elsewhere.

### Chronos-2
- Evaluated for both zero-shot probabilistic forecasting and covariate-informed forecasting, given its documented support for exogenous inputs.
- Probabilistic outputs from Chronos-2 should be evaluated for calibration exactly as any other probabilistic model output (see Probabilistic Forecasting).

### Ensemble
- Only constructed from models that individually demonstrate competitive out-of-sample performance.
- Weights are learned from validation/backtesting results (e.g., via a simple stacking/weighting scheme validated out-of-sample), never manually assigned based on intuition.
- The ensemble itself must go through the same backtesting and economic evaluation as any single model before being adopted.

---

## Decision Engine Interface

The forecasting layer must expose a structured, stable output contract that downstream decision-support modules consume. This corresponds to `forecasting/inference.py` plus `forecasting/uncertainty.py` in `architecture.md`, and populates the `forecasts` and `forecast_distributions` tables.

Required structured output per (route, vessel_class, decision_timestamp, horizon):

- Current freight (as of decision_timestamp)
- Forecast (point/median) for the requested horizon
- P10/P50/P90 (or equivalent interval representation)
- Probability of increase
- Probability of decrease
- Expected percentage change
- Uncertainty/volatility measure
- Model used (model_name + version_label, referencing `model_versions`)
- Model confidence/evaluation metadata (relevant benchmark metrics for that model version)

### Boundary rule

The forecasting layer must **not** contain vessel constraints, contract optimization logic, risk scoring, or UI/formatting logic. Those belong exclusively to `backend/domain/vessel/`, `backend/domain/contracts/`, `backend/domain/risk/`, and `backend/domain/recommendation/` respectively, per `architecture.md`. The decision engine (domain layer) consumes the structured forecast output above and combines it with feasibility, risk, and contract logic to produce a `Recommendation`. This separation must be preserved at the code-import level, not just conceptually — forecasting modules must not import from `domain/`, and vice versa forecasting internals must not be duplicated inside `domain/`.

---

## Explainability

- For tree-based models (XGBoost/LightGBM), **SHAP** may be used to attribute predictions to input features, since SHAP's attribution semantics are valid for this model family.
- For foundation models (TimesFM, Chronos-2) and neural models (LSTM/GRU), explanations must **not** claim that a specific feature "caused" the prediction unless the explanation method genuinely supports that interpretation for that model family. Where a rigorous per-feature attribution method is not available or not validated for a given model, the system should surface general evidence instead (e.g., recent trend direction, historical analogues, forecast confidence) rather than fabricating a feature-attribution explanation.
- The model layer's responsibility is to **expose evidence** (attributions where valid, or general supporting signals where not) that the recommendation layer (`backend/domain/recommendation/`) uses to construct the human-readable "Reasons" shown on the Decision Dashboard, per `project-overview.md`. The model layer does not construct the final natural-language explanation itself.

---

## Model Configuration & Artifacts

### Centralized configuration

All model parameters must be defined in centralized configuration (`backend/config/model_config.yaml` per `architecture.md`), never hard-coded across notebooks or application code. Configuration must cover:

- Forecast horizons
- Context/sequence lengths (candidate sets, not a single assumed value)
- Model hyperparameters (per model family)
- Feature configuration (which features are enabled, their lag/window settings)
- Backtesting configuration (train/validation/test period definitions, rolling-origin step size)
- Random seeds
- Artifact/version metadata references

Actual hyperparameter values must be the result of validation, not assumed-optimal defaults copied from unrelated domains.

### Model versioning and artifacts

Every trained model must be identifiable and reproducible via the `model_versions` table (`architecture.md`), recording:

- Model name and version label
- Training data period
- Feature configuration used (snapshot)
- Forecast horizon(s) the version was trained/evaluated for
- Hyperparameters used
- Validation results
- Backtest results (statistical and economic)
- Artifact path (model binary/weights location, per `architecture.md`'s Storage section)

Training and inference must be reproducible from this recorded metadata — given the same config snapshot and data period, re-running training should be able to reproduce comparable results (modulo any inherent stochasticity controlled by the recorded random seed).

---

## Invariants

1. No model family is selected or privileged upfront; model choice is determined solely by out-of-sample, chronological benchmarking against the actual dataset.
2. Random train/test splitting must never be used as the primary evaluation method — chronological/rolling-origin backtesting is required.
3. No feature, forecast, or backtest may use information that would not genuinely have been available at the relevant decision timestamp, across every feature category without exception.
4. A forecasted (not yet realized) value of an exogenous variable may be used as a feature only if that forecast itself would have genuinely existed and been available at the decision timestamp.
5. Forecasting model implementations must not contain vessel feasibility, contract optimization, risk scoring, API, or UI logic — those remain exclusively in the domain layer per `architecture.md`.
6. Ensemble weights, hyperparameters, and sequence/context lengths must be learned or selected via validation — never manually assumed to be optimal.
7. Model superiority claims (e.g., "foundation models outperform XGBoost") must never be asserted without supporting out-of-sample evaluation results on this project's actual data; if a simpler model wins, that result stands.
8. All probabilistic/uncertainty outputs must be evaluated for calibration before being described as reliable; uncertain or unevaluated intervals must be clearly flagged as such.
9. All economic/savings figures must be explicitly labeled as backtested/simulated estimates; guaranteed future savings must never be claimed anywhere in model outputs or documentation.
10. Explanations for neural and foundation-model predictions must not assert feature-level causation unless the explanation method genuinely supports that interpretation; SHAP-based causal-style attribution is reserved for tree-based models.
11. Every trained model version must be recorded with reproducible metadata (data period, feature config, hyperparameters, validation/backtest results, artifact path) before it can be promoted to active use.
12. The forecasting system must remain extensible to additional routes, vessel classes, cargo types, forecast horizons, and model families without requiring architectural restructuring — new candidates are added to the benchmark hierarchy, not substituted in as unquestioned replacements.
