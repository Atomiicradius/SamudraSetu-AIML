# SIH 2026 — Problem Statement 26006
## Intelligent Freight Forecasting & Vessel Chartering Decision Support System

**Organization:** Ministry of Steel  
**Department:** SAIL  
**Problem Statement ID:** 26006  
**Category:** Software  
**Theme:** Transportation & Logistics

---

# 1. Project Context

SAIL currently relies heavily on daily freight-market exploration and individual spot contracts for bulk-cargo procurement from overseas origins to ports on India's East Coast.

Freight markets are volatile. Rates depend on shipping supply/demand, commodity markets, bunker/fuel prices, port congestion, seasonality, vessel availability, macroeconomic conditions, weather, geopolitical disruptions, and route-specific characteristics.

The project aims to move SAIL from a **reactive, spot-market-driven process** toward a **proactive, predictive chartering strategy**, especially for short-term and medium-term multiple-voyage contracts.

The central technical challenge is **freight-rate forecasting**. Vessel selection, charter timing, contract strategy, and risk warnings should be built as downstream decision-support layers on top of the forecasting and data infrastructure.

---

# 2. One-Sentence Aim

> Build an intelligent freight forecasting and chartering decision-support platform that predicts future bulk-shipping freight rates for relevant origin–destination/vessel combinations and converts those forecasts into actionable recommendations for charter timing, contract strategy, vessel feasibility, and risk management.

---

# 3. Primary Objective

Develop a robust, explainable, backtested forecasting system capable of answering:

1. **What is the current/expected freight rate?**
2. **Where is the freight rate likely to move over the next 7/14/30/60 days?**
3. **How uncertain is that forecast?**
4. **Is the market likely to rise or fall?**
5. **When should SAIL enter the charter market?**
6. **Which vessel class is operationally/economically suitable?**
7. **Should SAIL use spot, short-term, or medium-term multiple-voyage contracting?**
8. **What risks or disruptions could materially affect the decision?**
9. **What would historically have happened if SAIL followed the system's recommendations?**

---

# 4. Scope

## 4.1 Initial geographic scope

Focus on overseas bulk-cargo movements into India's East Coast.

Relevant origins from the problem statement:

- Australia
- United States
- Mozambique
- Russia
- Indonesia

Relevant Indian East Coast destinations:

- Paradip
- Visakhapatnam / Vizag
- Gangavaram
- Gopalpur
- Dhamra
- Sagar / Sandheads
- Haldia

The architecture must be extensible to additional ports/routes.

## 4.2 Vessel classes

Initially support:

- Handysize
- Supramax
- Panamax
- Capesize

Do not hard-code the system around one vessel class.

## 4.3 Cargo

Coal is the primary example/use case from the problem statement, but the data model should allow other dry bulk commodities if relevant data becomes available.

---

# 5. Core Product Philosophy

The project should NOT be treated as:

> "Train an LSTM that predicts tomorrow's freight price."

It should be treated as:

> **A forecasting + uncertainty + decision-support system.**

The ML model is the core intelligence, but the final product is an operational decision system.

The system should separate:

### A. Forecasting
Predict future freight rates and uncertainty.

### B. Feasibility
Determine whether vessels can physically/operationally serve a route.

### C. Decision optimization
Convert forecasts and operational constraints into charter recommendations.

### D. Risk
Detect abnormal volatility, congestion, forecast uncertainty, and disruptions.

### E. Explainability
Tell the user WHY the system recommends an action.

---

# 6. User Inputs

The user should provide only information specific to the procurement requirement.

## Required inputs

| Input | Example |
|---|---|
| Cargo type | Coal |
| Cargo quantity | 50,000 MT |
| Origin | Australia |
| Destination | Paradip |
| First loading window | 15–25 Sep 2026 |
| Number of voyages | 3 |
| Contract horizon | 6 months |

## Optional inputs

- Preferred vessel class
- Maximum acceptable freight
- Required delivery deadline
- Minimum/maximum parcel size
- Risk preference
- Preferred contract duration
- Number of expected cargo parcels
- Commercial constraints

The user should NOT manually enter market, vessel, or port facts that the system can obtain from its databases.

---

# 7. Data Automatically Supplied to the System

The system should maintain/consume:

## 7.1 Freight data

- Historical freight rates
- Date/time
- Origin
- Destination
- Vessel class
- Cargo type
- Cargo quantity/parcel size
- Contract/spot classification where available
- Relevant freight/shipping indices

