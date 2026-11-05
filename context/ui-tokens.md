# UI Tokens

## Design Direction

This is an **instrument panel, not a dashboard in the marketing sense**. The user is a freight/procurement decision-maker who needs to read current state, forecast, uncertainty, feasibility, and risk quickly and unambiguously — the same posture as someone reading a ship's bridge console or a control-room panel, not someone browsing a product page. The design language is drawn from two real sources in the product's own domain: **maritime navigation instrumentation** (chart plotters, depth soundings, signal conventions) and **the precision/steel vocabulary of SAIL's own industry** (graphite, oxide, forge-amber). Neither is decorative — both map onto real functional needs of this product: charts that read like navigation plots (historical track, forecast heading, uncertainty as a charted band around it), and a restrained, high-precision numeric register appropriate to a steel/logistics enterprise tool.

Concretely, this means:
- Low-chroma, cool-neutral UI chrome that recedes, so data is always the loudest thing on screen.
- A monospace numeric register for every figure that must be compared or aligned in a column (freight rates, MAE/RMSE, DWT, draft) — because misaligned digits are a real readability failure in a dense financial/technical dashboard, not a stylistic afterthought.
- Small, uppercase "instrument label" micro-typography for stat/card headers (`CURRENT FREIGHT`, `CHARTER TIMING`), echoing how a gauge or console names what it's displaying.
- Flat surfaces with hairline borders instead of soft drop shadows, reserving elevation for genuinely transient UI (popovers, modals, toasts) — the interface should feel fixed and legible, not glossy.
- No color-only signaling anywhere. Risk, feasibility, and status always pair a color with an icon and a text label, because this system's outputs feed real chartering decisions and must remain legible to colorblind users and in poor lighting/print.

This is explicitly not: a cream/serif/terracotta marketing aesthetic, a near-black neon-accent dashboard, or a broadsheet/newspaper layout. Those are generic defaults; this system is derived from the product's own domain instead.

## Theme

**Light theme is the default and primary theme.** This is an office/enterprise decision tool used during working hours for active procurement decisions, not a 24-hour monitoring wall — readability in normal office lighting is the priority. A **dark "watch" theme** is also defined for extended monitoring sessions (e.g., the Freight Forecast or Backtesting pages left open for reference), built from the same semantic token names so no component needs theme-specific logic.

All component-level styling must reference **semantic tokens** (e.g., `surface-primary`, `text-secondary`, `border-default`), never the raw primitive color values directly. Primitives exist only to define semantic tokens once per theme.

| Semantic token | Light value | Dark value |
|---|---|---|
| `surface-canvas` | `slate-50` `#F5F6F8` | `slate-950` `#0B0D13` |
| `surface-primary` (cards, panels) | `slate-0` `#FFFFFF` | `slate-900` `#12151D` |
| `surface-secondary` (table headers, nav) | `slate-100` `#E9EBEF` | `slate-800` `#1C202B` |
| `surface-inverse` (nav rail) | `slate-800` `#1C202B` | `slate-950` `#0B0D13` |
| `text-primary` | `slate-900` `#12151D` | `slate-100` `#E9EBEF` |
| `text-secondary` | `slate-600` `#454C5E` | `slate-400` `#8B92A3` |
| `text-muted` | `slate-500` `#636B7E` | `slate-500` `#636B7E` |
| `text-inverse` | `slate-0` `#FFFFFF` | `slate-0` `#FFFFFF` |
| `border-default` | `slate-200` `#D6D9E0` | `slate-700` `#2E3444` |
| `border-strong` | `slate-300` `#B8BDC8` | `slate-600` `#454C5E` |

## Typography

**UI/heading face:** IBM Plex Sans — a technical, engineering-register sans-serif with good legibility at small sizes, distinct from generic default UI fonts.
**Numeric/data face:** IBM Plex Mono — used for every figure that participates in column alignment or side-by-side comparison (freight rates, MAE/RMSE/sMAPE, DWT/draft/LOA, percentages, dates in tables). This is a functional choice: financial and technical figures must align on the decimal point and digit width, which only a monospace face guarantees.
**Body face:** IBM Plex Sans (same as UI face) — no separate serif is introduced; this is not an editorial product.

Only these two families are used anywhere in the product.

### Type scale

