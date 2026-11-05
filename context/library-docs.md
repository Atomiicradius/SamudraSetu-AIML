# Library Documentation

## Purpose

This file is the single source of truth for which libraries, frameworks, and tools this project uses to solve a given problem. It exists so that every team member and AI coding agent reaches for the same dependency when the same kind of problem comes up, instead of independently picking whichever library they personally know.

An AI coding agent must consult this file before adding any import that is not already used elsewhere in the codebase. If the needed capability maps to an "Approved Usage" row below, use that library the way this file describes. If the capability maps to a row marked "Decision Pending," do not silently pick a library to fill the gap — implement the minimal solution possible within already-approved libraries, or flag the gap explicitly (e.g., in a PR description or a `TODO` naming the missing decision) rather than introducing an unreviewed dependency. If no row covers the need at all, follow the Dependency Selection process below before adding anything.

This file does not redefine system architecture (`architecture.md`), coding conventions (`code-standards.md`), ML methodology (`model.md`), or visual design (`ui-tokens.md`/`ui-rules.md`/`ui-registry.md`). It only governs *which library* is used for a given job and *how* it is approved to be used.

---

## Frontend Libraries

| Library | Purpose | Approved Usage | Notes |
|---|---|---|---|
| Next.js | Application framework, routing, rendering | All five pages (`app/dashboard`, `app/forecast`, `app/feasibility`, `app/risk`, `app/backtesting`) are Next.js routes. Server Components are the default; `"use client"` only where interactivity/browser APIs are required, per `code-standards.md`. | The only frontend application framework in this project — no parallel routing/rendering framework is introduced. |
| React | UI rendering library | Used only through Next.js; components follow the structure and reuse rules in `ui-registry.md`. | Version tracks whatever Next.js's current stable release requires — not pinned independently. |
| TypeScript | Static typing for all frontend code | `strict` mode on, per `code-standards.md`. Every `.tsx`/`.ts` file in `frontend/` is TypeScript; no plain `.jsx`/`.js` application files. | Compiler (`tsc`) is also the type-checking tool — see Development & Tooling. |
| Tailwind CSS | Styling / layout implementation | Implements the tokens and layout rules defined in `ui-tokens.md`/`ui-rules.md` (spacing scale, breakpoints, colors) via a Tailwind config mapped to those semantic tokens — components never hard-code raw Tailwind color/spacing utilities that bypass the token mapping. | Established in `architecture.md`. No competing CSS-in-JS or component-styling library is introduced alongside it. |
| Recharts | Primary charting library | Default choice for all charts: `ForecastChart`, `ModelComparisonChart`, `BacktestHistoryChart`, and any other chart in `ui-registry.md`'s inventory, implementing the line/dash/band conventions from `ui-rules.md` → Data Visualization. | Established in `architecture.md` as primary. |
| Plotly | Secondary charting library, conditional use | Used only where a specific chart requires statistical chart types or interactions Recharts cannot reasonably support (e.g., a dense multi-axis or highly customized statistical plot on Backtesting/Risk). This must be a deliberate exception per chart, not a default. | Established in `architecture.md` as the named fallback. This is the one place the project intentionally keeps two libraries for the same general purpose (charts); do not add a third. |
| Jest + React Testing Library | Frontend unit/component testing | Component tests per `code-standards.md` → Testing Standards (state coverage: loading/empty/error/populated; accessibility assertions for icon+label+color). | Established in `architecture.md`. |

**Not currently approved (Decision Pending):**

