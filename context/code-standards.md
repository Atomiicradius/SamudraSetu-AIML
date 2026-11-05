# Code Standards

## General Principles

- Code is written for the next engineer (human or AI agent) to read, not for the author to remember. Prefer explicit, boring code over clever code.
- Every module has one clear responsibility, matching the boundary it is assigned in `architecture.md`. If a change requires touching two unrelated responsibilities in one file, split the file first.
- Predictability beats brevity: naming, structure, and error handling should be consistent across the codebase so a reader can guess how an unfamiliar module behaves from familiar ones.
- Correctness for this system specifically means: point-in-time integrity (per `model.md`), layer boundaries (per `architecture.md`), and design-system fidelity (per `ui-tokens.md`/`ui-rules.md`/`ui-registry.md`) are never sacrificed for speed of delivery.
- Prefer the simplest implementation that satisfies the requirement and the architecture. Do not add configurability, abstraction layers, or generalization for needs that do not exist yet.
- No code is "temporary" in a shared branch. If something is a stopgap, it is marked with a `TODO` comment naming the follow-up, not left unmarked.
- When a standard in this document and a pattern already used elsewhere in the codebase conflict, raise it rather than picking one silently — see Invariant 10.

---

## Repository Organization

- Follow the folder structure in `architecture.md` exactly. Do not create new top-level folders (e.g. a second `services/` or `lib/` at the repo root) without updating `architecture.md` first.
- Frontend code lives only under `frontend/`; backend Python code lives only under `backend/`; ML notebooks/experiments live only under `notebooks/`; raw/processed data artifacts live only under `data/`. No module reaches across these roots by relative path.
- Within `backend/`, a new file goes into the existing subpackage that matches its responsibility (`domain/`, `forecasting/`, `data_access/`, `ingestion/`, `preprocessing/`, `features/`, `backtesting/`, `optimization/`, `jobs/`, `api/`, `config/`). A file that doesn't fit an existing subpackage is a signal to check the architecture boundary, not to create an ad hoc `misc/` or `helpers/` folder.
- Within `frontend/`, components go into the registry-defined subfolder under `components/` (see `ui-registry.md` → Naming & Organization) and routes go into `app/` matching the five pages. Shared, non-component utilities go into `frontend/lib/utils/`; API-calling code goes only into `frontend/lib/api-client/`.
- Tests live in a `tests/`-style directory mirroring the module they test (`backend/tests/domain/`, `backend/tests/forecasting/`, etc., per `architecture.md`; frontend tests colocate with or mirror `components/`). A test file's path should make it obvious which source module it exercises without opening it.
- Scripts for one-off or operational tasks (data backfills, manual migrations) go in a dedicated `scripts/` location, never inline inside `backend/api/` or `backend/domain/`, and never committed as an ad hoc notebook cell that's actually load-bearing.
- Configuration files (`model_config.yaml`, `.env.example`, `docker-compose.yml`, Dockerfiles) stay at the locations `architecture.md` defines. Do not duplicate configuration values into code; code reads from the defined config location.

---

## TypeScript Standards

- `strict` mode is enabled in `tsconfig.json` and must stay enabled. No file may locally opt out (`// @ts-nocheck`, `@ts-ignore` without a comment explaining why, or a relaxed local `tsconfig`).
- `any` is not allowed except at a verified I/O boundary (e.g., parsing an unknown third-party payload) and even then must be narrowed to a real type immediately via a type guard or schema parse — it must never propagate past the function that received it. Use `unknown` instead of `any` when the type is genuinely not known yet.
- Every exported function, component prop, and API client function has an explicit type signature; do not rely on inferred return types for anything exported across a module boundary.
- Component props are defined as a named `interface Props` (or `ComponentNameProps`) above the component, never as inline object types repeated across files.
- API response and request types live in `frontend/types/` and mirror the backend Pydantic schemas field-for-field, per `architecture.md` → Client Pattern. When a Pydantic schema changes, the corresponding TypeScript type is updated in the same change — they must never drift.
- Naming: `PascalCase` for components, types, and interfaces; `camelCase` for variables, functions, and hooks (`useForecastData`); `SCREAMING_SNAKE_CASE` only for true module-level constants. File names for components match the component's `PascalCase` name (per `ui-registry.md`).
- Async code uses `async`/`await`, not raw `.then()` chains. Every `await` that can reject is inside a function whose caller handles the rejection (try/catch, or a caller-level error boundary) — no unhandled promise rejections.
- Error handling: API client functions never throw a raw `Error` from `fetch`; they normalize failures into the shared `ApiError` shape defined in `frontend/lib/api-client/client.ts` (per `architecture.md`), so every consuming component handles one consistent error type.
- Imports: use absolute imports from the project root/alias (e.g. `@/components/...`) for cross-folder imports, relative imports only within the same feature folder. Do not import from another page's component folder directly — promote the component into a shared folder first (per `ui-registry.md`'s reusability rule).
- React/Next.js conventions: Server Components are the default for data-fetching/page-shell components; a component is only marked `"use client"` when it genuinely needs interactivity, browser APIs, or state. Data fetching for a page happens as high in the tree as practical and is passed down via props, not re-fetched redundantly in child components. Hooks follow the Rules of Hooks (no conditional hooks, no hooks outside components/hooks). Side effects in `useEffect` list every dependency they use; do not silently suppress the exhaustive-deps lint rule.
- No default exports for components or utilities that are imported by name elsewhere — use named exports so refactors and search stay reliable, except where Next.js requires a default export (e.g., `page.tsx`, `layout.tsx`).

