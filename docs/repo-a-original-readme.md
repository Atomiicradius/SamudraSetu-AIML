# Freight Forecasting & Vessel Chartering Decision Support (MVP Prototype)

SIH 2026 — Problem Statement 26006 (SAIL freight forecasting & vessel chartering decision support).

This is an overnight hackathon-qualifier prototype: a **single Streamlit app**, no
database, no auth, no microservices. It exists to show a working, end-to-end
pipeline — requirement → data → forecast → feasibility → risk → recommendation →
backtest — where every number on screen is genuinely computed, not asserted.

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

No data file is required to run the app: every origin/destination/vessel
combination is generated on the fly (see "Data" below). Run
`python data/generate_data.py` yourself only if you want a sample CSV on disk.

## The form

The sidebar is a procurement requirement, not a scenario picker:

- **Origin** — Australia, United States, Mozambique, Russia, Indonesia
- **Destination** — Paradip, Visakhapatnam, Gangavaram, Gopalpur, Dhamra,
  Sagar/Sandheads, Haldia
- **Vessel class** — Handysize, Supramax, Panamax, Capesize
- **Cargo quantity (mt)** — feeds directly into every cost/utilization
  calculation below (Cost efficiency table, Recommendation cost comparison)
- **Cargo type** — fixed to Coal for tonight (shown disabled in the form)
- **Forecast horizon** — 7 or 30 days

That's 5 × 7 × 4 = 140 combinations, all backed by the same computation
pipeline described below.

## Data

For any (origin, destination, vessel_class) combination, `data/generate_data.py`
generates a synthetic ~2-year daily rate series (trend + annual seasonal wobble
+ weekly wobble + noise + a small random-walk component) — clearly marked as
placeholder, **not real SAIL data**.

**Reproducibility is deliberate and load-bearing for a live demo:** the
random generator is seeded from a SHA-256 hash of the route + vessel + cargo
identifiers (not Python's built-in `hash()`, which is salted per-process and
would silently change on every restart). Re-selecting the exact same
combination — even after restarting the app — always regenerates the exact
same series and every downstream number. Series are cached
(`st.cache_data`) so switching between combinations stays fast.

If `data/freight_rates.csv` exists and contains rows matching the selected
(route, vessel_class, cargo_type), the app prefers that "real" data over
synthetic generation — so a real SAIL extract can be dropped in with the same
schema (`date, route, vessel_class, cargo_type, rate_usd_per_mt`) and
everything downstream recomputes from it unchanged, with no code changes.

## What's in here

- `data/generate_data.py` — deterministic, reproducible synthetic data generation.
- `forecasting.py` — naive baseline, Holt exponential-smoothing point forecast,
  P10/P50/P90 band from holdout-residual spread, probability-of-increase,
  and holdout MAE/RMSE for both the naive and statistical forecasts.
- `feasibility.py` — vessel-class specs, port limits for all 7 destinations,
  pass/fail/unknown checks.
- `risk.py` — volatility (computed) + congestion/availability (manual) → risk score.
- `recommendation.py` — Charter Now vs Wait/Monitor rule; a three-way cost
  comparison (spot-only, short-term multi-voyage, medium-term single
  contract) for the selected vessel and cargo quantity; and a cost/
  feasibility/utilization comparison across all four vessel classes.
- `backtest.py` — walks back through ~18 historical decision points, re-applies
  the same rule with no look-ahead, and compares it to a spot-only baseline.
- `app.py` — the single-page Streamlit UI wiring all of the above together.

## Honest note on what's real vs. simplified

**Data is synthetic.** Every series is generated placeholder data, clearly
marked as such in `data/generate_data.py`. It is **not** real SAIL
freight-rate data — see "Data" above for how a real CSV can override it.

**Genuinely computed, end-to-end, for whichever combination is selected:**
- The statistical forecast (Holt exponential smoothing), the naive baseline,
  and the P10/P50/P90 band (from real holdout-forecast residuals, widened
  with a sqrt(t) random-walk assumption — a deliberately crude but real
  uncertainty estimate, not a formal ARIMA confidence interval).
- Probability of increase (empirical share of historical N-day forward moves
  that were positive).