## 7.2 Vessel data

- Vessel class
- DWT
- LOA
- Beam
- Draft
- Current/estimated availability
- Position, if available
- Historical utilization
- Ballast/laden status, if available

## 7.3 Port data

For every origin and destination port:

- Maximum draft
- Maximum LOA
- Maximum beam
- Berth limitations
- Berth count/capacity
- Cargo handling rate
- Storage/handling constraints
- Historical turnaround time
- Historical congestion
- Waiting time
- Port operating restrictions

## 7.4 Market variables

Potential features:

- Bunker/fuel prices
- Coal/commodity prices
- Relevant Baltic/shipping indices
- FX rates
- Interest rates
- Industrial production
- Global trade indicators
- Steel production
- Energy demand
- Vessel orderbook / fleet growth
- Scrapping
- Vessel availability
- Port congestion

## 7.5 External/disruption variables

Where data is reliable:

- Weather
- Monsoon indicators
- Storm events
- Canal/route disruptions
- Sanctions/trade restrictions
- Geopolitical event indicators
- Major port closures

---

# 8. Important Terminology

## Freight rate

Cost of transporting cargo by sea, commonly represented as USD/metric tonne for voyage freight.

Example:

50,000 MT × $30/MT = $1.5M freight.

## Spot contract

A contract arranged for a specific immediate/near-term voyage.

## Multiple-voyage contract

One contractual arrangement covering multiple cargo movements/voyages over a defined period.

## Charter

Hiring a vessel under a commercial agreement.

## DWT

Deadweight tonnage — carrying capacity by weight, including cargo and other deadweight components.

## Draft

Vertical distance from the waterline to the lowest part of the ship. Critical for port access.

## LOA

Length Overall — total ship length.

## Beam

Maximum ship width.

## Berth

Designated location where a vessel docks for loading/unloading.

## Port congestion

Excess demand for port capacity causing waiting and/or turnaround delays.

## Idle time

Time during which a vessel is not productively operating, including relevant waiting periods.

## Deadheading / repositioning

Movement without useful cargo/employment, potentially increasing cost.

## Trade lane

A recurring origin–destination shipping route.

---

# 9. Forecasting Problem Definition

The forecasting problem should be defined explicitly before model development.

A forecast target should be a well-defined freight rate such as:

> Freight rate in USD/MT for a specified origin–destination route, vessel class, cargo type, and commercial basis.

Example:

> Australia → Paradip, Panamax, coal, voyage freight, USD/MT.

Avoid mixing fundamentally different rate definitions into one target without normalization.

---

# 10. Forecast Horizons

The system should support multiple horizons.

Recommended initial horizons:

- 7 days
- 14 days
- 30 days
- 60 days

Potentially:

- 90 days

Do not assume that forecast accuracy will be equally good across horizons.

The dashboard should make horizon-specific uncertainty explicit.

---

# 11. Forecast Output

The model should ideally provide a **probabilistic forecast**, not only one point estimate.

Example:

```text
Current estimated freight: $28.4/MT

7-day:
P10 = $27.2
P50 = $29.0
P90 = $31.1

30-day:
P10 = $29.5
P50 = $34.2
P90 = $40.0
```

The system should also calculate:

- Expected/median freight
- Prediction interval
- Probability of rate increase
- Probability of rate decrease
- Expected percentage change
- Volatility/uncertainty score
- Directional confidence

---

# 12. Model Strategy

Do NOT immediately commit to one model.

Use a model benchmark.

## Tier 1 — Baselines

### Naive

Example:

Forecast = latest observed freight.

### Seasonal naive

Forecast based on comparable historical seasonal observations where appropriate.

These establish whether ML actually adds value.

---

# 13. Model 2 — Statistical Model

Candidate:

- ARIMA/SARIMA
- Exponential smoothing

Purpose:

- Classical benchmark
- Understand seasonality/trend
- Establish a non-neural baseline

Do not over-invest in statistical models if modern models clearly outperform them.

---

# 14. Model 3 — Gradient Boosting

Primary candidate:

- XGBoost
- LightGBM

This is an important baseline and may become the production model if it performs best.

Create engineered features such as:

### Lag features

- freight_lag_1
- freight_lag_3
- freight_lag_7
- freight_lag_14
- freight_lag_30
- freight_lag_60

### Rolling features