---

## Python Standards

- Formatting is enforced by `black` (line length default) and import ordering by `isort` (or `ruff`'s equivalent), run via a pre-commit hook or CI check — not by hand. Do not hand-format around the tool.
- Every function signature has type hints for parameters and return type, including `Optional[...]`/`| None` where a value can genuinely be absent. Type hints are checked with `mypy` (or `pyright`) in CI; do not add hints that are silently wrong just to satisfy the linter.
- Naming: `snake_case` for functions, variables, and modules; `PascalCase` for classes; `SCREAMING_SNAKE_CASE` for module-level constants. Names describe the domain concept (`freight_observation_repo`, `compute_prediction_interval`), not the mechanism (`helper2`, `do_stuff`).
- Functions do one thing and are small enough to name precisely; a function whose name needs "and" to describe it should usually be split. Classes are used for genuine state/behavior coupling (a repository, a model wrapper), not as a namespace for what could be a module of functions.
- Public functions and classes (anything imported from outside their own module) have a docstring stating purpose, parameters, return value, and — where relevant to this project — the point-in-time or layer-boundary assumptions the caller must satisfy (e.g., "features passed in must already be point-in-time filtered"). Private/internal helpers only need a docstring when their behavior isn't obvious from the name and signature.
- Exceptions: raise specific, named exception types (define a small domain-specific exception hierarchy per subsystem, e.g. `ForecastUnavailableError`, `FeasibilityDataMissingError`) rather than raising or catching bare `Exception`. Never catch an exception only to suppress it — see Do Nots.
- Imports: standard library, then third-party, then local imports, each group separated and alphabetized (what `isort` enforces). No wildcard imports (`from module import *`). No circular imports between layers — this is also an architecture rule, not just a style one.
- Async code (in `backend/api/` route handlers and any I/O-bound job code) uses `async def` consistently down the call chain it participates in; do not mix blocking synchronous I/O calls inside an `async def` route without offloading them (e.g., via a thread pool) — this would block the event loop for all requests.
- Configuration values (thresholds, horizons, hyperparameters, feature flags) are read from `backend/config/model_config.yaml` or environment-driven settings in `backend/config/settings.py` — never hard-coded as literals inside `domain/`, `forecasting/`, or `api/` code. See Configuration & Secrets.
- Avoid unnecessary abstraction: do not introduce a factory, strategy pattern, or plugin system for a choice that currently has one implementation. Add the abstraction when a second real implementation exists (mirrors the reusability rule in `ui-registry.md`).

---

## FastAPI Standards

- Routers in `backend/api/routers/` contain only: request parsing/validation (via Pydantic schemas), calling into `domain/` or `forecasting/inference.py`, and shaping the response. A route handler should read as a short sequence of calls, not contain business rules, loops implementing feasibility/risk logic, or SQL.
- Every route has an explicit Pydantic request schema (for body/query params beyond trivial path params) and an explicit Pydantic response_model — never `dict`/`Any` as a route's declared response type.
- Validation belongs in the Pydantic schema (field constraints, validators) wherever it is a data-shape rule (e.g., `quantity_mt > 0`, `loading_window_start <= loading_window_end`). Business-rule validation (e.g., "this vessel class isn't feasible for this route") belongs in `domain/`, not in the schema.
- Dependency injection via FastAPI's `Depends` is the only way route handlers obtain a DB session, repository, or config — defined in `backend/api/deps.py`. A route handler never constructs a DB session or repository instance itself.
- Error handling: domain/data-access layers raise typed exceptions; `backend/api/` translates them to HTTP responses (404 for not-found, 422 for validation, 503/424 for "forecast unavailable" style data-availability boundaries per `project-overview.md`, 500 for unexpected). Exception-to-status-code mapping lives in one place (e.g., exception handlers registered in `main.py`), not duplicated per route.
- Service boundaries: a router only calls into the layer directly below it per `architecture.md`'s dependency direction (`api → domain → forecasting`, `api → data_access` only via domain or directly for simple reads that don't involve business rules). A router must never import from `forecasting/models/*` directly, and must never construct or reference an ML model object.
- Database access from `backend/api/` happens only through `backend/data_access/repositories/` methods, never raw SQL/ORM queries inline in a router — this mirrors `architecture.md`'s data-access boundary exactly.
- Authentication: per `architecture.md`, no auth provider is implemented yet. Routes are not to fake or stub authentication logic; if a route needs to reference "who submitted this," it uses the existing free-text `created_by` field, not an invented user/session concept. Any future auth work is added as middleware/`Depends` in `deps.py` without changing `domain/`/`forecasting/`/`data_access/`.

