# Architecture

## Stack

| Layer | Tool | Purpose |
|---|---|---|
| Frontend | Next.js + React + TypeScript | Dashboard UI, routing, rendering forecast/feasibility/risk/backtesting views |
| Frontend styling/charts | Tailwind CSS, Recharts / Plotly | Layout and data visualization (forecast bands, feasibility tables, risk indicators) |
| API | Python + FastAPI | Request handling, validation, orchestration of business logic, response serialization |
| Business logic | Python (domain layer, framework-agnostic) | Vessel feasibility rules, charter timing logic, contract strategy comparison, risk scoring |
| ML / Forecasting | Python: scikit-learn, XGBoost, PyTorch, TimesFM, Chronos-2 | Freight-rate forecasting models and uncertainty estimation |
| Data processing | pandas, NumPy (Polars optional if performance requires) | Feature engineering, aggregation, frequency alignment, cleaning |
| Optimization | OR-Tools / scipy.optimize | Contract strategy comparison / optimization where applicable |
| Database | PostgreSQL (TimescaleDB extension if time-series volume justifies it) | Persistent storage of reference data, observations, forecasts, and results |
| Cache / broker | Redis | Celery broker/result backend; short-lived caching of expensive read queries |
| Background jobs | Celery (workers) + Redis | Data ingestion, model training, backtesting runs — anything long-running |
| Charts | Recharts (primary) or Plotly (if richer statistical charting is needed) | Forecast bands, historical trends, backtest performance charts |
| Deployment | Docker (docker-compose for local/demo) | Containerized frontend, API, worker, database, Redis |
| Testing | pytest (backend/ML), Jest + React Testing Library (frontend) | Unit and integration tests across layers |

The tech stack is intentionally scoped for a maintainable SIH implementation, not enterprise-scale infrastructure. Cloud deployment, managed data-provider integrations, and additional services are out of scope unless explicitly added later.

---

## Folder Structure