- rolling_mean_7
- rolling_mean_14
- rolling_mean_30
- rolling_std_7
- rolling_std_30
- rolling_min/max

### Market features

- bunker_price
- commodity_price
- shipping_index
- vessel_availability
- port_congestion

### Calendar features

- day of week
- month
- quarter
- day of year
- seasonal indicators

### Route/vessel features

- origin
- destination
- vessel class
- route distance
- vessel capacity

Categorical features should be encoded appropriately.

---

# 15. Model 4 — LSTM/GRU

Use LSTM or GRU as a neural-network benchmark.

Typical conceptual input:

```text
Past N time steps
      ↓
LSTM/GRU
      ↓
Dense/output head
      ↓
7/14/30/60-day forecast
```

Possible initial sequence lengths to test:

- 30 days
- 60 days
- 90 days
- 180 days

Do NOT assume 90 is optimal. Select through validation.

LSTM should not automatically be considered the final model.

---

# 16. Model 5 — TimesFM

Primary foundation-model candidate:

> Google Research TimesFM / TimesFM 2.5

Use it in at least two modes where practical:

### Zero-shot

Use pretrained TimesFM without domain-specific fine-tuning.

### Domain adaptation

Evaluate fine-tuning/LoRA if the dataset and implementation support it.

TimesFM 2.5 supports external covariates through its XReg functionality and has LoRA/PEFT fine-tuning examples.

Use it as a serious candidate, not merely a novelty model.

---

# 17. Model 6 — Chronos-2

Primary foundation-model candidate:

> Amazon Chronos-2

Chronos-2 is especially relevant because it supports:

- Univariate forecasting
- Multivariate forecasting
- Covariate-informed forecasting
- Probabilistic forecasting

Evaluate:

### Zero-shot Chronos-2

versus

### Fine-tuned/domain-adapted Chronos-2

if the implementation and compute budget allow it.

---

# 18. Why Use Multiple Models?

There is no guarantee that a foundation model will outperform a well-engineered XGBoost model on this specific freight dataset.

Freight data may be:

- sparse
- noisy
- regime-changing
- route-specific
- highly affected by external events

Therefore the project should use empirical backtesting rather than assumptions.

Recommended comparison:

| Model | MAE | RMSE | sMAPE | Direction Accuracy | Interval Coverage | Economic Score |
|---|---:|---:|---:|---:|---:|---:|
| Naive | | | | | | |
| Seasonal Naive | | | | | | |
| ARIMA | | | | | | |
| XGBoost | | | | | | |
| LSTM | | | | | | |
| TimesFM | | | | | | |
| Chronos-2 | | | | | | |
| Ensemble | | | | | | |

The final model should be selected based on **out-of-sample performance**, not popularity.

---

# 19. Ensemble Strategy

If different models perform well under different market conditions, combine them.

Example:

```text
Final Forecast =
0.50 × Chronos-2
+ 0.30 × XGBoost
+ 0.20 × TimesFM
```

Do not manually choose these weights.

Learn ensemble weights using a validation set or rolling-origin backtesting.

Potential approaches:

- Weighted average
- Stacking
- Meta-model
- Regime-dependent weighting

A simpler weighted ensemble is preferable for the initial SIH implementation.

---

# 20. Model Inputs

The exact model input depends on the architecture.

## Common target

```text
freight_rate
```

## Historical target information

- lagged freight
- rolling statistics
- historical volatility
- trend
- rate changes

## Exogenous variables

Potential examples:

- bunker price
- coal price
- shipping index
- vessel supply/availability
- port congestion
- FX
- commodity demand proxies
- macroeconomic variables
- weather/disruption indicators

## Static/context variables

- origin
- destination
- vessel class
- cargo type
- route distance
- typical parcel size

---

# 21. Critical Data Leakage Rule

This is one of the most important project rules.

At prediction time, the model must only receive information that would genuinely have been available at that prediction timestamp.

Example:

If forecasting freight for the next 30 days on 1 September:

```text
Known on 1 Sep
    ↓
Can be used

Actual bunker price on 15 Sep
    ↓
UNKNOWN on 1 Sep
    ↓
Cannot be directly used
```

Do not use future observed values of:

- freight
- congestion
- bunker prices
- commodity prices
- vessel availability
- weather

unless those future values were genuinely known/forecast and would have been available at inference time.

This rule must be enforced in dataset construction and backtesting.

---

