# UI Registry

## Registry Principles

- A component is **reusable** only if it is genuinely used, unmodified in behavior, on two or more of the five pages, or if it wraps a pattern already codified as reusable in `ui-rules.md` (e.g., Badge, Card, Table) regardless of current usage count, because those patterns are contractually shared across the whole product.
- A component is **page-specific** when its content structure is unique to one page's information (e.g., the specific stat layout of the Decision Dashboard recommendation summary), even if it is internally composed from reusable primitives (Card, Badge, StatValue). Page-specific components must still be built entirely out of registry primitives — a page-specific component introducing its own spacing, color, or typography value is a defect per `ui-rules.md`.
- Prefer **composition over duplication**: if two pages need visually similar but not identical output, extend a shared component with props/variants rather than forking it into two components.
- A new shared component is added to this registry only when a second real usage exists or is concretely planned in this project's known scope (`project-overview.md`) — no speculative abstraction for hypothetical future pages.
- Every component that displays status, risk, feasibility, or forecast data must explicitly support the states listed in Component Contracts (loading/empty/error/unavailable, etc.) — a component missing state handling is incomplete, not a smaller valid version.

---

## Component Inventory

| Component | Purpose | Used On | Reusable? |
|---|---|---|---|
| `AppShell` | Top-level layout: nav rail + content area | All 5 pages | Yes |
| `NavRail` | Primary navigation between the 5 pages | All 5 pages | Yes |
| `NavItem` | Single nav entry with active/hover/focus states | Inside `NavRail` | Yes |
| `PageContainer` | Page-level width/padding/grid wrapper | All 5 pages | Yes |
| `PageHeader` | Page title + optional page-level actions | All 5 pages | Yes |
| `GlobalNotificationArea` | Toasts for transient success/error messages | All 5 pages | Yes |
| `Card` | Base bordered panel per `ui-rules.md` | All 5 pages | Yes |
| `StatCard` | Card variant showing one eyebrow-labeled headline figure | Decision Dashboard, Backtesting | Yes |
| `SummaryCard` | Card variant showing a labeled group of related fields | Decision Dashboard (requirement summary), Feasibility | Yes |
| `DataTable` | Base table with header/row/alignment/status-cell rules | Feasibility, Backtesting, Risk (factor table) | Yes |
| `Badge` | Icon+label+color chip (status/risk/feasibility/direction) | All 5 pages | Yes |
| `MetricValue` | Mono-typography value display with optional unit/label | Decision Dashboard, Forecast, Backtesting | Yes |
| `EmptyState` | No-data-yet pattern | All 5 pages | Yes |
| `LoadingSkeleton` | Skeleton block/row/chart placeholder | All 5 pages | Yes |
| `ErrorAlert` | Inline error/unavailable/insufficient-data alert | All 5 pages | Yes |
| `TextInput` | Base text/numeric input | Requirement form | Yes |
| `SelectInput` | Single-select dropdown | Requirement form | Yes |
| `NumericInput` | Numeric input with unit suffix | Requirement form | Yes |
| `DateRangeInput` | Loading-window date range picker | Requirement form | Yes |
| `FormSection` | Grouped set of form fields with a heading | Requirement form | Yes |
| `FormFieldError` | Inline validation error message | Requirement form | Yes |
| `RequirementForm` | Full procurement requirement input form | Decision Dashboard (entry point) | Page-specific (composes reusable form fields) |
| `ForecastChart` | Historical + forecast + interval line/band chart | Freight Forecast, Decision Dashboard (compact) | Yes |
| `HorizonSelector` | 7/14/30/60-day horizon toggle | Freight Forecast | Yes |
| `ForecastSummaryStat` | Current/forecast/direction stat block | Freight Forecast, Decision Dashboard | Yes |
| `ModelComparisonChart` | Multi-series chart comparing model outputs | Freight Forecast, Backtesting | Yes |
| `UncertaintyIndicator` | Compact volatility/confidence display | Freight Forecast, Risk, Decision Dashboard | Yes |
| `VesselCandidateTable` | Table of candidate vessels with spec + pass/fail | Port/Vessel Feasibility | Yes |
| `VesselSpecPanel` | Detail panel for one vessel's specs vs. port limits | Port/Vessel Feasibility | Yes |
| `FeasibilityStatusBadge` | Pass/Fail/Unknown badge (Badge variant) | Feasibility, Decision Dashboard | Yes |
| `FeasibilityExplanation` | Per-constraint reasoning list | Feasibility, Decision Dashboard (compact) | Yes |
| `RiskSummaryCard` | Overall risk level + category breakdown | Risk, Decision Dashboard | Yes |
| `RiskFactorBreakdown` | List/table of individual risk factors and scores | Risk page | Yes |
| `DisruptionIndicatorList` | External/disruption indicator list | Risk page | Yes |
| `RecommendationSummaryCard` | Highlighted recommendation card | Decision Dashboard | Page-specific (composes Badge, MetricValue, RecommendationReasoning) |
| `CharterTimingIndicator` | "Charter Now" / "Wait / Monitor" display | Decision Dashboard | Yes |
| `ContractStrategyComparison` | Spot/short-term/medium-term comparison table or cards | Decision Dashboard, Backtesting (strategy backtest) | Yes |
| `RecommendationReasoning` | Structured list of explanation reasons | Decision Dashboard | Yes |
| `SavingsEstimate` | Estimated savings figure with mandatory backtested qualifier | Decision Dashboard, Backtesting | Yes |
| `MetricsTable` | MAE/RMSE/sMAPE/directional accuracy table | Backtesting | Yes |
| `EconomicSimulationSummary` | Strategy-vs-baseline economic outcome display | Backtesting | Yes |
| `BacktestHistoryChart` | Historical rolling-backtest performance chart | Backtesting | Yes |

