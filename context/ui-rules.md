# UI Rules

This file defines how the tokens in `ui-tokens.md` must be applied when building components and pages — `ui-tokens.md` defines the values, `ui-rules.md` defines the usage.

---

## Font

- The only two font families in the product are **IBM Plex Sans** (UI, headings, body) and **IBM Plex Mono** (all data/numeric figures), as defined in `ui-tokens.md` → Typography. No other font family may be imported or referenced anywhere in the codebase.
- Load both families once, globally (e.g., via `next/font` in the root layout), and expose them as CSS variables (`--font-sans`, `--font-mono`) consumed by the token-to-CSS mapping. Individual components must never import a font directly.
- Plex Mono is used exclusively for values that participate in numeric comparison or column alignment: freight rates, MAE/RMSE/sMAPE, DWT/draft/LOA/beam, percentages, P10/P50/P90, dates inside tables. Plex Mono must never be used for prose, labels, or headings.
- Plex Sans is used for everything else, including card/stat "eyebrow" labels (`type-eyebrow`), which use Plex Sans at weight 600 with the token's defined letter-spacing — not a different face.
- Font weight is restricted to 400 / 500 / 600 exactly as defined in `ui-tokens.md`. Never request or apply weight 700 or any weight outside this set.

---

## Layout

- Max content width for the main content area (excluding the nav rail) is **1440px**, centered, per `ui-tokens.md` → Layout.
- Page horizontal padding: `space-16` at `xl`+ widths, `space-8` at `lg`/`md`, `space-4` at `sm` and below — exactly the breakpoint behavior defined in `ui-tokens.md` → Responsive Behavior. Do not invent intermediate padding values.
- Grid: 12-column grid with `space-6` gutter at desktop, `space-4` gutter below `lg`. Every page-level layout must be built on this grid, not ad hoc flex spacing.
- Section spacing (vertical gap between major page blocks, e.g., between the Decision Dashboard's recommendation summary and its supporting-evidence panels) is always `space-12`. Spacing between cards within the same section is `space-6`.
- Nav rail: fixed left rail, 240px expanded / 64px collapsed, present and persistent on all five pages. The main content area's left offset must always equal the rail's current width — never overlap or leave a gap.
- Density is "comfortable-dense" everywhere: default table row height `space-10` (40px), with the 32px compact variant reserved for dense metrics tables specifically (e.g., Backtesting model-comparison table). Do not apply compact density to primary decision-facing tables (e.g., Vessel Feasibility) where legibility matters more than row count.

---

## Navigation

- Nav rail background is `surface-inverse`; item labels use `text-inverse` (default) or `slate-300` (secondary), per `ui-tokens.md` → Theme/Components.
- **Inactive item:** `slate-300` label, `type-body` weight 400, no background, no border accent.
- **Hover:** background shifts to a subtle wash (`slate-700` at reduced opacity is acceptable as the hover wash since it derives from the existing `surface-inverse` neighbor color, not a new token) and label brightens to `text-inverse`.
- **Active item:** `marine-400` 3px left border accent + `slate-700` background wash + label weight 600 + `text-inverse` color. All three signals (border, background, weight) must be present together — never rely on the border accent alone, and never rely on background alone.
- **Focus (keyboard):** visible 2px `marine-500` outline with 2px offset, applied to the entire nav item hit area, regardless of active/inactive state. Focus must remain visible against the dark `surface-inverse` background.
- **Selected vs. active:** in this product these are the same state (the current page) — there is no separate "selected" concept in top-level navigation. Do not introduce one.
- **Disabled:** not used in top-level navigation (all five pages are always reachable); if a future sub-item must be disabled, it uses `slate-500` label color, no hover/focus response, and `aria-disabled="true"`.
- Below `md` (768px), the rail collapses per `ui-tokens.md` → Responsive Behavior (icon-only at `md`–`lg`, bottom bar/drawer below `md`). The active-state rules above still apply in full within the collapsed/drawer form.

---

## Cards

Standard card recipe (applies to every card unless a variant is explicitly noted):

- Background: `surface-primary`
- Border: `border-hairline` (1px) in `border-default`
- Radius: `radius-md`
- Elevation: `elevation-0` (no shadow)
- Padding: `space-6` (default) — use `space-5` only for compact/dense card variants (e.g., a small stat card in a 4-up grid), never mix the two paddings within the same grid row.
- Internal spacing between the eyebrow label, heading, and content: `space-2` between eyebrow and heading, `space-4` between heading and body content.
- Card header uses `type-eyebrow` for the label above the title (per `ui-tokens.md` Components), followed by `type-h3` for the card title if the card has one.

**When to use a card:** to group a discrete unit of decision-relevant information the user should be able to scan independently — a stat block, a feasibility result, a risk category, a recommendation summary. **When not to use a card:** do not wrap an entire page section or an entire table in a card merely for visual framing; tables and charts that already have their own container treatment (header row, axis, border) do not need an additional outer card unless they sit alongside other cards in the same grid row and need visual parity.

Cards never use `elevation-1` or higher — elevation is reserved for popovers/modals/toasts per `ui-tokens.md` → Elevation. A card must never be given a drop shadow "for emphasis"; emphasis is achieved with `border-strong` or the accent border pattern used for highlighted recommendations (see Decision & Status Indicators).

---

## Typography Hierarchy

| Element | Token | Notes |
|---|---|---|
| Page title (e.g., "Decision Dashboard") | `type-h1` | One per page, at the top of the main content area |
| Section heading (e.g., "Contract Strategy Comparison") | `type-h2` | One per major section |
| Card/panel heading | `type-h3` | Inside a card, below the eyebrow label if present |
| Card/stat eyebrow label (e.g., "CURRENT FREIGHT") | `type-eyebrow` | Always uppercase, always above the value/title it labels — never used as a standalone heading with no associated value |
| Body/explanation text | `type-body` or `type-body-lg` | `type-body-lg` only for the recommendation explanation paragraph on the Decision Dashboard; `type-body` everywhere else |
| Secondary/supporting text | `type-body-sm` | Sub-labels, helper text under form fields |
| Timestamps, footnotes, chart axis labels | `type-caption` | Always `text-muted` color |
| Primary stat figures (e.g., "$28.4/MT") | `type-data-lg` (Plex Mono) | Used only for the single most important figure in a stat block |
| Secondary figures, chart callouts | `type-data-md` (Plex Mono) | Used for supporting numbers within a stat block or chart annotation |
| Table cell numeric values | `type-data-sm` (Plex Mono) | Always right-aligned within the cell |
| Table header labels | `type-caption` weight 600, uppercase | Matches `ui-tokens.md` Components → Tables |
| Chart axis tick labels | `type-caption` in Plex Mono, `text-muted` | Numeric ticks always use Plex Mono even though `type-caption` is otherwise a Plex Sans size |

Heading levels must be used in document order (`h1` → `h2` → `h3`) for both visual hierarchy and semantic HTML — never skip a level to achieve a smaller/larger visual size; use the matching type token with the correct semantic tag instead.

---

## Badges

- Shape: `radius-full` (pill), padding `space-2` horizontal, `type-caption` weight 600 text.
- Every badge is **icon + label + color**, never color/text alone and never icon alone. This is non-negotiable per `ui-tokens.md` invariant 2.

| Variant | Color tokens | Icon | Used for |
|---|---|---|---|
| Success | Success 100/500/700 | check-circle | Positive confirmations, favorable outcomes |
| Warning | Warning 100/500/700 | triangle | Medium risk, caution states |
| Error | Danger 100/500/700 | x-circle | Failures, high risk |
| Info | Info 100/500/700 | info-circle | Neutral/informational states |
| Risk — Low | Success tokens | check-circle | Risk page, Decision Dashboard risk chip |
| Risk — Medium | Warning tokens | triangle | Risk page, Decision Dashboard risk chip |
| Risk — High | Danger tokens | octagon | Risk page, Decision Dashboard risk chip |
| Feasibility — Pass | Success tokens | check | Vessel/Port Feasibility page, per-constraint and overall result |
| Feasibility — Fail | Danger tokens | x | Vessel/Port Feasibility page |
| Feasibility — Unknown | `slate-400` text on `slate-100`, dashed border | question-mark | Constraint not evaluable due to missing data — must never be silently rendered as pass or fail |
| Forecast direction — Increase | Neutral (`text-secondary`), no status color | arrow-up | Freight Forecast page — direction is neutral, not good/bad (see Data Visualization) |
| Forecast direction — Decrease | Neutral (`text-secondary`), no status color | arrow-down | Freight Forecast page |

Badge text is always a real word or short phrase ("Low", "Pass", "Medium risk") — never a bare symbol or color swatch with no text.

---

## Buttons

| Variant | Background | Text | Border | Usage |
|---|---|---|---|---|
| Primary | `marine-500` | `text-inverse` | none | The single primary action in a given context (e.g., "Generate Recommendation") — at most one primary button visible per view |
| Secondary | transparent | `text-primary` | `border-strong` | Secondary actions alongside a primary action (e.g., "View Backtest Detail") |
| Ghost/tertiary | transparent | `marine-600` | none | Low-emphasis inline actions (e.g., "Change route") |
| Destructive | Danger `500` background, `text-inverse` | — | none | Reserved for genuinely destructive, non-recommendation actions only (e.g., deleting a saved requirement draft) — never used for navigation or for anything resembling chartering execution, per `project-overview.md` scope |

- Size: height 36px, `radius-md`, horizontal padding `space-4`, `type-body` weight 500 label.
- Icon placement: icon precedes the label with `space-2` gap when present; icon-only buttons are reserved for repeated toolbar actions (e.g., chart zoom) and must always carry an `aria-label`.
- States: hover darkens the background one step (`marine-500` → `marine-600` for primary); focus uses the standard 2px `marine-500` outline at 2px offset; disabled reduces opacity to ~50% and removes hover/focus response, with `aria-disabled="true"`.
- Buttons never trigger autonomous chartering, booking, or financial actions — every button in this product either navigates, filters/reconfigures a view, or triggers a computation (forecast, backtest run) that the user reviews, per `project-overview.md` scope boundaries.

---

## Form Inputs

- Height 36px, `radius-sm`, `border-default` border, `surface-primary` background, `type-body` text, padding `space-3` vertical / `space-4` horizontal.
- Label: `type-body-sm` weight 500, `text-primary`, positioned above the field with `space-2` gap. Every input has a visible label — placeholder text is never used as a substitute for a label.
- Placeholder text (when used for format hints, e.g., "e.g. 50,000"): `text-muted`, `type-body`, never conveys required information the label doesn't already state.
- Focus: `border-emphasis` (2px) in `marine-500`, 2px outer offset, matching the global focus treatment.
- Error state: border becomes Danger `500`, an inline message appears below the field in `type-body-sm` Danger `700` text with an x-circle icon preceding it, and the field's label gains no color change (color change lives on the border + message, not the label, to avoid relying on color alone — the icon+message pairing carries the meaning).
- Disabled: `slate-100` background, `text-muted` text, `border-default` border unchanged, cursor not-allowed, no focus ring.

**Procurement requirement inputs specifically** (per `project-overview.md` required inputs):

| Field | Input type | Notes |
|---|---|---|
| Cargo type | Select (single) | Options sourced from supported cargo types; free text not permitted for this required field |
| Quantity | Numeric input, Plex Mono value display | Must display unit ("MT") as a fixed suffix inside or adjacent to the field, not left implicit |
| Origin | Select (single) | Options limited to the initial geographic scope in `project-overview.md`; do not allow arbitrary text entry |
| Destination | Select (single) | Same constraint as Origin |
| Loading window | Date range picker | Two bounded dates (start/end); validation must enforce start ≤ end |
| Number of voyages | Numeric input (integer, min 1), Plex Mono value display | Stepper controls acceptable; no decimal input |
| Contract horizon | Numeric input (integer, months) or select of common horizons | Must be paired with a `type-body-sm` unit label ("months") |

All numeric fields render their live value in Plex Mono once populated (matching table/stat conventions), even though the input chrome itself uses `type-body`. Required fields are marked with a consistent asterisk or "Required" `type-caption` tag — pick one convention and apply it to every required field across the entire requirement form, never mix conventions within the same form.

---

## Tables

- Header row: `surface-secondary` background, `type-caption` weight 600 uppercase labels, `border-default` bottom border.
- Row divider: `border-default` hairline between rows; no zebra striping (per `ui-tokens.md`, calm dense tables over alternating fill).
- Row height: `space-10` (40px) default; 32px compact variant only for the Backtesting page's dense metrics tables.
- Alignment: text/label columns left-aligned; all numeric columns (Plex Mono) right-aligned, so digits align vertically for scanning/comparison. Status/badge columns are center-aligned.
- Hover: row background shifts to `surface-secondary` at reduced strength; hover state must not change text color or remove the row divider.
- Selected row (where row selection exists, e.g., choosing a candidate vessel): `marine-100` background wash plus a `marine-500` left border accent — same "two-signal" pattern as active navigation, never background alone.
- Status cells (e.g., a feasibility pass/fail column) use the Badges component, not raw colored text.
- Responsive: below `md`, tables become horizontally scrollable with the first (label/identifier) column sticky, per `ui-tokens.md` → Responsive Behavior. Do not collapse tables into stacked card lists as an alternative pattern — horizontal scroll with a sticky first column is the one reusable pattern for all tables in this product.

---

## Data Visualization

All chart rules below implement `ui-tokens.md` → Data Visualization; no chart may introduce a color, line style, or fill not defined there.

- **Historical freight:** solid line, `series-historical` (`slate-700`), 1.5px weight.
- **Forecast:** solid line in `series-forecast` (`marine-500`) up to the "today" marker, then dashed beyond it. The dash change at "today" is mandatory — color alone must never be the only signal separating known from predicted values.
- **Prediction intervals:** shaded band (`series-interval-fill`) with a dashed outer edge (`series-interval-edge`) — always a fill+dashed-edge, never a second solid line, so it cannot be mistaken for another series.
- **"Today" marker:** dashed vertical hairline (`series-today-marker`) with a small caption label, present on every chart that mixes historical and forecast data.
- **Positive/negative freight movement:** rendered with a neutral direction glyph (▲/▼ in `text-secondary`) plus the Plex Mono figure — never Success/Danger color, per `ui-tokens.md`'s explicit rule that rate direction is not intrinsically good or bad.
- **Uncertainty (volatility, confidence):** represented via the interval band width and, where a single volatility figure is shown, a `type-data-md` mono value with a `type-caption` label — never compressed into a single color-coded dot.
- **Model comparison (Backtesting page):** categorical palette `chart-1`–`chart-6`; when more than 3 model series are shown together, each series must also use a distinct line-dash pattern (solid/dashed/dotted/dash-dot) in addition to color.
- **Risk levels in charts:** Low/Medium/High risk plotted spatially (e.g., a risk-by-category bar or radar) use the Risk-state colors **and** a distinct marker shape (circle/triangle/square) per tier.
- **Feasibility states in charts:** any chart plotting feasibility (e.g., a constraint-by-vessel-class grid) uses the Feasibility-state colors **and** the Feasibility badge icon set (check/x/question-mark) inline in each cell — never a colored cell with no icon or label.
- **Axis/gridlines:** gridlines in `slate-100`/`slate-800` (theme-dependent); tick labels `type-caption` in Plex Mono, `text-muted`.
- **Legends:** always text-labeled (never color-swatch-only); on narrow viewports (`< md`), legends move below the chart rather than being dropped.

No chart in this product may communicate meaning through color alone — every rule above pairs color with a line style, shape, icon, or text label.

---

## Decision & Status Indicators

These are the reusable, cross-page patterns for the product's core decision-support outputs. A page must reuse these patterns rather than inventing a page-specific variant.

- **Recommendation summary (Decision Dashboard):** a highlighted card using `border-strong` (or the accent left-border pattern) to distinguish it from surrounding cards, containing: charter timing badge, recommended vessel, contract strategy, risk badge, and a `type-body-lg` explanation paragraph listing the reasons (per `project-overview.md` explainability requirements). This card never uses `elevation-1`+ for emphasis — emphasis comes from border/background treatment, consistent with Cards rules above.
- **Risk level:** always the Risk badge variant (Low/Medium/High) plus, wherever there is room, the contributing category breakdown (market/port/vessel/external) as smaller badges or a compact list — a bare risk badge with no visible breakdown-on-demand is discouraged on the Decision Dashboard and Risk page.
- **Feasibility pass/fail:** always shown per-constraint (draft/LOA/beam/DWT/etc.) using the Feasibility badges, with an overall Pass/Fail summary badge that is visually derived from (placed near, and consistent with) the per-constraint results — never a standalone overall badge with no accessible detail.
- **Charter timing:** rendered as a short, explicit label ("Charter Now" / "Wait / Monitor") in `type-h3` weight or via a prominent badge — never abbreviated to a color or icon alone.
- **Contract strategy comparison:** presented as a small comparison table or set of parallel stat cards (spot / short-term / medium-term), each showing expected expenditure, risk, and flexibility using the same Table or Card rules defined above — never a free-form paragraph in place of structured comparison.
- **Confidence / model metadata:** shown as `type-caption` `text-muted` text near the relevant figure (e.g., "XGBoost v3 · backtested sMAPE 6.2%"), never hidden behind a tooltip-only interaction — a user must be able to see model provenance without hovering.
- **Estimated savings:** always paired with the explicit qualifier "backtested/simulated estimate" in `type-caption`, directly adjacent to the figure (not in a separate footnote), using `outcome-favorable`/`outcome-unfavorable` tokens per `ui-tokens.md`. The qualifier text must never be omitted when the figure is shown, per `model.md`'s prohibition on implying guaranteed savings.

---

## Empty States

- Structure: icon (Plex Sans-adjacent line icon, `text-muted`) → `type-h3` message → optional `type-body-sm` supporting text → optional single action button (Ghost or Secondary variant).
- Message hierarchy: the `type-h3` line states what is missing in plain terms ("No procurement requirement yet"), the supporting text states what to do next ("Enter a cargo requirement to generate a forecast and recommendation.").
- Used whenever a page or panel has no data to show because the user hasn't yet taken an action (e.g., Decision Dashboard before any requirement is entered) — distinct from Loading and Error states below, which represent data that should exist but isn't currently available.
- Empty states never use Danger/Warning color — they are neutral (`text-muted`/`text-secondary`), since an empty state is an expected, non-error condition.

---

## Loading & Error States

- **Initial page loading:** skeleton blocks matching the shape of the eventual cards/stat blocks (using `surface-secondary` as the skeleton fill), not a full-page spinner — preserves layout stability.
- **Chart loading:** skeleton area matching the chart's final dimensions with a centered `type-body-sm` "Loading forecast…" label; never render an empty axis with no loading indicator.
- **Table loading:** skeleton rows at the table's default row height (`space-10`), same column structure as the loaded table.
- **API errors:** an inline Alert (per `ui-tokens.md` Components) using Danger tokens, x-circle icon, `type-body` message stating what failed in plain terms, and — where retry is meaningful — a Secondary button labeled "Retry".
- **Forecast unavailable** (e.g., no model covers the requested route/vessel-class/horizon): an Info-variant alert, not an Error — this is an expected data-availability boundary described in `project-overview.md`, not a system failure. Message must state specifically what is unavailable (e.g., "No forecast available for this origin–destination pair yet") rather than a generic failure message.
- **Insufficient data** (e.g., feasibility or risk cannot be evaluated for a constraint): rendered as the Feasibility "Unknown" badge or an inline Warning note, never silently omitted from the view.
- **Failed analysis/backtest run:** Danger alert with the specific failure reason if known, plus a Secondary "Retry" or "View logs" action where applicable — never a bare "Something went wrong" with no next step.

---

## Responsive Behavior

Exactly the breakpoints and behaviors defined in `ui-tokens.md` → Responsive Behavior; this section states how each component type maps onto them.

- **Grid:** dashboard stat grid moves 4 → 3 (`lg`–`xl`) → 2 (`md`–`lg`) → 1 column (`< md`), per `ui-tokens.md`.
- **Nav:** expanded rail (`≥ lg`) → icon-only rail (`md`–`lg`) → bottom bar/drawer (`< md`).
- **Cards:** padding never drops below `space-4` at any breakpoint; card content reflows to single-column internal layout below `md`.
- **Tables:** horizontally scrollable with sticky first column below `md`, per `ui-tokens.md` — no alternative "card list" pattern is used for tabular data anywhere in the product.
- **Charts:** retain full container width at all breakpoints; legends move below the chart below `md`; axis label density may thin (fewer tick labels) below `sm` but must never disappear entirely.
- **Forms:** the procurement requirement form's fields stack to a single column below `md`; field order in the DOM must match the visual order at every breakpoint (no reflow that changes tab order).

---

## Accessibility

- **Contrast:** every text/background pairing must meet the minimums in `ui-tokens.md` → Accessibility (4.5:1 body, 3:1 large text/icons) in both themes; this must be verified for every new semantic token combination introduced, not assumed.
- **Focus states:** the 2px `marine-500` outline at 2px offset is applied to every interactive element (links, buttons, inputs, nav items, table row selection, chart interactive elements) — never removed via `outline: none` without a compliant replacement.
- **Keyboard navigation:** all primary workflows (entering a requirement, switching between the five pages, expanding a feasibility/risk detail, changing forecast horizon) must be fully operable by keyboard alone, in a logical tab order matching visual order.
- **Semantic HTML:** headings use real `h1`–`h3` elements matching the Typography Hierarchy table; tables use real `<table>`/`<th>`/`<td>` markup (not div grids) so screen readers announce row/column structure; buttons use `<button>`, not clickable `<div>`s.
- **Screen-reader labels:** icon-only controls always carry `aria-label`; badges expose their text label to assistive tech (not just a colored icon); charts provide an accessible summary or linked data table.
- **Status communication:** every rule in this file that pairs color with icon+text exists specifically to satisfy this requirement — screen-reader and colorblind users must be able to determine risk/feasibility/status from the icon and text alone, with color removed.
- **Chart accessibility:** every chart on the Freight Forecast, Risk, and Backtesting pages has either an adjacent data table or a text summary of the key figures (current value, forecast, interval, direction) available to non-visual users.
- **Non-color indicators:** restated as the governing rule across Badges, Data Visualization, Tables, and Decision & Status Indicators — this is the single most important accessibility requirement in this product given its risk/feasibility/status-heavy content.

---

## Do Nots

- Never introduce a color not defined in `ui-tokens.md`, including one-off tints, gradients, or "just this once" hex values.
- Never introduce a font family other than IBM Plex Sans and IBM Plex Mono.
- Never use an arbitrary spacing value (e.g., `13px`, `22px`) when a `space-*` token already covers the need.
- Never communicate status, risk, feasibility, or recommendation meaning through color alone.
- Never invent a page-specific visual pattern (a one-off card style, a one-off badge shape, a one-off table density) when a reusable pattern already exists in this file.
- Never hard-code a visual value (color, spacing, radius, shadow, font size) directly in component code instead of referencing the token.
- Never override a token locally (e.g., a component-scoped shadow or radius override) without that override being promoted into `ui-tokens.md` first — local, undocumented overrides are exactly what causes visual drift between team members' work.
- Never apply a drop shadow to a default card or page surface for emphasis; use border/background treatment instead.
- Never color-code freight rate direction (increase/decrease) as favorable/unfavorable — that judgment does not exist at the rate-direction level, only at the recommendation-outcome level.
- Never present an estimated savings or economic figure without its "backtested/simulated estimate" qualifier immediately adjacent to it.
- Never replace the sticky-column horizontal-scroll table pattern with a stacked-card alternative on small screens.
- Never suppress a visible focus outline without providing an equally visible compliant replacement.

---

## Invariants

1. `ui-tokens.md` is the single source of truth for all visual values (color, type, spacing, radius, elevation); this file governs only how those values are applied.
2. Every component built for this product must follow the rules in this file; a component that deviates without updating this file first is a defect, not a valid variant.
3. New visual patterns must be assembled from existing tokens wherever possible; a genuinely new value is added to `ui-tokens.md` before it is used anywhere, never introduced ad hoc in a component.
4. Historical, forecast, and prediction-interval states must remain visually distinguishable through line style and fill technique, not color alone, on every chart in the product.
5. Risk level and vessel/port feasibility must never be communicated by color alone — icon and text label are always present alongside color.
6. The UI must remain readable at realistic dashboard information density (dense tables, multi-series charts, five concurrent pages of decision-support data) without introducing a lower-density "simplified" alternative UI.
7. Component behavior (navigation states, card recipe, badge composition, table density rules, focus treatment) must remain identical in implementation across all five pages — the Decision Dashboard, Freight Forecast, Feasibility, Risk, and Backtesting pages share one component system, not five separate ones.
8. Any genuinely new design pattern required by a future feature must be added to `ui-tokens.md`/`ui-rules.md` through an explicit update, never silently invented inside a single component or page.
