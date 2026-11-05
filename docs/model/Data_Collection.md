# SIH 26006 — Freight Forecasting Data Collection & Engineering Plan

**Project:** Development of an Intelligent Freight Forecasting Model for Optimized Vessel Chartering and Bulk Cargo Procurement from Overseas to the East Coast of India

**Purpose:** Shared operating plan for the 3-person data collection and ML team.

---

## 1. Core Principle

We are **not** simply collecting numbers and combining them into one Excel file.

We are building a reproducible data pipeline:

> **Raw sources → Standardization → Validation → Master dataset → Feature engineering → Forecasting models → Decision engine**

Manual collection is acceptable where APIs/data feeds are unavailable. However, naming, units, dates, definitions, validation, merging, and derived features must be standardized and preferably automated.

### Golden rule

> **Never put a value into the master dataset unless we know what it means, what unit it uses, what date/time it represents, and where it came from.**

---

## 2. Objective of the Dataset

The dataset should allow the system to answer:

1. What is the current/expected freight rate?
2. What is the likely freight rate over the short/medium term?
3. Should SAIL charter now or wait?
4. Which vessel class is economically/operationally appropriate?
5. What risks could materially change the forecast?
6. What contract/chartering strategy is preferable?

The **primary ML target** is:

`freight_rate_usd_per_mt`

Everything else is either:
- an explanatory/covariate variable,
- a static route/vessel constraint,
- or a feature generated from historical observations.

---

## 3. Unit of Observation

The basic observation is:

> **One date × one route × one vessel class × one cargo type**

Example:

```text
2025-04-17 | Newcastle | Paradip | Capesize | Coal | 21.45
```

This means the freight-rate observation applies to that specific date, route, vessel class, and cargo type.

Do not mix observations of different meanings:

- freight rate in USD/MT
- voyage charter rate in USD/day
- TCE in USD/day
- bunker price in USD/MT
- port waiting time in hours

Every variable must retain its original semantic meaning.

---

# 4. Team Division

## Person A — Freight & Shipping Market

Primary responsibility:

- Historical freight rates
- Relevant Baltic/shipping indices
- Vessel availability
- Tonnage supply
- Fleet utilization
- Charter-market indicators
- Bunker/fuel prices, if assigned here

Deliverables:

```text
raw_freight.csv
raw_shipping_market.csv
```

## Person B — Commodity & Macro

Primary responsibility:

- Coal prices
- Crude/fuel benchmarks
- USD/INR
- Relevant commodity indices
- Global trade indicators
- Industrial/economic indicators
- Other macro variables that plausibly affect shipping demand

Deliverables:

```text
raw_commodity.csv
raw_macro.csv
```

## Person C — Ports, Routes & Vessels

Primary responsibility:

- Port congestion
- Port waiting time
- Port throughput/utilization
- Port infrastructure
- Vessel specifications
- LOA
- Beam
- Draft
- DWT
- Route distance
- Typical transit time
- Port restrictions

Deliverables:

```text
raw_ports.csv
raw_vessels.csv
raw_routes.csv
```

## Shared responsibilities

Everyone must follow the same:

- column names
- date format
- units
- port names
- vessel-class names
- missing-value rules
- source-recording rules
- file structure
- validation rules

No person may independently change the master schema.

If a new variable is required:

1. Propose it.
2. Define it.
3. Specify unit/frequency/source.
4. Get team agreement.
5. Add it to the data dictionary.
6. Only then collect it.

---

# 5. Master Dataset Schema

## Recommended Version-1 master schema

```csv
date,origin_port,destination_port,route,vessel_class,cargo_type,freight_rate_usd_per_mt,bunker_price_usd_per_mt,coal_price_usd_per_mt,origin_congestion,destination_congestion,origin_waiting_time_hours,destination_waiting_time_hours,vessel_availability,distance_nm,typical_transit_days,month,quarter,day_of_week,season
```

