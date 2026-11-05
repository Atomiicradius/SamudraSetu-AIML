# Build Plan

## Core Principle

Every user-facing feature is built as a vertical slice: the real UI is built first against realistic mock data and verified for layout, states, interactions, and accessibility before any backend logic exists behind it. Backend/data/model logic is then implemented as its own testable unit, after which the already-built UI is reconnected to the real output and re-tested against loading, empty, error, and unavailable states. No phase produces backend work that cannot be independently demonstrated (via UI, a test suite, or a concrete script/log output), and no page is left wired to mock data once its supporting logic phase has completed.

---

## Phase 1 — Foundation

### 01 Monorepo & Docker Development Environment
**UI:** None (infrastructure only).
**Logic:** Create the top-level structure exactly per `architecture.md`: `frontend/`, `backend/{api,domain,forecasting,data_access,ingestion,preprocessing,features,backtesting,optimization,jobs,config,tests}`, `data/{raw,processed,external}`, `notebooks/{eda,forecasting,backtesting}`, `docker/`. Add `docker/frontend.Dockerfile`, `docker/backend.Dockerfile`, `docker/worker.Dockerfile`, `docker/docker-compose.yml` wiring Next.js, FastAPI, a Celery worker, PostgreSQL, and Redis as services. Add `.env.example` (per `code-standards.md` → Configuration & Secrets) and package manifests (`frontend/package.json`, `backend/requirements.txt`, `backend/pyproject.toml`) with pinned dependency placeholders per `library-docs.md`.
**Verification:** `docker-compose up` starts all five containers without error; each container's health/log output shows a clean start; a placeholder `README.md` documents the one-command startup.

### 02 Design Tokens, Fonts & Global Styles
**UI:** No screens yet, but the visual foundation every later screen depends on: Tailwind config mapped 1:1 to the semantic tokens in `ui-tokens.md` (`surface-*`, `text-*`, `border-*`, spacing scale, radius scale, type scale), light theme active by default, dark "watch" theme defined via the same token names, IBM Plex Sans/Mono loaded once via `next/font` in the root layout and exposed as `--font-sans`/`--font-mono` per `ui-rules.md` → Font.
**Logic:** `frontend/app/layout.tsx` (root layout, font loading), `tailwind.config.ts` (token mapping), a small `frontend/lib/utils/` theme helper if needed. No component library, no raw hex/px values anywhere in config.
**Verification:** A throwaway route renders one instance of each type-scale token and each semantic surface/text/border token in both themes; visually diffed against `ui-tokens.md`'s tables; removed once Feature 04 exists to demonstrate the same tokens through real components.

### 03 Application Shell & Page Navigation Skeleton
**UI:** `AppShell` (nav rail + content slot), `NavRail` with 5 `NavItem`s (Decision Dashboard, Freight Forecast, Feasibility, Risk, Backtesting) implementing inactive/hover/active/focus states exactly per `ui-rules.md` → Navigation, `PageContainer` (1440px max width, responsive padding/grid), `PageHeader` (page `type-h1` title), `GlobalNotificationArea` (toast host, `elevation-3`). Five route files (`frontend/app/dashboard`, `.../forecast`, `.../feasibility`, `.../risk`, `.../backtesting`) each rendering only `PageContainer` + `PageHeader` + a placeholder "Coming soon" line.
**Logic:** `frontend/components/shell/`, `frontend/components/nav/` per `ui-registry.md`'s folder mapping. Nav item active state driven by the current route, not manually set per page.
**Verification:** Manual click-through of all 5 nav items confirms active-state (border+background+weight), collapse behavior at `md`/`lg` breakpoints, keyboard-only navigation reaches every nav item with a visible focus ring, per `ui-rules.md` → Accessibility.

### 04 Shared UI Primitive Component Library
**UI:** `Card`, `Badge` (all variants: success/warning/error/info/risk-low/risk-medium/risk-high/feasibility-pass/feasibility-fail/feasibility-unknown/forecast-increase/forecast-decrease), `DataTable` (header/row/alignment/hover/selected-row/responsive sticky-column), `MetricValue`, `EmptyState`, `LoadingSkeleton` (block/row/chart variants), `ErrorAlert` (error/forecast-unavailable/insufficient-data variants) — built exactly to the contracts in `ui-registry.md` → Component Contracts.
**Logic:** `frontend/components/data-display/`. Each component's required states implemented per its contract (e.g., `Badge` refuses to render without a `variant`; `DataTable` renders `LoadingSkeleton` variant `row` when loading).
**Verification:** Jest + React Testing Library tests per component covering every documented variant/state; an assertion that every `Badge` variant renders visible icon + text (not color alone), satisfying `ui-tokens.md` Invariant 2.

### 05 FastAPI Skeleton, Configuration & Health Check
**UI:** None.
**Logic:** `backend/api/main.py` (app entrypoint, router registration, CORS), `backend/api/deps.py` (DB session dependency stub), `backend/config/settings.py` (pydantic-settings environment loader), a `GET /health` route. No routers, domain, or data_access logic yet beyond what health-check needs.
**Verification:** `curl localhost:8000/health` returns 200 from within the Docker network; a pytest using FastAPI's `TestClient` asserts the same.