| Category | Status | Notes |
|---|---|---|
| Form/validation library | Decision Pending | No library (e.g., `react-hook-form`, `zod`) is established in `architecture.md`. Until decided, forms (`RequirementForm` and its fields, per `ui-registry.md`) are built with plain React state and manual validation logic per `code-standards.md`'s validation rules. Do not introduce a form/validation library unilaterally — see Dependency Selection. |
| Data-fetching/state-management library | Not needed / Decision Pending if scope grows | `architecture.md`'s Client Pattern (`frontend/lib/api-client/`) plus Server Components and local component state (per `code-standards.md`) currently cover all data needs. Do not add `SWR`, `React Query`, `Redux`, `Zustand`, or similar without a demonstrated need (e.g., complex client-side cache invalidation that props/server-fetching cannot reasonably handle). |
| Icon set | Decision Pending | `ui-rules.md`/`ui-registry.md` require a consistent icon (check-circle, triangle, octagon, x-circle, etc.) for every Badge/Alert. A single SVG icon library must be chosen before these components are built broadly — do not let individual components pull icons from different sources. |
| Date/date-range picker | Decision Pending | The Loading Window field (`DateRangeInput`, per `ui-registry.md`) needs a bounded start/end date picker. No library is established; build the minimal version needed or resolve this decision before implementing the field broadly. |
| UI primitive/component library (e.g., Radix, shadcn/ui) | Not used | This project's component system is the bespoke registry defined in `ui-registry.md`, built on Tailwind directly. Do not introduce a third-party component library whose default styling would need to be overridden to match `ui-tokens.md` — build registry components directly. |

---

## Backend Libraries

| Library | Purpose | Approved Usage | Notes |
|---|---|---|---|
| FastAPI | HTTP API framework | The only framework in `backend/api/` — routers, dependency injection, request/response handling, per `architecture.md` and `code-standards.md` → FastAPI Standards. | Established in `architecture.md`. |
| Pydantic | Request/response schema validation, settings modeling | All `backend/api/schemas/` request/response models. Also the basis for typed configuration loading (see `pydantic-settings` below). | FastAPI's current stable releases default to Pydantic 2.x — write schemas using Pydantic v2 idioms (`model_config`, `model_dump()`, etc.), not v1-style patterns, unless a specific compatibility constraint forces otherwise. |
| pydantic-settings | Typed environment/config loading | `backend/config/settings.py`'s environment-variable loader, per `architecture.md`. | Minimal addition on top of Pydantic (same maintainer, same validation model) — not a separate configuration paradigm. |
| SQLAlchemy | ORM / database access layer | The only ORM. `backend/data_access/models.py` (table definitions) and `backend/data_access/repositories/*` (query methods), per `architecture.md`. No other layer issues ORM or raw SQL queries. | Sync vs. async engine/session style (`sqlalchemy` sync vs. `sqlalchemy[asyncio]` + `asyncpg`) is **Decision Pending** — pick one consistently across `data_access/` once decided; do not mix sync and async session patterns in the same layer. |
| Alembic | Database migrations | All schema changes to the tables defined in `architecture.md`'s Database Schema section go through an Alembic migration, per `code-standards.md` → Database Standards. | Standard companion to SQLAlchemy; no schema change is applied by hand against a running database. |
| psycopg (or asyncpg) | PostgreSQL driver | Underlying driver used by SQLAlchemy to connect to PostgreSQL/TimescaleDB. | Exact driver package and version is **Decision Pending**, dependent on the sync/async SQLAlchemy decision above. |
| TimescaleDB (Postgres extension) | Time-series storage optimization for `freight_observations`/`market_observations` | Enabled only if/when observation volume and query patterns justify it, per `architecture.md`. Until then, plain PostgreSQL tables are sufficient — do not add Timescale-specific schema features (hypertables, continuous aggregates) speculatively. | Not a separate client library — it changes how existing PostgreSQL tables are declared/queried, still through SQLAlchemy/`data_access/`. |
| Redis (`redis`/`redis-py`) | Celery broker/result backend; optional short-lived read cache | Configured as Celery's broker and result backend per `architecture.md`. Direct cache reads/writes (for expensive computed results, e.g., backtest summaries) go through a thin wrapper in `data_access/` or `backend/config/`, never scattered raw `redis.Redis()` calls across the codebase. | One Redis client library, one connection configuration path. |
| Celery | Background job execution | All long-running work — ingestion, training, backtesting (`backend/jobs/*`) — per `architecture.md`. API routes enqueue tasks and return immediately; they never run this work synchronously in-process. | Established in `architecture.md`. |
| pytest | Backend and ML testing | All tests under `backend/tests/`, per `code-standards.md` → Testing Standards. | Established in `architecture.md`. |
| httpx / FastAPI `TestClient` | API integration testing | Used to exercise `backend/api/` routes end-to-end in tests (request → response shape → status code), per `code-standards.md` → Testing Standards. | This is FastAPI's own recommended testing mechanism (built on Starlette's test client), not a separately introduced HTTP client — see Prohibited Alternatives regarding HTTP clients elsewhere in the backend. |
| PyYAML | Reading `backend/config/model_config.yaml` | The only mechanism for loading the centralized model configuration file described in `architecture.md` and `model.md`. | Do not parse YAML with a second library; do not replace the YAML config with JSON/TOML without an explicit architectural decision. |