---

## Application Shell

- **`AppShell`**: top-level layout composing `NavRail` and a content slot. Owns the fixed offset between rail width (240px/64px) and content area, per `ui-rules.md` → Layout. Rendered once at the root layout; individual pages never re-implement shell structure.
- **`NavRail`**: fixed left rail present on all 5 pages, composed of 5 `NavItem`s (one per page) plus a collapsed/expanded state driven by breakpoint (see `ui-rules.md` → Responsive Behavior).
- **`PageContainer`**: enforces max content width (1440px), responsive horizontal padding, and the 12-column grid for whatever page renders inside it. Every page's top-level element is a `PageContainer`.
- **`PageHeader`**: renders the page's `type-h1` title and, if applicable, a small set of page-level actions (e.g., a "Run new backtest" button on the Backtesting page). Does not render breadcrumbs — navigation context is carried entirely by `NavRail`'s active state.
- **`GlobalNotificationArea`**: fixed-position toast host for transient messages (e.g., "Forecast refreshed", "Backtest run failed"), using `elevation-3` per `ui-tokens.md`. Rendered once at the app root, not per-page.

---

## Navigation Components

- **`NavRail`**: see Application Shell. Handles expanded/collapsed/drawer layout transitions across breakpoints; does not own the active-item logic itself (delegated to `NavItem`).
- **`NavItem`**: single navigation entry (icon + label) implementing the inactive/hover/active/focus states defined in `ui-rules.md` → Navigation. Receives the current route to determine its own active state — no page component sets active state manually.

No secondary/sub-navigation component exists in this registry; the product has exactly 5 top-level, flat pages with no nested navigation (per `project-overview.md`), so no breadcrumb or tab-bar navigation component is defined.

---

## Data Display Components