Not every field needs to be manually collected. Some fields should be generated automatically.

---

# 6. Column Definitions

## 6.1 Identification

### `date`

**Definition:** Date associated with the observation.

**Format:**

```text
YYYY-MM-DD
```

Example:

```text
2025-04-17
```

Rules:
- ISO format only.
- No `17/04/2025`.
- No `04-17-25`.
- Use the source's observation date, not the date we downloaded it.

### `origin_port`

Port from which the cargo/voyage originates.

Use a standardized port name.

Examples:

```text
Newcastle
Richards_Bay
Gladstone
```

Do not use several variants such as `NEWCASTLE`, `Newcastle Port`, etc.

### `destination_port`

Port where cargo is discharged.

Examples:

```text
Paradip
Dhamra
Gangavaram
Visakhapatnam
Krishnapatnam
```

### `route`

Generated automatically:

```text
origin_port + "-" + destination_port
```

Example:

```text
Newcastle-Paradip
```

**Do not manually type this column.**

### `vessel_class`

Initial controlled vocabulary:

```text
Capesize
Panamax
Supramax
Handysize
```

If a source uses another classification, map it to the project's controlled vocabulary and document the mapping.

Never invent a vessel class.

### `cargo_type`

Initial controlled vocabulary:

```text
Coal
```

If the project expands to another commodity, add it formally to the data dictionary first.

---

# 7. Target Variable

## `freight_rate_usd_per_mt`

**Definition:** Freight transportation cost expressed in US dollars per metric tonne for the specified route, vessel class, cargo, and observation date.

**Unit:**

```text
USD/MT
```

Example:

```text
21.45
```

Do not substitute:
- vessel hire rate
- TCE
- demurrage
- bunker price
- total voyage cost

for freight rate unless the project explicitly defines a transformation.

If a source reports another unit, do not silently convert it. Record:

```text
original_value
original_unit
conversion_method
converted_value
converted_unit
```

---

# 8. Market Variables

## `bunker_price_usd_per_mt`

Price of the specified marine fuel/bunker used as a shipping-cost driver.

Unit:

```text
USD/MT
```

The exact fuel grade must be documented. Do not combine VLSFO, HSFO, MGO, etc. into one unnamed column.

## `coal_price_usd_per_mt`

Relevant benchmark coal price associated with the cargo market.

Unit:

```text
USD/MT
```

The benchmark must be recorded in metadata, including benchmark name and quality/specification where applicable.

Do not mix different coal benchmarks without identifying them.

## Shipping indices

If used, document:
- index name
- route/region
- vessel class
- unit
- publication frequency
- source

Do not call every different shipping index simply `shipping_index` without identifying which one it is.

---

# 9. Port Variables

## `origin_congestion` / `destination_congestion`

These must have a precise definition.

A recommended approach is a normalized congestion score:

```text
0 = very low congestion
1 = extremely high congestion
```

However, the underlying raw measurement must also be retained.

For example:

```text
raw_waiting_vessels = 14
raw_waiting_hours = 27.5
normalized_congestion = 0.62
```

Do not manually assign a score because a port "looks busy."

The normalization method must be documented and reproducible.

## `origin_waiting_time_hours` / `destination_waiting_time_hours`

Reported/estimated waiting time associated with vessels at the relevant port.

Unit:

```text
hours
```

If the source provides days:

```text
hours = days × 24
```

Record the original unit and conversion.

## Port utilization

If used, distinguish clearly between:
- berth utilization
- terminal utilization
- total port throughput

Do not mix them into one unnamed variable.

---

# 10. Vessel Variables

## `vessel_availability`

Number or index of vessels available to perform the relevant voyage under a defined vessel-class/market criterion.

The unit must be explicitly defined, e.g.:

```text
number_of_vessels
```

or

```text
normalized_availability_index
```

Do not mix the two.

## `dwt`

