"""Aggregate KPI / utilization / carbon / financial / service-quality analytics."""
from __future__ import annotations
from typing import List, Dict, Any
from statistics import mean

from carbon import (
    trees_equivalent, car_km_equivalent, EMISSION_FACTORS_G_PER_KM,
)


def _safe(values, default=0.0):
    return mean(values) if values else default


def compute_kpis(routes: List[Dict[str, Any]], dropped: List[str], total_orders: int) -> Dict[str, Any]:
    used = [r for r in routes if r["stops"]]
    total_distance = sum(r["total_distance_km"] for r in routes)
    total_time = sum(r["total_time_min"] for r in routes)
    total_co2 = sum(r["co2_kg"] for r in routes)
    total_cost = sum(r["cost_inr"] for r in routes)
    total_load = sum(r["total_load_kg"] for r in routes)
    served = total_orders - len(dropped)

    on_time_count = sum(1 for r in routes for s in r["stops"] if s["on_time"])
    total_stops = sum(len(r["stops"]) for r in routes)
    on_time_pct = (on_time_count / total_stops * 100.0) if total_stops else 0.0

    avg_load_util = _safe([r["load_utilization"] for r in used]) * 100.0
    avg_time_util = _safe([r["time_utilization"] for r in used]) * 100.0
    avg_stop_util = _safe([r["stop_utilization"] for r in used]) * 100.0

    return {
        "total_distance_km": round(total_distance, 1),
        "total_time_min": int(total_time),
        "total_co2_kg": round(total_co2, 2),
        "total_cost_inr": round(total_cost, 2),
        "total_load_kg": round(total_load, 1),
        "vehicles_total": len(routes),
        "vehicles_used": len(used),
        "stops_served": total_stops,
        "orders_total": total_orders,
        "orders_dropped": len(dropped),
        "drop_rate_pct": round(len(dropped) / max(total_orders, 1) * 100.0, 1),
        "on_time_delivery_pct": round(on_time_pct, 1),
        "avg_load_utilization_pct": round(avg_load_util, 1),
        "avg_time_utilization_pct": round(avg_time_util, 1),
        "avg_stop_utilization_pct": round(avg_stop_util, 1),
        "cost_per_delivery_inr": round(total_cost / max(total_stops, 1), 2),
        "cost_per_km_inr": round(total_cost / max(total_distance, 0.001), 2),
        "cost_per_kg_inr": round(total_cost / max(total_load, 0.001), 2),
    }


def utilization_breakdown(routes: List[Dict[str, Any]]) -> Dict[str, Any]:
    per_vehicle = []
    underutilized = []
    idle = []
    for r in routes:
        load_pct = round(r["load_utilization"] * 100.0, 1)
        time_pct = round(r["time_utilization"] * 100.0, 1)
        stop_pct = round(r["stop_utilization"] * 100.0, 1)
        entry = {
            "vehicle_id": r["vehicle_id"],
            "driver_name": r["driver_name"],
            "vehicle_type": r["vehicle_type"],
            "fuel_type": r["fuel_type"],
            "load_pct": load_pct,
            "time_pct": time_pct,
            "stop_pct": stop_pct,
            "stops": len(r["stops"]),
            "distance_km": r["total_distance_km"],
        }
        per_vehicle.append(entry)
        if not r["stops"]:
            idle.append(entry)
        elif load_pct < 50 and time_pct < 50:
            underutilized.append(entry)
    return {
        "per_vehicle": per_vehicle,
        "idle": idle,
        "underutilized": underutilized,
    }