- **`Card`**: base bordered panel (`surface-primary`, `border-default`, `radius-md`, `elevation-0`) per `ui-rules.md` → Cards. All other card-like components (`StatCard`, `SummaryCard`, `RiskSummaryCard`, `RecommendationSummaryCard`) compose `Card` rather than reimplementing its border/radius/padding.
- **`StatCard`**: `Card` variant for a single headline figure — eyebrow label + `MetricValue` + optional direction indicator + optional caption. Used for "Current Freight", "30-day P50", MAE/RMSE headline tiles.
- **`SummaryCard`**: `Card` variant for a labeled group of key-value fields (e.g., the procurement requirement summary: cargo, quantity, origin, destination, loading window).
- **`DataTable`**: base table implementing header/row/alignment/hover/selected-row/status-cell/responsive rules from `ui-rules.md` → Tables. All page-specific tables (`VesselCandidateTable`, `MetricsTable`, `RiskFactorBreakdown` in table form) compose `DataTable`, supplying columns and row data rather than re-implementing table chrome.
- **`Badge`**: single component with a `variant` prop covering Success/Warning/Error/Info/Risk-Low/Risk-Medium/Risk-High/Feasibility-Pass/Feasibility-Fail/Feasibility-Unknown/Forecast-Increase/Forecast-Decrease, per `ui-rules.md` → Badges. Always renders icon + label + color together; no variant may be rendered with the icon or label omitted.
- **`MetricValue`**: Plex Mono value display with optional unit suffix and optional `type-caption` label underneath, used everywhere a numeric figure appears outside a table cell.
- **`EmptyState`**: icon + `type-h3` message + optional supporting text + optional action, per `ui-rules.md` → Empty States.
- **`LoadingSkeleton`**: three shape variants — `block` (card-shaped), `row` (table row-shaped), `chart` (chart-area-shaped) — per `ui-rules.md` → Loading & Error States. One component, variant-driven, not three separate components.
- **`ErrorAlert`**: inline alert with `variant` covering error / forecast-unavailable (info) / insufficient-data (warning), per `ui-rules.md` → Loading & Error States. Optional retry action slot.

---

## Form Components

- **`TextInput`**: base labeled text input with focus/error/disabled states per `ui-rules.md` → Form Inputs.
- **`SelectInput`**: single-select dropdown; used for Cargo Type, Origin, Destination — options are constrained to the product's supported values (per `project-overview.md`), never free text.
- **`NumericInput`**: numeric input with a fixed unit suffix (e.g., "MT", "months") and Plex Mono value rendering once populated; used for Quantity, Number of Voyages, Contract Horizon.
- **`DateRangeInput`**: bounded start/end date picker with start ≤ end validation; used for Loading Window.
- **`FormSection`**: groups related fields under a `type-h3` or `type-eyebrow` heading (e.g., "Cargo Details", "Route", "Contract Terms" groupings within the requirement form).
- **`FormFieldError`**: inline validation message (icon + `type-body-sm` Danger text) rendered beneath a field, per `ui-rules.md` → Form Inputs.
- **`RequirementForm`** (page-specific): composes `FormSection`, `SelectInput`, `NumericInput`, `DateRangeInput`, `TextInput` (for optional free-text commercial constraints), and `FormFieldError` into the full procurement requirement entry flow described in `project-overview.md`. This is page-specific because its field set and grouping are unique to the Decision Dashboard's entry flow, but it introduces no visual pattern beyond composed primitives.

---

## Forecast Components

- **`ForecastChart`**: renders historical series, forecast series (solid-to-dashed at "today"), and prediction interval band per `ui-rules.md` → Data Visualization. Accepts a `compact` display mode for embedding a smaller version on the Decision Dashboard alongside the recommendation.
- **`HorizonSelector`**: toggle/segmented control for 7/14/30/60-day horizon selection, driving `ForecastChart` and `ForecastSummaryStat` data.
- **`ForecastSummaryStat`**: composes `StatCard`/`MetricValue` to show current rate, forecast median, P10–P90 range, and direction (neutral glyph, no status color) for a given horizon.
- **`ModelComparisonChart`**: multi-series chart using the categorical palette + dash-pattern redundancy (>3 series) per `ui-rules.md`. Used on Freight Forecast (comparing candidate models for the current forecast) and Backtesting (comparing historical model performance).
- **`UncertaintyIndicator`**: compact display of a volatility/confidence figure (`MetricValue` + caption), used wherever uncertainty needs to be surfaced outside the full chart (Risk page, Decision Dashboard recommendation reasoning).