Deadweight tonnage.

Unit:

```text
metric tonnes
```

## `loa_m`

Length overall.

Unit:

```text
metres
```

## `beam_m`

Maximum vessel breadth/width.

Unit:

```text
metres
```

## `design_draft_m`

Vessel design draft.

Unit:

```text
metres
```

Where operational/maximum draft is more relevant, document the exact definition.

---

# 11. Route Variables

## `distance_nm`

Voyage distance.

Unit:

```text
nautical miles
```

The route definition must be consistent. Do not use straight-line distance for one route and actual sailing distance for another without labeling the distinction.

## `typical_transit_days`

Typical sailing/transit duration for the defined route/vessel assumptions.

Unit:

```text
days
```

If estimated rather than directly observed, mark it as estimated in metadata.

---

# 12. Temporal Features

These should generally be generated programmatically.

### `month`

```text
1–12
```

### `quarter`

```text
1–4
```

### `day_of_week`

Use:

```text
0 = Monday
1 = Tuesday
...
6 = Sunday
```

### `season`

Use one predefined project convention. For example:

```text
Winter
Spring
Summer
Autumn
```

Do not let different team members choose season labels independently.

---

# 13. Feature Engineering

Do not manually enter historical lag/rolling features into raw CSVs.

Generate them using Python.

Recommended freight-history features:

```text
freight_lag_1d
freight_lag_3d
freight_lag_7d
freight_lag_14d
freight_lag_30d
freight_lag_60d

freight_ma_7d
freight_ma_14d
freight_ma_30d

freight_std_7d
freight_std_30d
```

Definitions:
- `lag_Nd` = freight rate N days earlier.
- `ma_Nd` = moving average over the previous N days.
- `std_Nd` = rolling standard deviation over the previous N days.

These must use only information available at that point in time.

---

# 14. Data Leakage — STRICT RULE

> **At prediction time, the model may only use information that would actually have been available at prediction time.**

Example:

If predicting the freight rate for:

```text
2025-09-10
```

we cannot use a congestion value that was published on:

```text
2025-09-12
```

even if it describes September 10.

Likewise, do not use future:
- freight rates
- coal prices
- bunker prices
- congestion
- vessel availability

to predict an earlier date.

### Publication-time rule

When practical, distinguish:

```text
observation_date
publication_date
```

If a variable is published later, the model should not see it until its publication time.

---

# 15. Raw vs Cleaned vs Processed Data

Maintain three layers.

## Layer 1 — Raw

Exactly what was collected.

```text
data/raw/
```

Rules:
- Do not overwrite.
- Preserve original values.
- Preserve original units.
- Preserve source.
- Preserve collection metadata.

## Layer 2 — Cleaned / Master

Standardized and merged data:

```text
data/cleaned/master_dataset.csv
```

Here we:
- standardize dates
- standardize port names
- standardize vessel classes
- standardize units
- handle duplicates
- map sources
- join datasets

## Layer 3 — Processed / Model Data

Generated by code:

```text
data/processed/model_dataset.csv
```

Contains:
- lag features
- rolling features
- temporal features
- normalized variables where required
- model-ready representations

Never manually edit this file.

---

# 16. Recommended Repository Structure

```text
SIH_Freight_Forecasting/
│
├── README.md
│
├── data/
│   ├── raw/
│   │   ├── freight/
│   │   ├── shipping_market/
│   │   ├── commodity/
│   │   ├── macro/
│   │   ├── ports/
│   │   ├── vessels/
│   │   └── routes/
│   │
│   ├── cleaned/
│   │   └── master_dataset.csv
│   │
│   └── processed/
│       └── model_dataset.csv
│
├── scripts/
│   ├── validate_raw_data.py
│   ├── clean_freight.py
│   ├── clean_market.py
│   ├── clean_ports.py
│   ├── clean_vessels.py
│   ├── merge_data.py
│   └── feature_engineering.py
│
├── models/
│
├── documentation/
│   ├── data_dictionary.xlsx
│   └── source_registry.csv
│
└── reports/
```