# 22. Forecasting Dataset Structure

Recommended canonical data table:

```text
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
...
```

The actual schema should be adapted to the available data.

For multiple routes, each route/vessel combination can be treated as a separate series or as grouped multivariate data.

---

# 23. Time-Series Splitting

Never use random train/test splitting for the primary evaluation.

Use chronological splitting.

Example:

```text
2018 ───────── 2022 | 2023 | 2024 | 2025 | 2026
        TRAIN       | VAL  | TEST
```

Better:

## Rolling-origin backtesting

Example:

```text
Train: 2018–2021 → predict 2022
Train: 2018–2022 → predict 2023
Train: 2018–2023 → predict 2024
Train: 2018–2024 → predict 2025
```

This better represents actual deployment.

---

# 24. Evaluation Metrics

Do not use only RMSE.

## Statistical metrics

### MAE

Mean Absolute Error.

Easy to interpret.

### RMSE

Penalizes large errors.

### sMAPE

Useful for relative error while avoiding some MAPE issues.

### MASE

Consider if appropriate for comparing across series.

---

# 25. Business Metrics

The ultimate goal is not to win an ML leaderboard.

The system exists to improve chartering decisions.

Therefore calculate:

## Directional accuracy

Percentage of times the model correctly predicts:

- rate increases
- rate decreases

## Turning-point detection

Can the model detect meaningful upcoming rate changes?

## Charter simulation

Backtest:

> If SAIL followed the system's recommendations historically, what would the estimated freight expenditure have been?

Compare:

- Always spot
- Simple fixed strategy
- Forecast-based strategy
- Forecast + risk-aware strategy

Potential output:

```text
Historical simulation

Spot-only cost:          ₹100.0 Cr
Forecast strategy:       ₹94.2 Cr
Estimated saving:          ₹5.8 Cr
Saving percentage:          5.8%
```

All savings claims must clearly state that they are **backtested/simulated**, not guaranteed future savings.

---

# 26. Risk Engine

Risk should initially be a decision-support layer rather than an unnecessarily complex independent AI model.

Potential risk signals:

## Market risk

- Forecast volatility
- Wide prediction interval
- Large expected price movement
- Unusual historical deviation

## Port risk

- Rising congestion
- Increased waiting time
- Reduced berth availability
- Weather-related restrictions

## Vessel risk

- Low vessel availability
- High positioning cost
- Route mismatch
- Draft/LOA/beam incompatibility

## External risk

- Major weather events
- Geopolitical disruptions
- Route closures
- Sanctions/trade restrictions

---

# 27. Risk Score

Possible initial formulation:

```text
Risk Score =
w1 × Market Volatility
+ w2 × Forecast Uncertainty
+ w3 × Port Congestion
+ w4 × Vessel Availability Risk
+ w5 × Disruption Risk
```

Normalize each component to 0–100.

Then classify:

```text
0–30    LOW
31–60   MEDIUM
61–100  HIGH
```

The weights should eventually be calibrated using historical outcomes or expert input.

Do not pretend arbitrary weights are statistically optimal.

---

# 28. Vessel Feasibility Engine

This should initially be deterministic/rule-based.

For every candidate vessel:

```text
DWT >= required cargo capacity
AND
draft <= destination maximum draft
AND
LOA <= destination maximum LOA
AND
beam <= destination maximum beam
AND
origin constraints satisfied
AND
cargo handling constraints satisfied
```

Additional constraints can include:

- berth restrictions
- tidal restrictions
- seasonal restrictions
- loading/unloading rates
- expected turnaround time

Output:

```text
Panamax
Draft: FAIL

Supramax
Draft: PASS
LOA: PASS
Beam: PASS
Cargo capacity: PASS

→ Operationally feasible
```

---

# 29. Vessel Recommendation

After filtering infeasible vessels, rank feasible options based on:

- Expected freight cost
- Capacity utilization
- Port compatibility
- Expected turnaround
- Idle-time risk
- Vessel availability
- Repositioning/deadheading cost

Example:

```text
Vessel       Feasible    Expected Cost    Idle Risk
Handysize      YES          High            Low
Supramax       YES          Low             Low
Panamax        NO           —               —
Capesize       NO           —               —
```

Recommendation:

> Supramax

The recommendation must be explainable.

---

# 30. Charter Timing Engine

The forecasting model predicts the future freight distribution.

The decision engine converts that into a timing recommendation.