---

## Feasibility Components

- **`VesselCandidateTable`**: `DataTable` composition listing candidate vessel classes with DWT/draft/LOA/beam columns and a `FeasibilityStatusBadge` per constraint plus an overall result column.
- **`VesselSpecPanel`**: detail view for a single vessel class showing its specs against the relevant port's limits (side-by-side or delta format), used when a user drills into one candidate from `VesselCandidateTable`.
- **`FeasibilityStatusBadge`**: `Badge` variant restricted to Pass/Fail/Unknown, used both per-constraint (in table cells) and as the overall summary badge.
- **`FeasibilityExplanation`**: structured list of constraint-by-constraint reasoning (e.g., "Draft: PASS — vessel draft 12.5m within port limit 14m"), used on the Feasibility page in full and in a condensed form within the Decision Dashboard's recommendation reasoning.

---

## Risk Components

- **`RiskSummaryCard`**: `Card` composition showing the overall Risk badge plus a compact category breakdown (market/port/vessel/external), used on both the Risk page (full detail) and Decision Dashboard (condensed).
- **`RiskFactorBreakdown`**: detailed list or `DataTable` of individual risk factors (e.g., "Port congestion: Medium — based on 14-day average waiting time") with per-factor `Badge`s, used on the Risk page.
- **`DisruptionIndicatorList`**: list of external/disruption indicators (weather, geopolitical, route closures) each with a status `Badge` and short description, used on the Risk page.

---

## Recommendation Components

- **`RecommendationSummaryCard`** (page-specific): the Decision Dashboard's highlighted recommendation panel, composing `CharterTimingIndicator`, `FeasibilityStatusBadge`/vessel name, `ContractStrategyComparison` summary, `RiskSummaryCard` (condensed), `SavingsEstimate`, and `RecommendationReasoning`. Page-specific because its exact composition is unique to the Decision Dashboard, but every element inside it is a shared component.
- **`CharterTimingIndicator`**: renders "Charter Now" / "Wait / Monitor" as a prominent label or badge per `ui-rules.md` → Decision & Status Indicators.
- **`ContractStrategyComparison`**: table or parallel-card comparison of spot / short-term / medium-term strategies, showing expected expenditure, risk, and flexibility per strategy. Reused on Backtesting when showing how strategy comparison performed historically.
- **`RecommendationReasoning`**: structured, itemized list of the reasons behind a recommendation (forecast direction, probability, vessel availability, congestion, etc.), per `project-overview.md` explainability requirements.
- **`SavingsEstimate`**: renders an estimated savings/cost figure via `MetricValue` using `outcome-favorable`/`outcome-unfavorable` tokens, always paired with an adjacent "backtested/simulated estimate" qualifier — this qualifier is built into the component and cannot be omitted by a consumer.

---

## Backtesting Components

- **`MetricsTable`**: `DataTable` composition showing MAE, RMSE, sMAPE, and directional accuracy per model version/horizon.
- **`ModelComparisonChart`**: shared with Forecast Components (see above) — same component, different data source.
- **`EconomicSimulationSummary`**: composes `StatCard`/`MetricValue` and `SavingsEstimate` to show simulated economic outcome vs. baseline for a backtest run.
- **`BacktestHistoryChart`**: time-series chart of rolling-backtest performance over historical decision dates, using the same historical/series conventions as `ForecastChart` where applicable (e.g., plotting realized vs. predicted rate over the backtest window).

---

## Component Contracts