Routes must remain thin. Business logic must not be embedded directly inside route handlers.

---

## Database Standards

- Schema changes go through migrations (e.g., Alembic) checked into the repo — never applied by hand against a running database and never expressed only as an updated `models.py` without a corresponding migration file.
- Every migration is reviewed for whether it's reversible; a destructive migration (dropping a column/table) documents why the data is safe to lose.
- Naming: tables and columns are `snake_case`, matching `architecture.md`'s schema exactly. A new table/column introduced during implementation must be added to `architecture.md`'s Database Schema section in the same change, not left undocumented.
- Every table has a UUID primary key named `id`, per the schema in `architecture.md`. Foreign keys are named `<referenced_singular>_id` (e.g., `route_id`, `vessel_class_code` where the referenced table's key is a natural code) and declared with real FK constraints, not just implied by naming.
- Indexes follow `architecture.md`'s specified indexes as a floor, not a ceiling — a query pattern introduced during implementation that scans a large table without an index gets an index added via migration, documented with the query it supports.
- Timestamps: use `timestamptz` (UTC) for all datetime columns, matching `architecture.md`. `created_at` defaults to `now()`; any column representing "when data became knowable" (`available_as_of`) is required, not optional, on `freight_observations` and `market_observations` — this field is load-bearing for point-in-time correctness (see `model.md`) and must never be nullable or backfilled with a guess.
- Transactions: a single logical write operation (e.g., persisting a `Recommendation` plus its constituent `RiskAssessment`/`ContractStrategy` records) is wrapped in one transaction so partial writes cannot occur. Repository methods that perform multi-table writes are explicit about transaction boundaries, not relying on autocommit accidentally producing atomicity.
- Query organization: all queries live in `backend/data_access/repositories/*.py` as named, purpose-specific methods (e.g., `get_observations_available_as_of(route_id, cutoff)`), never as ad hoc query strings built inside `domain/` or `api/`. A repository method's name states what data it returns and any filtering it applies (especially point-in-time filtering) so a caller doesn't need to read the SQL to know if a query is point-in-time-safe.
- Validation at the database layer (NOT NULL, CHECK constraints for `quantity_mt > 0`, `num_voyages >= 1`, unique constraints per `architecture.md`) is a backstop, not a replacement for Pydantic/domain-level validation — both layers validate, since either can be reached independently (e.g., a Celery job writing directly via a repository).
- Time-series data (`freight_observations`, `market_observations`) is always queried and stored with its `observation_date` and `available_as_of` distinct and both populated; a query that needs "what was known as of date X" must filter on `available_as_of`, never assume `observation_date <= X` is sufficient (an observation dated in the past can still have been published late).

Database access must remain within the architecture-defined data-access layer.

---

## ML & Data Standards

- Data preprocessing (`backend/preprocessing/`) — cleaning, outlier/unit-mismatch checks, and frequency alignment — happens once, in these modules, and produces the point-in-time-tagged data that `features/` consumes. Feature code must never re-implement its own ad hoc cleaning.
- Feature engineering lives only in `backend/features/`, is documented per feature per `model.md`'s Feature Documentation Requirement (timestamp, availability timestamp, frequency, alignment method, missing-value treatment, leakage risk), and is the only place that constructs model inputs from raw observations.
- Model interfaces are uniform across model families: every model in `backend/forecasting/models/` implements the same `fit`/`predict` (or equivalent) interface expected by `forecasting/inference.py`, accepting feature arrays/dataframes and returning predictions + uncertainty — no model-specific special-casing inside `inference.py` beyond a registry lookup.
- Training and inference are separated: training code (`jobs/training_tasks.py`, `forecasting/models/*` fit paths) never runs inside a live API request path; inference (`forecasting/inference.py`) only loads an already-trained, registered model artifact. A route or domain call must never trigger on-the-fly model training.
- Model configuration (hyperparameters, horizons, sequence-length candidates, feature toggles) is defined only in `backend/config/model_config.yaml`, never hard-coded inside a model file or notebook cell that then gets copy-pasted into application code.
- Reproducibility: every training run fixes and records its random seed, records the exact config snapshot used, and records the training data period, per `model.md`. A model cannot be promoted to `is_active = true` in `model_versions` without this metadata populated.
- Model artifacts are written to `backend/forecasting/artifacts/{model_name}/{version_label}/` per `architecture.md`'s Storage section and referenced by `model_versions.artifact_path` — never loaded from an untracked ad hoc path.
- Experiment logging: every benchmarked model/config combination's validation and backtest metrics are recorded in `model_versions.benchmark_metrics`, including losing candidates and simpler-model wins (per `model.md`) — results are never overwritten or discarded because a later candidate looks more sophisticated.
- Backtesting (`backend/backtesting/rolling_backtest.py`) always uses chronological/rolling-origin evaluation, never a random split, and always re-applies the same `features/point_in_time.py` gate used at inference time — backtesting code must not take a shortcut that reads the fully realized historical dataset.

**Future information must never enter historical training or evaluation.** Every feature, at training, inference, and backtest time, is filtered to `available_as_of <= decision_timestamp` via `backend/features/point_in_time.py`; no model, repository call, or backtest step may bypass this gate by querying raw observation tables directly.

---

## API & Data Contracts

- Every FastAPI route declares an explicit Pydantic request schema and `response_model` in `backend/api/schemas/`; these schemas are the contract, and the contract is what changes, not ad hoc dict shapes.
- Serialization: Pydantic's standard JSON serialization is used; do not hand-roll response dict construction inside a router when a schema's `.model_dump()`/response_model handles it.
- Dates/timestamps: all timestamps are ISO 8601 in UTC across the wire (matching `timestamptz` storage per `architecture.md`); a plain `date` (no time component) is used only for genuinely date-only concepts (`loading_window_start`, `observation_date`) — never conflate the two.
- Numeric units: every numeric field's unit is unambiguous from its name or explicit metadata (`quantity_mt`, `rate_usd_per_mt`, matching `architecture.md`'s column naming) — a schema must never introduce a bare `amount` or `value` field without a unit-qualified name or an accompanying unit field.
- Nullability: a field is `Optional` in the Pydantic schema if and only if the underlying data can genuinely be absent (e.g., optional procurement-requirement fields, `unknown` feasibility results) — required product inputs (per `project-overview.md`) are never modeled as optional to "be safe."
- Error formats: all error responses share one shape (the `ApiError` contract consumed by the frontend's `client.ts`) — an error code/type, a human-readable message, and optionally a field-level detail list for validation errors. No route returns a bespoke error shape.
- Versioning: this project does not introduce API versioning (e.g., `/v2/`) preemptively; if a breaking schema change is needed, it is called out explicitly as a breaking change and coordinated with the frontend type update in the same change, per Invariant 8, rather than silently versioned or silently broken.
- Frontend/backend type consistency: `frontend/types/` mirrors `backend/api/schemas/` field-for-field. A schema change (add/remove/rename/retype a field) is not complete until the corresponding TypeScript type is updated in the same change.

---

## Frontend Standards

- Component structure, server/client boundaries, and reusability follow `ui-registry.md` exactly: a component is built by composing existing registry primitives (`Card`, `Badge`, `DataTable`, `MetricValue`, etc.) rather than reimplementing their visual treatment. A new page-specific component still imports only from shared component folders, never redefines spacing/color/typography inline (per `ui-rules.md`).
- Data fetching happens through `frontend/lib/api-client/*` only — no component calls `fetch`/`axios` directly against the backend, and no component queries a database or cache directly (this is also an architecture invariant).
- State management: server-derived data (forecasts, feasibility results, risk assessments) is fetched and passed down via props/server components; client-only UI state (form input values, selected horizon, expanded/collapsed panels) uses local component state or a lightweight shared store — do not introduce a global state library for data that the API client and props already carry cleanly.
- Forms (the procurement requirement form and any future form) validate required fields client-side before submission for immediate feedback, but the backend's Pydantic validation is still the source of truth — client-side validation is a UX convenience, never a substitute for server validation.
- Every data-bearing component implements its full state contract as defined in `ui-registry.md` → Component Contracts: loading (via `LoadingSkeleton`), empty (via `EmptyState`), error (via `ErrorAlert`), and, where applicable, the domain-specific "unavailable"/"unknown" state (e.g., feasibility `unknown`, forecast `unavailable`). A component that only renders the happy path is incomplete.
- API usage: a page's data-fetching and error/loading handling is written once, at the point closest to the API call, and consumed by presentational children — do not duplicate the same `getForecast`/error-handling logic across multiple components that need the same data.
- Reusable components are added to `frontend/components/<category>/` and registered in `ui-registry.md`'s inventory in the same change that introduces them (per that document's own Invariant 10) — a component is never introduced silently inside a single page's folder when it duplicates or resembles an existing registry entry.