- Feasibility pass/fail/unknown badges (real comparisons against the specs/limits
  tables below — "unknown" only ever means the port limit isn't defined, never a
  silently assumed pass or fail; some ports deliberately have several limits
  undefined, so "Unknown" keeps showing up genuinely, not just at one port).
- The risk score's volatility component (coefficient of variation over the
  recent window of the actual series).
- The Charter Now / Wait / Monitor recommendation and its listed reasons
  (an explicit point-scoring rule over forecast direction, probability of
  increase, and risk level).
- The three-way cost comparison (spot-only, short-term multi-voyage, medium-term
  single contract) computed from the forecast and the requirement's actual
  cargo quantity — the cheapest of the three is what "Cheapest strategy" reports.
- The backtest's "estimated savings vs. spot-only" figure (re-runs the exact
  same rule at ~18 past decision points using only data available before
  each point — no look-ahead — then compares to what spot-only would have cost).
  **This is always a backtested/simulated estimate over a limited number of
  historical points, not a guarantee of future performance**, and the UI
  labels it that way every time it's shown.
- Holdout MAE/RMSE for both the naive baseline and the statistical forecast
  (same train/test split used for the P10/P90 band, computed independently
  so it can never change the forecast, band, risk score, or backtest numbers).
- The cost-efficiency table/chart across all four vessel classes (not just
  the selected vessel): feasibility comes from the same `feasibility.py`
  checks used elsewhere, utilization is cargo quantity ÷ vessel DWT
  (capped at 100%), and cost uses the same current rate and contract premium
  as the Recommendation section, adjusted per vessel class by the
  illustrative economies-of-scale discount described below (the dataset
  itself only carries one route-level spot rate, not a rate per vessel
  class). The "cost-efficient choice" is the lowest-cost feasible vessel,
  ties broken by the best (highest) utilization. When no vessel class is
  feasible at the selected port (this genuinely happens, e.g. most vessel
  classes at the shallow-draft Haldia/Sagar-Sandheads ports), the app says
  so instead of forcing a choice.

**Hardcoded / manually set (illustrative, not fetched or surveyed):**
- Vessel-class specs (draft/LOA/beam/DWT for Handysize/Supramax/Panamax/Capesize)
  and port limits (all 7 destinations) in `feasibility.py` are representative
  approximations, not a class-society or port-authority source.
- Port congestion and vessel availability are sliders the user sets by hand in
  the sidebar — not pulled from any live AIS/port feed. They still feed into
  a real, computed risk score; they just aren't live data.
- The contract premium (1.5% for the medium-term single contract, 1.0% for
  the short-term multi-voyage tier) used in the cost comparisons are
  simplifying assumptions, not derived from real charter-party terms.

### Vessel-class cost-discount assumption

The vessel-comparison chart ("Cost efficiency across feasible vessels") used
to show an identical cost for every feasible vessel class, because the
dataset carries one route-level spot rate rather than a rate per vessel
class — a flat, uninformative chart. To make the comparison meaningful,
`recommendation.py` now applies a documented, illustrative
**economies-of-scale discount** per vessel class before computing that
chart's cost:

```python
VESSEL_CLASS_COST_DISCOUNT = {
    "Handysize": 0.00,
    "Supramax": 0.03,
    "Panamax": 0.06,
    "Capesize": 0.10,
}
```

**What it is:** a placeholder assumption that larger vessels spread fixed
voyage/port costs over more cargo, so their effective $/mt cost is lower.
**Why it exists:** we have no live source for real per-vessel-class freight
differentials on a given route — only one observed rate per route/vessel
combination — so without this adjustment the comparison chart would be flat
and uninformative regardless of vessel choice. **It is not real market
data** — the magnitudes are indicative, not sourced from a specific freight
index, and should be replaced with real vessel-class rate data (or removed)
if/when that becomes available. It is scoped narrowly: it only affects
`compare_vessel_costs()` (the vessel-comparison chart) and does **not**
touch `cost_comparison()` (the main Recommendation section's three-way cost
comparison), the backtest, or port feasibility checks.

**Deliberately out of scope for tonight** (per the brief): no LSTM/XGBoost/
TimesFM/Chronos-2 model benchmarking, no database, no multi-user auth, no
multi-page navigation. The forecasting method is intentionally simple
(Holt exponential smoothing) so it's fast, explainable, and honestly framed
as a baseline statistical model rather than a production forecasting engine.