### `Badge`
- **Purpose:** Render a status/risk/feasibility/direction chip with mandatory icon + label + color.
- **Inputs:** `variant` (enum: success | warning | error | info | risk-low | risk-medium | risk-high | feasibility-pass | feasibility-fail | feasibility-unknown | forecast-increase | forecast-decrease), `label` (string, required — never auto-derived silently from variant alone, so copy stays explicit), `icon` (auto-selected from variant per `ui-rules.md` table, override not permitted).
- **Outputs/events:** none (presentational only).
- **Required states:** all listed variants; no "no variant" default — a `Badge` without a variant is a build-time error, not a fallback style.
- **Data shape:** `{ variant: BadgeVariant; label: string }`.
- **Composition rules:** used inside table cells, cards, and inline text; never nested inside another `Badge`.
- **Accessibility:** icon has `aria-hidden`, label text is always present in the accessible tree (not image-only).

### `DataTable`
- **Purpose:** Shared table chrome (header, rows, alignment, hover/selected state, responsive sticky-column scroll).
- **Inputs:** `columns` (array of `{ key, label, align: left|right|center, isNumeric?: boolean }`), `rows` (array of row data objects), `rowKey` (accessor), `density` ('default' | 'compact'), `selectedRowKey?`, `onRowSelect?`.
- **Outputs/events:** `onRowSelect(rowKey)` when row selection is enabled.
- **Required states:** loading (renders `LoadingSkeleton` variant `row`), empty (renders `EmptyState`), populated.
- **Data shape:** generic row objects matching the caller's domain type (e.g., a vessel candidate, a backtest metric row); `DataTable` itself is data-agnostic.
- **Composition rules:** numeric columns must set `isNumeric: true` to receive right-alignment and Plex Mono rendering automatically — callers must not manually format numeric cell alignment.
- **Accessibility:** renders semantic `<table>`/`<th>`/`<td>`; sticky first column retains a scoped header association for screen readers.

### `ForecastChart`
- **Purpose:** Render historical + forecast + prediction-interval visualization for one route/vessel-class/horizon selection.
- **Inputs:** `historicalSeries` (array of `{ date, value }`), `forecastSeries` (array of `{ date, value }`), `interval` (array of `{ date, p10, p90 }`), `todayDate`, `horizonDays`, `compact?` (boolean, for Decision Dashboard embed).
- **Outputs/events:** `onPointHover(date)` optional, for coordinating a shared tooltip/legend.
- **Required states:** loading (`LoadingSkeleton` variant `chart`), empty/no-data (`EmptyState` — "No forecast available for this selection"), error (`ErrorAlert`), populated.
- **Data shape:** all series pre-aligned to a common date axis by the caller; `ForecastChart` does not perform date alignment itself (that is a data-layer concern, not a UI concern).
- **Composition rules:** always renders the "today" marker when `historicalSeries` and `forecastSeries` are both present; never renders interval band without an accompanying forecast line.
- **Accessibility:** exposes a linked/adjacent data table or textual summary (current value, P50, P10–P90, direction) for screen-reader users, per `ui-rules.md` → Accessibility.

### `VesselCandidateTable`
- **Purpose:** List candidate vessel classes with specs and per-constraint feasibility.
- **Inputs:** `candidates` (array of `{ vesselClass, dwt, draft, loa, beam, constraints: { draft, loa, beam, dwt }: FeasibilityResult, overall: FeasibilityResult }`), `onSelectCandidate?`.
- **Outputs/events:** `onSelectCandidate(vesselClass)` to drive `VesselSpecPanel`.
- **Required states:** loading, empty ("No candidate vessels evaluated yet"), populated.
- **Data shape:** `FeasibilityResult = 'pass' | 'fail' | 'unknown'`.
- **Composition rules:** every constraint column renders via `FeasibilityStatusBadge`, never raw text/color.
- **Accessibility:** each status cell's badge label is announced with its column header context (e.g., "Draft: Pass") via standard table semantics.