```
project/
│
├── frontend/                              → Next.js application. Owns all UI. Never touches DB directly.
│   ├── app/
│   │   ├── dashboard/                     → Decision Dashboard route
│   │   ├── forecast/                      → Freight Forecast route
│   │   ├── feasibility/                   → Port/Vessel Feasibility route
│   │   ├── risk/                          → Risk route
│   │   └── backtesting/                   → Backtesting/Model Performance route
│   ├── components/
│   │   ├── dashboard/                     → Decision Dashboard-specific components
│   │   ├── forecast/                      → Forecast charts, horizon selectors, interval bands
│   │   ├── feasibility/                   → Vessel/port pass-fail tables
│   │   ├── risk/                          → Risk category cards/badges
│   │   ├── backtesting/                   → Metric tables, economic simulation charts
│   │   └── shared/                        → Cross-page UI primitives (cards, tabs, badges)
│   ├── lib/
│   │   ├── api-client/                    → Typed fetch wrappers to FastAPI (see Client Pattern)
│   │   └── utils/                         → Formatting, date/number helpers
│   ├── types/                             → TypeScript types mirroring backend Pydantic schemas
│   ├── public/
│   ├── package.json
│   └── tsconfig.json
│
├── backend/
│   ├── api/                               → FastAPI app: routers, request/response schemas only
│   │   ├── main.py                        → App entrypoint, router registration, middleware
│   │   ├── routers/
│   │   │   ├── requirements.py            → Procurement requirement endpoints
│   │   │   ├── forecast.py                → Forecast retrieval/generation endpoints
│   │   │   ├── feasibility.py             → Vessel/port feasibility endpoints
│   │   │   ├── risk.py                    → Risk assessment endpoints
│   │   │   ├── recommendation.py          → Recommendation (timing/contract/explanation) endpoints
│   │   │   └── backtesting.py             → Backtest results/model performance endpoints
│   │   ├── schemas/                       → Pydantic request/response models (API contract only)
│   │   └── deps.py                        → Dependency injection (DB session, config)
│   │
│   ├── domain/                            → Framework-agnostic business logic. No FastAPI/DB imports.
│   │   ├── vessel/                        → Feasibility constraint evaluation
│   │   ├── charter/                       → Charter timing decision logic
│   │   ├── contracts/                     → Contract strategy comparison logic
│   │   ├── risk/                          → Risk scoring/aggregation logic
│   │   └── recommendation/                → Combines forecast + feasibility + risk + contracts → explainable Recommendation
│   │
│   ├── forecasting/                       → Central intelligence layer. Usable independently of API.
│   │   ├── models/
│   │   │   ├── baseline.py
│   │   │   ├── xgboost_model.py
│   │   │   ├── lstm_model.py
│   │   │   ├── timesfm_model.py
│   │   │   └── chronos_model.py
│   │   ├── inference.py                   → Unified forecast-generation interface used by domain/API/backtesting
│   │   ├── uncertainty.py                 → Prediction interval / distribution construction
│   │   └── registry.py                    → Model selection/versioning (benchmark-driven, not hard-coded "best" model)
│   │
│   ├── data_access/                       → ONLY layer allowed to talk to PostgreSQL. Repository pattern.
│   │   ├── repositories/
│   │   │   ├── requirement_repo.py
│   │   │   ├── route_repo.py
│   │   │   ├── port_repo.py
│   │   │   ├── vessel_repo.py
│   │   │   ├── freight_observation_repo.py
│   │   │   ├── market_observation_repo.py
│   │   │   ├── forecast_repo.py
│   │   │   ├── risk_repo.py
│   │   │   ├── feasibility_repo.py
│   │   │   ├── recommendation_repo.py
│   │   │   └── backtest_repo.py
│   │   ├── models.py                      → ORM (SQLAlchemy) table definitions
│   │   └── session.py                     → DB engine/session management
│   │
│   ├── ingestion/                         → Pulls/loads freight, vessel, port, market, external data
│   │   ├── freight_ingestion.py
│   │   ├── market_ingestion.py
│   │   ├── vessel_ingestion.py
│   │   └── port_ingestion.py
│   │
│   ├── preprocessing/                     → Cleaning, validation, frequency alignment
│   │   ├── cleaning.py
│   │   ├── validation.py                  → Data quality checks (duplicates, outliers, unit mismatches, etc.)
│   │   └── frequency_alignment.py         → Resampling to canonical daily frequency
│   │
│   ├── features/                          → Feature engineering, point-in-time enforcement
│   │   ├── feature_builder.py
│   │   └── point_in_time.py               → Enforces "available at decision timestamp" rule
│   │
│   ├── backtesting/                       → Chronological/rolling backtesting, economic simulation
│   │   ├── rolling_backtest.py
│   │   ├── metrics.py                     → MAE, RMSE, sMAPE, directional accuracy
│   │   └── economic_simulation.py         → Strategy-vs-baseline simulated performance
│   │
│   ├── optimization/                      → OR-Tools/scipy-based contract/timing comparison helpers
│   │   └── contract_optimizer.py
│   │
│   ├── jobs/                              → Celery tasks (ingestion, training, backtesting)
│   │   ├── celery_app.py
│   │   ├── ingestion_tasks.py
│   │   ├── training_tasks.py
│   │   └── backtesting_tasks.py
│   │
│   ├── config/                            → Centralized configuration (model params, horizons, thresholds)
│   │   ├── model_config.yaml
│   │   └── settings.py                    → Environment/config loader
│   │
│   ├── tests/
│   │   ├── domain/
│   │   ├── forecasting/
│   │   ├── data_access/
│   │   └── api/
│   │
│   ├── requirements.txt
│   └── pyproject.toml
│
├── data/
│   ├── raw/                               → Unmodified ingested data
│   ├── processed/                         → Cleaned/aligned data used for feature building
│   └── external/                          → Third-party reference data (bunker prices, indices, etc.)
│
├── notebooks/
│   ├── eda/
│   ├── forecasting/
│   └── backtesting/
│
├── docker/
│   ├── frontend.Dockerfile
│   ├── backend.Dockerfile
│   ├── worker.Dockerfile
│   └── docker-compose.yml
│
└── README.md
```

---

## System Boundaries