### 06 Database Schema Foundation & Migrations
**UI:** None.
**Logic:** `backend/data_access/session.py` (engine/session), `backend/data_access/models.py` with SQLAlchemy ORM definitions for the shared reference tables only: `routes`, `ports`, `vessel_classes`, `vessels`, exactly matching the columns/constraints in `architecture.md` → Database Schema. First Alembic migration created and applied.
**Verification:** `alembic upgrade head` succeeds against the Dockerized Postgres; `\dt` in `psql` shows the four tables with correct columns/constraints; a pytest confirms the unique constraint on `routes(origin_name, destination_port_id)`.

### 07 Reference Data Seeding, Read Endpoints & Frontend API Client Foundation
**UI:** None yet — this feature proves the full stack round-trip that later pages depend on, without introducing page UI.
**Logic:** A seed script populating `ports` (Paradip, Visakhapatnam, Gangavaram, Gopalpur, Dhamra, Sagar/Sandheads, Haldia), `vessel_classes` (Handysize, Supramax, Panamax, Capesize), and `routes` (each of the 5 initial origins × relevant destination ports) per `project-overview.md`'s initial geographic/vessel scope. `backend/data_access/repositories/route_repo.py`, `port_repo.py`, `vessel_repo.py` with basic list/get methods. `backend/api/routers/` read-only endpoints (`GET /routes`, `GET /ports`, `GET /vessel-classes`) with Pydantic response schemas in `backend/api/schemas/`. `frontend/lib/api-client/client.ts` (base fetch wrapper, `ApiError` normalization) and a first typed client function calling one of these endpoints. Matching types added to `frontend/types/`.
**Verification:** Integration test hits each new endpoint via `TestClient` and asserts the seeded rows come back; a temporary frontend call logs the fetched routes/ports in the browser console, confirming the client wrapper and `ApiError` shape work end-to-end.

---

## Phase 2 — Decision Dashboard & Procurement Flow