### `RiskSummaryCard`
- **Purpose:** Show overall risk level and category breakdown.
- **Inputs:** `overallRisk` ('low'|'medium'|'high'), `categories` (array of `{ category: 'market'|'port'|'vessel'|'external', level: RiskLevel, note?: string }`), `condensed?` (boolean, for Decision Dashboard embed).
- **Outputs/events:** none (presentational; navigation to full Risk page handled by caller).
- **Required states:** loading, populated. No "empty" state — risk assessment is only rendered once a requirement exists, per page composition below.
- **Data shape:** `RiskLevel = 'low' | 'medium' | 'high'`.
- **Composition rules:** `condensed` mode shows overall `Badge` + up to 4 category badges inline; full mode additionally renders `RiskFactorBreakdown`.
- **Accessibility:** category badges are individually labeled, not conveyed only via a color-coded row.

### `RecommendationReasoning`
- **Purpose:** Render the structured list of reasons behind a recommendation.
- **Inputs:** `reasons` (array of `{ label: string, detail: string, direction?: 'supports' | 'against' }`).
- **Outputs/events:** none.
- **Required states:** loading, populated. (Never rendered empty — a recommendation is not shown without reasoning, per `project-overview.md` explainability requirement.)
- **Data shape:** ordered list, rendered in the order provided by the domain layer (most significant factor first, per `model.md`/`architecture.md` recommendation assembly).
- **Composition rules:** each reason renders as a list item with `type-body` text; `direction` (if present) uses a neutral glyph, not status color, consistent with the freight-direction rule.
- **Accessibility:** rendered as a semantic list (`<ul>`/`<li>`), not styled `<div>`s.

### `SavingsEstimate`
- **Purpose:** Display an estimated savings/cost figure with its mandatory backtested qualifier.
- **Inputs:** `amount` (number), `currency` (string), `outcome` ('favorable' | 'unfavorable' | 'neutral'), `baselineLabel` (string, e.g., "vs. spot-only").
- **Outputs/events:** none.
- **Required states:** loading, populated, unavailable (renders `EmptyState`/`ErrorAlert` variant "insufficient backtest data" rather than a zero/blank figure).
- **Data shape:** `{ amount, currency, outcome, baselineLabel }`.
- **Composition rules:** the qualifier text "backtested/simulated estimate" is hard-coded into the component's render output and cannot be passed as an optional prop that a caller could omit.
- **Accessibility:** qualifier text is in the same accessible text block as the figure, not a separate tooltip.

---

## Page Composition

### 1. Decision Dashboard
`PageContainer` → `PageHeader` → `RequirementForm` (entry, or `SummaryCard` showing the current requirement once submitted) → `RecommendationSummaryCard` (composing `CharterTimingIndicator`, `FeasibilityStatusBadge`, `ContractStrategyComparison`, `RiskSummaryCard [condensed]`, `SavingsEstimate`, `RecommendationReasoning`) → `ForecastChart [compact]` → `EmptyState`/`LoadingSkeleton`/`ErrorAlert` as applicable at each stage.

### 2. Freight Forecast
`PageContainer` → `PageHeader` → `HorizonSelector` → `ForecastSummaryStat` (one or more `StatCard`s) → `ForecastChart [full]` → `ModelComparisonChart` → `UncertaintyIndicator` → `EmptyState`/`LoadingSkeleton`/`ErrorAlert` as applicable.

### 3. Port/Vessel Feasibility
`PageContainer` → `PageHeader` → `VesselCandidateTable` → `VesselSpecPanel` (on selection) → `FeasibilityExplanation` → `EmptyState`/`LoadingSkeleton`/`ErrorAlert` as applicable.

### 4. Risk
`PageContainer` → `PageHeader` → `RiskSummaryCard [full]` → `RiskFactorBreakdown` → `DisruptionIndicatorList` → `UncertaintyIndicator` → `EmptyState`/`LoadingSkeleton`/`ErrorAlert` as applicable.

### 5. Backtesting / Model Performance
`PageContainer` → `PageHeader` → `MetricsTable` → `ModelComparisonChart` → `BacktestHistoryChart` → `EconomicSimulationSummary` (composing `SavingsEstimate`) → `ContractStrategyComparison` (historical view) → `EmptyState`/`LoadingSkeleton`/`ErrorAlert` as applicable.

