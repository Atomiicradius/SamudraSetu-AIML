"""
Freight forecasting & vessel chartering decision support -- overnight MVP.

SIH 2026, Problem Statement 26006. Single-page Streamlit prototype: every
number on screen is computed live from a procurement requirement the user
fills in (origin, destination, vessel class, cargo quantity) -- see
README.md for exactly what's real computation vs simplified for time.
"""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from backend.backtest import run_backtest
from backend.feasibility import PORT_LIMITS, VESSEL_SPECS, check_all_vessel_classes
from backend.forecasting import build_forecast_from_series, holdout_errors
from backend.model_service import ModelRegistry
from backend.recommendation import UTILIZATION, build_recommendation, compare_vessel_costs
from backend.risk import AVAILABILITY_LEVELS, CONGESTION_LEVELS, compute_risk
from backend.synthetic_data import generate_synthetic_series

DATA_PATH = Path(__file__).parent / "data" / "freight_rates.csv"

ORIGINS = ["Australia", "United States", "Mozambique", "Russia", "Indonesia"]
DESTINATIONS = list(PORT_LIMITS.keys())  # Paradip, Visakhapatnam, Gangavaram, Gopalpur, Dhamra, Sagar/Sandheads, Haldia
VESSEL_CLASSES = list(VESSEL_SPECS.keys())  # Handysize, Supramax, Panamax, Capesize
CARGO_TYPE = "Coal"  # fixed for this prototype -- out of scope to change tonight
MODEL_REGISTRY = ModelRegistry()

STATUS_BADGE = {"pass": "🟢 Pass", "fail": "🔴 Fail", "unknown": "⚪ Unknown"}
RISK_COLOR = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}


@st.cache_data
def load_real_data() -> pd.DataFrame | None:
    """Optional real-data override: if data/freight_rates.csv exists and
    has rows matching the selected (route, vessel_class, cargo_type), those
    rows are preferred over synthetic generation. Not required -- the app
    works fully without this file."""
    if DATA_PATH.exists():
        return pd.read_csv(DATA_PATH, parse_dates=["date"])
    return None


@st.cache_data
def resolve_series(origin: str, destination: str, vessel_class: str, cargo_type: str):
    """Resolve the daily rate series for a requirement. Prefers real data
    (data/freight_rates.csv) when a matching route/vessel/cargo history
    exists there; otherwise generates a synthetic series deterministically
    seeded from the route+vessel identifiers (see data/generate_data.py) --
    so re-selecting the same combination always reproduces the exact same
    series and every downstream number, even across app restarts. Cached
    so switching between combinations stays fast."""
    route = f"{origin}-{destination}"
    real_df = load_real_data()
    if real_df is not None:
        mask = (
            (real_df["route"] == route)
            & (real_df["vessel_class"] == vessel_class)
            & (real_df["cargo_type"] == cargo_type)
        )
        sub = real_df.loc[mask]
        if len(sub) >= 90:
            series = sub.sort_values("date").set_index("date")["rate_usd_per_mt"]
            return series, "real data (data/freight_rates.csv)"

    synth = generate_synthetic_series(origin, destination, vessel_class, cargo_type)
    series = synth.set_index("date")["rate_usd_per_mt"]
    return series, "synthetic (deterministically seeded from origin + destination + vessel)"


@st.cache_data
def cached_forecast(origin, destination, vessel_class, cargo_type, horizon):
    series, source = resolve_series(origin, destination, vessel_class, cargo_type)
    trained = MODEL_REGISTRY.predict_freight(
        origin, destination, vessel_class, horizon
    )
    if trained is not None:
        if vessel_class == "Capesize":
            series = MODEL_REGISTRY.lstm_target_series()
        points = trained["series"]
        return {
            "series": series,
            "forecast_dates": pd.to_datetime([point["date"] for point in points]),
            "naive": [trained["current_rate_usd_per_mt"]] * horizon,
            "point": [point["p50"] for point in points],
            "p10": [point["p10"] for point in points],
            "p50": [point["p50"] for point in points],
            "p90": [point["p90"] for point in points],
            "prob_increase": trained["probability_increase"],
            "residual_sigma": trained["metrics"]["rmse"],
            "holdout_days_used": 0,
            "current_rate": trained["current_rate_usd_per_mt"],
            "data_source": f"trained artifact: {trained['model']['artifact']}",
        }
    fc = build_forecast_from_series(series, horizon)
    fc["data_source"] = source
    return fc