---

# 17. Source Registry

Every externally sourced dataset must be registered.

Recommended file:

```text
documentation/source_registry.csv
```

Schema:

```csv
source_id,dataset,variable,source_name,source_url,observation_frequency,original_unit,standard_unit,collection_method,notes
```

Example:

```text
SRC001,freight,freight_rate,Example Source,https://...,daily,USD/MT,USD/MT,manual,...
```

### Source ID convention

```text
SRC001
SRC002
SRC003
...
```

Never delete a source ID. If a source becomes unavailable, mark it inactive.

---

# 18. File Naming Convention

Use:

```text
lowercase_snake_case
```

Examples:

```text
raw_freight.csv
raw_ports.csv
master_dataset.csv
model_dataset.csv
source_registry.csv
data_dictionary.xlsx
```

Avoid:

```text
Final Data.csv
finalFINAL2.csv
Freight Data NEW.csv
TeamAData.xlsx
```

If versions are needed:

```text
master_dataset_v01.csv
master_dataset_v02.csv
```

Prefer Git/version control over endless file copies.

---

# 19. Column Naming Convention

Use lowercase snake case.

Correct:

```text
freight_rate_usd_per_mt
origin_waiting_time_hours
distance_nm
coal_price_usd_per_mt
```

Incorrect:

```text
Freight Rate
FreightRate
freight-rate
coalPrice
```

---

# 20. Missing Values

Never use random placeholders such as:

```text
0
-
?
999
-999
```

unless explicitly defined.

Use a consistent missing-value convention handled by the processing pipeline.

### Critical distinction

A missing value is NOT the same as zero.

For example:

```text
vessel_availability = 0
```

means zero vessels.

A blank/NA means:

> We do not have the value.

Never convert missing data to zero just to make the dataset look complete.

---

# 21. Duplicates

For the core freight dataset, the expected logical key is approximately:

```text
date + origin_port + destination_port + vessel_class + cargo_type
```

There should not normally be two different records for the same key.

If duplicates exist:

1. Do not randomly delete one.
2. Investigate the source.
3. Determine whether they represent different benchmarks/conditions.
4. Document the resolution.

---

# 22. Units — Strict Policy

Use one standard unit throughout the master dataset.

| Variable | Standard Unit |
|---|---|
| Freight | USD/MT |
| Bunker | USD/MT |
| Coal price | USD/MT |
| Waiting time | hours |
| Distance | nautical miles |
| Transit time | days |
| LOA | metres |
| Beam | metres |
| Draft | metres |
| DWT | metric tonnes |
| FX | INR per USD |

Never assume two sources use the same unit. Always check.

---

# 23. Time Frequency

### Preferred

```text
Daily
```

because the project is intended for short/medium-term freight forecasting.

If a variable is weekly/monthly, do not simply duplicate it across every day without documenting the transformation.

For example, a weekly coal price may be forward-filled for daily modeling, but the methodology must explicitly state that the value represents the latest known observation.

Never use future observations to fill the past.

---

# 24. Combining Data from Different Frequencies

Example:

```text
Freight → daily
Bunker → daily
Coal → weekly
Macro → monthly
```

These can still be combined.

The master dataset uses the daily freight observation as the primary time axis.

For lower-frequency variables, use a clearly defined alignment method such as:
- last known value
- published value available at that date
- interpolation, only where scientifically justified

Never use future observations to fill the past.

---

# 25. Port Master Table

Maintain a separate controlled table:

```csv
port_id,standard_port_name,country,region,latitude,longitude
```

Example:

```text
PORT001,Paradip,India,East Coast,...
PORT002,Dhamra,India,East Coast,...
```

All datasets should map source port names to this standardized representation.

This prevents:

```text
Paradip
Paradip Port
Paradip, Odisha
PARADIP
```

from becoming different entities.

---

# 26. Vessel-Class Master Table

Maintain:

```csv
vessel_class,dwt_min,dwt_max,description
```

The exact ranges must be agreed upon and sourced/documented.

This table is important because vessel recommendation later depends on physical and operational feasibility.

---

# 27. Route Master Table

Maintain:

```csv
route_id,origin_port,destination_port,distance_nm,typical_transit_days,canal_required
```

Static route properties should not be repeatedly typed into every daily record.

---

# 28. Data Validation Checklist

Before data enters the master dataset:

### Format

- [ ] Dates are valid.
- [ ] Dates use `YYYY-MM-DD`.
- [ ] Column names use `lowercase_snake_case`.
- [ ] Numeric columns contain numeric values.
- [ ] Units are known.

### Categories

- [ ] Ports match the port master table.
- [ ] Vessel classes match the controlled vocabulary.
- [ ] Cargo types match the controlled vocabulary.

### Quality

- [ ] No unexpected duplicates.
- [ ] Missing values identified.
- [ ] Negative values investigated.
- [ ] Extreme values investigated.
- [ ] Date gaps identified.
- [ ] Source recorded.

### Leakage

- [ ] Observation date known.
- [ ] Publication/availability date recorded where relevant.
- [ ] No future information is being used.

---

# 29. Outliers

Do **not** automatically delete unusual freight rates.

A sudden jump may represent a real market event.

Example:

```text
20 → 21 → 22 → 30 → 23
```

The 30 may be:
- a data-entry error,
- a source change,
- a genuine market shock.

Flag it first.

Do not remove it until investigated.

If needed, maintain:

```text
is_outlier_flag
outlier_reason
```

---

# 30. Data Quality Flags

Where useful, add metadata rather than silently changing values.

Examples:

```text
is_missing
is_outlier
is_estimated
is_converted
source_confidence
```

These should be defined clearly rather than assigned arbitrary scores.

---

# 31. What Should NOT Be Manually Collected

Do not manually calculate:

```text
route
month
quarter
day_of_week
season
lags
moving averages
rolling standard deviations
percentage changes
```

Generate these using code.

This ensures that every model receives the same transformations.

---

# 32. Model-Specific Dataset Preparation

The master dataset should be model-agnostic.

From the same master dataset we generate different inputs.

### XGBoost

Uses:
- historical lags
- rolling statistics
- market variables
- port variables
- vessel variables
- temporal variables

### LSTM

Uses sequences/windows of historical observations.

Example:

```text
past 30 days → predict next 7 days
```

### Chronos-2 / TimesFM

Can use historical target sequences and, depending on the chosen implementation, relevant covariates.

Important principle:

> **One clean master dataset → model-specific transformations.**

Do not create separate manually maintained datasets for each model.

---

# 33. Forecasting Evaluation

Do not randomly split the dataset into train/test.

Use chronological evaluation.

Example:

```text
Past ------------------------------> Future

TRAIN          VALIDATION      TEST
|---------------|---------------|
```

Better: use rolling/walk-forward backtesting:

```text
Train → Forecast → Evaluate
Train expands → Forecast → Evaluate
Train expands → Forecast → Evaluate
...
```

This better simulates real deployment.

---

# 34. Recommended Forecast Horizons

Benchmark multiple horizons, for example:

```text
7 days
14 days
30 days
60 days
```

The exact horizons can be adjusted according to the business requirement.

Report performance separately for each horizon.

---

# 35. Baselines Are Mandatory

Before claiming an advanced AI model is good, compare against simple methods.

At minimum:

```text
Naive forecast
Moving Average
XGBoost
LSTM
Chronos-2
TimesFM
```

The winning model should be determined from backtesting, not assumed in advance.

---

# 36. Probabilistic Forecasting

A freight forecast should ideally provide more than:

```text
Expected freight = $22.4/MT
```

It should eventually provide uncertainty, for example:

```text
Expected: $22.4/MT
Likely range: $20.8–$24.7/MT
Risk: Moderate
```

This uncertainty can feed the downstream chartering/risk engine.

---

# 37. Data Collection DOs

- Define every variable before collecting it.
- Record the source.
- Record units.
- Record observation dates.
- Record publication dates where possible.
- Preserve raw data.
- Use controlled vocabularies.
- Use ISO dates.
- Validate before merging.
- Keep source provenance.
- Automate transformations.
- Investigate anomalies.
- Keep missing values distinct from zero.
- Use chronological backtesting.
- Document assumptions.

---

# 38. Data Collection DON'Ts

- Don't copy numbers without knowing their meaning.
- Don't mix USD/day with USD/MT.
- Don't mix different fuel grades without labeling them.
- Don't mix different coal benchmarks without labeling them.
- Don't rename ports arbitrarily.
- Don't manually calculate lag features.
- Don't overwrite raw data.
- Don't silently delete outliers.
- Don't replace missing values with zero.
- Don't use future information.
- Don't randomly shuffle time-series data for final evaluation.
- Don't create different naming conventions for different team members.
- Don't create a separate manually maintained dataset for every model.
- Don't trust a source simply because the number looks reasonable.

---

# 39. What To Do When a Source Doesn't Match Our Schema

Suppose a source says:

```text
Port: Paradip Port, India
Waiting time: 1.7 days
```

Our standard requires:

```text
destination_port = Paradip
destination_waiting_time_hours = 40.8
```

Conversion:

```text
1.7 × 24 = 40.8 hours
```

Record the original source value and conversion in the raw/metadata layer.

Never silently change it.

---

# 40. What To Do When Data Is Unavailable

Do not fabricate data.

If a variable has:

```text
2025-01-01
2025-01-02
2025-01-04
```

do not invent January 3.

Mark it missing and determine whether an approved imputation method is appropriate later.

### Critical rule

> **Synthetic data may be used for testing/demo purposes, but it must never be presented as historical real-world data.**

---

# 41. Data Coverage

Before modeling, create a coverage report.

Example:

```text
Freight data:
2023-01-01 → 2025-12-31

Bunker:
2023-01-01 → 2025-12-31

Coal:
2023-01-06 → 2025-12-26

Port congestion:
2024-03-01 → 2025-12-31
```

This immediately shows where the usable common period begins.

Do not assume all variables cover the same historical period.

---

# 42. Minimum Viable Dataset

If time becomes limited, prioritize:

## Tier 1 — Essential

```text
date
origin_port
destination_port
route
vessel_class
cargo_type
freight_rate_usd_per_mt
```

## Tier 2 — High-value explanatory variables

```text
bunker_price_usd_per_mt
coal_price_usd_per_mt
shipping_index
vessel_availability
origin_waiting_time_hours
destination_waiting_time_hours
```

## Tier 3 — Additional intelligence

```text
port_utilization
weather
macro indicators
FX
trade indicators
route-specific constraints
```

It is better to have **a smaller, accurate, well-defined dataset** than a huge dataset containing questionable measurements.

---

# 43. Recommended Team Workflow

## Phase 1 — Schema

All three members agree on:
- columns
- definitions
- units
- categories
- sources
- file structure

No large-scale collection before this is complete.

## Phase 2 — Individual Raw Collection

Each person collects their assigned variables independently.

Every dataset gets:

```text
source_id
source_name
source_url
collection_date
original_unit
notes
```

## Phase 3 — Standardization

Each person converts their data into the agreed schema.

## Phase 4 — Validation

Run:

```text
validate_raw_data.py
```

Fix problems before merging.

## Phase 5 — Merge

Run:

```text
merge_data.py
```

to create:

```text
data/cleaned/master_dataset.csv
```

