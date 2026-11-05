# Merge summary

## What was merged

- Repo A's React/Vite UI is now `frontend/` and is the primary browser UI.
- Repo A's forecasting, feasibility, risk, recommendation, backtest, and
  deterministic sample-data modules are now under `backend/`.
- Repo A's Streamlit application is retained as `streamlit_app.py` and uses
  the same trained-artifact adapter for supported freight requests.
- Repo B's PyTorch and XGBoost artifacts are under `backend/artifacts/`.
- Repo B's model-ready datasets and metrics are under `data/model/`.
- Repo B's training/reproduction scripts are under `backend/training/` and its
  original research/context documents are under `docs/model/`.
- Generated benchmark plots are retained under `results/`.

`context/` was read but not modified.

## Git/contributor preservation

The unified root merge commit has both original repository tips as parents:

- Repo A: `7d1c52905e591be8a0cd89c5ede07a91a1250799`
- Repo B: `f143717ea47e1fadce780f0b6b2673f80b0f57c5`

This preserves all original commits, author names, and author emails. The
original GitHub remotes remain configured as `repo-a` and `repo-b`. The source
clones were moved to the recoverable sibling directory
`C:\Users\Lenovo\Desktop\sih\SamudraSeva-source-repositories`.

## Connected endpoints

| Endpoint | Connected code/artifact |
|---|---|
| `GET /health` | FastAPI process health |
| `GET /api/v1/models/status` | Loaded-artifact status, exact scopes, cutoffs |
| `GET /api/v1/pipeline/config` | Backend-owned UI defaults, constraints, and trained-artifact scenarios |
| `POST /api/v1/predict/freight` | Scope-aware LSTM/XGBoost freight inference; no implicit fallback |
| `POST /api/v1/pipeline/run` | Forecast → feasibility → risk → recommendation → decision-rule backtest |

The React client loads `GET /api/v1/pipeline/config` and calls
`POST /api/v1/pipeline/run` through `frontend/src/api.js`. The browser exposes
only scenarios reported by loaded trained artifacts; it does not synthesize
form options, result values, or missing numeric fields.
Vite proxies `/api` to `http://127.0.0.1:8000` in development. A separately
hosted frontend can set `VITE_API_BASE_URL`.

## Model routing

- Australia → Paradip, Capesize, 7/14/30/60 days: committed PyTorch LSTM.
- Australia → Paradip, Supramax, 1 day: committed XGBoost freight regressor
  (available through both the direct prediction endpoint and the browser).
- Paradip port risk: committed XGBoost congestion and wait-time regressors.
- All other freight combinations: Repo A's Holt exponential-smoothing model,
  explicitly labeled `statistical_fallback` with its data source.

## Assumptions and unresolved issues

1. Repo B did not include a model-serving application, so the new
   `backend/model_service.py` adapter reconstructs the committed architectures
   and preprocessing metadata and FastAPI provides the serving boundary.
2. Repo B's trained scopes are narrow; the artifacts must not be represented
   as covering all UI route/vessel combinations.
3. The LSTM preprocessing fitted `StandardScaler` on the full dataset and used
   backward-fill. This conflicts with the point-in-time rules in
   `context/model.md`; the artifact is integrated for demonstration but needs
   leakage-safe retraining before production use.
4. LSTM/XGBoost P10/P90 values are RMSE-based normal approximations and are
   explicitly marked uncalibrated. Repo B did not contain probabilistic model
   artifacts.
5. Repo B's data is described as proxy/simulated and has fixed cutoffs (LSTM
   source through 2026-09-11; XGBoost source through 2025-12-31). No live market
   feed was introduced.
6. The preserved React frontend is Vite/JavaScript, not the aspirational
   Next.js/TypeScript stack in `context/architecture.md`. Converting frameworks
   was deliberately not bundled into the repository/model integration.
7. The original training scripts still expect missing raw source files and
   current-working-directory paths; see `backend/training/README.md`.