| Layer/Folder | OWNS | MUST NOT DO |
|---|---|---|
| `frontend/` | UI rendering, routing, client-side state, calling the API client | Must not import DB drivers, must not call PostgreSQL/Redis directly, must not contain business logic (feasibility rules, risk scoring, recommendation logic) |
| `backend/api/` | HTTP routing, request/response validation (Pydantic schemas), calling domain/forecasting layers, error responses | Must not contain ML model code, must not contain SQL/ORM queries directly, must not implement feasibility/risk/contract logic inline |
| `backend/domain/` | Vessel feasibility rules, charter timing logic, contract strategy comparison, risk scoring, recommendation assembly | Must not import FastAPI, must not import Celery, must not perform DB queries directly (must receive data via repositories/service calls) |
| `backend/forecasting/` | Model training/inference interfaces, uncertainty estimation, model registry | Must not import FastAPI, must not query the database directly, must not know about HTTP requests/responses |
| `backend/data_access/` | All PostgreSQL access (reads/writes), ORM models, repository methods | Must not contain business rules or forecasting logic, must not be imported by `forecasting/` model internals (only by API layer, domain layer via injected repos, ingestion, and jobs) |
| `backend/ingestion/` | Pulling/loading raw external and market data, tagging with timestamps/source | Must not perform feature engineering or modeling, must not call domain/recommendation logic |
| `backend/preprocessing/` | Cleaning, validation, frequency alignment | Must not perform forecasting, must not access API layer |
| `backend/features/` | Feature construction, point-in-time enforcement | Must not query DB directly (receives data from data_access via a calling layer), must not silently forward-fill without documented justification |
| `backend/backtesting/` | Rolling/chronological backtests, metrics, economic simulation | Must not use any data unavailable at the simulated decision timestamp; must not call live/production forecast endpoints in a way that bypasses point-in-time constraints |
| `backend/optimization/` | Contract/timing comparison computations | Must not perform autonomous execution, must not directly mutate recommendation state without going through domain layer |
| `backend/jobs/` | Scheduling and running long-running Celery tasks | Must not block the API process; must not contain business logic beyond orchestration (delegates to ingestion/forecasting/backtesting modules) |
| `backend/config/` | Centralized model parameters, horizons, thresholds | Must not be bypassed by hard-coded values elsewhere in the codebase |

Dependency direction is strictly one-directional:

```
frontend → backend/api → backend/domain → backend/forecasting
                        → backend/data_access

backend/ingestion, backend/preprocessing, backend/features → backend/data_access
backend/backtesting → backend/forecasting, backend/features, backend/data_access
backend/jobs → backend/ingestion, backend/forecasting, backend/backtesting
```

`backend/forecasting/` and `backend/domain/` must never import from `backend/api/` or `backend/jobs/`. This keeps forecasting usable independently of the API (e.g., from notebooks or backtesting scripts).

---

## Data Flow

### 1. Procurement decision request

```
User (frontend) submits Procurement Requirement
    → frontend/lib/api-client → POST /requirements
    → api/routers/requirements.py validates payload (Pydantic schema)
    → domain layer creates Procurement Requirement object
    → data_access/repositories/requirement_repo.py persists it
    → response returns requirement_id to frontend
```

### 2. Forecast generation

```
frontend requests forecast for a requirement/route/vessel-class/horizon set
    → api/routers/forecast.py
    → data_access: fetch relevant Freight Observations + Market Observations (as-of request timestamp)
    → features/feature_builder.py + features/point_in_time.py: build point-in-time-safe feature set
    → forecasting/inference.py: run selected model(s) (registry-selected, benchmark-driven)
    → forecasting/uncertainty.py: compute prediction intervals / directional probability
    → data_access/forecast_repo.py: persist Forecast + Forecast Distribution
    → api layer serializes response → frontend renders Freight Forecast page
```

### 3. Background data ingestion

```
Celery beat/schedule or manual trigger
    → jobs/ingestion_tasks.py (Celery task, runs in worker process, non-blocking to API)
    → ingestion/freight_ingestion.py, market_ingestion.py, vessel_ingestion.py, port_ingestion.py
    → preprocessing/cleaning.py + validation.py (data quality checks)
    → preprocessing/frequency_alignment.py (resample to canonical daily frequency)
    → data_access/repositories/*: persist Freight Observations, Market Observations, updated reference data
    → each record tagged with timestamp/source for later point-in-time validation
```

### 4. Model training