def carbon_breakdown(routes: List[Dict[str, Any]], baseline_routes: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    total_co2 = sum(r["co2_kg"] for r in routes)
    total_distance = sum(r["total_distance_km"] for r in routes)
    total_load = sum(r["total_load_kg"] for r in routes)
    total_stops = sum(len(r["stops"]) for r in routes)

    by_type: Dict[str, float] = {}
    by_vehicle = []
    ev_deliveries = 0
    diesel_deliveries = 0
    for r in routes:
        by_type[r["vehicle_type"]] = by_type.get(r["vehicle_type"], 0.0) + r["co2_kg"]
        by_vehicle.append({
            "vehicle_id": r["vehicle_id"],
            "vehicle_type": r["vehicle_type"],
            "fuel_type": r["fuel_type"],
            "co2_kg": r["co2_kg"],
            "distance_km": r["total_distance_km"],
            "stops": len(r["stops"]),
            "green_score": r["green_score"],
        })
        if r["fuel_type"] == "electric":
            ev_deliveries += len(r["stops"])
        else:
            diesel_deliveries += len(r["stops"])

    ev_pct = (ev_deliveries / max(total_stops, 1)) * 100.0
    avg_green = sum(r["green_score"] for r in routes if r["stops"]) / max(sum(1 for r in routes if r["stops"]), 1)

    saved_kg = saved_pct = None
    if baseline_routes is not None:
        base_co2 = sum(r["co2_kg"] for r in baseline_routes)
        saved_kg = round(base_co2 - total_co2, 2)
        saved_pct = round((saved_kg / base_co2) * 100.0, 1) if base_co2 > 0 else 0.0

    return {
        "total_co2_kg": round(total_co2, 2),
        "co2_per_delivery_kg": round(total_co2 / max(total_stops, 1), 3),
        "co2_per_km_g": round((total_co2 * 1000.0) / max(total_distance, 0.001), 1),
        "co2_per_kg_shipped_g": round((total_co2 * 1000.0) / max(total_load, 0.001), 2),
        "by_type_kg": {k: round(v, 2) for k, v in by_type.items()},
        "by_vehicle": by_vehicle,
        "ev_delivery_pct": round(ev_pct, 1),
        "diesel_delivery_pct": round(100 - ev_pct, 1),
        "ev_deliveries": ev_deliveries,
        "diesel_deliveries": diesel_deliveries,
        "avg_green_score": round(avg_green, 1),
        "trees_to_offset": round(trees_equivalent(total_co2), 1),
        "car_km_equivalent": round(car_km_equivalent(total_co2), 1),
        "saved_vs_baseline_kg": saved_kg,
        "saved_vs_baseline_pct": saved_pct,
        "emission_factors_g_per_km": EMISSION_FACTORS_G_PER_KM,
    }


def financial_impact(opt_kpis: Dict[str, Any], base_kpis: Dict[str, Any] | None) -> Dict[str, Any]:
    if not base_kpis:
        return {
            "daily_savings_inr": 0.0,
            "monthly_savings_inr": 0.0,
            "annual_savings_inr": 0.0,
            "co2_saved_tonnes_annual": 0.0,
            "extrapolation": {},
        }
    daily = max(0.0, base_kpis["total_cost_inr"] - opt_kpis["total_cost_inr"])
    co2_daily = max(0.0, base_kpis["total_co2_kg"] - opt_kpis["total_co2_kg"])
    monthly = daily * 26  # working days
    annual = daily * 312
    co2_annual_tonnes = (co2_daily * 312) / 1000.0
    # Multi-depot extrapolation (e.g., 10 depots)
    return {
        "daily_savings_inr": round(daily, 2),
        "monthly_savings_inr": round(monthly, 2),
        "annual_savings_inr": round(annual, 2),
        "co2_saved_kg_daily": round(co2_daily, 2),
        "co2_saved_tonnes_annual": round(co2_annual_tonnes, 2),
        "cost_per_delivery_baseline": base_kpis["cost_per_delivery_inr"],
        "cost_per_delivery_optimized": opt_kpis["cost_per_delivery_inr"],
        "extrapolation": {
            "depots": 10,
            "annual_savings_inr": round(annual * 10, 2),
            "annual_savings_cr": round(annual * 10 / 1e7, 2),
            "annual_co2_saved_tonnes": round(co2_annual_tonnes * 10, 1),
        },
    }


def service_quality(routes: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_priority: Dict[str, Dict[str, int]] = {
        "express": {"on_time": 0, "total": 0},
        "urgent": {"on_time": 0, "total": 0},
        "normal": {"on_time": 0, "total": 0},
    }
    violations = []
    for r in routes:
        for s in r["stops"]:
            p = s["priority"]
            by_priority.setdefault(p, {"on_time": 0, "total": 0})
            by_priority[p]["total"] += 1
            if s["on_time"]:
                by_priority[p]["on_time"] += 1
            else:
                violations.append({
                    "vehicle_id": r["vehicle_id"],
                    "order_id": s["order_id"],
                    "customer_name": s["customer_name"],
                    "priority": p,
                    "eta_min": s["eta_min"],
                })
    sla_compliance = {}
    for p, c in by_priority.items():
        sla_compliance[p] = round((c["on_time"] / c["total"]) * 100.0, 1) if c["total"] else 100.0
    total_stops = sum(c["total"] for c in by_priority.values())
    on_time_total = sum(c["on_time"] for c in by_priority.values())
    return {
        "on_time_pct": round(on_time_total / max(total_stops, 1) * 100.0, 1),
        "sla_compliance_pct_by_priority": sla_compliance,
        "time_window_violations": violations,
        "violations_count": len(violations),
    }


def _delta_summary(opt_value: float, base_value: float | None, unit: str, lower_is_better: bool = True) -> Dict[str, Any]:
    """Return a small serializable comparison object for optimization explainability."""
    if base_value is None:
        return {
            "optimized": round(opt_value, 2),
            "baseline": None,
            "delta": None,
            "delta_pct": None,
            "unit": unit,
            "improved": None,
        }
    delta = opt_value - base_value
    delta_pct = (delta / base_value * 100.0) if base_value else 0.0
    improved = delta < 0 if lower_is_better else delta > 0
    return {
        "optimized": round(opt_value, 2),
        "baseline": round(base_value, 2),
        "delta": round(delta, 2),
        "delta_pct": round(delta_pct, 1),
        "unit": unit,
        "improved": improved,
    }


def optimization_reasoning(
    routes: List[Dict[str, Any]],
    dropped: List[str],
    total_orders: int,
    kpis: Dict[str, Any],
    baseline_routes: List[Dict[str, Any]] | None = None,
    baseline_kpis: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Explain what changed and why the optimized plan was selected.

    This is intentionally deterministic and derived only from OR-Tools outputs and
    KPI deltas. Mistral may summarize the result in chat, but it does not create or
    override the optimization rationale.
    """
    comparisons = {
        "distance": _delta_summary(
            kpis["total_distance_km"],
            baseline_kpis.get("total_distance_km") if baseline_kpis else None,
            "km",
            lower_is_better=True,
        ),
        "cost": _delta_summary(
            kpis["total_cost_inr"],
            baseline_kpis.get("total_cost_inr") if baseline_kpis else None,
            "EUR",
            lower_is_better=True,
        ),
        "co2": _delta_summary(
            kpis["total_co2_kg"],
            baseline_kpis.get("total_co2_kg") if baseline_kpis else None,
            "kg CO2e",
            lower_is_better=True,
        ),
        "on_time": _delta_summary(
            kpis["on_time_delivery_pct"],
            baseline_kpis.get("on_time_delivery_pct") if baseline_kpis else None,
            "pct",
            lower_is_better=False,
        ),
        "drops": _delta_summary(
            kpis["orders_dropped"],
            baseline_kpis.get("orders_dropped") if baseline_kpis else None,
            "orders",
            lower_is_better=True,
        ),
    }

    improved = [name for name, item in comparisons.items() if item["improved"] is True]
    protected = [name for name, item in comparisons.items() if item["baseline"] is not None and item["delta"] == 0]

    why: List[str] = [
        "OR-Tools evaluated feasible stop sequences against capacity, max-stop, driver-shift and customer time-window constraints.",
        "The objective combines travel distance/cost with a carbon shadow price, while priority-aware drop penalties protect express and urgent orders.",
    ]
    if improved:
        labels = {
            "distance": "distance",
            "cost": "operating cost",
            "co2": "CO2 emissions",
            "on_time": "on-time performance",
            "drops": "drop count",
        }
        why.append("The selected plan improves " + ", ".join(labels[i] for i in improved) + " versus the baseline.")
    if protected:
        why.append("The plan preserves " + ", ".join(protected) + " while optimizing other objectives.")
    if dropped:
        why.append(f"{len(dropped)} orders remain dropped because serving them would violate active constraints or incur a lower-priority trade-off.")

    top_routes = sorted(
        [r for r in routes if r["stops"]],
        key=lambda r: (len(r["stops"]), r["load_utilization"], r["green_score"]),
        reverse=True,
    )[:5]
    route_reasoning = []
    for r in top_routes:
        priorities: Dict[str, int] = {}
        for stop in r["stops"]:
            priorities[stop["priority"]] = priorities.get(stop["priority"], 0) + 1
        priority_text = ", ".join(f"{count} {priority}" for priority, count in sorted(priorities.items()))
        reasons = [
            f"Assigned {len(r['stops'])} stops within {round(r['load_utilization'] * 100, 1)}% load and {round(r['time_utilization'] * 100, 1)}% shift utilization.",
            f"Sequenced stops to respect time windows; {sum(1 for s in r['stops'] if s['on_time'])}/{len(r['stops'])} stops are on time.",
        ]
        if r["fuel_type"] == "electric":
            reasons.append("EV route receives a high green score because France-grid emissions are lower than diesel alternatives.")
        if priority_text:
            reasons.append(f"Priority mix handled on this route: {priority_text}.")
        route_reasoning.append({
            "vehicle_id": r["vehicle_id"],
            "driver_name": r["driver_name"],
            "stops": len(r["stops"]),
            "distance_km": r["total_distance_km"],
            "cost_eur": r["cost_inr"],
            "co2_kg": r["co2_kg"],
            "green_score": r["green_score"],
            "reasons": reasons,
        })

    summary = "Optimized plan generated with OR-Tools constraint solving."
    if baseline_kpis:
        dist = comparisons["distance"]
        cost = comparisons["cost"]
        co2 = comparisons["co2"]

        def direction(item: Dict[str, Any], lower_label: str = "reduced", higher_label: str = "increased") -> str:
            delta = item["delta"] or 0
            if delta < 0:
                return lower_label
            if delta > 0:
                return higher_label
            return "held flat"

        summary = (
            f"Optimized plan serves {kpis['stops_served']}/{kpis['orders_total']} orders and "
            f"{direction(dist)} distance by {abs(dist['delta'] or 0):.1f} km, "
            f"{direction(cost)} cost by €{abs(cost['delta'] or 0):.0f}, and "
            f"{direction(co2)} CO2e by {abs(co2['delta'] or 0):.1f} kg versus baseline."
        )

    return {
        "summary": summary,
        "optimizer": "Google OR-Tools VRP solver",
        "selected_objective": "Minimize distance/cost/carbon while satisfying capacity, shift, max-stop, time-window and priority drop-penalty constraints.",
        "baseline_reference": "Naive priority-sorted round-robin assignment with nearest-neighbor sequencing" if baseline_routes is not None else None,
        "comparisons": comparisons,
        "why_optimized": why,
        "route_reasoning": route_reasoning,
        "dropped_order_ids": dropped,
        "generated_from": [
            "analytics.kpis",
            "optimizer.routes",
            "baseline.kpis" if baseline_kpis else "baseline unavailable",
            "OR-Tools constraints",
        ],
    }


def full_analytics(
    routes: List[Dict[str, Any]],
    dropped: List[str],
    total_orders: int,
    baseline_routes: List[Dict[str, Any]] | None = None,
    baseline_kpis: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    kpis = compute_kpis(routes, dropped, total_orders)
    return {
        "kpis": kpis,
        "utilization": utilization_breakdown(routes),
        "carbon": carbon_breakdown(routes, baseline_routes),
        "financial": financial_impact(kpis, baseline_kpis),
        "service": service_quality(routes),
        "optimization_reasoning": optimization_reasoning(
            routes, dropped, total_orders, kpis, baseline_routes=baseline_routes, baseline_kpis=baseline_kpis
        ),
    }