@st.cache_data
def cached_holdout_metrics(origin, destination, vessel_class, cargo_type, horizon):
    trained = MODEL_REGISTRY.predict_freight(
        origin, destination, vessel_class, horizon
    )
    if trained is not None:
        metrics = trained["metrics"]
        return {
            "holdout_days_used": 0,
            "model_name": trained["model"]["name"],
            "stat_mae": metrics["mae"],
            "stat_rmse": metrics["rmse"],
            "naive_mae": float("nan"),
            "naive_rmse": float("nan"),
        }
    series, _ = resolve_series(origin, destination, vessel_class, cargo_type)
    return holdout_errors(series)


st.set_page_config(page_title="SAIL Freight Forecasting & Chartering", layout="wide")

st.title("SamudraSetu")
st.caption("SIH 2026 - Problem Statement 26006 | Prototype MVP - all figures computed live from the requirement below")

with st.sidebar:
    st.header("Procurement requirement")
    origin = st.selectbox("Origin", ORIGINS)
    destination = st.selectbox("Destination", DESTINATIONS)
    vessel_class = st.selectbox("Vessel class", VESSEL_CLASSES)
    default_cargo_qty = VESSEL_SPECS[vessel_class]["dwt_max"] * UTILIZATION
    cargo_quantity_mt = st.number_input(
        "Cargo quantity (mt)", min_value=1000.0, max_value=250000.0,
        value=float(default_cargo_qty), step=1000.0,
    )
    st.selectbox("Cargo type", ["Coal"], disabled=True, help="Fixed for this prototype -- out of scope to change tonight.")

    horizon = st.radio("Forecast horizon", [7, 30], format_func=lambda h: f"{h} days", horizontal=True)

    st.header("Risk inputs (illustrative)")
    congestion_level = st.select_slider("Port congestion", CONGESTION_LEVELS, value="Medium")
    availability_level = st.select_slider("Vessel availability", AVAILABILITY_LEVELS, value="Medium")

    st.caption("Congestion and availability are manually set here for the demo -- not fetched from a live feed. See README.")

route = f"{origin}-{destination}"
port = destination
cargo_type = CARGO_TYPE

forecast = cached_forecast(origin, destination, vessel_class, cargo_type, horizon)

# ---------------------------------------------------------------- Forecast
st.subheader(f"Current rate & {horizon}-day forecast -- {route} ({vessel_class}, {cargo_type})")

col1, col2, col3 = st.columns(3)
col1.metric("Current rate (last observed)", f"${forecast['current_rate']:.2f}/mt")
col2.metric(f"Statistical forecast, day {horizon}", f"${forecast['point'][-1]:.2f}/mt",
            delta=f"{forecast['point'][-1] - forecast['current_rate']:+.2f}")
col3.metric(f"Probability of increase over {horizon}d", f"{forecast['prob_increase']:.0%}",
            help="Share of historical horizon-day forward moves in this series that were positive.")

hist = forecast["series"].tail(120)
fig = go.Figure()

fig.add_trace(go.Scatter(x=hist.index, y=hist.values, name="Historical rate",
                          mode="lines", line=dict(color="#1f77b4", width=2)))

fig.add_trace(go.Scatter(
    x=list(forecast["forecast_dates"]) + list(forecast["forecast_dates"][::-1]),
    y=list(forecast["p90"]) + list(forecast["p10"][::-1]),
    fill="toself", fillcolor="rgba(255,127,14,0.18)", line=dict(color="rgba(255,255,255,0)"),
    name="P10-P90 band", hoverinfo="skip",
))