```
jobs/training_tasks.py (Celery task, worker process)
    → data_access: retrieve historical Freight/Market Observations
    → features/feature_builder.py: construct training feature set (point-in-time safe)
    → forecasting/models/*: train candidate model(s) per config/model_config.yaml
    → forecasting/registry.py: register trained model version with benchmark metrics
    → model artifacts persisted to storage (see Storage section)
    → API/domain layers consume the currently-registered model via forecasting/inference.py
```

### 5. Backtesting

```
jobs/backtesting_tasks.py (Celery task, worker process)
    → backtesting/rolling_backtest.py: iterate over historical decision dates chronologically
    → for each simulated date: features/point_in_time.py restricts inputs to data available as-of that date
    → forecasting/inference.py: generate forecast using only point-in-time-safe features
    → domain layer: generate simulated recommendation (timing/vessel/contract) as it would have been made then
    → backtesting/economic_simulation.py: compare simulated recommendation outcome vs. baseline strategy
    → backtesting/metrics.py: compute MAE, RMSE, sMAPE, directional accuracy
    → data_access/backtest_repo.py: persist Backtest Result records
    → API layer exposes results to Backtesting/Model Performance page
```

### 6. Recommendation generation

```
Triggered after forecast generation (step 2) for a given requirement
    → domain/vessel: evaluate candidate vessel classes against Port + Vessel constraints → Vessel Feasibility Result(s)
    → domain/charter: convert forecast + uncertainty into Charter Timing Recommendation (charter now / wait-monitor)
    → domain/contracts: compare contract strategies (spot / short-term / medium-term) using forecast + feasibility + backtested evidence
    → domain/risk: aggregate market/port/vessel/external risk into a Risk Assessment
    → domain/recommendation: assemble Recommendation object combining timing + vessel + contract + risk + explanation reasons
    → data_access/recommendation_repo.py: persist Recommendation
    → api/routers/recommendation.py: serialize and return to frontend
    → frontend renders Decision Dashboard with explanation reasons and links to supporting pages
```

---

## Database Schema

All tables use PostgreSQL. Timestamps are stored in UTC (`timestamptz`). Shared domain/reference data (ports, vessels, routes, freight/market observations) intentionally has **no `user_id` column** — this is enterprise shared reference data, not per-user SaaS data.

### `procurement_requirements`

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| cargo_type | text | Required (e.g., "coal") |
| quantity_mt | numeric | Required, > 0 |
| origin_id | UUID | FK → `routes.origin_id` or resolved via `routes` (see below) |
| destination_id | UUID | FK → `ports.id` |
| origin_port_or_region | text | Origin identifier (country/region, not necessarily a single port) |
| loading_window_start | date | Required |
| loading_window_end | date | Required |
| num_voyages | integer | Required, >= 1 |
| contract_horizon_months | integer | Required |
| preferred_vessel_class | text | Optional, FK-like reference to `vessel_classes.code` |
| max_acceptable_freight | numeric | Optional |
| required_delivery_deadline | date | Optional |
| min_parcel_size_mt | numeric | Optional |
| max_parcel_size_mt | numeric | Optional |
| risk_preference | text | Optional (e.g., "low", "medium", "high") |
| preferred_contract_duration_months | integer | Optional |
| expected_num_parcels | integer | Optional |
| commercial_constraints | text | Optional, free text |
| created_at | timestamptz | Default now() |
| created_by | text | Free-text identifier of submitting user (no auth-linked FK unless authentication is implemented — see Authentication) |

Indexes: `(destination_id)`, `(loading_window_start)`, `(created_at)`.

### `routes`

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| origin_name | text | e.g., "Australia" — required |
| destination_port_id | UUID | FK → `ports.id`, required |
| is_active | boolean | Default true; supports adding/retiring routes without deletion |
| created_at | timestamptz | Default now() |

Unique constraint: `(origin_name, destination_port_id)`.

### `ports`

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| name | text | e.g., "Paradip", required, unique |
| country | text | Required |
| max_draft_m | numeric | Nullable if unknown |
| max_loa_m | numeric | Nullable |
| max_beam_m | numeric | Nullable |
| berth_capacity_mt_per_day | numeric | Nullable |
| cargo_handling_rate_mt_per_hour | numeric | Nullable |
| storage_capacity_mt | numeric | Nullable |
| avg_historical_turnaround_hours | numeric | Nullable, derived/updatable via ingestion |
| avg_historical_congestion_score | numeric | Nullable, derived |
| operating_restrictions | text | Free text, nullable |
| created_at | timestamptz | Default now() |
| updated_at | timestamptz | Updated on ingestion refresh |