Example:

```text
Current rate:          $28/MT
30-day median:         $34/MT
Probability increase:  78%
```

Recommendation:

> CHARTER NOW

Conversely:

```text
Current:       $35
30-day median: $29
```

Recommendation:

> WAIT / MONITOR

The engine should consider uncertainty rather than only the median forecast.

---

# 31. Contract Strategy Engine

Compare:

### Strategy A
Repeated spot contracts

### Strategy B
Short-term multiple-voyage contract

### Strategy C
Medium-term multiple-voyage contract

For each strategy estimate:

- Expected freight expenditure
- Risk
- Price uncertainty
- Flexibility
- Commitment
- Expected savings versus baseline

Example:

```text
Strategy             Expected Cost     Risk
Spot                 ₹100 Cr           High
3-voyage contract     ₹96 Cr           Medium
6-voyage contract     ₹95 Cr           High commitment

Recommended: 3-voyage
```

Do not recommend a long-term contract purely because its expected rate is lower. Contract flexibility and uncertainty matter.

---

# 32. Decision Objective

A conceptual optimization objective:

```text
Minimize:

Expected Freight Cost
+ Idle Cost
+ Congestion Cost
+ Repositioning Cost
+ Risk Penalty
+ Contract Commitment Penalty
```

subject to:

```text
Cargo requirements
Port constraints
Vessel constraints
Delivery windows
Contract constraints
Operational feasibility
```

This separates forecasting from optimization.

---

# 33. Overall Architecture

```text
                         ┌─────────────────────┐
                         │      USER/UI        │
                         │                     │
                         │ Cargo               │
                         │ Quantity            │
                         │ Origin              │
                         │ Destination         │
                         │ Loading window      │
                         │ Contract horizon    │
                         └──────────┬──────────┘
                                    │
                                    ↓
                    ┌─────────────────────────────┐
                    │     REQUEST PROCESSOR       │
                    └─────────────┬───────────────┘
                                  │
                 ┌────────────────┼────────────────┐
                 ↓                ↓                ↓
        ┌────────────────┐ ┌───────────────┐ ┌──────────────┐
        │ Freight DB     │ │ Port/Vessel DB│ │ External Data│
        └───────┬────────┘ └───────┬───────┘ └──────┬───────┘
                └──────────────────┼────────────────┘
                                   ↓
                         ┌──────────────────┐
                         │ Data Processing  │
                         │ & Feature Engine │
                         └────────┬─────────┘
                                  ↓
                    ┌────────────────────────────┐
                    │    Forecasting Layer      │
                    │                            │
                    │ XGBoost                   │
                    │ LSTM/GRU                  │
                    │ TimesFM                    │
                    │ Chronos-2                 │
                    └─────────────┬──────────────┘
                                  ↓
                    ┌────────────────────────────┐
                    │ Forecast + Uncertainty     │
                    └─────────────┬──────────────┘
                                  ↓
             ┌────────────────────┼────────────────────┐
             ↓                    ↓                    ↓
      ┌──────────────┐    ┌────────────────┐   ┌───────────────┐
      │ Vessel       │    │ Charter/Contract│   │ Risk Engine   │
      │ Feasibility  │    │ Optimization   │   │               │
      └──────┬───────┘    └───────┬────────┘   └───────┬───────┘
             └────────────────────┼────────────────────┘
                                  ↓
                         ┌──────────────────┐
                         │ Recommendation   │
                         │ & Explanation     │
                         └────────┬─────────┘
                                  ↓
                         ┌──────────────────┐
                         │    DASHBOARD     │
                         └──────────────────┘
```

---

# 34. Recommended Tech Stack

## Backend

Recommended:

- Python
- FastAPI

Why:

- Strong ML ecosystem
- Easy model serving
- Fast API development
- Good separation between ML and frontend

## Data processing

- pandas
- NumPy
- Polars if performance becomes relevant

## ML

- scikit-learn
- XGBoost
- LightGBM
- PyTorch
- Hugging Face ecosystem
- TimesFM
- Chronos-2

## Optimization

Potential:

- OR-Tools
- scipy.optimize
- custom optimization where simple

## Database

For prototype:

- PostgreSQL

Potential extensions:

- TimescaleDB for time-series-heavy workloads
- PostGIS if geospatial vessel/port analysis becomes relevant

## Frontend

Recommended:

- React
- TypeScript
- Tailwind CSS
- Recharts / Plotly

