"""
Recommendation module.

An explicit, transparent point-scoring rule over forecast direction,
probability of increase, and risk level decides Charter Now vs
Wait/Monitor -- never a hardcoded verdict. A spot-only vs short-term
multi-voyage vs medium-term single-contract cost comparison is computed
from the forecast, and every decision ships with the list of reasons that
drove it.
"""

import numpy as np

from backend.feasibility import VESSEL_SPECS, check_feasibility

CONTRACT_PREMIUM = 0.015  # illustrative premium for a single fixed-rate contract (one lock, no multi-voyage commitment)
MULTI_VOYAGE_PREMIUM = 0.010  # illustrative, slightly better premium for committing to a short-term multi-voyage deal
MULTI_VOYAGE_COUNT = 3  # illustrative number of voyages in the short-term multi-voyage tier
UTILIZATION = 0.90  # sensible default cargo tonnage as a share of vessel DWT capacity (used only to seed the UI's default cargo quantity)

# Illustrative economies-of-scale adjustment: larger vessels spread fixed
# voyage/port costs over more cargo, so $/mt cost decreases with vessel size.
# This is a documented placeholder assumption, NOT a live per-class market
# rate -- our dataset only carries one route-level spot rate. Magnitudes are
# indicative, not sourced from a specific index. Used ONLY by
# compare_vessel_costs() below, for the vessel-comparison chart -- it does
# not touch cost_comparison() (the main Recommendation section), the
# backtest, or port feasibility.
VESSEL_CLASS_COST_DISCOUNT = {
    "Handysize": 0.00,
    "Supramax": 0.03,
    "Panamax": 0.06,
    "Capesize": 0.10,
}


def score_decision(forecast: dict, risk: dict) -> tuple[str, list[str]]:
    reasons = []
    score = 0

    current_rate = forecast["current_rate"]
    end_point = forecast["point"][-1]
    prob_increase = forecast["prob_increase"]
    risk_level = risk["level"]

    if not np.isnan(prob_increase) and prob_increase > 0.55:
        score += 1
        reasons.append(f"Historical {len(forecast['point'])}-day forward moves were positive {prob_increase:.0%} of the time.")
    elif not np.isnan(prob_increase) and prob_increase < 0.45:
        score -= 1
        reasons.append(f"Historical {len(forecast['point'])}-day forward moves were positive only {prob_increase:.0%} of the time.")

    if end_point > current_rate:
        score += 1
        reasons.append(f"Statistical forecast trends up: \\${current_rate:.2f} -> \\${end_point:.2f}/mt over the horizon.")
    else:
        score -= 1
        reasons.append(f"Statistical forecast trends down or flat: \\${current_rate:.2f} -> \\${end_point:.2f}/mt over the horizon.")

    if risk_level == "High":
        score += 1
        reasons.append("Risk score is High -- locking in now avoids further uncertainty.")
    elif risk_level == "Low":
        score -= 1
        reasons.append("Risk score is Low -- there is room to wait for a potentially better rate.")
    else:
        reasons.append("Risk score is Medium -- a neutral factor in this decision.")

    decision = "Charter Now" if score >= 1 else "Wait / Monitor"
    return decision, reasons


def cost_comparison(forecast: dict, vessel_class: str, dwt_max: float, cargo_quantity_mt: float) -> dict:
    """Three-way cost comparison for the requirement's actual cargo
    quantity: spot-only (avg forecast rate), a medium-term single fixed
    contract (CONTRACT_PREMIUM), and a short-term multi-voyage deal
    (MULTI_VOYAGE_PREMIUM, MULTI_VOYAGE_COUNT voyages) -- same rate-times-
    tonnage formula for all three, just a different rate/premium per tier."""
    tonnage = cargo_quantity_mt
    utilization = min(cargo_quantity_mt / dwt_max, 1.0)

    avg_spot_rate = float(np.mean(forecast["point"]))
    contract_rate = forecast["current_rate"] * (1 + CONTRACT_PREMIUM)
    multi_voyage_rate = forecast["current_rate"] * (1 + MULTI_VOYAGE_PREMIUM)

    spot_cost = avg_spot_rate * tonnage
    contract_cost = contract_rate * tonnage
    multi_voyage_cost = multi_voyage_rate * tonnage

    return {
        "tonnage_mt": tonnage,
        "utilization": utilization,
        "avg_spot_rate": avg_spot_rate,
        "contract_rate": contract_rate,
        "multi_voyage_rate": multi_voyage_rate,
        "multi_voyage_count": MULTI_VOYAGE_COUNT,
        "spot_cost_usd": spot_cost,
        "contract_cost_usd": contract_cost,
        "multi_voyage_cost_usd": multi_voyage_cost,
        "savings_usd": spot_cost - contract_cost,
        "multi_voyage_savings_usd": spot_cost - multi_voyage_cost,
    }