| Token | Size / line-height | Face | Weight | Usage |
|---|---|---|---|---|
| `type-display` | 2.25rem / 1.2 | Plex Sans | 600 | Rare — top-level page identity only |
| `type-h1` | 1.75rem / 1.25 | Plex Sans | 600 | Page title |
| `type-h2` | 1.375rem / 1.3 | Plex Sans | 600 | Section heading |
| `type-h3` | 1.125rem / 1.35 | Plex Sans | 600 | Card/panel heading |
| `type-body-lg` | 1rem / 1.5 | Plex Sans | 400 | Emphasized body text, explanation paragraphs |
| `type-body` | 0.875rem / 1.5 | Plex Sans | 400 | Default UI text |
| `type-body-sm` | 0.8125rem / 1.45 | Plex Sans | 400 | Secondary/support text |
| `type-caption` | 0.75rem / 1.4 | Plex Sans | 500 | Timestamps, footnotes, chart axis labels |
| `type-eyebrow` | 0.6875rem / 1.3, uppercase, +0.04em tracking | Plex Sans | 600 | Instrument-style card/stat labels (e.g. `CURRENT FREIGHT`) |
| `type-data-lg` | 1.5rem / 1.2 | Plex Mono | 600 | Primary stat figures (Decision Dashboard hero numbers) |
| `type-data-md` | 1.125rem / 1.3 | Plex Mono | 500 | Secondary figures, chart callouts |
| `type-data-sm` | 0.875rem / 1.4 | Plex Mono | 400 | Table cell figures, inline numeric values |

Weights are restricted to 400 (Regular), 500 (Medium), and 600 (Semibold). Bold (700) is not used — Semibold is the system's maximum emphasis, keeping the interface from feeling like marketing copy. Data-bearing text is never set below `type-caption` (12px equivalent is not used for anything meaningful — `type-caption` at 0.75rem/13px effective is the floor).

## Colors

All primitives feed into semantic tokens (see Theme). Raw primitives are listed here as the single source of truth; components consume semantic tokens only.

### Neutral (graphite/steel, cool undertone)
`slate-0 #FFFFFF` · `slate-50 #F5F6F8` · `slate-100 #E9EBEF` · `slate-200 #D6D9E0` · `slate-300 #B8BDC8` · `slate-400 #8B92A3` · `slate-500 #636B7E` · `slate-600 #454C5E` · `slate-700 #2E3444` · `slate-800 #1C202B` · `slate-900 #12151D` · `slate-950 #0B0D13`

### Primary — marine blue (navigation/instrument blue; primary actions, links, forecast median line)
`marine-100 #DCE8F5` · `marine-300 #7FA8CC` · `marine-500 #2C5F8A` (primary) · `marine-600 #204864` · `marine-700 #163349`

### Accent — oxide amber (steel-forge amber; used sparingly for high-attention emphasis, e.g. a "Charter Now" recommendation highlight)
`amber-100 #FBE8CF` · `amber-400 #D98E3B` · `amber-600 #A8621F`

### Status
| Role | 100 (tint bg) | 500 (default) | 700 (text on tint) |
|---|---|---|---|
| Success | `#DCEEE1` | `#2E7D4F` | `#1F5636` |
| Warning | `#FBEFCF` | `#B8791E` | `#8A5A14` |
| Danger | `#F8DEDC` | `#B23A32` | `#832920` |
| Info | `marine-100` | `marine-500` | `marine-700` |

### Risk states (Decision Dashboard, Risk page)
- `risk-low` → Success tokens
- `risk-medium` → Warning tokens
- `risk-high` → Danger tokens
Each risk level pairs its color with a distinct icon (circle-check / triangle / octagon) and a text label — never color alone (see Invariants).

### Feasibility states (Port/Vessel Feasibility page)
- `feasibility-pass` → Success tokens, check icon
- `feasibility-fail` → Danger tokens, cross icon
- `feasibility-unknown` → `slate-400` text on `slate-100` tint, dashed border, question icon (used when a constraint cannot be evaluated due to missing data — must remain visually distinct from both pass and fail, never silently defaulted to either)

### Freight rate movement — deliberately neutral

Freight rate increases and decreases are **not** color-coded red/green. A rising rate is not intrinsically bad (SAIL may already be covered) nor is falling intrinsically good (it may mean a missed window) — coloring direction would encode a false judgment. Movement is shown with a neutral **direction glyph** (▲/▼) in `text-secondary`, plus the numeric change in `type-data` mono, with no status color applied.