### `vessel_classes`

| Column | Type | Notes |
|---|---|---|
| code | text | Primary key, e.g., "supramax" |
| display_name | text | e.g., "Supramax" |
| typical_dwt_min | numeric | Nullable |
| typical_dwt_max | numeric | Nullable |
| typical_loa_m | numeric | Nullable |
| typical_beam_m | numeric | Nullable |
| typical_draft_m | numeric | Nullable |
| created_at | timestamptz | Default now() |

### `vessels`

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| vessel_class_code | text | FK → `vessel_classes.code`, required |
| name | text | Nullable if unnamed/generic representative vessel |
| dwt | numeric | Nullable |
| loa_m | numeric | Nullable |
| beam_m | numeric | Nullable |
| draft_m | numeric | Nullable |
| current_position | text | Nullable, free text or lat/long if available |
| ballast_laden_status | text | Nullable ("ballast" / "laden" / unknown) |
| availability_date | date | Nullable |
| historical_utilization_pct | numeric | Nullable |
| updated_at | timestamptz | Updated on ingestion refresh |

Index: `(vessel_class_code)`.

### `freight_observations`

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| observation_date | date | Required — the freight rate date, not ingestion date |
| route_id | UUID | FK → `routes.id`, required |
| vessel_class_code | text | FK → `vessel_classes.code`, required |
| cargo_type | text | Required |
| parcel_size_mt | numeric | Nullable |
| rate_usd_per_mt | numeric | Required, > 0 |
| classification | text | Nullable ("spot" / "contract" / index-derived) |
| source | text | Required — data provenance |
| available_as_of | timestamptz | Required — when this observation became knowable, used for point-in-time filtering |
| ingested_at | timestamptz | Default now() |

Unique constraint: `(observation_date, route_id, vessel_class_code, cargo_type, source)`.
Index: `(route_id, vessel_class_code, observation_date)`.

### `market_observations`

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| variable_name | text | Required, e.g., "bunker_price_singapore", "baltic_dry_index" |
| observation_date | date | Required |
| value | numeric | Required |
| unit | text | Nullable |
| source | text | Required |
| available_as_of | timestamptz | Required — publication/availability timestamp, used for point-in-time filtering |
| ingested_at | timestamptz | Default now() |

Unique constraint: `(variable_name, observation_date, source)`.
Index: `(variable_name, observation_date)`.

### `forecasts`

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| requirement_id | UUID | FK → `procurement_requirements.id`, nullable (forecasts may also be generated standalone, e.g., during backtesting) |
| route_id | UUID | FK → `routes.id`, required |
| vessel_class_code | text | FK → `vessel_classes.code`, required |
| model_version_id | UUID | FK → `model_versions.id` (see below), required |
| decision_timestamp | timestamptz | Required — the point-in-time the forecast was generated as-of |
| horizon_days | integer | Required (7 / 14 / 30 / 60) |
| point_estimate_usd_per_mt | numeric | Required |
| created_at | timestamptz | Default now() |

Index: `(route_id, vessel_class_code, decision_timestamp, horizon_days)`.

### `forecast_distributions`

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| forecast_id | UUID | FK → `forecasts.id`, required |
| p10 | numeric | Required |
| p50 | numeric | Required |
| p90 | numeric | Required |
| probability_increase | numeric | Nullable, 0–1 |
| probability_decrease | numeric | Nullable, 0–1 |
| expected_pct_change | numeric | Nullable |
| volatility_score | numeric | Nullable |

Unique constraint: `(forecast_id)`.

### `model_versions`

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| model_name | text | Required (e.g., "xgboost", "timesfm", "chronos-2") |
| version_label | text | Required |
| trained_at | timestamptz | Required |
| config_snapshot | jsonb | Required — copy of `model_config.yaml` values used |
| benchmark_metrics | jsonb | Nullable — MAE/RMSE/sMAPE/directional accuracy from validation |
| artifact_path | text | Nullable — see Storage |
| is_active | boolean | Default false; only one active version per (model_name, route scope) at a time |