Alternative for rapid prototype:

- Streamlit

For SIH demo quality, a React dashboard is preferable if the team has frontend capacity.

## Deployment

Possible:

- Docker
- FastAPI backend
- PostgreSQL
- React frontend

Cloud deployment can be added if required.

---

# 35. Suggested Python Project Structure

```text
project/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── external/
│
├── notebooks/
│   ├── eda/
│   ├── forecasting/
│   └── backtesting/
│
├── src/
│   ├── ingestion/
│   ├── preprocessing/
│   ├── features/
│   ├── models/
│   │   ├── baseline.py
│   │   ├── xgboost_model.py
│   │   ├── lstm_model.py
│   │   ├── timesfm_model.py
│   │   └── chronos_model.py
│   ├── forecasting/
│   ├── risk/
│   ├── vessel/
│   ├── optimization/
│   └── api/
│
├── frontend/
│
├── tests/
│
├── configs/
│
├── requirements.txt
│
└── README.md
```

---

# 36. Model Configuration Should Be Centralized

Do not hard-code model parameters throughout notebooks.

Maintain a configuration file, e.g.:

```yaml
forecast:
  horizons:
    - 7
    - 14
    - 30
    - 60

  context_lengths:
    - 30
    - 60
    - 90
    - 180

models:
  xgboost:
    n_estimators: ...
    max_depth: ...
    learning_rate: ...

  lstm:
    hidden_size: ...
    num_layers: ...
    dropout: ...
    sequence_length: ...

  timesfm:
    model: "TimesFM 2.5"

  chronos:
    model: "Chronos-2"
```

Actual values should be selected through validation rather than arbitrarily.

---

# 37. Feature Engineering Rules

For every feature ask:

1. Is it available at prediction time?
2. What is its timestamp?
3. Is it measured or forecast?
4. What is its frequency?
5. How is it aligned with the target?
6. How are missing values handled?
7. Is there potential leakage?

Do not blindly forward-fill variables where doing so creates false information.

---

# 38. Frequency Alignment

Datasets may have different frequencies:

```text
Freight         Daily
Bunker          Daily
Commodity       Daily
Macro indicator Monthly
Port congestion Hourly/Daily
Weather         Hourly
```

Choose a canonical forecasting frequency, likely daily for the first implementation.

Aggregate/resample all inputs carefully.

Example:

```text
Hourly congestion
        ↓
Daily mean/max/percentile

Monthly macro indicator
        ↓
Value available as-of each date
```

Never use a monthly value before its actual publication/availability date if that would introduce look-ahead bias.

---

# 39. Missing Data

Missing data should be treated explicitly.

Possible methods:

- Forward fill only when logically valid
- Interpolation for appropriate continuous variables
- Missing indicator features
- Model-specific handling
- Exclusion where justified

Document every imputation rule.

---

# 40. Data Quality Checks

Before model training:

- Duplicate timestamps
- Duplicate route records
- Impossible freight rates
- Negative prices where invalid
- Unit mismatches
- Sudden data-source changes
- Missing periods
- Outliers
- Incorrect port/vessel identifiers
- Timestamp/time-zone inconsistencies

Build automated validation.

---

# 41. Explainability

The dashboard should not simply say:

> "Charter now."

It should say:

> **Charter now because:**

- Forecasted freight increase: +18%
- Probability of increase: 78%
- Current rate below predicted 30-day median
- Vessel availability currently favorable
- Port congestion risk: Low

For XGBoost, use SHAP where appropriate.

For foundation models, explanations should not falsely claim that a specific feature "caused" the prediction unless the method supports that interpretation.

---

# 42. Dashboard Pages

## Page 1 — Decision Dashboard

Show:

- Cargo requirement
- Route
- Current freight
- Forecast
- Recommended vessel
- Charter timing
- Contract strategy
- Risk level
- Estimated savings

## Page 2 — Freight Forecast

Interactive:

- Historical freight
- 7/14/30/60-day forecast
- Prediction intervals
- Model comparison

## Page 3 — Port/Vessel Feasibility

Show:

- Candidate vessel classes
- Draft
- LOA
- Beam
- DWT
- Port limits
- Pass/fail explanation

## Page 4 — Risk

Show:

- Market volatility
- Congestion
- Vessel availability
- Disruption indicators
- Forecast uncertainty

## Page 5 — Backtesting / Model Performance

