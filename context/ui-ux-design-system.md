# SamudraSetu — UI/UX Design System & Product Context Guide

> **Audience**: UI/UX Designers, Product Designers, Design Technologists  
> **Repository Branch**: `feature/samudrasetu-dashboard-redesign`  
> **Platform Category**: Institutional Maritime Intelligence & Bulk Chartering Decision Support  
> **Last Updated**: September 2026

---

## 1. Product Executive Summary

### 1.1 What is SamudraSetu?
**SamudraSetu** ("Ocean Bridge") is an institutional-grade freight forecasting, port operational risk, and vessel chartering decision-support system tailored for dry-bulk commodities (specifically thermal and coking coal procurement into India).

Commercial charterers and procurement heads make multi-million dollar shipping decisions. A standard Capesize shipment of 150,000 MT coal carries freight exposure of \$2M–\$5M+ and demurrage exposure exceeding \$25,000/day.

SamudraSetu replaces guesswork and delayed broker reports with an **end-to-end, deterministic, multi-stage analytical engine**:
1. **Scenario Definition**: Origin port, Indian destination port, cargo volume, vessel class, and forecast horizon.
2. **Forward Freight Forecasting**: Machine-learning probabilistic rate trajectory ($/MT with P10, P50, and P90 confidence intervals).
3. **Port Congestion & Demurrage Risk**: Waiting time estimates and turnaround risk models (XGBoost for major hubs like Paradip).
4. **Physical Berth Feasibility**: Deterministic compliance check (Draft, LOA, Beam, DWT limits) determining full discharge vs. required lighterage / transshipment.
5. **Charter Recommendation Engine**: Actionable procurement verdict comparing **Spot Voyage**, **Short-term Time Charter (TC)**, and **Contract of Affreightment (COA)** with detailed financial rationale and risk sensitivity.

---

## 2. Target Personas & UX Goals

| Persona | Role | Key Pain Point | Primary UX Requirement |
| :--- | :--- | :--- | :--- |
| **Chief Procurement Officer (CPO)** | Executive | High-level financial volatility, supplier compliance | Immediate bottom-line verdict: *“Should we fix spot or lock a contract?”* |
| **Chartering Manager / Freight Trader** | Operator | Market timing, vessel routing, demurrage penalties | Clear forward rate spreads (P10/P50/P90), vessel compliance flags, and congestion outlook |
| **Port & Logistics Coordinator** | Operations | Draft restrictions, tidal windows, lighterage costs | Berth physical parameter checks, draft limits, and congestion metrics |

### Core UX Principles
1. **Analytical & Institutional ("Bloomberg meets modern SaaS")**: The interface must feel serious, dependable, authoritative, and data-dense. Avoid playful consumer UI or flashy neon gamer styling.
2. **Zero Ambiguity on Model Provenance**: The system always tells the user whether a forecast is powered by a high-fidelity trained PyTorch LSTM model, an XGBoost model, or a documented mathematical baseline fallback (Holt-Winters).
3. **Progressive Disclosure**: High-level verdict first (Executive Strip), followed by granular drill-downs (Forecast chart, Port risks, Feasibility metrics, Methodology).
4. **Spatial & Visual Context**: Global shipping routes are physical. An interactive maritime corridor map anchors the geographic reality of the voyage.

---

## 3. Design System & Visual Language

### 3.1 Aesthetic & Theming
- **Theme Foundation**: Light Institutional Workspace (Off-White, Deep Slate, Maritime Navy, and Precise Functional Status Colors).
- **Surface Elevation**: Clean, crisp hairline borders (`1px solid #e2e8f0`) with subtle backdrop blurs on sticky elements. Heavy drop shadows are avoided in favor of flat data density.

### 3.2 Design Tokens (Color Palette)