### `vessel_feasibility_results`

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| requirement_id | UUID | FK → `procurement_requirements.id`, required |
| vessel_class_code | text | FK → `vessel_classes.code`, required |
| draft_check | text | "pass" / "fail" / "unknown" |
| loa_check | text | "pass" / "fail" / "unknown" |
| beam_check | text | "pass" / "fail" / "unknown" |
| dwt_check | text | "pass" / "fail" / "unknown" |
| other_constraint_notes | text | Nullable, free text explanation |
| overall_feasible | boolean | Required |
| evaluated_at | timestamptz | Default now() |

### `risk_assessments`

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| requirement_id | UUID | FK → `procurement_requirements.id`, required |
| market_risk_score | numeric | Nullable |
| port_risk_score | numeric | Nullable |
| vessel_risk_score | numeric | Nullable |
| external_risk_score | numeric | Nullable |
| overall_risk_level | text | Required ("low" / "medium" / "high") |
| explanation | jsonb | Required — structured list of contributing factors/reasons |
| evaluated_at | timestamptz | Default now() |

### `contract_strategies`

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| requirement_id | UUID | FK → `procurement_requirements.id`, required |
| strategy_type | text | Required ("spot" / "short_term_multi_voyage" / "medium_term_multi_voyage") |
| expected_expenditure_usd | numeric | Nullable |
| risk_level | text | Nullable |
| flexibility_score | numeric | Nullable |
| backtested_estimated_savings_usd | numeric | Nullable — must be labeled as backtested estimate, never guaranteed |
| evaluated_at | timestamptz | Default now() |

### `recommendations`

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| requirement_id | UUID | FK → `procurement_requirements.id`, required, unique per active recommendation |
| forecast_id | UUID | FK → `forecasts.id`, required |
| charter_timing | text | Required ("charter_now" / "wait_monitor") |
| recommended_vessel_class_code | text | FK → `vessel_classes.code`, nullable if none feasible |
| recommended_contract_strategy_id | UUID | FK → `contract_strategies.id`, nullable |
| risk_assessment_id | UUID | FK → `risk_assessments.id`, required |
| explanation | jsonb | Required — structured reasons array shown in UI |
| created_at | timestamptz | Default now() |

### `backtest_runs`

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| model_version_id | UUID | FK → `model_versions.id`, required |
| route_id | UUID | FK → `routes.id`, nullable (nullable = run across all routes) |
| vessel_class_code | text | FK → `vessel_classes.code`, nullable |
| start_date | date | Required |
| end_date | date | Required |
| baseline_strategy | text | Required — description of comparison baseline |
| status | text | Required ("running" / "completed" / "failed") |
| created_at | timestamptz | Default now() |
| completed_at | timestamptz | Nullable |

### `backtest_results`

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| backtest_run_id | UUID | FK → `backtest_runs.id`, required |
| decision_date | date | Required — simulated point-in-time decision date |
| mae | numeric | Nullable |
| rmse | numeric | Nullable |
| smape | numeric | Nullable |
| directional_accuracy | numeric | Nullable |
| simulated_recommendation | jsonb | Required — the simulated timing/vessel/contract recommendation at that date |
| simulated_outcome_usd | numeric | Nullable |
| baseline_outcome_usd | numeric | Nullable |
| estimated_savings_usd | numeric | Nullable — backtested estimate only |
| created_at | timestamptz | Default now() |

Index: `(backtest_run_id, decision_date)`.

---

## Storage

| Storage | Path/key pattern | Contents | Access rules |
|---|---|---|---|
| Local/container filesystem (or mounted volume) | `data/raw/{source}/{date}/` | Raw ingested files before processing | Written only by `ingestion/`; read only by `preprocessing/` |
| Local/container filesystem | `data/processed/{dataset}/{date}/` | Cleaned, frequency-aligned datasets | Written by `preprocessing/`; read by `features/` |
| Local/container filesystem | `data/external/{provider}/` | Third-party reference datasets (bunker prices, indices, etc.) | Written by `ingestion/`; read by `preprocessing/` |
| Model artifact storage | `backend/forecasting/artifacts/{model_name}/{version_label}/` | Trained model binaries/weights, scalers, feature metadata | Written by training jobs; read by `forecasting/inference.py` via `model_versions.artifact_path` |
| Configuration | `backend/config/model_config.yaml` | Centralized model parameters, horizons, context lengths | Read-only at runtime; changed only via reviewed config updates, never hard-coded elsewhere |
| Logs | Container stdout/stderr, aggregated by Docker | Application and job logs | Read by developers/operators; no PII expected given enterprise domain data |

