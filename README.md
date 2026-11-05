# SamudraSetu unified freight decision-support system

This root is the merged codebase for the pipeline/UI repository and the
trained-model repository. The primary end-to-end path is:

```text
React/Vite UI
  → POST /api/v1/pipeline/run
  → scope-aware model registry
      → PyTorch LSTM freight model (supported scope)
      → XGBoost port-risk models (Paradip)
      → documented Holt fallback (unsupported freight scope)
  → feasibility + risk + contract recommendation + backtest summary
  → UI
```

See `docs/merge-summary.md` for exact endpoint mapping, model coverage, and
unresolved methodological issues.

## Structure

```text
backend/             FastAPI, model serving, pipeline/domain modules, tests
frontend/            React 19 + Vite browser UI
data/model/          Model-ready datasets, preprocessing metadata, metrics
backend/artifacts/   Trained PyTorch/XGBoost artifacts
backend/training/    Preserved model-build/training scripts
results/             Model plots from Repo B
docs/model/          Repo B source documentation
context/             Original project architecture/background (unchanged)
streamlit_app.py     Optional legacy UI using the same model registry
```

## Run locally

Python 3.10+ and Node.js are required. The currently verified environment is
Python 3.13 and Node.js 24.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements-dev.txt

# Terminal 1
python -m uvicorn backend.api.main:app --reload --port 8000

# Terminal 2
cd frontend
npm ci
npm run dev
```

Open `http://localhost:5173`. API documentation is at
`http://localhost:8000/docs`.

The browser first loads `GET /api/v1/pipeline/config`. Form defaults, input
constraints, and available route/vessel/horizon choices come from that response
and are limited to scopes backed by loaded trained artifacts. Forecast values,
charts, recommendations, risk, feasibility, costs, and evidence are rendered
from `POST /api/v1/pipeline/run`; the frontend does not substitute sample
numbers for missing fields.

For the optional Streamlit UI:

```powershell
streamlit run streamlit_app.py
```

## Verify

```powershell
python -m pytest
cd frontend
npm run build
```

The API test suite verifies both the trained LSTM route and the explicit Holt
fallback route. The browser production build verifies that the merged UI
contract compiles.

## Important data/model caveat

The committed model repository contains useful trained demonstration artifacts,
but its LSTM preprocessing is not fully point-in-time safe (full-series scaling
and backfill). The API and UI disclose this limitation. Retrain through a
leakage-safe feature pipeline before treating results as production forecasts.
The committed freight targets are proxy/simulated rather than live market
quotes, so "backend-sourced" must not be interpreted as live real-world data.

## Preserved source history

The root `main` branch is a true two-parent merge whose parents are the
original `main` tips from Repo A and Repo B. The original GitHub repositories
are configured as the `repo-a` and `repo-b` remotes. Use `git log --all --graph`
or `git shortlog -sne --all` to inspect the retained authorship.

The original local clones were moved, not destroyed, to the recoverable sibling
directory `C:\Users\Lenovo\Desktop\sih\SamudraSeva-source-repositories` after
their histories were imported.