fig.add_trace(go.Scatter(x=forecast["forecast_dates"], y=forecast["point"], name="Statistical forecast (P50)",
                          mode="lines", line=dict(color="#ff7f0e", width=2, dash="dash")))

fig.add_trace(go.Scatter(x=forecast["forecast_dates"], y=forecast["naive"], name="Naive baseline (last value)",
                          mode="lines", line=dict(color="#7f7f7f", width=1.5, dash="dot")))

fig.update_layout(height=420, margin=dict(l=10, r=10, t=10, b=10),
                   yaxis_title="USD / mt", legend=dict(orientation="h", yanchor="bottom", y=1.02))
st.plotly_chart(fig, use_container_width=True)
st.caption(f"P10-P90 band derived from {forecast['holdout_days_used']}-day holdout residual spread "
           f"(sigma = ${forecast['residual_sigma']:.2f}/mt), widened with sqrt(t). Naive baseline shown for comparison. "
           f"Data: {forecast['data_source']} -- re-selecting this exact combination always reproduces the same series.")

hm = cached_holdout_metrics(origin, destination, vessel_class, cargo_type, horizon)
mcol1, mcol2 = st.columns(2)
mcol1.metric(f"Statistical model MAE / RMSE ({hm['holdout_days_used']}d holdout)",
             f"\\${hm['stat_mae']:.2f} / \\${hm['stat_rmse']:.2f}")
mcol2.metric(f"Naive baseline MAE / RMSE ({hm['holdout_days_used']}d holdout)",
             f"\\${hm['naive_mae']:.2f} / \\${hm['naive_rmse']:.2f}")
st.caption(f"Model: {hm['model_name']} · Holdout MAE \\${hm['stat_mae']:.2f}/mt, "
           f"RMSE \\${hm['stat_rmse']:.2f}/mt (vs. Naive MAE \\${hm['naive_mae']:.2f}/mt)")

# ---------------------------------------------------------------- Feasibility
st.subheader(f"Vessel feasibility at {port}")
st.caption("Representative specs/limits are hardcoded for this demo; every badge below is a computed comparison, "
           "never a preset verdict. 'Unknown' means the port limit isn't defined here.")

feas = check_all_vessel_classes(port)
feas_cols = st.columns(len(feas))
for col, (vc, checks) in zip(feas_cols, feas.items()):
    with col:
        highlight = " (selected)" if vc == vessel_class else ""
        st.markdown(f"**{vc}{highlight}**")
        for c in checks:
            limit_str = f"{c['port_limit']}" if c["port_limit"] is not None else "no limit on record"
            st.markdown(f"{STATUS_BADGE[c['status']]}  {c['constraint']}: {c['vessel_value']} vs {limit_str}")

# ---------------------------------------------------------------- Cost efficiency across vessels
st.subheader("Cost efficiency across feasible vessels")
st.caption(f"Using the cargo quantity from the requirement above: {cargo_quantity_mt:,.0f} mt.")

vessel_cost_cmp = compare_vessel_costs(port, forecast["current_rate"], cargo_quantity_mt)
feasible_rows = [r for r in vessel_cost_cmp["rows"] if r["feasible"]]

if not feasible_rows:
    st.warning("No vessel class is fully feasible at this port for the checked constraints.")