Color for "good/bad" is reserved exclusively for **recommendation-outcome and backtest economics**, where the semantic is genuinely unambiguous relative to a stated baseline:
- `outcome-favorable` → Success tokens (e.g., backtested estimated savings vs. baseline)
- `outcome-unfavorable` → Danger tokens (e.g., backtested estimated cost vs. baseline)

### Forecast / historical / prediction-interval palette
- `series-historical` → `slate-700` (solid line)
- `series-forecast` → `marine-500` (solid up to "today," dashed beyond)
- `series-interval-fill` → `marine-300` at 12% opacity
- `series-interval-edge` → `marine-300` at 45% opacity, dashed
- `series-today-marker` → `slate-400`, dashed vertical hairline

### Categorical data-viz palette (model comparison, multi-series charts)
`chart-1 marine-500 #2C5F8A` · `chart-2 amber-400 #D98E3B` · `chart-3 teal-500 #2E8A82` · `chart-4 violet-500 #6E5A9E` · `chart-5 slate-500 #636B7E` · `chart-6 rose-500 #B2456B`

This 6-color set is chosen to remain distinguishable under common color-vision deficiencies. When more than 3 series are shown (e.g., XGBoost vs. LSTM vs. TimesFM vs. Chronos-2), color must be paired with a distinct line-dash pattern per series (see Data Visualization).

## Spacing

4px base unit.

| Token | Value | Typical usage |
|---|---|---|
| `space-0` | 0 | Reset |
| `space-1` | 4px | Icon-to-text gap, tight inline spacing |
| `space-2` | 8px | Compact control padding, badge internal padding |
| `space-3` | 12px | Input/button vertical padding |
| `space-4` | 16px | Default component padding, form field gaps |
| `space-5` | 20px | Card internal padding (compact variant) |
| `space-6` | 24px | Card internal padding (default), grid gutter (desktop) |
| `space-8` | 32px | Section separation within a page |
| `space-10` | 40px | Default table row height |
| `space-12` | 48px | Page-level vertical rhythm between major blocks |
| `space-16` | 64px | Top-level page padding (desktop) |
| `space-20` | 80px | Reserved for rare large-format spacing (empty states) |

## Layout

- **Max content width:** 1440px, centered, for the main content area (excludes the fixed nav rail). Wide enough to support the multi-panel Decision Dashboard without wrapping key stat blocks prematurely.
- **Grid:** 12-column grid. Gutter `space-6` (24px) at desktop widths, `space-4` (16px) below `lg`.
- **Page padding:** `space-16` (64px) horizontal at desktop (`xl`+), reducing to `space-8` at `lg`/`md`, `space-4` at `sm` and below.
- **Section spacing:** `space-12` between major page sections (e.g., between the recommendation summary and the supporting-evidence panels on the Decision Dashboard).
- **Density:** "comfortable-dense" — optimized for an operator scanning many figures quickly, not a consumer app. Default table row height `space-10` (40px); a compact table variant at 32px is available for dense metrics tables (e.g., Backtesting page model-comparison tables).
- **Navigation rail:** fixed left rail, 240px expanded / 64px icon-only collapsed, persistent across all five pages so the user always has one-click access to Decision Dashboard, Freight Forecast, Feasibility, Risk, and Backtesting.

## Borders & Radius

- **Border widths:** `border-hairline` 1px (default for cards, tables, inputs), `border-emphasis` 2px (focus rings, selected states).
- **Radius scale:** `radius-none` 0px (table cells, dense grids), `radius-sm` 4px (inputs, small controls), `radius-md` 6px (cards, buttons, panels — the system default), `radius-lg` 10px (modals, large overlay panels), `radius-full` (status badges/pills only).

Radius is kept small and restrained throughout — the interface should read as precise instrumentation, not a soft consumer app. Pill radius (`radius-full`) is reserved specifically for status badges/chips, where the fully-rounded shape is a widely understood convention for a compact status label and does not conflict with the flatter, rectangular treatment used everywhere else.

## Elevation

Shadows are used sparingly. Default surfaces (cards, panels) are distinguished from the canvas by a hairline border and a subtly different surface color, **not** a drop shadow — this keeps the dashboard feeling flat and fixed, appropriate to an instrument-panel reading, and reserves shadow specifically as a signal of temporary/overlaid UI.