---

## ML & Data Libraries

Per `model.md`, model selection itself is empirical and benchmark-driven — this section documents which *libraries* implement each benchmark tier already defined there; it does not restate or alter that methodology.

| Library | Purpose | Category | Approved Usage | Notes |
|---|---|---|---|---|
| pandas | Tabular data manipulation | Core | Used throughout `backend/preprocessing/`, `backend/features/`, `backend/backtesting/` for cleaning, feature construction, and result aggregation. | Established in `architecture.md`. |
| NumPy | Numerical arrays/operations | Core | Underlies pandas and feeds array-based model inputs (tree-based, neural, foundation models). | Established in `architecture.md`. |
| Polars | High-performance dataframe alternative | Optional | Only introduced for a specific `backend/preprocessing/`/`backend/features/` operation demonstrated to be a pandas performance bottleneck at real data volume, per `architecture.md` and `code-standards.md` → Performance. | Not used by default; do not adopt it project-wide speculatively. |
| statsmodels | ARIMA/SARIMA, Exponential Smoothing | Model-specific (Statistical tier) | Implements the Statistical benchmark tier in `model.md` (`backend/forecasting/models/`). | The standard Python library for this tier; not named explicitly in `architecture.md`'s stack table but required to implement `model.md`'s mandated Statistical tier. |
| scikit-learn | Baselines, preprocessing utilities, classical ML helpers, quantile/residual-based interval methods | Core | Naive/seasonal-naive baseline helpers, feature preprocessing utilities, and — where a model family lacks native probabilistic output — a documented interval-estimation method per `model.md`'s calibration requirement. | Established in `architecture.md`. |
| XGBoost | Gradient boosting (primary candidate) | Model-specific (Gradient Boosting tier) | Implements the primary Gradient Boosting benchmark tier candidate in `model.md`. | Established in `architecture.md` as the primary candidate — not asserted as superior to other tiers without the benchmarking `model.md` requires. |
| LightGBM | Gradient boosting (comparison/speed) | Model-specific, optional | Used only as an internal benchmarking comparison against XGBoost per `model.md` ("where useful as a comparison or for speed") — not treated as a second parallel production path unless it demonstrably wins the benchmark. | Optional per `model.md`; do not ship both as interchangeable "current model" options without a benchmark-driven decision recorded per `model_versions`. |
| SHAP | Explainability for tree-based models | Evaluation/explainability only | Used only to attribute XGBoost/LightGBM predictions, per `model.md` → Explainability. Never used to claim feature-level causation for neural/foundation models. | Established by `model.md`'s explicit mention. |
| PyTorch | Neural sequence models (LSTM/GRU); underlying framework for foundation models | Model-specific (Neural tier) + framework dependency | Implements the Neural benchmark tier in `model.md`, and is also the runtime most foundation-model packages (TimesFM/Chronos-2) build on. | Established in `architecture.md`. |
| TimesFM | Foundation-model forecasting (zero-shot and adapted) | Model-specific (Foundation Models tier) | Implements the TimesFM path of the Foundation Models benchmark tier in `model.md`, evaluated zero-shot first per that document. | Package name/version pinned to whatever release is compatible with the project's chosen PyTorch/Python versions — see Versioning. |
| Chronos-2 | Foundation-model forecasting (probabilistic, covariate-informed) | Model-specific (Foundation Models tier) | Implements the Chronos-2 path of the Foundation Models benchmark tier in `model.md`. | Same version-compatibility note as TimesFM. |
| scipy | Continuous numerical optimization; general scientific computing | Optimization/evaluation | `scipy.optimize` used in `backend/optimization/contract_optimizer.py` for continuous optimization problems (e.g., parameter fitting, calibration), per `architecture.md`. | Established in `architecture.md`. |
| OR-Tools | Combinatorial/constraint optimization | Optimization only | Used in `backend/optimization/contract_optimizer.py` for discrete/constraint-satisfaction problems (e.g., combinatorial contract-strategy comparisons), per `architecture.md`. | `scipy.optimize` and OR-Tools solve different problem shapes within `contract_optimizer.py` (continuous vs. combinatorial) — this is not a duplicate-library situation; do not use both for the same sub-problem. |