else:
    bar_colors = [
        "#2ca02c" if r["vessel_class"] == vessel_cost_cmp["cost_efficient_choice"] else "#1f77b4"
        for r in feasible_rows
    ]
    bar_line_widths = [
        3 if r["vessel_class"] == vessel_cost_cmp["cost_efficient_choice"] else 0
        for r in feasible_rows
    ]
    vfig = go.Figure(go.Bar(
        x=[r["vessel_class"] for r in feasible_rows],
        y=[r["estimated_cost_usd"] for r in feasible_rows],
        marker=dict(color=bar_colors, line=dict(width=bar_line_widths, color="white")),
        customdata=[[r["utilization"]] for r in feasible_rows],
        hovertemplate="%{x}<br>Estimated cost: $%{y:,.0f}<br>Utilization: %{customdata[0]:.0%}<extra></extra>",
    ))
    vfig.update_layout(height=340, margin=dict(l=10, r=10, t=10, b=10), yaxis_title="Estimated cost (USD)")
    st.plotly_chart(vfig, use_container_width=True)

    st.markdown(f"**Cost-efficient choice:** {vessel_cost_cmp['cost_efficient_choice']} "
                f"(lowest estimated cost among feasible vessels; ties broken by best utilization) -- "
                f"highlighted in green above.")

with st.expander("Show exact vessel comparison figures"):
    cost_rows = [{
        "Vessel": r["vessel_class"],
        "Feasible?": "✅ Yes" if r["feasible"] else "❌ No",
        "Utilization": f"{r['utilization']:.0%}",
        "Estimated cost": f"${r['estimated_cost_usd']:,.0f}",
    } for r in vessel_cost_cmp["rows"]]
    st.dataframe(pd.DataFrame(cost_rows), use_container_width=True, hide_index=True)

st.caption("Estimated cost = (current rate + contract premium) x cargo quantity, using the same current rate and "
           "premium as the Recommendation section below. Larger vessels get an illustrative economies-of-scale "
           "discount (spreading fixed voyage/port costs over more cargo) since this dataset carries one "
           "route-level rate rather than a rate per vessel class. Discount magnitudes are a documented "
           "placeholder, not live market data -- see README.")

# ---------------------------------------------------------------- Risk
st.subheader("Risk assessment")
risk = compute_risk(forecast["series"], congestion_level, availability_level)
st.markdown(f"### {RISK_COLOR[risk['level']]} {risk['level']} risk  ({risk['total_score']} / {risk['max_score']})")

rfig = go.Figure(go.Bar(
    y=[f["name"] for f in risk["factors"]],
    x=[f["score"] for f in risk["factors"]],
    orientation="h",
    marker=dict(color="#d62728"),
    customdata=[[f["value"], f["max"]] for f in risk["factors"]],
    hovertemplate="%{y}<br>Value: %{customdata[0]}<br>Contributes %{x} / %{customdata[1]} pts<extra></extra>",
))
rfig.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10),
                    xaxis=dict(title="Points contributed to risk score (of 2 max each)", range=[0, 2.5]))
st.plotly_chart(rfig, use_container_width=True)

with st.expander("Show exact risk figures"):
    for f in risk["factors"]:
        st.markdown(f"- **{f['name']}**: {f['value']} -- contributes {f['score']} / {f['max']} to the risk score.")

# ---------------------------------------------------------------- Recommendation
st.subheader("Recommendation")
dwt_max = VESSEL_SPECS[vessel_class]["dwt_max"]
rec = build_recommendation(forecast, risk, vessel_class, dwt_max, cargo_quantity_mt)

rcol1, rcol2 = st.columns([1, 2])
with rcol1:
    verdict_color = "green" if rec["decision"] == "Charter Now" else "orange"
    st.markdown(f"#### :{verdict_color}[{rec['decision']}]")
    st.markdown(f"**Vessel:** {rec['vessel_class']}")
    st.markdown(f"**Cheapest strategy:** {rec['contract_strategy']}")
    st.markdown(f"**Risk:** {RISK_COLOR[rec['risk_level']]} {rec['risk_level']}")

with rcol2:
    st.markdown("**Why:**")
    for reason in rec["reasons"]:
        st.markdown(f"- {reason}")

costs = rec["costs"]
ccol1, ccol2, ccol3 = st.columns(3)
ccol1.metric("Spot-only", f"${costs['spot_cost_usd']:,.0f}",
             help="Average forecast rate over the horizon x cargo quantity.")