No cloud storage provider (S3, GCS, Azure Blob, etc.) is specified. If model artifacts or datasets exceed what local/container volumes can reasonably hold, introducing a cloud storage provider is an explicit architectural decision to be made later — it must not be silently assumed.

---

## Authentication

Authentication provider and method are **not yet decided** and must be treated as an explicit pending architectural decision, not invented.

What is known from `project-overview.md`:
- This is an internal enterprise decision-support tool for SAIL procurement/freight users, not a consumer-facing product.
- No multi-tenant, per-user data ownership model is required for domain/reference data (ports, vessels, freight/market observations).
- `procurement_requirements.created_by` is currently a free-text field rather than a foreign key to a user table, because no user/auth system has been defined.

Until a decision is made:
- All API routes are treated as **internal/protected-by-deployment-environment** (e.g., accessible only within SAIL's network or via a reverse proxy with basic auth) rather than implementing application-level authentication.
- No specific auth provider (OAuth, SSO, JWT-based custom auth, etc.) should be implemented or assumed.
- If/when authentication is introduced, it should be added as FastAPI middleware in `backend/api/` (e.g., a dependency in `deps.py`) without requiring changes to `domain/`, `forecasting/`, or `data_access/` layers.

---

## Client Pattern

Frontend communicates with the backend exclusively through a typed API client layer — never directly with PostgreSQL, Redis, or Celery.

**API client location:** `frontend/lib/api-client/`

Structure:

```
frontend/lib/api-client/
├── client.ts          → base fetch wrapper (base URL, headers, error handling)
├── requirements.ts    → createRequirement(), getRequirement()
├── forecast.ts        → getForecast(requirementId, horizons[])
├── feasibility.ts     → getFeasibility(requirementId)
├── risk.ts            → getRisk(requirementId)
├── recommendation.ts  → getRecommendation(requirementId)
└── backtesting.ts     → getBacktestResults(modelVersionId?)
```

**Request/response typing:** Types in `frontend/types/` mirror the Pydantic schemas defined in `backend/api/schemas/`. Any change to a Pydantic response schema must be reflected in the corresponding TypeScript type.

**Error handling:** `client.ts` normalizes FastAPI error responses (4xx validation errors, 5xx failures) into a consistent `ApiError` shape consumed by UI components, which render appropriate fallback/error states rather than crashing.

**Authentication headers/session handling:** Not applicable until authentication is decided (see Authentication section above). The client wrapper should have a single place (`client.ts`) where an auth header could later be attached without touching individual endpoint files.

**Example GET pattern:**

```
frontend component
    → api-client/forecast.ts: getForecast(requirementId, [7,14,30,60])
    → fetch(`${API_BASE_URL}/requirements/${id}/forecast?horizons=7,14,30,60`)
    → FastAPI router validates query params → calls domain/forecasting layers
    → typed JSON response → parsed into TypeScript ForecastResponse type
    → rendered in Freight Forecast page components
```

**Example POST pattern:**

```
frontend component (requirement form)
    → api-client/requirements.ts: createRequirement(payload)
    → fetch POST `${API_BASE_URL}/requirements` with JSON body
    → FastAPI validates via Pydantic RequirementCreate schema
    → domain layer + data_access persist the requirement
    → response returns RequirementResponse (includes id)
    → frontend redirects/loads Decision Dashboard for that requirement_id
```

---

## Key Integration Patterns

**FastAPI**
- Owns HTTP concerns only: routing, request validation (Pydantic), response serialization, dependency injection of repositories/config.
- Calls into `domain/` for business logic and `forecasting/inference.py` for model predictions.
- Never contains SQL, ORM queries, or model training/inference code inline.

**PostgreSQL / TimescaleDB**
- Accessed exclusively through `backend/data_access/repositories/`.
- `domain/`, `forecasting/`, `api/` never issue raw SQL or ORM queries directly — they call repository methods, which return domain-shaped data (not raw ORM rows) where practical.
- TimescaleDB extension is used only if/when freight/market observation volume and query patterns justify it; PostgreSQL alone is sufficient for the SIH prototype scale.

**Redis / Celery**
- Redis serves as the Celery broker and result backend, and optionally as a short-lived cache for expensive read-heavy queries (e.g., recently computed backtest summaries).
- Celery workers execute `backend/jobs/*` tasks: ingestion, model training, backtesting. These are triggered either on a schedule (Celery beat) or via an API endpoint that enqueues a task and returns a job/status identifier rather than blocking the HTTP request.
- The API layer never performs long-running computation synchronously within a request-response cycle.

**ML model inference**
- `forecasting/inference.py` provides the single entrypoint used by both the live API path (via `domain/`) and the backtesting path (via `backtesting/rolling_backtest.py`).
- Models themselves (`forecasting/models/*.py`) have no knowledge of FastAPI, Celery, or the database — they accept feature arrays/dataframes and return predictions + uncertainty.
- Model selection is benchmark-driven via `forecasting/registry.py` and `model_versions` table; no single model is architecturally privileged as "the" model.

**Background training/backtesting**
- Triggered via `jobs/training_tasks.py` / `jobs/backtesting_tasks.py`, run in Celery worker processes.
- Training tasks call `forecasting/` and `features/` directly (not through the API layer) and persist results via `data_access/`.
- Backtesting tasks call `forecasting/inference.py`, `features/point_in_time.py`, and `domain/` (to simulate historical recommendations) and persist results via `data_access/backtest_repo.py`.

**External data ingestion**
- `backend/ingestion/*.py` modules are the only components that pull from external/raw sources.
- No specific external data provider or API has been selected in this document; ingestion modules should be structured so a concrete provider integration can be added per source without restructuring the ingestion boundary.
- All ingested records are persisted with `source` and `available_as_of` fields to support point-in-time validation downstream.

**Optimization engine**
- `backend/optimization/contract_optimizer.py` is called by `domain/contracts/` when comparing contract strategies, not called directly by the API layer.
- Optimization logic consumes forecast + feasibility + risk outputs; it does not independently query the database or the forecasting layer.

---

## Invariants

1. The frontend must never access PostgreSQL, Redis, or Celery directly — all data flows through the FastAPI client layer.
2. `backend/forecasting/` must never import FastAPI, Celery, or any API/UI concern — it must remain independently usable (e.g., from notebooks or backtesting scripts).
3. `backend/api/` must never contain ML model implementations or SQL/ORM queries — it orchestrates calls to `domain/`, `forecasting/`, and `data_access/`.
4. Long-running operations (data ingestion, model training, backtesting) must run in Celery background workers and must never block an API request.
5. All PostgreSQL access must go through `backend/data_access/repositories/` — no other module issues direct database queries.
6. Forecasting and backtesting must never use information that would not genuinely have been available at the relevant decision timestamp; `available_as_of` timestamps must be enforced via `features/point_in_time.py`.
7. Every ingested freight and market observation must retain its `source` and `available_as_of` metadata so point-in-time correctness can be validated and audited.
8. Vessel feasibility results must always derive from explicit, inspectable constraint checks (draft/LOA/beam/DWT/etc.) — never a hard-coded or arbitrary vessel recommendation.
9. Every recommendation (charter timing, vessel, contract strategy, risk) must carry a structured, human-readable explanation of the factors behind it.
10. Shared domain/reference data (ports, vessels, vessel classes, routes, freight observations, market observations) must never be given a `user_id` foreign key or otherwise modeled as per-user data.
11. Model selection must remain benchmark-driven through `model_versions`/`forecasting/registry.py` — the architecture must not privilege one model type as permanently "the" model.
12. The system must never implement autonomous execution of charter contracts, financial transactions, vessel booking, or automated broker/shipowner communication — all such functionality is explicitly out of scope per `project-overview.md`.
13. New external services, data providers, or authentication providers must not be introduced without explicit architectural justification; if undecided, they must be marked as a pending decision rather than assumed.
14. The architecture must support adding new routes, ports, vessel classes, cargo types, forecast horizons, and models by adding data/config rather than restructuring existing layers.