Show:

- MAE
- RMSE
- sMAPE
- Directional accuracy
- Economic simulation

This page is particularly useful for demonstrating technical credibility to judges.

---

# 43. Example End-to-End User Flow

User enters:

```text
Cargo: Coal
Quantity: 50,000 MT
Origin: Australia
Destination: Paradip
Loading: 15–25 Sep
Voyages: 3
Contract horizon: 6 months
```

System:

### Step 1
Retrieves relevant historical route/vessel freight data.

### Step 2
Retrieves market and external variables.

### Step 3
Checks data availability and timestamps.

### Step 4
Constructs forecasting features.

### Step 5
Runs forecasting models.

### Step 6
Produces:

```text
Current: $28.4/MT
30-day P50: $34.2/MT
P10–P90: $29.5–$40.0
Probability increase: 78%
```

### Step 7
Checks feasible vessels.

### Step 8
Estimates vessel economics/idle risk.

### Step 9
Compares spot vs multiple-voyage strategies.

### Step 10
Produces recommendation:

```text
RECOMMENDATION

Charter timing: NOW
Vessel: Supramax
Contract: 3 voyages
Risk: MEDIUM
Expected savings vs spot-only:
₹X lakh (backtested estimate)
```

### Step 11
Displays reasoning and confidence.

---

# 44. What Counts as a Strong SIH Deliverable?

The minimum credible deliverable should contain:

## 1. Working data pipeline

Historical + external data can be loaded, cleaned, aligned and transformed.

## 2. Multiple forecasting models

At minimum:

- Baseline
- XGBoost
- One deep-learning/foundation model

Ideally:

- XGBoost
- LSTM
- TimesFM
- Chronos-2

## 3. Proper backtesting

Chronological/rolling evaluation.

## 4. Probabilistic forecast

Not only a single number.

## 5. Decision engine

Forecast → charter timing/contract recommendation.

## 6. Port/vessel feasibility

Rule-based constraints.

## 7. Risk layer

Market + port + forecast uncertainty.

## 8. Dashboard

User-friendly interface.

## 9. Explainability

Why the system recommends an action.

## 10. Economic validation

Historical simulation of potential savings.

---

# 45. What NOT to Do

Avoid these common mistakes:

### Do not say:
"We use AI to predict freight."

Instead specify:

- target
- horizon
- features
- model
- evaluation
- uncertainty

### Do not train only on a random train/test split.

Time-series leakage can make results look artificially excellent.

### Do not use future information.

This is the most dangerous modeling mistake.

### Do not assume LSTM is superior because it is neural.

Benchmark it.

### Do not assume Chronos/TimesFM is superior because it is a foundation model.

Benchmark it.

### Do not report only RMSE.

Business usefulness matters.

### Do not hard-code vessel recommendations.

Use port/vessel constraints.

### Do not create arbitrary risk scores without explaining/calibrating them.

### Do not claim actual savings unless validated.

Use "backtested estimated savings."

---

# 46. Research/Innovation Angle

The strongest technical story is not:

> "We made a dashboard."

It is:

> **"We developed a domain-adapted, probabilistic freight forecasting system and converted its predictions into an optimization-based chartering strategy."**

Potential novelty:

1. Combining freight time series with external market covariates.
2. Comparing conventional ML, recurrent networks and time-series foundation models.
3. Probabilistic forecasting rather than single-value prediction.
4. Route/vessel/port-aware forecasting.
5. Forecast-to-decision optimization.
6. Historical chartering simulation.
7. Risk-aware contracting.
8. Explainable recommendations.

---

# 47. Recommended Development Order

Do not build the entire application simultaneously.

## Phase 1 — Data audit

Determine:

- What data exists?
- Time range?
- Frequency?
- Route coverage?
- Vessel coverage?
- Missingness?
- Rate definitions?
- Data licensing/access?

**This phase determines feasibility.**

## Phase 2 — Define target

Lock:

- Freight definition
- Unit
- Route
- Vessel class
- Forecast frequency
- Forecast horizons

## Phase 3 — Baseline

Build:

- Naive
- Seasonal naive
- XGBoost

## Phase 4 — Foundation models

Implement:

- Chronos-2
- TimesFM

## Phase 5 — LSTM

Implement only as a meaningful benchmark.

## Phase 6 — Backtesting

Build rolling-origin evaluation.

## Phase 7 — Probabilistic/risk layer

