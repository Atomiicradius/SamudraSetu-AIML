"""
Feasibility module.

Representative vessel-class specs and port limits are hardcoded (illustrative,
not surveyed data) -- but the pass/fail/unknown verdict per constraint is
always computed by comparing the two, never asserted. A constraint is
"unknown" whenever the port limit isn't defined in PORT_LIMITS, never
silently treated as a pass or a fail.
"""

# Representative vessel-class specs (illustrative, not a class society source)
VESSEL_SPECS = {
    "Handysize": {"draft_m": 10.5, "loa_m": 190.0, "beam_m": 32.3, "dwt_min": 25000, "dwt_max": 40000},
    "Supramax":  {"draft_m": 12.0, "loa_m": 200.0, "beam_m": 32.3, "dwt_min": 50000, "dwt_max": 60000},
    "Panamax":   {"draft_m": 14.5, "loa_m": 225.0, "beam_m": 32.3, "dwt_min": 60000, "dwt_max": 80000},
    "Capesize":  {"draft_m": 17.5, "loa_m": 290.0, "beam_m": 45.0, "dwt_min": 150000, "dwt_max": 180000},
}

# Representative port limits for all 7 destinations in the requirement form.
# A missing key means the limit is not defined for that port -> the
# constraint check must report "unknown", never a silent pass/fail. Some
# ports deliberately carry undefined limits here (matching real-world
# uneven publication of port particulars), so "Unknown" badges keep showing
# up genuinely rather than every port always resolving to pass/fail.
# Dict key order also drives the Destination dropdown order in app.py.
PORT_LIMITS = {
    "Paradip": {"max_draft_m": 18.1, "max_loa_m": 300.0, "max_dwt": 180000},  # beam limit not published -> unknown
    "Visakhapatnam": {"max_draft_m": 17.0, "max_loa_m": 280.0, "max_beam_m": 45.0, "max_dwt": 150000},
    "Gangavaram": {"max_draft_m": 20.0, "max_loa_m": 300.0, "max_dwt": 180000},  # deep-water port; beam limit not published -> unknown
    "Gopalpur": {"max_draft_m": 16.5, "max_dwt": 100000},  # LOA / beam limits not published -> unknown
    "Dhamra": {"max_draft_m": 18.5, "max_dwt": 180000},  # LOA / beam limits not published -> unknown
    "Sagar/Sandheads": {"max_draft_m": 13.0, "max_loa_m": 230.0},  # river-approach anchorage; DWT / beam limits not published -> unknown
    "Haldia": {"max_draft_m": 9.0, "max_loa_m": 186.0, "max_dwt": 40000},  # shallow river port; beam limit not published -> unknown
}

CONSTRAINTS = [
    ("draft_m", "max_draft_m", "Draft"),
    ("loa_m", "max_loa_m", "LOA"),
    ("beam_m", "max_beam_m", "Beam"),
    ("dwt_max", "max_dwt", "DWT"),
]


def check_feasibility(vessel_class: str, port: str) -> list[dict]:
    spec = VESSEL_SPECS[vessel_class]
    limits = PORT_LIMITS.get(port, {})

    results = []
    for spec_key, limit_key, label in CONSTRAINTS:
        vessel_value = spec[spec_key]
        limit_value = limits.get(limit_key)

        if limit_value is None:
            status = "unknown"
        elif vessel_value <= limit_value:
            status = "pass"
        else:
            status = "fail"

        results.append({
            "constraint": label,
            "vessel_value": vessel_value,
            "port_limit": limit_value,
            "status": status,
        })
    return results


def check_all_vessel_classes(port: str) -> dict:
    return {vc: check_feasibility(vc, port) for vc in VESSEL_SPECS}