## Phase 6 — Feature Engineering

Run:

```text
feature_engineering.py
```

to create:

```text
data/processed/model_dataset.csv
```

## Phase 7 — Forecasting

Run chronological backtests for:

```text
Naive
Moving Average
XGBoost
LSTM
Chronos-2
TimesFM
```

---

# 44. Final Architecture

```text
                 EXTERNAL SOURCES
                       │
        ┌──────────────┼──────────────┐
        │              │              │
     Freight        Commodity        Ports/
    Shipping          Macro          Vessels
        │              │              │
        ▼              ▼              ▼
    Raw Data        Raw Data        Raw Data
        │              │              │
        └──────────────┼──────────────┘
                       ▼
                STANDARDIZATION
                       │
                       ▼
                 DATA VALIDATION
                       │
                       ▼
                 MASTER DATASET
                       │
                       ▼
               FEATURE ENGINEERING
                       │
                       ▼
              TIME-SERIES DATASETS
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       XGBoost        LSTM     Chronos/TimesFM
          │            │            │
          └────────────┼────────────┘
                       ▼
                MODEL COMPARISON
                       │
                       ▼
              PROBABILISTIC FORECAST
                       │
                       ▼
              DECISION / RISK ENGINE
                       │
                       ▼
             CHARTERING RECOMMENDATION
```

---

# 45. Final Goal

The dataset is **not the final product**.

It is the foundation for:

> **Historical + market + commodity + port + vessel intelligence → freight forecast → uncertainty → chartering recommendation**

The final system should move the user from:

```text
"Let's check today's freight market."
```

to:

```text
"Based on the current market and historical patterns,
freight is expected to move in this range over the next
30 days. Given the vessel and port constraints, this is
the recommended chartering window and strategy."
```

---

# 46. Team Golden Rules

Keep these visible:

1. **Define before collecting.**
2. **Source every value.**
3. **Standardize every unit.**
4. **Use one naming convention.**
5. **Never overwrite raw data.**
6. **Never fabricate missing historical data.**
7. **Never confuse missing with zero.**
8. **Never use future information.**
9. **Never manually create derived ML features.**
10. **Validate before merging.**
11. **Keep provenance.**
12. **Prefer reproducible code over manual spreadsheet operations.**
13. **Use chronological backtesting.**
14. **Do not assume the most complicated model is the best model.**
15. **A smaller clean dataset is better than a larger unreliable dataset.**

---

# 47. Immediate Action Items

## All 3 members

- [ ] Read this document.
- [ ] Agree on the master schema.
- [ ] Agree on controlled port names.
- [ ] Agree on vessel classes.
- [ ] Agree on units.
- [ ] Agree on minimum historical period.
- [ ] Set up shared repository.
- [ ] Create `data_dictionary.xlsx`.
- [ ] Create `source_registry.csv`.

## Person A

- [ ] Identify freight-rate sources.
- [ ] Identify shipping-market sources.
- [ ] Identify bunker/fuel sources.
- [ ] Create raw freight-market files.

## Person B

- [ ] Identify coal-price sources.
- [ ] Identify macro/FX sources.
- [ ] Identify relevant commodity/trade indicators.
- [ ] Create raw commodity/macro files.

## Person C

- [ ] Identify port-congestion sources.
- [ ] Identify port infrastructure sources.
- [ ] Build port master table.
- [ ] Build vessel-class master table.
- [ ] Build route master table.

## Then, together

- [ ] Validate all raw datasets.
- [ ] Merge into `master_dataset.csv`.
- [ ] Generate features programmatically.
- [ ] Produce a data-coverage report.
- [ ] Begin baseline forecasting.

---

## One-Sentence Summary

**Collect independently by source domain, but under one frozen schema; preserve raw data and provenance, standardize and validate everything, merge programmatically into one master dataset, generate model features in code, and enforce strict time-aware leakage prevention before forecasting.**