No page introduces a component outside this registry. If a page appears to need something new during implementation, the correct action is to extend this registry (see Invariants), not to build a one-off.

---

## Naming & Organization

- **Naming convention:** PascalCase component names exactly as listed in the Component Inventory (e.g., `ForecastChart`, not `forecast-chart` or `FreightForecastChart`). Component names describe what the component displays, not which page it's on — page-specific components are the only exception, and even they are named for their role (`RecommendationSummaryCard`, `RequirementForm`), not their page.
- **File/folder organization** (mirrors `architecture.md`'s `frontend/components/` structure):

```
frontend/components/
├── shell/          → AppShell, PageContainer, PageHeader, GlobalNotificationArea
├── nav/            → NavRail, NavItem
├── data-display/   → Card, StatCard, SummaryCard, DataTable, Badge, MetricValue,
│                     EmptyState, LoadingSkeleton, ErrorAlert
├── forms/          → TextInput, SelectInput, NumericInput, DateRangeInput,
│                     FormSection, FormFieldError
├── forecast/       → ForecastChart, HorizonSelector, ForecastSummaryStat,
│                     ModelComparisonChart, UncertaintyIndicator
├── feasibility/    → VesselCandidateTable, VesselSpecPanel,
│                     FeasibilityStatusBadge, FeasibilityExplanation
├── risk/           → RiskSummaryCard, RiskFactorBreakdown, DisruptionIndicatorList
├── recommendation/ → CharterTimingIndicator, ContractStrategyComparison,
│                     RecommendationReasoning, SavingsEstimate
├── backtesting/    → MetricsTable, EconomicSimulationSummary, BacktestHistoryChart
└── page-specific/  → RequirementForm, RecommendationSummaryCard
```

- **Shared vs. page-specific rule:** a component lives outside `page-specific/` the moment it is used, or concretely planned to be used, on more than one page — matching the Reusable? column in the Component Inventory. `page-specific/` components must import only from the other folders above (composition of shared primitives), never define new Card/Badge/Table visual treatment inline.
- Every component folder maps 1:1 to a section of this registry document — a new component is added to both the matching folder and the matching section, never one without the other.

---

## Invariants

1. Every page reuses registry components instead of creating duplicates; a new visual pattern that resembles an existing registry component is treated as a variant of that component, not a new one.
2. Every component's visual output must conform to `ui-tokens.md` (values) and `ui-rules.md` (usage rules) — this registry defines structure and contracts only, never new visual values.
3. No page-specific copy of a shared component (e.g., a Feasibility-page-only badge style) may exist; if a page needs different behavior, the shared component gains a variant/prop, defined here.
4. Components must not have overlapping responsibilities — e.g., `RiskSummaryCard` and `RiskFactorBreakdown` are distinct because one is a condensed overview and the other is the full itemized list; a new component must not duplicate either's purpose.
5. Every reusable component has an explicit data/state contract as defined in Component Contracts before it is implemented — no component is built from a name alone.
6. Loading, empty, error, and unavailable states are implemented for every component that can be in those states, per each component's "Required states"; a component shipped without them is incomplete.
7. Status, risk, and feasibility components (`Badge` and everything built on it) must never rely on color alone — icon and label are structurally required inputs, not optional props.
8. Forecast, historical, and uncertainty visualizations (`ForecastChart`, `ModelComparisonChart`, `BacktestHistoryChart`) must preserve the line-style/fill distinctions defined in `ui-rules.md` — a component may not simplify these into color-only distinctions for any reason, including a "compact" display mode.
9. A registry component must remain usable, without modification to its contract, on every page listed in its "Used On" column; if a page needs materially different behavior, that is a signal to introduce a variant or a new page-specific component, not to special-case the shared component's internals per page.
10. Any new reusable UI pattern discovered during implementation is added to this registry (inventory table, relevant section, contract if warranted) before or alongside its first implementation — it is never introduced silently inside a single page's code.