```css
/* Surface & Backgrounds */
--bg-canvas:        #f8fafc;  /* Main workspace background (Off-white / Slate 50) */
--bg-surface:       #ffffff;  /* Primary card / panel background */
--bg-subtle:        #f1f5f9;  /* Secondary background / Table headers (Slate 100) */
--bg-muted:         #e2e8f0;  /* Dividers, inactive fills (Slate 200) */

/* Typography & Contrast */
--text-primary:     #0f172a;  /* Main headers & values (Slate 900) */
--text-secondary:   #334155;  /* Body copy, labels (Slate 700) */
--text-muted:       #64748b;  /* Meta descriptions, captions (Slate 500) */
--text-faint:       #94a3b8;  /* Watermarks, disabled indicators (Slate 400) */

/* Borders & Separators */
--border-subtle:    #e2e8f0;  /* Standard card/table border */
--border-medium:    #cbd5e1;  /* Input borders, active card borders */
--border-strong:    #94a3b8;  /* Focused or highlighted edges */

/* Brand & Maritime Accents */
--navy-deep:        #0f172a;  /* Header navigation background, institutional anchors */
--navy-slate:       #1e293b;  /* Elevated brand panels */
--teal-primary:     #0284c7;  /* Primary action CTA, interactive links (Sky 600) */
--teal-dark:        #0369a1;  /* Hover state for primary CTAs (Sky 700) */
--teal-light:       #e0f2fe;  /* Pill badge backgrounds, subtle highlights (Sky 100) */

/* Functional Decision & Status Colors */
--state-pass:       #16a34a;  /* Compliant / Safe / Feasible / Bullish (Green 600) */
--state-pass-bg:    #dcfce7;  /* Compliant badge background (Green 100) */
--state-warn:       #d97706;  /* Lighterage Required / Elevated Demurrage (Amber 600) */
--state-warn-bg:    #fef3c7;  /* Warning badge background (Amber 100) */
--state-fail:       #dc2626;  /* Berth Violation / High Risk (Red 600) */
--state-fail-bg:    #fee2e2;  /* Failure badge background (Red 100) */
```

### 3.3 Typography Hierarchy

| Role | Font Family | Weight | Size | Usage Example |
| :--- | :--- | :--- | :--- | :--- |
| **Brand / Display** | `Inter` | 800 | 32px–40px | Platform Hero Title |
| **Section Headings** | `Inter` | 700 | 20px–24px | Section titles (`#forecast`, `#feasibility`) |
| **Card Headings** | `Inter` | 600 | 16px–18px | Metric card labels, panel titles |
| **Body Copy** | `Inter` | 400 / 500 | 14px–15px | Recommendations, descriptions, tooltips |
| **Eyebrow / Subhead** | `Inter` | 600 (Uppercase) | 11px–12px | `TRACKED PORT METRICS`, `DECISION VERDICT` |
| **Data / Numbers** | `JetBrains Mono` | 600 | 18px–32px | `$14.85 / MT`, `150,000 MT`, `7.2 Days` |
| **Codes / Metadata** | `JetBrains Mono` | 500 | 12px–13px | Coordinates `[-32.92, 151.78]`, Model IDs |

> **Strict Typography Rule**: Never use proportional fonts (`Inter`) for financial numbers, coordinates, dates, or rates. Always use `JetBrains Mono` so column values remain tabular and visually scannable.

### 3.4 Spatial System & Grid
- **Max Content Width**: `1440px` centered.
- **Section Spacing**: `32px` to `48px` vertical gap between major sections.
- **Card Padding**: `20px` to `24px` standard; `14px` on compact mobile cards.
- **Corner Radii**:
  - `6px` (`--radius-sm`) for badges, inputs, buttons.
  - `10px` (`--radius-md`) for cards, modal dialogs, data widgets.
  - `14px` (`--radius-lg`) for major container shells.

---

## 4. Architecture of the Screen & Layout Sections