ccol2.metric(f"Short-term ({costs['multi_voyage_count']}-voyage)", f"${costs['multi_voyage_cost_usd']:,.0f}",
             help="Current rate + a slightly better multi-voyage premium, x cargo quantity.")
ccol3.metric("Medium-term (single contract)", f"${costs['contract_cost_usd']:,.0f}",
             help="Current rate + the single fixed-contract premium, x cargo quantity.")
st.caption(f"Assumes {costs['tonnage_mt']:,.0f} mt cargo ({costs['utilization']:.0%} of the {vessel_class} vessel's "
           f"{dwt_max:,} mt DWT capacity). Simplified for time -- see README.")

# ---------------------------------------------------------------- Backtest
st.subheader("Backtest: rule vs spot-only")
bt = run_backtest(forecast["series"], horizon, congestion_level, availability_level)

if bt["n_points"] == 0:
    st.info("Not enough history to backtest this horizon.")
else:
    savings = bt["avg_savings_per_mt"]
    st.markdown(
        f"### Estimated avg. savings vs spot-only: **${savings:,.2f}/mt** "
        f"&nbsp; <span style='font-size:0.8em;color:gray'>(backtested/simulated estimate, {bt['n_points']} historical decision points)</span>",
        unsafe_allow_html=True,
    )
    full_series = forecast["series"]
    bt_fig = go.Figure()
    bt_fig.add_trace(go.Scatter(
        x=full_series.index, y=full_series.values, name="Historical rate",
        mode="lines", line=dict(color="#1f77b4", width=1.5), hoverinfo="skip",
    ))

    def _decision_marker_trace(points, name, color, symbol):
        return go.Scatter(
            x=[p["decision_date"] for p in points],
            y=[p["rate_at_decision"] for p in points],
            name=name, mode="markers",
            marker=dict(color=color, size=12, symbol=symbol, line=dict(width=1, color="white")),
            customdata=[[p["decision_date"].strftime("%Y-%m-%d"), p["rate_at_decision"], p["savings_per_mt"]]
                        for p in points],
            hovertemplate="Decision date: %{customdata[0]}<br>Rate at decision: $%{customdata[1]:.2f}/mt<br>"
                           "Savings/mt vs spot-only: $%{customdata[2]:.2f}<extra></extra>",
        )

    charter_now_points = [p for p in bt["points"] if p["decision"] == "Charter Now"]
    wait_points = [p for p in bt["points"] if p["decision"] == "Wait / Monitor"]
    bt_fig.add_trace(_decision_marker_trace(charter_now_points, "Charter Now", "#2ca02c", "triangle-up"))
    bt_fig.add_trace(_decision_marker_trace(wait_points, "Wait / Monitor", "#d62728", "circle"))

    bt_fig.update_layout(height=380, margin=dict(l=10, r=10, t=10, b=10), yaxis_title="USD / mt",
                          legend=dict(orientation="h", yanchor="bottom", y=1.02))
    st.plotly_chart(bt_fig, use_container_width=True)

    with st.expander("Show exact backtest figures"):
        bt_rows = [{
            "Decision date": p["decision_date"].date(),
            "Decision": p["decision"],
            "Rate at decision": f"${p['rate_at_decision']:.2f}",
            f"Actual rate +{horizon}d": f"${p['realized_rate_after_horizon']:.2f}",
            "Strategy rate": f"${p['strategy_rate']:.2f}",
            "Savings/mt vs spot-only": f"${p['savings_per_mt']:.2f}",
        } for p in bt["points"]]
        st.dataframe(pd.DataFrame(bt_rows), use_container_width=True, hide_index=True)

    st.caption("Each marker re-runs the same forecast + risk + recommendation rule using only data available before "
               "that date (no look-ahead). The spot-only baseline waits and pays whatever spot costs when the cargo "
               "actually needs to move; a 'Charter Now' call locks a contract early instead, at a small premium. "
               "Congestion/availability inputs use today's slider values throughout history -- a simplification, see README.")