def build_recommendation(forecast: dict, risk: dict, vessel_class: str, dwt_max: float,
                          cargo_quantity_mt: float) -> dict:
    decision, reasons = score_decision(forecast, risk)
    costs = cost_comparison(forecast, vessel_class, dwt_max, cargo_quantity_mt)

    cost_options = [
        {
            "id": "spot_market",
            "name": "Spot market",
            "rate_usd_per_mt": costs["avg_spot_rate"],
            "total_cost_usd": costs["spot_cost_usd"],
        },
        {
            "id": "short_term_multi_voyage",
            "name": f"Short-term multi-voyage ({costs['multi_voyage_count']} voyages)",
            "rate_usd_per_mt": costs["multi_voyage_rate"],
            "total_cost_usd": costs["multi_voyage_cost_usd"],
        },
        {
            "id": "medium_term_fixed",
            "name": "Medium-term (single fixed contract)",
            "rate_usd_per_mt": costs["contract_rate"],
            "total_cost_usd": costs["contract_cost_usd"],
        },
    ]
    lowest_cost = min(option["total_cost_usd"] for option in cost_options)
    for option in cost_options:
        option["is_lowest_modeled_cost"] = option["total_cost_usd"] == lowest_cost

    strategy_costs = {
        option["name"]: option["total_cost_usd"] for option in cost_options
    }
    strategy = min(strategy_costs, key=strategy_costs.get)

    return {
        "decision": decision,
        "reasons": reasons,
        "vessel_class": vessel_class,
        "risk_level": risk["level"],
        "contract_strategy": strategy,
        "costs": costs,
        "cost_options": cost_options,
    }


def compare_vessel_costs(port: str, current_rate: float, cargo_quantity_mt: float) -> dict:
    """Cost/feasibility comparison across every vessel class for a fixed
    cargo requirement (not just the scenario's preset vessel). Uses the
    same current_rate and CONTRACT_PREMIUM already computed elsewhere --
    no new rate is fetched or estimated. The underlying data only carries
    one route-level spot rate (not a rate per vessel class), so each
    vessel's rate is adjusted by the illustrative VESSEL_CLASS_COST_DISCOUNT
    above (larger vessels assumed cheaper per mt) -- a documented
    placeholder, not real per-class market data. What differs between
    vessel classes here is therefore this illustrative discount, plus
    feasibility and utilization; the "cost-efficient choice" breaks any
    remaining cost ties on the best (highest) utilization among the
    feasible, lowest-cost vessels."""
    effective_rate = current_rate * (1 + CONTRACT_PREMIUM)

    rows = []
    for vessel_class, spec in VESSEL_SPECS.items():
        checks = check_feasibility(vessel_class, port)
        feasible = all(c["status"] != "fail" for c in checks)
        utilization = min(cargo_quantity_mt / spec["dwt_max"], 1.0)
        adjusted_rate = effective_rate * (1 - VESSEL_CLASS_COST_DISCOUNT[vessel_class])
        estimated_cost = adjusted_rate * cargo_quantity_mt

        rows.append({
            "vessel_class": vessel_class,
            "feasible": feasible,
            "utilization": utilization,
            "estimated_cost_usd": estimated_cost,
        })

    feasible_rows = [r for r in rows if r["feasible"]]
    cost_efficient_choice = None
    if feasible_rows:
        best = min(feasible_rows, key=lambda r: (r["estimated_cost_usd"], -r["utilization"]))
        cost_efficient_choice = best["vessel_class"]

    return {
        "rows": rows,
        "cost_efficient_choice": cost_efficient_choice,
        "effective_rate": effective_rate,
        "cargo_quantity_mt": cargo_quantity_mt,
    }
