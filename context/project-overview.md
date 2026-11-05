# Project Overview

## About the Project

This project is being developed for Smart India Hackathon 2026, Problem Statement 26006, submitted by SAIL (Steel Authority of India Limited) under the Ministry of Steel, in the Transportation & Logistics category.

SAIL currently relies heavily on daily freight-market exploration and individual spot contracts for bulk-cargo procurement from overseas origins to ports on India's East Coast. This project builds a decision-support system that helps SAIL move from a reactive, spot-market-driven process toward a proactive, predictive chartering strategy, particularly for short-term and medium-term multiple-voyage contracts.

The central technical challenge is freight-rate forecasting. Freight-rate forecasting is the central intelligence layer of the system. Vessel feasibility, charter timing, contract strategy comparison, and risk assessment are downstream decision-support modules that consume the forecast's outputs — they do not operate independently of it.

The product concept flows as:

```
USER REQUIREMENT
→ DATA + MARKET CONTEXT
→ FREIGHT FORECAST
→ FORECAST UNCERTAINTY + MARKET RISK
→ VESSEL FEASIBILITY
→ CHARTER / CONTRACT DECISION
→ EXPLAINABLE RECOMMENDATION
→ DASHBOARD
```

North Star: Given a real cargo procurement requirement today, the system uses information that was actually available today to estimate future freight-rate distributions, assess uncertainty and operational constraints, and recommend a commercially sensible chartering strategy — with evidence from historical backtesting that the strategy would have improved upon a reasonable baseline.

This is a **decision-support system**. It is explicitly **not** an autonomous chartering system. It does not execute contracts, book vessels, move money, or communicate with shipowners/brokers on SAIL's behalf.

**Initial geographic scope** — overseas origins: Australia, United States, Mozambique, Russia, Indonesia. Indian East Coast destinations: Paradip, Visakhapatnam/Vizag, Gangavaram, Gopalpur, Dhamra, Sagar/Sandheads, Haldia. The product should be designed so additional routes/ports can be added later without redesign.

**Initial vessel scope**: Handysize, Supramax, Panamax, Capesize. The product must not be designed around a single vessel class.

**Cargo scope**: Coal is the primary example/use case for the initial implementation. The conceptual data model should allow other dry-bulk commodities if suitable data becomes available, but the system must not claim to support all commodities initially.

## The Problem It Solves

The system should help a SAIL procurement/freight decision-maker answer:

1. What is the current/expected freight rate?
2. Where is the freight rate likely to move over the next 7/14/30/60 days?
3. How uncertain is that forecast?
4. Is the market likely to rise or fall?
5. When should SAIL enter the charter market?
6. Which vessel class is operationally/economically suitable?
7. Should SAIL use spot, short-term, or medium-term multiple-voyage contracting?
8. What market, port, vessel, or external risks could materially affect the decision?
9. What would historically have happened if SAIL followed the system's recommendations?

The system must connect forecasting to a commercial decision — it must not merely display a predicted freight number. Every recommendation must be explainable in business terms, not presented as an opaque model output.

### Critical product principle: point-in-time information

All recommendations, and especially all historical backtesting, must be based only on information that would genuinely have been available at the decision timestamp. For example, if forecasting on 1 September, an observed bunker price from 15 September must never be treated as known on 1 September. This principle governs both the live recommendation flow and the backtesting/economic-validation functionality, and must be respected by any AI agent implementing data pipelines, feature construction, or backtest logic.

## Pages

The initial product contains five main pages.

### 1. Decision Dashboard
The primary decision-making page. Shows: cargo requirement, route, current freight, forecast, recommended vessel, charter timing, contract strategy, risk level, and estimated savings (backtested estimate, not a guarantee).

### 2. Freight Forecast
Interactive view containing: historical freight, 7/14/30/60-day forecasts, prediction intervals, and model comparison.

### 3. Port / Vessel Feasibility
Shows: candidate vessel classes, draft, LOA, beam, DWT, port limits, and pass/fail explanations for each constraint.

### 4. Risk
Shows: market volatility, congestion, vessel availability, disruption indicators, and forecast uncertainty.