| Token | Value | Usage |
|---|---|---|
| `elevation-0` | none | Default cards, panels, table surfaces |
| `elevation-1` | `0 2px 8px rgba(11,13,19,0.08)` | Dropdowns, tooltips, popovers |
| `elevation-2` | `0 8px 24px rgba(11,13,19,0.16)` | Modals, dialog overlays |
| `elevation-3` | `0 12px 32px rgba(11,13,19,0.22)` | Toasts/transient notifications |

## Components

- **Buttons:** height 36px, `radius-md`, `type-body` weight 500. Primary: `marine-500` background, `text-inverse` label. Secondary: transparent background, `border-strong` outline, `text-primary` label. Tertiary/text button: no border, `marine-600` label. No destructive button variant is defined at the token level for primary workflows, since this system performs no autonomous execution or data-destructive actions (per `project-overview.md`); if a destructive action is later introduced (e.g., deleting a saved requirement), it uses the Danger status tokens.
- **Inputs:** height 36px, `radius-sm`, `border-default` border, `surface-primary` background, `type-body` text. Focus state: `border-emphasis` (2px) in `marine-500` with 2px outer offset — never suppressed.
- **Cards:** `surface-primary` background, `border-default` hairline border, `radius-md`, `elevation-0`, padding `space-6` (default) or `space-5` (compact). Card headers use `type-eyebrow` for the label (e.g., `RECOMMENDATION`, `RISK`) above the primary content — the instrument-label treatment described in Design Direction.
- **Tables:** header row `surface-secondary` background, `type-caption` weight 600 uppercase labels; body rows separated by `border-default` hairline dividers rather than zebra striping, keeping dense financial tables calm; numeric cells right-aligned in `type-data-sm` mono; row height `space-10` default, 32px compact variant.
- **Badges/chips:** `radius-full`, `space-2` horizontal padding, `type-caption` weight 600, always icon + label + status-color pairing (never a bare color dot). Used for risk level, feasibility result, contract-strategy type, model name.
- **Navigation (rail):** `surface-inverse` background, `text-inverse`/`slate-300` label color. Active item: `marine-400` 3px left border accent + `slate-700` background wash + weight 600 label — never indicated by color alone, since the border accent and weight change are independently sufficient.
- **Alerts/banners:** `border-left` 3px in the relevant status color, tinted status-100 background, status-700 text, paired icon (info/check/triangle/cross) — never tint-only.
- **Stat blocks** (Decision Dashboard hero figures): `type-eyebrow` label, `type-data-lg` mono value, optional neutral direction glyph + `type-caption` supporting text underneath (e.g., "as of 28 Aug 2026").
- **Status indicators (inline, e.g. within tables):** icon + `type-body-sm` text label at minimum; color is additive, never the sole carrier of meaning.

## Data Visualization

- **Historical series:** solid line, `series-historical` (`slate-700`), 1.5px weight.
- **Forecast series:** solid line in `series-forecast` (`marine-500`) up to the current date; dashed from the current date forward, so "known" vs. "predicted" is legible even without color (line-style redundancy, not color alone).
- **Prediction interval:** rendered as a shaded band (`series-interval-fill`, 12% opacity) with a dashed outer boundary (`series-interval-edge`) — deliberately a different rendering technique (fill vs. line) from both the historical and forecast lines, so uncertainty can never be mistaken for a third data series.
- **"Today" reference marker:** dashed vertical hairline (`series-today-marker`) with a small caption label, present on every forecast chart so historical/forecast boundary is always explicit.
- **Freight movement (▲/▼):** neutral glyph + mono figure, no status color (see Colors — Freight rate movement).
- **Risk visualization:** three-tier chip (Low/Medium/High) using Risk-state tokens, plus icon; where risk is plotted spatially (e.g., a risk-by-category chart), each tier also gets a distinct marker shape (circle / triangle / square) for colorblind-safe redundancy.
- **Feasibility visualization:** pass/fail/unknown chips per constraint (draft, LOA, beam, DWT), each with its own icon per the Feasibility-state tokens; a feasibility summary table always shows all evaluated constraints, not only the failing ones, so the "why" is inspectable.
- **Model comparison charts (Backtesting page):** categorical palette (`chart-1`–`chart-6`); when more than 3 series are shown simultaneously, each series is additionally assigned a distinct dash pattern (solid / dashed / dotted / dash-dot) so hue is never the only distinguishing signal.
- **Axis/gridlines:** gridlines in `slate-100` (light) / `slate-800` (dark); axis tick labels use `type-caption` in `series-historical`-adjacent mono styling (`Plex Mono`, `text-muted`) so numeric axis values align visually with the data-ink figures elsewhere on the page.
- **Economic/backtest outcome bars or deltas:** use `outcome-favorable` / `outcome-unfavorable` tokens (see Colors), always labeled explicitly as "backtested/simulated estimate" per `model.md` — never presented as a guaranteed figure.