The dashboard is structured as a continuous, high-performance analytical workflow divided into **7 functional sections**:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ 0. Sticky Global Header (Logo, Active Status, Section Jumps, Run CTA)  │
├────────────────────────────────────────────────────────────────────────┤
│ 1. Platform Hero (Context, Scope Pills, Architecture Overview)         │
├────────────────────────────────────────────────────────────────────────┤
│ 2. Scenario Setup & Interactive Maritime Map (#scenario)               │
│    [ Left: Inputs & Sliders ]  [ Right: Leaflet Water-Way Corridor ]   │
├────────────────────────────────────────────────────────────────────────┤
│ 3. Executive Overview Strip (#overview)                                │
│    [ Verdict Card ] [ Projected Rate ] [ Feasibility ] [ Port Risk ]   │
├────────────────────────────────────────────────────────────────────────┤
│ 4. Forward Freight Trajectory (#forecast)                              │
│    [ Recharts P10/P50/P90 Confidence Fan Chart + Data Summary Table ]  │
├────────────────────────────────────────────────────────────────────────┤
│ 5. Port Operational Risk & Demurrage (#risk)                           │
│    [ Waiting Time Gauge ] [ Congestion Tier ] [ Risk Mitigation Note ] │
├────────────────────────────────────────────────────────────────────────┤
│ 6. Navigational Feasibility & Economics (#feasibility)                 │
│    [ Draft / LOA / Beam / DWT Matrix ] [ Lighterage vs Full Discharge] │
├────────────────────────────────────────────────────────────────────────┤
│ 7. Chartering Recommendation Verdict (#recommendation)                 │
│    [ Primary Strategy Badge: SPOT vs TC vs COA ] [ Financial Model ]   │
├────────────────────────────────────────────────────────────────────────┤
│ 8. Technical Provenance & Model Limitations (#methodology)             │
├────────────────────────────────────────────────────────────────────────┤
│ 9. Platform Institutional Footer                                       │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Detailed Component Specifications

### 5.1 Scenario Panel & Maritime Route Map (`ScenarioPanel.jsx`, `RouteMap.jsx`)
- **Inputs**:
  - **Origin**: Australia (Newcastle), United States (Hampton Roads), Mozambique (Maputo), Indonesia (Balikpapan), Russia (Vladivostok).
  - **Destination Port**: Paradip, Visakhapatnam, Gangavaram, Gopalpur, Dhamra, Sagar/Sandheads, Haldia.
  - **Vessel Class**: Capesize (~150,000 DWT), Panamax (~75,000 DWT), Supramax (~55,000 DWT), Handysize (~35,000 DWT).
  - **Cargo Quantity**: Numeric input (Metric Tons).
  - **Horizon**: 1, 7, 14, 30, or 60 days.
  - **Port Congestion & Vessel Availability**: Low / Medium / High.
- **Route Map Visualization**:
  - Built with `react-leaflet` + OpenStreetMap CartoDB Positron / Esri Ocean tiles.
  - Renders true water-only navigational corridors (e.g., routing south of Australia through the Great Australian Bight or around Singapore / Malacca Strait into the Bay of Bengal).
  - Custom pulsing ping markers for origin port (teal) and destination port (amber/red).

### 5.2 Executive Overview Strip (`ExecutiveStrip.jsx`)
- 4 high-impact KPI summary cards:
  1. **Recommendation**: Displays primary strategy (e.g. `TIME_CHARTER_FAVORABLE` or `SPOT_RECOMMENDED`) with confidence score.
  2. **Projected Freight Rate**: Expected baseline forward rate ($/MT) with percentage delta vs. 30-day average.
  3. **Berth Feasibility**: `FEASIBLE_DIRECT`, `FEASIBLE_LIGHTERAGE_REQUIRED`, or `NON_FEASIBLE_PHYSICAL_LIMIT`.
  4. **Port Risk Exposure**: Demurrage exposure index and expected berth wait days.

### 5.3 Forecast Section (`ForecastSection.jsx`)
- Visualizes forward freight expectations.
- **Interactive Fan Chart (`recharts`)**:
  - `P50` (solid primary line): Expected forward rate.
  - `P10` – `P90` (semi-transparent filled area / confidence fan): Represents market volatility.
  - Historical reference baseline points.
- **Model Badge**: Prominently displays model source:
  - `Trained PyTorch LSTM (4-layer)` for Australia → Paradip Capesize.
  - `Trained XGBoost Regressor` for Supramax 1-day horizon.
  - `Documented Holt-Winters Exponential Smoothing` for other routes.

### 5.4 Port Risk Section (`PortRiskSection.jsx`)
- Focuses on operational bottlenecks at Indian discharge ports.
- **Key Metrics**:
  - Expected Port Waiting Time (Days).
  - Estimated Demurrage Risk ($ Total Exposure).
  - Congestion Probability Index (0%–100%).
  - Pre-berthing delays and weather impact factor.

### 5.5 Feasibility Section (`FeasibilitySection.jsx`)
- Evaluates whether the chosen vessel class can physically dock at the chosen Indian port berth.
- **Physical Matrix Checklist**:
  - **Draft**: Vessel laden draft vs. Port maximum permissible draft.
  - **Length Overall (LOA)**: Vessel length vs. Maximum berth length.
  - **Beam (Width)**: Vessel width vs. Channel / unloader clearance.
  - **Deadweight Tonnage (DWT)**: Vessel cargo capacity vs. Port berth displacement rating.
- **Lighterage Economics Calculator**: If vessel draft exceeds port depth, calculates lighterage cost at Sandheads or deep anchorage (e.g., \$4.50/MT barge transshipment fee).

### 5.6 Chartering Decision Section (`DecisionSection.jsx`)
- The definitive commercial payoff matrix:
  - **Recommended Strategy**: Spot vs. Time Charter vs. COA.
  - **Cost Comparison Breakdown**: Total freight landed cost in Million USD.
  - **Sensitivity Analysis**: Break-even fuel/bunker price, demurrage break-even days.
  - **Action Checklist**: Operational next steps for the chartering desk.

### 5.7 Methodology & Data Transparency (`MethodologySection.jsx`)
- Discloses data sources (FRED Macro, US EIA coal prices, RBI exchange rates, Baltic Exchange proxies).
- Point-in-time safety disclosures and known model caveats.

---

## 6. Interaction & Motion Guidelines

- **Libraries Used**: `gsap` (GreenSock 3) + `ScrollTrigger` + `@gsap/react`.
- **Motion Personality**: Crisp, subtle, purposeful. Elements do not fly wildly across the screen.
- **Trigger Classes**:
  - `[data-hero-reveal]`: Initial hero stagger upon load (opacity 0 → 1, y: 16px → 0px, duration 0.6s).
  - `[data-section-reveal]`: Triggered when each analytical section scrolls to top 92% of viewport.
  - `[data-card-reveal]`: Staggered card reveals within grid containers.
- **Accessibility**: All GSAP animations check `window.matchMedia('(prefers-reduced-motion: no-preference)')`. If reduced motion is requested, transitions are instant.
- **Loading State**: `AnalyticalResultsSkeleton` displays shimmer wave cards while API calculates pipeline runs.

---

## 7. High-Value Opportunities for UI/UX Designers to Add

When designing new features or iterating on the platform, consider these planned enhancements:

1. **Scenario Comparison / Split-Screen Mode**:
   - Compare two scenarios side-by-side (e.g., *Capesize direct to Paradip* vs. *Panamax to Haldia*).
   - Show cost delta, voyage duration, and risk variance.
2. **Interactive Vessel Fleet & AIS Tracker**:
   - Overlay active bulk carriers along the route on the Leaflet map.
   - Show real-time vessel speeds, ballast status, and ETA countdowns.
3. **Executive PDF Export / Board Brief Generator**:
   - A single-click "Export Chartering Brief" generating a pixel-perfect 2-page executive summary PDF.
4. **Carbon Emissions & IMO CII Rating Widget**:
   - Calculate fuel consumption, total CO2 emissions (MT), and Carbon Intensity Indicator (CII A-to-E grade) for the voyage.
5. **Real-Time Market Alerts & Threshold Triggers**:
   - Set price triggers: *"Notify me if Paradip Capesize forward rate drops below \$14.00/MT"*.
6. **Dark Mode Toggle**:
   - Institutional dark theme (Navy/Charcoal background, high-contrast cyan/emerald charting) for evening trading desk shifts.
7. **Demurrage Calculator Sandbox**:
   - Interactive slider allowing users to test *"What if port wait is 3 days longer?"* to see demurrage sensitivity in real time.

---

## 8. Directory & File Reference

For UI/UX design inspection and code reference:
- **Design System CSS Tokens & Styles**: [`frontend/src/index.css`](file:///c:/Users/Samarth%20Naik/OneDrive/Desktop/SIHPro/SamudraSetu/frontend/src/index.css)
- **Main View & Page Structure**: [`frontend/src/App.jsx`](file:///c:/Users/Samarth%20Naik/OneDrive/Desktop/SIHPro/SamudraSetu/frontend/src/App.jsx)
- **Top Header & Sticky Nav**: [`frontend/src/components/Navigation.jsx`](file:///c:/Users/Samarth%20Naik/OneDrive/Desktop/SIHPro/SamudraSetu/frontend/src/components/Navigation.jsx)
- **Scenario Form & Map Container**: [`frontend/src/components/ScenarioPanel.jsx`](file:///c:/Users/Samarth%20Naik/OneDrive/Desktop/SIHPro/SamudraSetu/frontend/src/components/ScenarioPanel.jsx)
- **Maritime Map & Coordinates**: [`frontend/src/components/RouteMap.jsx`](file:///c:/Users/Samarth%20Naik/OneDrive/Desktop/SIHPro/SamudraSetu/frontend/src/components/RouteMap.jsx)
- **Executive KPI Strip**: [`frontend/src/components/ExecutiveStrip.jsx`](file:///c:/Users/Samarth%20Naik/OneDrive/Desktop/SIHPro/SamudraSetu/frontend/src/components/ExecutiveStrip.jsx)
- **Forecast Fan Chart**: [`frontend/src/components/ForecastSection.jsx`](file:///c:/Users/Samarth%20Naik/OneDrive/Desktop/SIHPro/SamudraSetu/frontend/src/components/ForecastSection.jsx)
- **Port Risk Gauges**: [`frontend/src/components/PortRiskSection.jsx`](file:///c:/Users/Samarth%20Naik/OneDrive/Desktop/SIHPro/SamudraSetu/frontend/src/components/PortRiskSection.jsx)
- **Feasibility & Lighterage**: [`frontend/src/components/FeasibilitySection.jsx`](file:///c:/Users/Samarth%20Naik/OneDrive/Desktop/SIHPro/SamudraSetu/frontend/src/components/FeasibilitySection.jsx)
- **Decision Engine Output**: [`frontend/src/components/DecisionSection.jsx`](file:///c:/Users/Samarth%20Naik/OneDrive/Desktop/SIHPro/SamudraSetu/frontend/src/components/DecisionSection.jsx)
- **Methodology & Provenance**: [`frontend/src/components/MethodologySection.jsx`](file:///c:/Users/Samarth%20Naik/OneDrive/Desktop/SIHPro/SamudraSetu/frontend/src/components/MethodologySection.jsx)
- **Status Formatters & Badges**: [`frontend/src/utils/statusHelpers.js`](file:///c:/Users/Samarth%20Naik/OneDrive/Desktop/SIHPro/SamudraSetu/frontend/src/utils/statusHelpers.js)