### 5. Backtesting / Model Performance
Shows: MAE, RMSE, sMAPE, directional accuracy, and economic simulation results. This page exists both for technical credibility and to validate whether the system's recommendations have historical evidence behind them.

## Navigation

The Decision Dashboard is the primary landing page and the default entry point for the user's workflow. From it, the user can navigate to the Freight Forecast, Port/Vessel Feasibility, Risk, and Backtesting/Model Performance pages to inspect the evidence underlying a given recommendation. These four supporting pages are detail/drill-down views for the recommendation shown on the Decision Dashboard, not independent workflows. A user should be able to move from "what is the recommendation" (Decision Dashboard) to "why" (the four supporting pages) without losing the context of the procurement requirement they entered.

## Core User Flow

1. User enters cargo/procurement requirement (see required/optional inputs below).
2. System retrieves relevant historical route/vessel freight data.
3. System retrieves available market and external variables.
4. System checks data availability and timestamps, respecting the point-in-time information principle.
5. System constructs forecasting inputs/features.
6. Forecasting layer generates forecasts for the supported horizons.
7. System produces uncertainty/prediction intervals around the forecast (not a single point estimate).
8. System estimates direction/probability of rate movement (e.g., probability of increase vs. decrease).
9. System evaluates feasible vessel classes against explicit operational constraints.
10. System evaluates charter timing (e.g., charter now vs. wait/monitor) based on forecast and uncertainty.
11. System compares contract strategies (repeated spot, short-term multiple-voyage, medium-term multiple-voyage).
12. System evaluates risk across market, port, vessel, and external categories.
13. System generates an explainable recommendation that references the specific factors behind it.
14. System presents the recommendation on the Decision Dashboard.
15. User can inspect the supporting forecast, feasibility, risk, and backtesting views to understand the evidence behind the recommendation.

### Example: user-provided requirement

```
Cargo: Coal
Quantity: 50,000 MT
Origin: Australia
Destination: Paradip
Loading: 15–25 Sep
Voyages: 3
Contract horizon: 6 months
```

**Required inputs**: cargo type, cargo quantity, origin, destination, first loading window, number of voyages, contract horizon.

**Optional inputs**: preferred vessel class, maximum acceptable freight, required delivery deadline, minimum/maximum parcel size, risk preference, preferred contract duration, number of expected cargo parcels, commercial constraints.

The user must not be asked to manually supply market, vessel, or port facts that the system can obtain from its own data sources (freight data, vessel data, port data, market variables — see Data Architecture).

### Example: system output

```
Current: $28.4/MT
30-day P50: $34.2/MT
P10–P90: $29.5–$40.0
Probability increase: 78%

Recommendation:
Charter timing: NOW
Vessel: Supramax
Contract: 3 voyages
Risk: MEDIUM
Expected savings vs spot-only: backtested estimate
```

### Example: explainability

```
RECOMMENDATION: CHARTER NOW

Reasons:
- Forecasted freight increase: +18%
- Probability of increase: 78%
- Current rate below predicted 30-day median
- Vessel availability currently favorable
- Port congestion risk: Low
```

### Example: vessel feasibility

```
Supramax
- Draft: PASS
- LOA: PASS
- Beam: PASS
- Cargo capacity: PASS
→ Operationally feasible

Panamax
- Draft: FAIL
→ Not feasible
```

Vessel feasibility results must always be explained against explicit constraints (draft, LOA, beam, DWT, berth/tidal/seasonal restrictions, etc.) — never presented as a hard-coded or arbitrary recommendation.

The system must never claim a longer contract is better merely because its expected rate is lower; contract flexibility, uncertainty, and commitment must be weighed as part of the comparison. All statements about future savings must be phrased as backtested/estimated, never guaranteed.

## Data Architecture

This section describes product-level entities and their relationships conceptually. Detailed database schema, storage technology, and implementation-level design belong in `architecture.md`, not here.

### Conceptual entities