No claim is made in this file, or to be made in any implementation, that one model family (statistical, gradient boosting, neural, or foundation model) is inherently superior — per `model.md`'s Invariant 7, that is determined solely by this project's own out-of-sample benchmarking.

---

## Development & Tooling

| Tool | Purpose | Standard Usage |
|---|---|---|
| npm | Frontend package management | `frontend/package.json` + lockfile; the only frontend package manager (no mixing with yarn/pnpm in the same project). |
| pip + `requirements.txt`/`pyproject.toml` | Backend package management | `backend/requirements.txt` and `backend/pyproject.toml`, per `architecture.md`. |
| ESLint | Frontend linting | Standard Next.js/TypeScript ESLint configuration; run in CI and locally before commit. |
| black | Backend formatting | Enforced per `code-standards.md`; run via pre-commit hook/CI, not manual formatting. |
| isort (or Ruff's equivalent) | Backend import ordering | Enforced per `code-standards.md`. |
| Ruff (optional consolidation) | Backend linting | May be adopted to consolidate linting/import-sorting into one tool; if adopted, it replaces the separate lint tool it subsumes rather than running alongside it — see Prohibited Alternatives. |
| TypeScript compiler (`tsc`) | Frontend type checking | `strict` mode, run in CI; no merge with type errors. |
| mypy (or pyright) | Backend type checking | Checks the type hints required by `code-standards.md` → Python Standards; run in CI. |
| pytest | Backend/ML testing | See Backend Libraries and ML & Data Libraries tables. |
| Jest + React Testing Library | Frontend testing | See Frontend Libraries table. |
| Docker + docker-compose | Local development and deployment containers | `docker/frontend.Dockerfile`, `docker/backend.Dockerfile`, `docker/worker.Dockerfile`, `docker/docker-compose.yml`, per `architecture.md`. This is the only supported way to run the full stack locally. |
| pydantic-settings + `.env` files | Environment/configuration tooling | Backend environment variables loaded via `backend/config/settings.py`; `.env.example` documents required variables per `code-standards.md` → Configuration & Secrets. |
| Next.js built-in env handling | Frontend environment/configuration tooling | `NEXT_PUBLIC_*` variables only for values safe to expose to the browser, per `code-standards.md`. |
| Alembic | Database migration tooling | See Backend Libraries table. |

---

## Usage Rules

- **Where each library may be used** is fixed by `architecture.md`'s layer ownership: a library approved for `backend/forecasting/` (PyTorch, TimesFM, Chronos-2, statsmodels) is never imported into `backend/api/` or `backend/domain/` directly — those layers consume forecasting outputs only through `forecasting/inference.py`'s structured interface. A library approved for `backend/data_access/` (SQLAlchemy) is never imported into `backend/domain/`, `backend/forecasting/`, or `frontend/`.
- **Which architectural layer owns it**: each library in the tables above belongs to exactly one layer per `architecture.md`'s System Boundaries table. If a capability seems to require crossing a layer to use a library directly (e.g., a route wanting to run a pandas transformation itself), the correct fix is to move that logic into the owning layer and call it, not to import the library into the wrong layer.
- **Direct usage vs. wrapping**: `frontend/` never calls `fetch` directly outside `frontend/lib/api-client/` — all HTTP calls are wrapped there. `backend/` never issues raw SQL/ORM calls outside `backend/data_access/repositories/` — all DB access is wrapped there. Redis is accessed directly only through Celery's own broker/backend configuration or a single thin cache-access helper — not scattered raw client calls. ML libraries are used directly only inside `backend/forecasting/models/*`, behind the uniform interface `forecasting/inference.py` exposes to callers.
- **Configuration**: library-level configuration (DB connection strings, Redis URL, model hyperparameters, forecast horizons) is never hard-coded next to a library call. Backend infra config comes from `backend/config/settings.py` (environment-driven); model/domain parameters come from `backend/config/model_config.yaml`, per `architecture.md` and `code-standards.md`.
- **Error handling**: a library's native exceptions are caught at the boundary of the layer that owns it and translated into this project's own typed exceptions/response shapes (e.g., a SQLAlchemy error becomes a repository-level typed exception; a FastAPI/Pydantic validation error becomes the shared `ApiError` response) — raw third-party exceptions/stack traces are never returned to the frontend or another layer, per `code-standards.md` → Error Handling & Logging.
- **Version management**: see Versioning below. In short — pin what's already pinned, don't casually bump majors, and record any compatibility-driven version choice (e.g., a PyTorch version required by TimesFM/Chronos-2) as a documented constraint, not a silent pin.

---

## Dependency Selection

Before adding any dependency not already listed in this file, the implementer (human or AI agent) must consider and be able to answer:

1. **Existing project capability** — can an already-approved library in this file solve the problem? If yes, use it; a new dependency is not justified merely because it's a slightly better fit.
2. **Maintenance/activity** — is the candidate actively maintained (recent releases, responsive issue tracker), or effectively abandoned?
3. **Compatibility** — does it work with the pinned/expected versions of Python, Node, FastAPI, Pydantic, PyTorch, etc. already in use, without forcing an unwanted upgrade elsewhere?
4. **Security** — does it have known unpatched critical vulnerabilities? Is its dependency tree reasonable?
5. **Bundle/runtime cost** — for frontend: does it meaningfully increase bundle size for the value it provides? For backend/ML: does it add meaningful startup time, memory, or install complexity (this matters especially for ML packages with heavy native dependencies)?
6. **Complexity** — does it introduce a new mental model/paradigm the team has to learn, or does it fit naturally alongside what's already used?
7. **Licensing** — is the license compatible with this project's use (permissive open-source; avoid anything with restrictive/viral terms inappropriate for an enterprise deliverable)?
8. **Long-term maintainability** — will this still be a sensible choice a year from now, or is it solving today's problem in a way that creates tomorrow's cleanup work?

A dependency that cannot be justified against these points is not added. When a new dependency is approved, it is added to this file (correct table, with Purpose/Approved Usage/Notes filled in) in the same change that introduces it — it is never added to `requirements.txt`/`package.json` silently.

---

## Prohibited Alternatives

- Do not use more than one charting library beyond the two already sanctioned by `architecture.md` (Recharts primary, Plotly for specific unsupported chart types). No D3-from-scratch, no Chart.js, no Highcharts.
- Do not introduce a second ORM or a raw-SQL data-access pattern alongside SQLAlchemy. All database access is SQLAlchemy through `backend/data_access/`.
- Do not introduce a second HTTP client library on the frontend (e.g., axios) alongside the native `fetch`-based `frontend/lib/api-client/` wrapper.
- Do not introduce a second background-job/queue system (e.g., RQ, Dramatiq, arq) alongside Celery + Redis.
- Do not introduce more than one schema-validation library on the backend — Pydantic is the only validation layer for API contracts and settings.
- Do not introduce more than one frontend state-management pattern — Server Components, props, and local component state are the standard until/unless a data-fetching library is explicitly approved (see Frontend Libraries → Decision Pending).
- Do not introduce a second gradient-boosting library as a parallel "default" production path — LightGBM exists only as a benchmarking comparison to XGBoost per `model.md`, not a second shipped option chosen ad hoc per route.
- Do not introduce a second migration tool alongside Alembic, and do not apply schema changes by hand outside the migration system.
- Do not introduce a UI component library/design-system package (Radix, MUI, Chakra, shadcn/ui, Ant Design) — the bespoke registry in `ui-registry.md` is the only component system.

---

## Integration Notes

- **Next.js ↔ FastAPI**: the two are fully decoupled processes communicating over HTTP via the typed client in `frontend/lib/api-client/`, per `architecture.md` → Client Pattern. Next.js never imports Python code or vice versa; there is no server-side "API route in Next.js" layer duplicating FastAPI's responsibilities.
- **FastAPI ↔ Pydantic**: request/response schemas in `backend/api/schemas/` are the API contract. A schema change must be mirrored in `frontend/types/` in the same change, per `code-standards.md` → API & Data Contracts.
- **FastAPI ↔ database**: FastAPI routes never hold a raw DB connection or session directly beyond what `backend/api/deps.py` injects (a SQLAlchemy session), and only pass it to `backend/data_access/repositories/` — never used to build ad hoc queries inside the route.
- **Celery ↔ Redis**: Redis is configured once as both broker and result backend for Celery, per `architecture.md`; task definitions (`backend/jobs/*`) do not need to know Redis-specific details beyond what Celery's app configuration already provides.
- **ML libraries ↔ Python environment**: PyTorch, TimesFM, and Chronos-2 typically require specific, mutually compatible Python/PyTorch/CUDA (if GPU is used) version combinations. These constraints must be resolved together — pick a Python version that satisfies all three simultaneously rather than upgrading one in isolation. Document the resolved constraint set once decided (see Versioning).
- **Forecasting models ↔ backtesting pipeline**: every model family (`backend/forecasting/models/*`) is called only through `forecasting/inference.py`'s uniform interface from `backend/backtesting/rolling_backtest.py`, per `model.md` and `architecture.md` — backtesting code never imports a specific model library (e.g., `torch`, `xgboost`) directly.
- **Charts ↔ backend forecast response schemas**: `ForecastChart`/`ModelComparisonChart`/`BacktestHistoryChart` consume data already shaped to the chart's needs (pre-aligned series, per `ui-registry.md`'s `ForecastChart` contract) from the typed API response — chart components never reshape raw `Forecast`/`ForecastDistribution` API objects themselves; that alignment is a data-layer concern per `code-standards.md` → Performance.