## Responsive Behavior

Breakpoints: `sm 640px` · `md 768px` · `lg 1024px` · `xl 1280px` · `2xl 1536px`.

- **≥ xl (1280px):** Full layout — expanded nav rail (240px), 12-column grid, all five pages at full density.
- **lg–xl (1024–1280px):** Nav rail remains expanded; page padding reduces to `space-8`; dashboard stat grid moves from 4 columns to 3.
- **md–lg (768–1024px):** Nav rail collapses to icon-only (64px); stat grid moves to 2 columns; charts retain full width but legends move below the chart area.
- **< md (768px):** Nav rail becomes a bottom bar or slide-out drawer; stat grid becomes single column; tables become horizontally scrollable with the first (label) column sticky; page padding reduces to `space-4`.
- This is primarily a desktop/tablet enterprise tool — the design is not optimized below `sm`, but must remain functional (readable, scrollable, no data loss) at `sm` for occasional field/tablet use at a port or terminal.

## Accessibility

- **Contrast:** minimum 4.5:1 for body text against its surface, minimum 3:1 for large text (`type-h1`/`type-h2`/`type-data-lg`) and meaningful icons, in both light and dark themes. Data-critical numeric text (freight figures, risk scores, metrics) targets AAA (7:1) where achievable without breaking the palette.
- **Focus states:** every interactive element has a visible 2px `marine-500` focus outline with 2px offset; focus is never suppressed via CSS reset.
- **Status communication:** color is always additive to an icon and a text label for risk, feasibility, alerts, and status indicators — never the sole channel (restated as a hard invariant below).
- **Charts:** categorical series use the colorblind-safe palette plus shape/dash redundancy per Data Visualization; every chart has an accessible data-table fallback or sufficient `aria` labeling for screen-reader users; prediction-interval fill must retain sufficient contrast against the surface to be perceivable, independent of hue perception.
- **Typography:** no meaningful (non-decorative) text is set smaller than `type-caption` (0.75rem); body text defaults to `type-body` (0.875rem) minimum for primary content.
- **Motion:** `prefers-reduced-motion` is respected; no status, risk, or recommendation information is conveyed through animation alone.

## Invariants

1. Components consume semantic tokens (`surface-*`, `text-*`, `border-*`, status/risk/feasibility tokens) — never raw hex values or primitive token names directly.
2. Risk level, feasibility result, and any status indicator must always pair a color with an icon and a text label; color alone is never sufficient.
3. Freight rate direction (increase/decrease) is never color-coded red/green; only recommendation-outcome and backtest-economics figures (favorable/unfavorable vs. a stated baseline) may use Success/Danger tokens, and must be labeled as backtested/simulated estimates per `model.md`.
4. Prediction intervals are always rendered as a shaded band with a dashed outer edge — a distinct rendering technique from the solid historical and forecast lines — never as a third solid line.
5. Any numeric value that participates in column alignment or side-by-side comparison uses the `type-data-*` monospace scale; UI labels and body copy never use the monospace face.
6. Default page surfaces (cards, panels, tables) use `elevation-0` with a hairline border; shadow elevation is reserved for genuinely transient overlays (popovers, modals, toasts).
7. Minimum contrast ratios (4.5:1 body text, 3:1 large text/icons) are met in both the light and dark theme.
8. No meaningful status, risk, feasibility, or recommendation information is conveyed by color or animation alone.
9. Categorical chart series beyond three simultaneous series must use both color and a line-pattern or marker-shape redundancy.
10. Spacing, radius, elevation, and typography values are always token references in implementation — no hardcoded pixel or hex values in component code.
11. Light theme is the default; the dark theme is a 1:1 remap of the same semantic token names, never a separately designed system.
12. Card and stat-block "eyebrow" micro-labels use the defined `type-eyebrow` treatment consistently on all five pages (Decision Dashboard, Freight Forecast, Feasibility, Risk, Backtesting) — this is the system's one signature typographic device and must not be applied inconsistently or embellished further.