- **Procurement Requirement** — the cargo/route/timing/contract request entered by the user for a given decision.
- **Cargo** — cargo type and quantity characteristics associated with a requirement.
- **Route** — an origin–destination pairing within the supported geographic scope.
- **Port** — reference data for a specific port (draft, LOA, beam, berth, handling, congestion, turnaround characteristics).
- **Vessel / Vessel Class** — reference and/or instance-level data describing vessel classes (Handysize, Supramax, Panamax, Capesize) and, where available, individual vessels.
- **Freight Observation** — a historical freight-rate data point tied to date, route, vessel class, and cargo type.
- **Market Observation** — a historical market/external variable data point (e.g., bunker price, index value, FX rate) tied to a timestamp.
- **Forecast** — a generated freight-rate forecast for a route/vessel-class combination and horizon, produced from information available as of the decision timestamp.
- **Forecast Distribution / Prediction Interval** — the uncertainty representation (e.g., P10/P50/P90) associated with a Forecast.
- **Risk Assessment** — a derived, explainable risk evaluation across market, port, vessel, and external categories for a given requirement/recommendation.
- **Vessel Feasibility Result** — the pass/fail evaluation of a candidate vessel class against operational constraints for a given requirement.
- **Charter Timing Recommendation** — the derived "charter now" vs. "wait/monitor" decision output, with supporting reasons.
- **Contract Strategy** — a comparison record for a candidate contracting approach (repeated spot, short-term multiple-voyage, medium-term multiple-voyage) including expected expenditure, risk, and flexibility characteristics.
- **Recommendation** — the overall explainable output combining timing, vessel, contract strategy, and risk for a given Procurement Requirement.
- **Backtest Result** — the outcome of running the system's historical recommendation logic against past point-in-time data, evaluated against a reasonable baseline.

### Data categories

Clarify which data represents:

1. **User-provided procurement requirements** — data entered per-session by the SAIL user (Procurement Requirement, Cargo, optional constraints). This is request-scoped, not shared reference data.
2. **Shared reference/master data** — Route, Port, and Vessel/Vessel Class data. This is shared maritime market/reference data, not data owned by an individual user account. Do not model this as user-owned data; this is an enterprise decision-support application operating on shared market and reference data, not a consumer SaaS application with per-user data silos.
3. **Historical market data** — Freight Observation and Market Observation records, ingested over time and always tagged with the timestamp at which they became available.
4. **Forecast outputs** — Forecast and Forecast Distribution/Prediction Interval records generated by the forecasting layer.
5. **Derived decision-support results** — Vessel Feasibility Result, Charter Timing Recommendation, Contract Strategy, Risk Assessment, and Recommendation — all downstream consumers of the Forecast.
6. **Historical evaluation results** — Backtest Result records used for model-performance and economic-validation reporting.

### Data availability categories (subject to actual dataset availability)

- **Freight data**: historical freight rates, timestamp/date, origin, destination, vessel class, cargo type, cargo quantity/parcel size, spot/contract classification where available, relevant freight/shipping indices.
- **Vessel data**: vessel class, DWT, LOA, beam, draft, availability, position (if available), historical utilization, ballast/laden status (if available).
- **Port data**: maximum draft, maximum LOA, maximum beam, berth limitations, berth capacity, cargo handling rate, storage/handling constraints, historical turnaround time, historical congestion, waiting time, port operating restrictions.
- **Market variables** (potential): bunker/fuel prices, coal/commodity prices, relevant Baltic/shipping indices, FX rates, interest rates, industrial production, global trade indicators, steel production, energy demand, vessel orderbook/fleet growth, scrapping, vessel availability, port congestion.
- **External/disruption variables** (where reliable data is available): weather, monsoon indicators, storm events, route disruptions, sanctions/trade restrictions, geopolitical event indicators, major port closures.

Not every listed variable is guaranteed to be available in the first release. Which external features are actually implemented is determined by real dataset availability, and this must be treated as a genuine constraint by any implementing agent — not worked around by fabricating or assuming data.

## Features In Scope

Required for the initial credible SIH deliverable:

- Procurement requirement input (required and optional fields as specified above)
- Route selection within the initial geographic scope
- Historical freight retrieval
- Forecast generation for supported origin–destination/vessel-class combinations
- Multiple forecast horizons (7, 14, 30, 60 days; 90 days may be considered later)
- Probabilistic forecast / uncertainty display (e.g., P10/P50/P90), not a point estimate alone
- Forecast direction/probability (probability of increase/decrease, expected % change, volatility, directional confidence)
- Vessel feasibility evaluation against explicit operational constraints
- Port constraint evaluation
- Charter timing recommendation (e.g., charter now vs. wait/monitor)
- Contract strategy comparison (repeated spot, short-term multiple-voyage, medium-term multiple-voyage)
- Risk assessment across market, port, vessel, and external categories, explainable rather than arbitrary
- Explainable recommendations (reasons behind timing, vessel, and contract outputs)
- Backtesting using chronological/rolling evaluation and point-in-time information only
- Model-performance metrics (MAE, RMSE, sMAPE, directional accuracy)
- Economic simulation of the recommendation strategy against a reasonable baseline
- Decision Dashboard
- Freight Forecast dashboard
- Vessel/Port Feasibility dashboard
- Risk dashboard
- Backtesting/Model Performance dashboard

Functionality that depends on actual data availability (e.g., specific external/disruption variables, additional commodities beyond coal, additional routes/ports beyond the initial scope) should be clearly flagged as data-dependent rather than presented as guaranteed initial functionality.

## Features Out of Scope

The following are explicitly excluded to prevent scope creep:

- Autonomous execution of real charter contracts
- Automatic financial transactions
- Automatic vessel booking
- Automatic communication with shipowners/brokers
- Guaranteed freight-rate predictions
- Guaranteed savings
- Fully autonomous procurement decisions
- A general-purpose chatbot unrelated to the decision workflow
- A generic CRM
- A generic ERP
- Consumer account-management functionality unrelated to the enterprise workflow
- Random train/test split evaluation as the primary validation method (chronological/point-in-time backtesting is required instead)
- Claims that one ML architecture is automatically superior to another
- Hard-coded vessel recommendations without constraint evaluation
- Unexplained arbitrary risk scores
- Use of future information in historical backtesting
- Features that require unavailable proprietary data, unless clearly marked as future/integration-dependent work

If a capability is useful but not necessary for the SIH demonstration, it should be classified as future work rather than silently included.

## Target User

The primary user is an enterprise freight/procurement decision-maker at SAIL involved in overseas bulk-cargo procurement and vessel chartering decisions.

The user should be assumed to:

- Understand cargo procurement and shipping terminology
- Need commercially actionable information, not raw model output
- Need to evaluate tradeoffs rather than simply view ML predictions
- Prefer concise explanations of why a recommendation was generated
- Need evidence supporting recommendations
- Need to understand uncertainty and operational feasibility

The user is **not** assumed to be a machine-learning engineer. The system should expose technical evidence where useful — especially through the Backtesting/Model Performance page — while keeping the main Decision Dashboard focused on business decisions rather than model internals.

## Success Criteria

1. A user can enter a realistic cargo procurement requirement (cargo type, quantity, origin, destination, loading window, number of voyages, contract horizon) and receive a response.
2. The system can produce forecasts for the supported horizons (7/14/30/60 days) for supported route/vessel-class combinations.
3. The system exposes uncertainty (e.g., prediction intervals) rather than only a single point forecast.
4. The system can identify operationally feasible vessel classes using explicit, explained constraints (draft, LOA, beam, DWT, port limits) rather than hard-coded outcomes.
5. The system can produce an explainable charter timing and contract strategy recommendation that references the specific forecast, feasibility, and risk factors behind it.
6. The system can surface relevant market, port, vessel, and external risk factors tied to the specific requirement.
7. The system can demonstrate chronological/rolling historical backtesting that uses only point-in-time information at each simulated decision date.
8. The system can show backtested economic performance (e.g., MAE, RMSE, sMAPE, directional accuracy, simulated savings) against a reasonable baseline, clearly labeled as a backtested/estimated result rather than a guarantee.

Success is measured by whether the end-to-end decision workflow — from procurement requirement to explainable, risk-aware, backtested recommendation — is demonstrably useful and technically credible, not merely by whether a dashboard renders.