### 08 Procurement Requirement Form — UI with Mock Submission
**UI:** `RequirementForm` composing `FormSection`, `SelectInput` (Cargo Type, Origin, Destination — options from Feature 07's real reference endpoints, no free text), `NumericInput` (Quantity with "MT" suffix, Number of Voyages integer stepper, Contract Horizon with "months" label), `DateRangeInput` (Loading Window, start ≤ end validation), `TextInput` (optional commercial constraints), `FormFieldError` — grouped per `ui-registry.md` (Cargo Details / Route / Contract Terms), consistent required-field marking per `ui-rules.md` → Form Inputs. Submission is client-side only (validates, then logs the payload and shows a mock success toast via `GlobalNotificationArea`).
**Logic:** `frontend/components/forms/` primitives, `frontend/components/page-specific/RequirementForm.tsx` on the Decision Dashboard route.
**Verification:** Manual + RTL tests: every required-field validation error renders (icon + message per `ui-rules.md`), start>end date is rejected, numeric fields render live values in Plex Mono once populated, form stacks to one column below `md` with unchanged tab order.

### 09 Procurement Requirement Persistence — Backend
**UI:** None.
**Logic:** Add `procurement_requirements` table + migration exactly per `architecture.md`. `backend/api/schemas/` `RequirementCreate`/`RequirementResponse`. `backend/domain/` requirement construction (thin — mostly shape validation already covered by Pydantic, per `code-standards.md`). `backend/data_access/repositories/requirement_repo.py`. `backend/api/routers/requirements.py`: `POST /requirements`, `GET /requirements/{id}`.
**Verification:** `TestClient` integration test: POST the example payload from `frontend and user flow.md` (Coal, 50,000 MT, Australia→Paradip, 15–25 Sep, 3 voyages, 6 months), assert 201 + persisted row + correct FK resolution to `routes`/`ports`.

### 10 Procurement Requirement Form — Real API Integration
**UI:** Same `RequirementForm` from Feature 08, now wired to real submission; on success, redirects to the Decision Dashboard with the new `requirement_id`; on failure, renders the shared `ApiError` inline (not a toast-only failure) with a retry-safe resubmit.
**Logic:** `frontend/lib/api-client/requirements.ts` (`createRequirement()`), replacing the Feature 08 mock submit handler.
**Verification:** Manual submission creates a real row (cross-checked via `GET /requirements/{id}`); network failure (DB stopped) shows the error state without crashing the form; loading state (disabled submit + spinner) visible during the request.

### 11 Decision Dashboard — Requirement Summary & Empty State
**UI:** `EmptyState` ("No procurement requirement yet" / "Enter a cargo requirement to generate a forecast and recommendation.") shown when no requirement is active; once one exists, a `SummaryCard` shows cargo/quantity/origin/destination/loading window/voyages/horizon.
**Logic:** Decision Dashboard route reads `requirement_id` (query param or route state) and calls `GET /requirements/{id}` via the Feature 09/10 client function.
**Verification:** Fresh visit shows the empty state; after Feature 10's flow, the same page shows the correct `SummaryCard` content; loading skeleton shown while the fetch is in flight.

### 12 Decision Dashboard — Recommendation Summary UI with Mock Data
**UI:** `RecommendationSummaryCard` (highlighted via `border-strong`/accent border, never elevation) composing: `CharterTimingIndicator` ("Charter Now" / "Wait / Monitor"), recommended vessel name + `FeasibilityStatusBadge`, `ContractStrategyComparison` (spot / short-term / medium-term parallel cards or table), `RiskSummaryCard` [condensed] (overall badge + up to 4 category badges), `SavingsEstimate` (with the mandatory "backtested/simulated estimate" qualifier baked in), `RecommendationReasoning` (ordered list per the explainability example in `project-overview.md`). `ForecastChart` [compact] beneath it. All data is realistic mock matching the example output in `frontend and user flow.md` and `project-overview.md`.
**Logic:** `frontend/components/page-specific/RecommendationSummaryCard.tsx`, `frontend/components/recommendation/`, `frontend/components/forecast/ForecastChart.tsx` (compact mode) — all built to the registry contracts so no rework is needed when real data arrives.
**Verification:** Visual QA against every relevant `ui-rules.md` rule (badge icon+label+color, no color-only freight direction, dashed forecast beyond "today", qualifier text adjacent to savings figure); responsive check at all breakpoints; RTL test asserts the qualifier text is present and cannot be omitted.

---

## Phase 3 — Freight Forecasting

### 13 Freight Forecast Page — UI Shell & Mock Data
**UI:** `HorizonSelector` (7/14/30/60-day toggle), `ForecastSummaryStat` (current, forecast median, P10–P90, direction — neutral glyph only), `ForecastChart` [full] (historical solid line, forecast solid-to-dashed at "today", shaded interval band with dashed edge, "today" marker), `ModelComparisonChart` (categorical palette + dash-pattern redundancy beyond 3 series), `UncertaintyIndicator`. All backed by realistic mock series matching the example numbers in `project-overview.md`.
**Logic:** `frontend/components/forecast/` per `ui-registry.md`; page composition per `ui-registry.md` → Page Composition → Freight Forecast.
**Verification:** Switching horizon updates all four components consistently (mock data per horizon); every chart rule from `ui-rules.md` → Data Visualization is visually confirmed; legend moves below chart under `md`.

### 14 Historical Data Ingestion Pipeline
**UI:** None.
**Logic:** `backend/ingestion/freight_ingestion.py` and `market_ingestion.py`, plus `freight_observations`/`market_observations` tables + migration exactly per `architecture.md`, each record tagged with `source` and `available_as_of`. Because the exact SAIL dataset (unit, frequency, coverage) is one of `deliverables.md`'s unresolved "Critical Questions," this pipeline is built and tested against a structurally-representative **sample dataset** placed in `data/raw/sample/` that conforms to the canonical schema in `model.md` — explicitly labeled as a development placeholder, not a real or invented external data source, pending SAIL's actual dataset.
**Verification:** Running the ingestion module against the sample files populates both tables with correct `available_as_of` tagging; a pytest asserts the unique constraints and that no row is missing its availability timestamp.

### 15 Data Preprocessing, Cleaning & Frequency Alignment
**UI:** None.
**Logic:** `backend/preprocessing/cleaning.py`, `validation.py` (duplicate/outlier/unit-mismatch checks), `frequency_alignment.py` (resample to canonical daily frequency, with forward-fill only where genuinely still the latest known value per `model.md`'s explicit rule). Output written to `data/processed/`.
**Verification:** pytest fixtures with intentionally injected duplicates/outliers are correctly flagged/handled; a resampled series is asserted to be daily-frequency with no forward-fill crossing a real publication gap.

### 16 Point-in-Time Feature Engineering Pipeline
**UI:** None.
**Logic:** `backend/features/point_in_time.py` (the `available_as_of <= decision_timestamp` gate) and `feature_builder.py` (lags, rolling stats, trend/rate-of-change, static/context features) per `model.md` → Data & Features. Every implemented feature documented per `model.md`'s Feature Documentation Requirement, alongside the code.
**Verification:** The project's most safety-critical test: a fixture with a known future observation asserts it is excluded from features built as of an earlier decision date. This test must exist and pass before any model tier below is implemented.

### 17 Chronological Evaluation Harness & Naive/Seasonal-Naive Baselines
**UI:** None.
**Logic:** `backend/backtesting/metrics.py` (MAE, RMSE, sMAPE, directional accuracy) and a first chronological train/validation/test split utility. `backend/forecasting/models/baseline.py` (Naive, Seasonal Naive), `forecasting/inference.py` minimal interface, `model_versions` table + migration, first two `model_versions` rows recorded with `benchmark_metrics`.
**Verification:** A script/pytest runs both baselines over the sample data's chronological split and prints/asserts metrics are recorded in `model_versions` — this is the mandatory floor every later tier must beat.

### 18 Statistical Model Tier (ARIMA/SARIMA, Exponential Smoothing)
**UI:** None.
**Logic:** `backend/forecasting/models/` statistical model file(s) using `statsmodels`, order/seasonal-term selection via the validation split (not fixed a priori), per `model.md`.
**Verification:** Benchmark run compares metrics against Feature 17's baseline under the same harness; result (win or lose) recorded in `model_versions.benchmark_metrics` regardless of outcome.

### 19 Gradient Boosting Tier (XGBoost, optional LightGBM comparison)
**UI:** None.
**Logic:** `backend/forecasting/models/xgboost_model.py` consuming the full feature set from Feature 16; hyperparameters tuned via the validation split and recorded in `model_versions.config_snapshot`. LightGBM run only as an internal comparison per `model.md`/`library-docs.md`, not a second production path.
**Verification:** Metrics recorded and compared against Statistical and Baseline tiers under the same harness; optional SHAP attribution smoke-tested on one trained model.

### 20 Neural Sequence Model Tier (LSTM/GRU)
**UI:** None.
**Logic:** `backend/forecasting/models/lstm_model.py` (PyTorch); sequence length selected via validation from {30, 60, 90, 180}; dropout/hidden size/layers tuned and recorded; same point-in-time feature construction reused, no shortcut window extending past the decision timestamp.
**Verification:** Metrics recorded under the same harness; explanation surfaced (per `model.md`) never claims feature-level causation for this model family.

### 21 Foundation Model Tier — TimesFM
**UI:** None.
**Logic:** `backend/forecasting/models/timesfm_model.py`; zero-shot evaluation first; domain adaptation/fine-tuning evaluated only if practical and explicitly compared against zero-shot, per `model.md`.
**Verification:** Zero-shot (and fine-tuned, if attempted) metrics recorded under the same harness against the same sample-data split.

### 22 Foundation Model Tier — Chronos-2
**UI:** None.
**Logic:** `backend/forecasting/models/chronos_model.py`; evaluated for both zero-shot probabilistic and covariate-informed forecasting per `model.md`.
**Verification:** Metrics recorded under the same harness; probabilistic output shape captured for use in Feature 24.

### 23 Model Comparison & Benchmark Reporting
**UI:** None (feeds Feature 40/43's UI later; this feature's own output is a reviewable artifact).
**Logic:** A comparison report (script/notebook in `notebooks/forecasting/` plus the authoritative `model_versions` rows) ranking every tier from Features 17–22 on MAE/RMSE/sMAPE/directional accuracy for the sample data. No tier is asserted superior without this evidence, per `model.md` Invariant 7 and `deliverables.md`'s explicit warning against assuming LSTM/foundation-model superiority.
**Verification:** The report/table is generated and readable; every tier's numbers trace to a real `model_versions.benchmark_metrics` entry, none fabricated.

### 24 Probabilistic Forecasting & Interval Calibration
**UI:** None.
**Logic:** `backend/forecasting/uncertainty.py`: P10/P50/P90, probability of increase/decrease, expected % change, volatility score — using each model's native probabilistic output where supported, or a documented method (quantile regression / residual-based intervals / ensemble spread) where not, per `model.md`. Empirical coverage/calibration of the P10–P90 interval evaluated against realized outcomes.
**Verification:** A calibration test asserts empirical coverage is computed and recorded; any model whose interval is unevaluated is explicitly flagged rather than presented as reliable.

### 25 Rolling-Origin (Walk-Forward) Backtesting
**UI:** None.
**Logic:** `backend/backtesting/rolling_backtest.py`: repeated re-evaluation as the origin date advances (per `model.md`'s illustrative rolling structure), re-applying `features/point_in_time.py` at every simulated date for every model tier from Features 17–22, not a single split.
**Verification:** Re-running the leading candidates under this harness reproduces results consistent with Feature 23's simple-split ranking (or documents where rolling evaluation changes the ranking); this is the required methodology gate — no tier is considered validated until it has passed through this feature.

### 26 Model Selection, Registry & Ensemble Evaluation
**UI:** None.
**Logic:** `backend/forecasting/registry.py`: selects the active model version per (route, vessel_class) scope based solely on Feature 25's rolling-backtest results and business usefulness, never architecture popularity, per `model.md`'s Selection Principle. An ensemble (per `model.md` tier 6) is constructed and evaluated only if ≥2 models independently perform well, with weights learned from validation — never manually assigned.
**Verification:** `model_versions.is_active` is set only via this registry logic, traceable to recorded benchmark results; if the simplest model (e.g., Naive or ARIMA) wins, that result is recorded and used, not hidden in favor of a more complex candidate.

### 27 Forecast Serving Integration (Backend)
**UI:** None.
**Logic:** `backend/api/schemas/` forecast request/response schemas; `backend/api/routers/forecast.py`: `GET /requirements/{id}/forecast?horizons=7,14,30,60` calling `forecasting/inference.py` (registry-selected model) + `uncertainty.py`, persisting `forecasts`/`forecast_distributions` via `forecast_repo.py`, per `architecture.md`'s Data Flow → Forecast Generation.
**Verification:** `TestClient` integration test requests a forecast for the seeded Australia→Paradip/Supramax combination and asserts a correctly-shaped response (point estimate, P10/P50/P90, probability of increase/decrease, model provenance) for each horizon.

### 28 Freight Forecast Page — Real Data Integration
**UI:** Feature 13's UI, now wired to Feature 27's real endpoint; `ForecastChart`/`ForecastSummaryStat`/`ModelComparisonChart`/`UncertaintyIndicator` all render real data; "forecast unavailable" Info alert shown for an unsupported route/vessel-class combination (never a generic error).
**Logic:** `frontend/lib/api-client/forecast.ts` (`getForecast()`), replacing Feature 13's mock data source.
**Verification:** Live horizon switching reflects real recomputed values; an intentionally unsupported route shows the Info-variant "no forecast available" state, not a crash or blank chart; loading skeleton shown during the real request.

---

## Phase 4 — Vessel & Port Feasibility

### 29 Port/Vessel Feasibility Page — UI Shell & Mock Data
**UI:** `VesselCandidateTable` (DWT/draft/LOA/beam columns + per-constraint `FeasibilityStatusBadge` + overall result), `VesselSpecPanel` (drill-in detail on row selection), `FeasibilityExplanation` (constraint-by-constraint reasoning list) — all with mock candidates including at least one Pass, one Fail, and one Unknown (dashed border, question icon) result.
**Logic:** `frontend/components/feasibility/` per `ui-registry.md`.
**Verification:** Selecting a table row opens the correct `VesselSpecPanel`; Unknown is visually and textually distinct from both Pass and Fail; table becomes horizontally scrollable with sticky first column below `md`.

### 30 Vessel/Port Reference Data Completion
**UI:** None.
**Logic:** Extend the `ports`/`vessel_classes`/`vessels` rows seeded in Feature 07 with real constraint-relevant values (`max_draft_m`, `max_loa_m`, `max_beam_m`, berth/handling fields on `ports`; `typical_dwt_min/max`, `typical_loa_m`, `typical_beam_m`, `typical_draft_m` on `vessel_classes`) for the initial scope's ports and vessel classes, leaving genuinely unknown fields `null` rather than guessed.
**Verification:** A repository-level test confirms every seeded port/vessel-class row has either a real value or an explicit `null` for each constraint field — no placeholder numbers presented as real data.

### 31 Vessel Feasibility Domain Logic
**UI:** None.
**Logic:** `backend/domain/vessel/`: explicit per-constraint evaluation (draft/LOA/beam/DWT) against a given requirement's port and candidate vessel classes, returning `pass`/`fail`/`unknown` (unknown when a constraint field is `null`, never silently defaulted). `vessel_feasibility_results` table + migration; `feasibility_repo.py`.
**Verification:** Unit tests cover: a vessel that passes all constraints, one that fails exactly one, and one evaluated against a port with a missing constraint field (must return `unknown` for that constraint, not `pass` or `fail`) — directly enforcing `project-overview.md`'s "never hard-coded or arbitrary" requirement.

### 32 Feasibility API Endpoint & Real Integration
**UI:** Feature 29's UI wired to real data; empty state ("No candidate vessels evaluated yet") shown before a requirement exists.
**Logic:** `backend/api/routers/feasibility.py`: `GET /requirements/{id}/feasibility`; `frontend/lib/api-client/feasibility.ts`.
**Verification:** Real requirement against the seeded Paradip/Supramax data returns the expected pass/fail/unknown mix; each status cell's accessible label announces with its column header (e.g., "Draft: Pass") per `ui-registry.md`'s accessibility contract.

---

## Phase 5 — Risk & Decision Support

### 33 Risk Page — UI Shell & Mock Data
**UI:** `RiskSummaryCard` [full] (overall badge + market/port/vessel/external category breakdown), `RiskFactorBreakdown` (per-factor table/list with badges), `DisruptionIndicatorList`, `UncertaintyIndicator` — mock data covering all three risk tiers.
**Logic:** `frontend/components/risk/` per `ui-registry.md`.
**Verification:** Category badges are individually labeled (not a color-coded row); visual QA against `ui-rules.md` → Data Visualization risk-shape redundancy rules.

### 34 Risk Domain Logic & Scoring
**UI:** None.
**Logic:** `backend/domain/risk/`: aggregates market risk (from Feature 24's volatility/uncertainty output), port risk (from Feature 30's congestion/turnaround fields), vessel risk (from `vessels.historical_utilization_pct`/availability where present), and external/disruption indicators limited to whatever `project-overview.md` confirms is actually available — anything not available is omitted and flagged as data-dependent, never fabricated. `risk_assessments` table + migration with a structured `explanation` jsonb, per `deliverables.md`'s explicit warning against arbitrary, uncalibrated risk scores.
**Verification:** Unit test traces a `risk_assessments.overall_risk_level` back to its contributing category scores and explanation entries — no score without an inspectable reason.

### 35 Risk API Endpoint & Real Integration
**UI:** Feature 33's UI wired to real data.
**Logic:** `backend/api/routers/risk.py`: `GET /requirements/{id}/risk`; `frontend/lib/api-client/risk.ts`.
**Verification:** Real requirement returns a risk assessment whose category breakdown is visible and consistent with Feature 34's explanation payload.

### 36 Charter Timing Domain Logic & Dashboard Wiring
**UI:** Feature 12's `CharterTimingIndicator` on the Decision Dashboard, now driven by real logic instead of mock.
**Logic:** `backend/domain/charter/`: converts the forecast + uncertainty output (Feature 27) into "charter now" vs. "wait/monitor" per `model.md`'s Decision Engine Interface consumption pattern — this module has no knowledge of vessels, contracts, or risk beyond the forecast it consumes.
**Verification:** Unit tests with a clearly-rising, clearly-falling, and ambiguous forecast scenario each produce the expected timing decision with a traceable reason.

### 37 Contract Strategy Comparison Domain Logic
**UI:** Feature 12's `ContractStrategyComparison` on the Decision Dashboard, now driven by real logic.
**Logic:** `backend/domain/contracts/` + `backend/optimization/contract_optimizer.py` (OR-Tools for the combinatorial strategy comparison, `scipy.optimize` only if a continuous sub-problem needs it, per `library-docs.md`): compares spot / short-term / medium-term using the forecast (Feature 27) and feasibility (Feature 32) outputs. `contract_strategies` table + migration; `expected_expenditure_usd`, `risk_level`, `flexibility_score` populated; `backtested_estimated_savings_usd` left `null` — Phase 6 has not run yet, so `SavingsEstimate` renders its `unavailable` ("insufficient backtest data") state rather than a fabricated figure.
**Verification:** Unit test confirms no strategy is favored merely for a lower expected rate without flexibility/uncertainty weighed in, per `project-overview.md`; `SavingsEstimate` correctly shows "unavailable," never a blank or zero figure.

### 38 Recommendation Assembly & Explainability
**UI:** None directly (assembles the object Feature 39 renders).
**Logic:** `backend/domain/recommendation/`: combines Feature 36 (timing) + Feature 32 (feasibility/vessel) + Feature 37 (contract) + Feature 34 (risk) into a `Recommendation`, with an ordered `reasons` array (most significant factor first) per the explainability example in `project-overview.md`. `recommendations` table + migration; `recommendation_repo.py`. Evidence for reasons follows `model.md` → Explainability (SHAP-based only for tree-based models; general evidence otherwise — never fabricated feature-level causation).
**Verification:** Unit test asserts a `Recommendation` is never producible without a non-empty `reasons` array, and that reasons reference real upstream factors (forecast direction, feasibility result, risk category), not placeholder text.

### 39 Recommendation API Endpoint & Decision Dashboard Real Integration
**UI:** Feature 12's full `RecommendationSummaryCard` now wired end-to-end to real data; `SavingsEstimate` shows the "insufficient backtest data" state until Phase 6/7 completes.
**Logic:** `backend/api/routers/recommendation.py`: `GET /requirements/{id}/recommendation` (triggers assembly if not already computed); `frontend/lib/api-client/recommendation.ts`.
**Verification:** The example scenario from `frontend and user flow.md` produces a recommendation whose shape matches that document's example output structure (timing, vessel, contract, risk, reasoning) with real, traceable values; loading/error states confirmed.

---

## Phase 6 — Backtesting & Model Performance

### 40 Backtesting/Model Performance Page — UI Shell & Mock Data
**UI:** `MetricsTable` (MAE/RMSE/sMAPE/directional accuracy per model/horizon), `ModelComparisonChart` (shared with Forecast), `BacktestHistoryChart`, `EconomicSimulationSummary` (composing `SavingsEstimate`), `ContractStrategyComparison` [historical view] — mock data reflecting realistic ranges.
**Logic:** `frontend/components/backtesting/` per `ui-registry.md`.
**Verification:** Dense compact-density table variant renders correctly per `ui-rules.md`; every economic figure carries its "backtested/simulated estimate" qualifier.

### 41 Backtest Run Orchestration (Celery + Rolling Backtest Execution)
**UI:** None.
**Logic:** `backend/jobs/backtesting_tasks.py` (Celery task) triggers `backend/backtesting/rolling_backtest.py` across historical decision dates for a given model/route/vessel-class scope, calling `domain/` at each simulated date to produce the recommendation that *would have been made then*, using only point-in-time-safe data (Feature 16's gate) — never live/current data. `backtest_runs` table + migration tracks `status`.
**Verification:** Triggering the task via a management command/test enqueue moves `backtest_runs.status` from `running` to `completed`; a pytest confirms no simulated decision date used an observation dated after it.

### 42 Economic Simulation & Baseline Comparison
**UI:** None.
**Logic:** `backend/backtesting/economic_simulation.py`: simulates the four baseline strategies from `model.md` (spot-only, simple fixed, forecast-based, forecast+risk-aware) against the system's own historical recommendations; `backtest_results` table + migration populated with `mae`/`rmse`/`smape`/`directional_accuracy`/`simulated_outcome_usd`/`baseline_outcome_usd`/`estimated_savings_usd` per decision date.
**Verification:** Unit test confirms `estimated_savings_usd` is only ever computed relative to a named baseline and never asserted as a guarantee anywhere in the persisted record or its serialization.

### 43 Backtesting API Endpoints & Real Integration
**UI:** Feature 40's UI wired to real data; `SavingsEstimate`/`EconomicSimulationSummary` show real backtested figures with the qualifier intact.
**Logic:** `backend/api/routers/backtesting.py`: `GET /backtests`, `GET /backtests/{id}/results`; `frontend/lib/api-client/backtesting.ts`. Also backfills `contract_strategies.backtested_estimated_savings_usd` (per route/vessel-class/strategy scope) from these results so Phase 5's Decision Dashboard has real data to consume in Phase 7.
**Verification:** The Backtesting page renders real MAE/RMSE/sMAPE/directional accuracy and simulated-vs-baseline economics for at least one completed backtest run; every model tier from Phase 3 that was benchmarked appears in `ModelComparisonChart`, including any simpler model that won.

---

## Phase 7 — End-to-End Integration

### 44 Post-Requirement Orchestration Pipeline
**UI:** Decision Dashboard shows a single coherent loading sequence (skeletons across the recommendation card and compact forecast chart) rather than independently-loading fragments.
**Logic:** On requirement submission, orchestrate forecast (27) → feasibility (32) → risk (35) → recommendation (39) generation as one pipeline call from `backend/api/routers/requirements.py` (or a dedicated orchestration function in `domain/recommendation/`), matching `architecture.md`'s Data Flow → Recommendation Generation. Given SIH prototype scale this may be a synchronous chained call; if any step is slow enough to matter, it is dispatched via Celery with a status the frontend can poll.
**Verification:** Submitting the example requirement from a clean requirement produces a fully-populated Decision Dashboard without the user needing to manually trigger each supporting page first.

### 45 Decision Dashboard SavingsEstimate — Real Backtested Data Wiring
**UI:** `SavingsEstimate` on the Decision Dashboard now reflects Feature 43's real backtested figures instead of the "unavailable" placeholder, once a backtest run covering the relevant route/vessel-class/strategy exists.
**Logic:** `recommendation.ts`/`contracts` read path updated to include `backtested_estimated_savings_usd` where present; falls back to "unavailable" gracefully where a backtest hasn't been run for that specific scope.
**Verification:** For a route/vessel-class with a completed backtest, the real figure and qualifier render; for one without, the honest "insufficient backtest data" state still renders — never a guessed number.

### 46 Cross-Page Navigation & Requirement Context Persistence
**UI:** Moving from the Decision Dashboard to Freight Forecast, Feasibility, Risk, or Backtesting preserves the active `requirement_id`/route/vessel-class context, per `project-overview.md`'s Navigation section (drill-down without losing context).
**Logic:** Shared requirement context (route param or lightweight shared state) read by all five page routes.
**Verification:** Starting from a submitted requirement, navigating to each of the four supporting pages shows data scoped to that same requirement's route/vessel-class without re-entering anything.

### 47 Full End-to-End Workflow Verification
**UI:** The complete flow, exercised as one path.
**Logic:** No new code — this is an integration checkpoint.
**Verification:** Execute the exact example from `frontend and user flow.md` (Coal, 50,000 MT, Australia→Paradip, 15–25 Sep, 3 voyages, 6 months) end-to-end and confirm each of its 11 documented steps produces a real, non-mock result: historical retrieval, market variables, point-in-time check, feature construction, forecast run, forecast output shape, feasible vessels, vessel economics/idle-risk input to contract comparison, spot-vs-multi-voyage comparison, final recommendation, and displayed reasoning/confidence.

---

## Phase 8 — Validation & Demo Readiness

### 48 Data-Quality & Edge-Case Handling Pass
**UI:** Every page's edge-case state, exercised deliberately: unsupported route/vessel-class → Freight Forecast's Info "forecast unavailable" alert; missing port constraint → Feasibility's Unknown badge; no backtest yet for a scope → Decision Dashboard's `SavingsEstimate` unavailable state; no requirement yet → each page's `EmptyState`.
**Logic:** Any gaps found are fixed in the owning feature's module (not patched with page-level special-casing).
**Verification:** A written checklist confirms all five pages handle their documented empty/unavailable conditions per `ui-rules.md` → Loading & Error States, with no unhandled blank screen.

### 49 Error-State & Resilience Testing
**UI:** `ErrorAlert` with retry, across all five pages, under simulated failure.
**Logic:** Manually/automatedly induce a DB outage, a stopped Celery worker, and a forced 500 from one router; confirm the shared `ApiError` shape reaches the frontend intact in each case.
**Verification:** Each induced failure produces the correct `ErrorAlert` variant and a working "Retry" action once the underlying service is restored — never a raw stack trace or an unhandled crash.

### 50 Accessibility & Responsive QA Pass
**UI:** All five pages, all breakpoints (`sm`/`md`/`lg`/`xl`/`2xl`).
**Logic:** No new code expected beyond fixes surfaced by the audit.
**Verification:** Keyboard-only pass through every primary workflow (per `ui-rules.md` → Accessibility); contrast spot-checks against the 4.5:1/3:1 minimums in both themes; every chart confirmed to have an accessible data-table/summary fallback; screen-reader pass on Badge/status components confirms label is announced.

### 51 Performance & Load Sanity Check
**UI:** Chart and table responsiveness under realistic data volume.
**Logic:** Load the full sample historical series into `ForecastChart`/`BacktestHistoryChart` and the densest `MetricsTable`/`VesselCandidateTable` configurations; check API response times for the recommendation-pipeline endpoints.
**Verification:** No janky chart re-render or multi-second table load at the realistic demo data volume; any real bottleneck found is profiled before any optimization is applied, per `code-standards.md` → Performance (no premature optimization).

### 52 Demo Script & Judge-Facing Walkthrough Preparation
**UI:** The same five pages, presented in a rehearsed order.
**Logic:** A documented demo script walking Decision Dashboard → Freight Forecast → Feasibility → Risk → Backtesting for the example scenario, deliberately spending time on the Backtesting page's technical-credibility evidence per `frontend and user flow.md`'s note. One-command `docker-compose up` startup re-verified from a clean checkout.
**Verification:** A full dry run of the demo script, from clean environment startup to final recommendation and backtested-savings display, completes without manual workarounds.

---

## Feature Count

| Phase | Feature Count | Purpose |
|---|---:|---|
| Phase 1 | 7 | Application, database, and shared-component foundation; first real full-stack round trip |
| Phase 2 | 5 | Procurement requirement flow and Decision Dashboard UI (mock recommendation) |
| Phase 3 | 16 | Freight Forecast UI, data pipeline, full model benchmark hierarchy, probabilistic forecasting, rolling backtesting, forecast serving |
| Phase 4 | 4 | Vessel/port feasibility data, constraint logic, and UI integration |
| Phase 5 | 7 | Risk scoring, charter timing, contract strategy, recommendation assembly, and Decision Dashboard real integration |
| Phase 6 | 4 | Rolling backtest execution, economic simulation, and Backtesting page real integration |
| Phase 7 | 4 | End-to-end orchestration, real savings wiring, cross-page context, full workflow verification |
| Phase 8 | 5 | Edge cases, resilience, accessibility, performance, and demo readiness |
| **Total** | **52** | |

---

## Critical Dependencies

- Phase 1's shared component library (04) and reference-data API (07) are consumed by every later page — no page-specific component is built before its registry primitives exist.
- Phase 3's point-in-time feature gate (16) must exist and pass its leakage test before any model tier (17–22) is implemented; no model is trained on ungated features at any point.
- Phase 3's baseline (17) must exist before any advanced tier (18–22) is benchmarked, and every tier is compared against it — no tier skips straight to being "the" model.
- Phase 3's rolling-origin backtesting (25) must complete, and Phase 3's registry-driven selection (26) must run, before Phase 3's forecast-serving integration (27) exposes a model to the rest of the system.
- Phase 3 (forecasting) and Phase 4 (feasibility) must both be real before Phase 5's charter timing (36), contract strategy (37), and recommendation assembly (38) — recommendation logic never bypasses forecasting or feasibility.
- Phase 5's contract strategy (37) intentionally ships without real backtested savings; Phase 6's economic simulation (42) must complete before Phase 7's savings wiring (45) — no savings figure is ever displayed before its backtest has actually run.
- Phase 7 (44–47) requires Phases 2–6 to already be individually real and working; it only connects and verifies, it does not introduce new business logic.
- Phase 8 requires Phase 7's full path to be real end-to-end — edge-case, resilience, and demo passes are meaningless against a still-mocked flow.

---

## Definition of Done

A feature is complete only when:

- Its UI (if user-facing) exists and matches `ui-tokens.md`, `ui-rules.md`, and `ui-registry.md`.
- It uses mock data only where explicitly scheduled to, and real data everywhere its dependency chain has already delivered real data.
- Its required logic (domain, forecasting, data-access, or infrastructure) works as specified in `architecture.md`, `model.md`, and `code-standards.md`.
- Loading, empty, error, and unavailable states all work as specified — not only the success path.
- Its stated verification step has actually been run and passed, not merely described.
- It follows `architecture.md`'s layer boundaries and `code-standards.md`'s conventions without introducing a parallel pattern.
- Any new or modified reusable component is reflected in `ui-registry.md`'s inventory and contracts in the same change.
- No future information has entered any historical training, feature, or backtest step it touches, and no savings/performance claim is made without a completed backtest behind it.