All UI implementation must follow `ui-tokens.md`, `ui-rules.md`, and `ui-registry.md`.

---

## Error Handling & Logging

- Expected errors — a missing forecast for an unsupported route, insufficient data for a feasibility constraint, a validation failure on user input — are modeled as typed results/exceptions and rendered as the appropriate UI state (Info/Warning alert, `Unknown` badge) per `ui-rules.md`; they are not logged as errors/exceptions at error severity, since they are normal operating conditions.
- Unexpected errors — a DB connection failure, an unhandled exception in model inference, a bug — are logged at error severity with enough context (route, timestamp, request id if available) to reproduce, and surfaced to the user as a generic `ErrorAlert` with a retry action where retry is meaningful, per `ui-rules.md` → Loading & Error States. The user never sees a raw stack trace or exception message.
- API errors follow the shared `ApiError` contract (see API & Data Contracts); the backend logs the full exception server-side but returns only a safe, human-readable message and error code to the client.
- ML/data errors (e.g., a model artifact fails to load, a feature has unexpected nulls beyond the documented missing-value treatment) are raised as typed exceptions from `forecasting/`/`features/` and handled by the calling layer (`domain/` or `backtesting/`) — they must not be silently caught and replaced with a fabricated fallback value.
- Background-job failures (Celery tasks in `backend/jobs/`) are logged with the task name, arguments (excluding secrets), and failure reason, and the job's status is persisted where a status is tracked (e.g., `backtest_runs.status = "failed"`) so the API/UI can reflect it rather than a task failing silently with no visible trace.
- Logging levels: `DEBUG` for developer-only diagnostic detail (disabled in production), `INFO` for normal lifecycle events (job started/completed, model version activated), `WARNING` for expected-but-notable conditions (a feature fell back to a documented missing-value treatment), `ERROR` for unexpected failures needing investigation. Do not log routine successful requests at `WARNING` or above.
- What must be logged: enough structured context (identifiers, timestamps, operation name) to trace an issue across layers. What must never be logged: full request/response bodies containing procurement-requirement free-text fields beyond what's needed for debugging, and — absolutely — any secret or credential value.

