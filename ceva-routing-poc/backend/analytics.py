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
    }