---

## Versioning

- No exact package versions are invented in this file beyond what is already implied by compatibility necessity (e.g., "Pydantic 2.x, matching FastAPI's current default"). Where architecture.md and model.md do not specify a version, versions are pinned in `requirements.txt`/`pyproject.toml` (backend) and `package.json`'s lockfile (frontend) at implementation time and treated as the recorded decision from that point forward.
- All dependencies are pinned to a specific version or a narrow compatible range — never left floating — so builds are reproducible, per `code-standards.md` → Dependencies.
- Upgrading a **major** version of any library in this file (Next.js, React, FastAPI, Pydantic, SQLAlchemy, PyTorch, etc.) requires explicit justification (what breaks without it, what the migration involves) and is done as its own reviewed change — never bundled silently into an unrelated feature change.
- ML foundation-model packages (TimesFM, Chronos-2) and their PyTorch dependency are versioned together as a compatibility set; changing one requires re-verifying the others.
- Python and Node runtime version floors are **Decision Pending** — to be fixed once the ML dependency set's minimum requirements (PyTorch/TimesFM/Chronos-2) are confirmed, then recorded in `backend/pyproject.toml`/Dockerfiles and `frontend/package.json`'s `engines` field respectively.

---

## Invariants

1. Use approved libraries when an approved solution exists — do not reach for an unlisted library to solve a problem this file already covers.
2. Do not introduce a duplicate library for a responsibility already owned by an approved library (see Prohibited Alternatives).
3. Do not upgrade or change a major dependency (Next.js, FastAPI, Pydantic, SQLAlchemy, PyTorch, etc.) without explicit justification and a dedicated reviewed change.
4. Do not import a library across an architectural boundary it doesn't belong to — library placement follows `architecture.md`'s layer ownership exactly.
5. Keep ML dependencies (PyTorch, XGBoost, statsmodels, TimesFM, Chronos-2, SHAP) isolated to `backend/forecasting/` and `backend/backtesting/`; they are never imported into `backend/api/`, `backend/domain/`, or `frontend/`.
6. Keep frontend dependencies isolated from backend concerns — no frontend package is added to solve a backend problem or vice versa.
7. Do not add a dependency merely for convenience or personal familiarity — every addition goes through Dependency Selection.
8. Every new dependency requires explicit, recorded justification and an update to this file in the same change that introduces it.
9. Do not silently replace an established project library (e.g., swapping SQLAlchemy for a different ORM, or Recharts for a different charting library) without an explicit, reviewed architectural decision.
10. Keep the dependency ecosystem small, pinned, and reproducible — every dependency should be traceable to a real, current need documented in this file.