Never expose secrets, credentials, or sensitive internal information in logs or API responses.

---

## Configuration & Secrets

- All environment-specific values (database URL, Redis URL, API base URL, model artifact base path, any third-party data-provider credentials) are read from environment variables via `backend/config/settings.py` (backend) or Next.js environment variables (frontend, `NEXT_PUBLIC_*` only for values safe to expose to the browser).
- A `.env.example` file documents every required environment variable with a placeholder value; actual `.env` files are gitignored and never committed.
- Model/domain parameters that are not secrets (forecast horizons, hyperparameters, thresholds) go in `backend/config/model_config.yaml`, not environment variables — environment variables are for deployment-specific values, `model_config.yaml` is for the project's own tunable parameters, per `architecture.md`.
- Local development configuration (Docker Compose defaults, local `.env`) uses safe, non-production placeholder credentials only; production configuration is supplied through the deployment environment (e.g., orchestrator secrets), never checked into the repo in any form.
- No code path branches on "is this a demo/hackathon build" to skip validation or safety checks that would matter in a real deployment — write the code as if it will run against real data, since the point-in-time and layer-boundary rules exist regardless of deployment context.

Never hard-code credentials, API keys, passwords, or environment-specific secrets.

---

## Testing Standards

- Unit tests cover `backend/domain/` logic (feasibility constraint evaluation, charter timing rules, contract comparison, risk scoring) with deterministic inputs/expected outputs — these are the highest-value tests since they encode the product's decision logic.
- Unit tests cover `backend/forecasting/` at the interface level (given a feature array, does `inference.py` return a correctly shaped structured output per `model.md`'s Decision Engine Interface) without requiring a fully trained model for every test — use small fixture models or mocked model objects where full training is impractical in a test run.
- Integration tests cover a full request flow through `backend/api/` (e.g., POST a requirement, then GET a forecast/recommendation) against a test database, verifying the response shape matches the declared Pydantic `response_model`.
- API tests specifically verify error-path behavior: invalid input returns the shared `ApiError` shape and correct status code; an unsupported route/vessel-class combination returns the "unavailable" response, not a 500.
- Database tests verify repository methods, especially point-in-time filtering (`get_observations_available_as_of` never returns a record whose `available_as_of` is after the cutoff) and constraint enforcement (unique constraints, required fields) — this is the single most safety-critical class of test in the project given `model.md`'s point-in-time rule.
- ML/data tests include: a dedicated point-in-time leakage test (constructing a scenario where a future observation exists and asserting it is excluded from feature construction as of an earlier decision date), a feature-documentation completeness check where practical, and a backtest regression test asserting rolling-origin backtesting never regresses to a random split.
- Frontend tests (Jest + React Testing Library) cover: rendering of each required component state (loading/empty/error/populated per `ui-registry.md` contracts), that status/risk/feasibility components render icon + label + color together (never color-only, verifiable by asserting the accessible text is present), and that the API client correctly maps a backend error response to the shared `ApiError` shape.
- Regression tests are added alongside every bug fix, reproducing the original failure before the fix and passing after — a bug fix without a corresponding test is incomplete.

Focus testing on business-critical behavior and architectural boundaries: point-in-time correctness, layer boundaries (no DB access from the wrong layer, no business logic in routes), and the non-color-alone accessibility rule are the three categories most worth a test's cost.

---

## Dependencies

- A new package (frontend or backend) is added only when the existing stack defined in `architecture.md` (Next.js/React/TypeScript, Tailwind, Recharts/Plotly, FastAPI, SQLAlchemy, pandas/NumPy, scikit-learn/XGBoost/PyTorch/TimesFM/Chronos-2, OR-Tools/scipy, Celery/Redis) cannot reasonably solve the problem.
- Version management: dependencies are pinned to specific versions (or a narrow compatible range) in `requirements.txt`/`pyproject.toml` and `package.json`/lockfile — never left unpinned in a way that makes builds non-reproducible.
- Before adding a package, check for an existing dependency (or a small amount of code using an existing dependency) that already covers the need — e.g., do not add a new HTTP client when `fetch`/the existing API client wrapper suffices, do not add a new date library when the one already in use covers the need.
- Evaluate a new dependency's maintenance status (recent releases, open critical issues) and security posture (no known unpatched critical CVEs) before adding it, and prefer well-established libraries over niche ones for anything touching data correctness or security.
- Any dependency material to the project's architecture (a new ML framework, a new charting library, a new state-management library) is documented in `architecture.md`'s stack table in the same change that introduces it — it is not silently added to `requirements.txt`/`package.json` without that update.

Do not introduce a library when existing project dependencies already solve the problem adequately.

---

## Git & Collaboration

- Branch naming: `<type>/<short-description>` where `<type>` is one of `feat`, `fix`, `refactor`, `test`, `docs`, `chore` (e.g., `feat/vessel-feasibility-table`, `fix/point-in-time-filter-off-by-one`).
- Commit messages are written in the imperative mood, describe what changed and why in the first line (≤72 chars), with additional detail in the body if needed. Avoid vague messages like "fix stuff" or "updates."
- Pull requests are scoped to one feature/fix and describe: what changed, why, which layer(s)/pages it touches, and how it was tested. A PR touching both `backend/domain/` and `frontend/components/` for one coherent feature is fine; a PR mixing an unrelated refactor with a feature is not (see Do Nots).
- Code review checks, at minimum: layer-boundary compliance (per `architecture.md`'s System Boundaries table), point-in-time correctness for anything touching data/features/backtesting, design-token/rule compliance for anything touching UI, and whether new components/patterns were registered per `ui-registry.md`.
- Merge behavior: prefer squash or rebase-and-merge to keep history readable per feature; avoid merge commits that bundle multiple unrelated features into one commit on the main branch.
- Conflict resolution: when two team members (or an AI agent and a human) touch the same shared component or repository method, the resolution keeps both intended behaviors by composing (adding a variant/prop, adding a repository method) rather than one side's change silently overwriting the other's — consistent with the "extend, don't fork" principle in `ui-registry.md`.
- Keep changes focused: a PR does not "drive-by" reformat unrelated files, rename unrelated variables, or restructure an unrelated module while fixing a specific bug or building a specific feature.

The standards should support multiple team members working independently without creating incompatible implementations — this is why layer boundaries, the component registry, and typed contracts are enforced rather than left to convention alone.

---

## Documentation

- Code: a function/module needs a comment or docstring when its behavior isn't obvious from its name, signature, and the surrounding code — not for every function unconditionally.
- APIs: every route's request/response schema is self-documenting via Pydantic field descriptions where a field's meaning isn't obvious from its name (e.g., what `available_as_of` means, what `horizon_days` accepts).
- Models: every trained model version's assumptions (feature set, training period, point-in-time behavior) are captured in its `model_versions` metadata record, not only in a comment in the training script — the metadata is the durable record.
- Configuration: a new entry added to `model_config.yaml` includes an inline comment stating what it controls and its valid range/options, since this file is the single source of truth for tunable parameters.
- Non-obvious decisions — e.g., why a particular forward-fill is safe here but wouldn't be elsewhere, why a specific feasibility constraint is evaluated the way it is, why a component deviates from the "obvious" reusable pattern — are documented at the point of the decision (a code comment or a short note in the PR description), not left for a future reader to reverse-engineer.
- Public interfaces (repository methods, `forecasting/inference.py`'s contract, the API client functions, exported components' props) are documented clearly enough that a caller does not need to read the implementation to use them correctly.

Document WHY when the implementation is non-obvious, not merely WHAT the code already makes clear.

---

## Performance

- API requests: a route handler does not perform unbounded work synchronously; anything long-running (training, backtesting, bulk ingestion) is dispatched to a Celery task and the route returns a job/status reference immediately, per `architecture.md`.
- Database queries: use the indexes defined in `architecture.md`/added via migration; avoid N+1 query patterns in repository methods that loop and query per item — batch-fetch instead where the access pattern is known upfront.
- Frontend rendering: prefer Server Components and server-side data fetching for initial page loads to avoid client-side request waterfalls; avoid re-fetching data a parent component already has by refetching identical data in a child.
- Large datasets: `backend/preprocessing/` and `backend/features/` use pandas/NumPy vectorized operations rather than row-by-row Python loops for anything operating over the full observation history; consider Polars (per `architecture.md`, marked optional) only if a specific pandas operation is demonstrated to be a bottleneck.
- Charts: chart components receive already-aggregated/pre-shaped data from the API rather than performing heavy client-side aggregation over large raw series; large historical series are down-sampled server-side for chart rendering where full point-level detail isn't needed for the requested horizon.
- ML inference: a live recommendation request uses the already-trained, loaded model artifact (per Training/Inference separation above); do not reload a model from disk on every request if it can be cached in the serving process's memory.
- Background jobs: long Celery tasks report progress/status where practical (e.g., `backtest_runs.status`) rather than leaving the caller to guess whether a job is stuck or still running.

Do not introduce premature optimization: profile or otherwise demonstrate an actual bottleneck before adding caching layers, denormalization, or non-obvious data structures beyond what's listed above.

---

## Security

- Input validation: every external input (API request body/params, uploaded/ingested data) is validated at the boundary — Pydantic schemas for API input, `preprocessing/validation.py` checks for ingested data — before it reaches business logic.
- Authentication/authorization: per `architecture.md`, no application-level auth is implemented yet; routes rely on deployment-environment protection. Do not implement ad hoc, partial auth logic (e.g., a hard-coded API key check) as a substitute — that gives a false sense of security. If auth is needed sooner than the architecture decision is made, escalate rather than inventing an interim scheme.
- Secrets: per Configuration & Secrets above — environment variables only, never committed, never logged.
- SQL injection prevention: all database access goes through the ORM/repository layer using parameterized queries; raw SQL string interpolation with user-controlled or externally-ingested values is never used.
- Dependency safety: per Dependencies above — pinned versions, checked for known vulnerabilities before adding, kept up to date for security patches.
- File handling: any file ingestion (raw data drops into `data/raw/`) validates file type/structure before parsing and does not execute or `eval()` content from ingested files; ingestion code treats all external files as untrusted input.
- API exposure: the API surface exposes only the endpoints needed for the five pages' workflows (per `project-overview.md`'s scope); no debug/admin endpoint that bypasses validation or exposes internal state is left reachable outside a clearly gated development-only configuration.
- Logging: per Error Handling & Logging above — no secrets, credentials, or full sensitive payloads in logs.

---

## Do Nots

- No duplicated business logic — feasibility, risk, timing, or contract-comparison rules are implemented once in `backend/domain/` and consumed everywhere else, never re-implemented inline in a route, a component, or a script.
- No database access from the frontend — all data flows through `frontend/lib/api-client/`.
- No database queries inside ML models — `forecasting/models/*` accept arrays/dataframes only; they never call a repository or issue SQL.
- No ML implementation inside API routes — `backend/api/` calls `forecasting/inference.py`/`domain/`; it never contains model training/inference code inline.
- No hard-coded secrets — see Configuration & Secrets.
- No future-data leakage — every feature, forecast, and backtest step respects `available_as_of <= decision_timestamp` via `features/point_in_time.py`, without exception.
- No arbitrary UI values outside the design system — no hex color, pixel spacing, font, or shadow value that isn't a token defined in `ui-tokens.md`.
- No unnecessary dependencies — see Dependencies.
- No unexplained magic numbers — a literal threshold, limit, or constant (a risk cutoff, a retry count, a horizon day count) is named as a constant or pulled from `model_config.yaml`/`settings.py`, with a comment or name explaining its meaning if not otherwise obvious.
- No silent exception swallowing — an empty `except:`/`except Exception: pass` (or a caught error whose message is discarded) is never acceptable; catch specific exceptions and either handle, re-raise, or log with context.
- No large unrelated changes in a single feature — see Git & Collaboration.

---

## Invariants

1. Follow `architecture.md` boundaries: dependency direction, layer ownership, and the "MUST NOT DO" column of its System Boundaries table are never violated.
2. Follow `model.md` data/model rules: benchmark hierarchy, chronological evaluation, calibration requirements, and the forecasting-layer boundary (no vessel/contract/risk/UI logic inside `forecasting/`).
3. Follow `ui-tokens.md`, `ui-rules.md`, and `ui-registry.md` for all frontend work — values, usage rules, and component contracts respectively.
4. Keep business logic independent of presentation: `backend/domain/` contains no HTTP, template, or rendering concerns; UI components contain no feasibility/risk/timing/contract logic.
5. Keep ML logic independent of HTTP/UI: `backend/forecasting/` never imports FastAPI, Celery, or anything from `api/`/`frontend/`.
6. Keep database access within the defined data-access boundary: only `backend/data_access/repositories/` issues queries; no other layer does.
7. Preserve point-in-time correctness: no feature, forecast, recommendation, or backtest result may be produced using information not genuinely available at its decision timestamp.
8. Maintain type/schema consistency between frontend and backend: a Pydantic schema change and its mirrored TypeScript type change land together, in the same change.
9. Do not introduce architectural changes (new services, new top-level folders, new external providers, new auth scheme) without explicit justification and an update to `architecture.md`.
10. Do not silently create new conventions when an existing project convention exists — extend the existing pattern (component, repository method, exception type, config entry) or raise the conflict explicitly; never fork a parallel pattern quietly.