Add:

- Prediction intervals
- Probability of increase/decrease
- Volatility
- Risk score

## Phase 8 — Vessel/port engine

Implement deterministic feasibility.

## Phase 9 — Decision engine

Implement:

- Charter timing
- Contract comparison
- Vessel ranking

## Phase 10 — Dashboard

Only after the analytical core works.

---

# 48. Team Division

A practical team split:

## Team A — Data Engineering

Responsible for:

- Data ingestion
- Cleaning
- Alignment
- Database
- Data validation
- Feature store/pipeline

## Team B — Forecasting/ML

Responsible for:

- Baselines
- XGBoost
- LSTM
- TimesFM
- Chronos-2
- Hyperparameter tuning
- Backtesting

## Team C — Optimization/Decision

Responsible for:

- Vessel feasibility
- Charter timing
- Contract strategy
- Risk engine
- Economic simulation

## Team D — Product/Frontend

Responsible for:

- API integration
- Dashboard
- Visualization
- UX
- Recommendation explanation

Everyone must use the same canonical data schema and model-evaluation protocol.

---

# 49. Team-Wide Rules

These rules should remain fixed unless the team explicitly agrees to change them:

1. No random train/test split for primary time-series evaluation.
2. No future information leakage.
3. Every feature must have an "available as-of" timestamp.
4. Every model must be evaluated on the same test periods.
5. Baselines must be included.
6. Models are selected using validation/backtesting, not preference.
7. Point forecasts and uncertainty should be reported separately.
8. Business metrics must accompany ML metrics.
9. Vessel feasibility is constraint-based unless there is a clear reason otherwise.
10. Every recommendation must have an explanation.
11. Savings are reported as simulated/backtested unless actual procurement results exist.
12. Data definitions and units must be documented.

---

# 50. Recommended Initial Model Experiment

The first serious experiment should answer:

> **Can we predict the next 7/14/30 days of freight rates better than a naive baseline using the data we actually have?**

Run:

```text
Baseline
   ↓
XGBoost
   ↓
LSTM
   ↓
Chronos-2
   ↓
TimesFM
   ↓
Ensemble
```

For every model calculate:

- MAE
- RMSE
- sMAPE
- Direction accuracy
- Prediction interval coverage (where applicable)
- Economic/chartering simulation score

Do not build the dashboard around a model until this experiment is complete.

---

# 51. Critical Questions to Resolve Early

Before final architecture lock:

1. What exact freight-rate dataset does SAIL provide?
2. Is the rate voyage-specific or index-based?
3. Is it USD/MT, USD/day, or another unit?
4. What historical period is available?
5. What is the data frequency?
6. How many observations exist for each route/vessel class?
7. Are rates available for all listed origins/destinations?
8. Are port congestion records available historically?
9. Are vessel availability/position data available?
10. Which external variables are actually available?
11. Which external data sources are legally/licensing-wise usable?
12. How frequently can the production system refresh data?
13. What forecast horizon does SAIL actually care about?
14. What constitutes a "successful" recommendation?
15. What baseline chartering strategy should savings be compared against?

These questions matter more than choosing between two neural architectures at the beginning.

---

# 52. Final System Concept

The final product should be understood as:

```text
              USER REQUIREMENT
                     │
                     ↓
          DATA + MARKET CONTEXT
                     │
                     ↓
            FREIGHT FORECAST
                     │
          ┌──────────┴──────────┐
          ↓                     ↓
    Forecast range         Market risk
          │                     │
          └──────────┬──────────┘
                     ↓
             DECISION ENGINE
                     │
       ┌─────────────┼──────────────┐
       ↓             ↓              ↓
   Vessel        Charter         Contract
 recommendation  timing         strategy
       │             │              │
       └─────────────┼──────────────┘
                     ↓
               FINAL ACTION
                     │
                     ↓
                DASHBOARD
```

The **freight forecasting model is the central intelligence layer**.

The vessel, contract, chartering and risk components are downstream consumers of that intelligence.

---

# 53. Project North Star

The project should ultimately demonstrate:

> **Given a real cargo procurement requirement today, the system can use information that was actually available today to estimate future freight-rate distributions, assess uncertainty and operational constraints, and recommend a commercially sensible chartering strategy — with evidence from historical backtesting that the strategy would have improved upon a reasonable baseline.**

That is the standard against which architecture, model selection, features, and implementation decisions should be judged.
