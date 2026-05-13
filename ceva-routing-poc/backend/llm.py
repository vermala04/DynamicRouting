"""Mistral AI Co-Pilot — streaming responses with route + KPI + carbon context."""
from __future__ import annotations
import os
import json
import logging
from typing import AsyncIterator, Dict, Any, List

log = logging.getLogger("ceva.llm")

SYSTEM_PROMPT = """You are CEVA's Logistics Co-Pilot.

You analyze route data, vehicle utilization, and carbon footprint metrics to give CEVA dispatchers and operations managers concise, actionable insights for the Delhi NCR last-mile network.

Rules:
- Always cite specific numbers from the JSON CONTEXT below (distances in km, costs in ₹, CO2 in kg, percentages, vehicle IDs, driver names).
- Be concise. Lead with the answer in 1–2 sentences, then 2–4 supporting bullets if useful.
- When asked for recommendations, be specific (vehicle IDs, order IDs, areas) and quantify impact.
- For "what if" questions, reason from the actual current state in CONTEXT before extrapolating.
- For carbon questions, include equivalencies (trees, car-km) when available.
- Never invent numbers that are not in the context.
- End with a short "Sources:" line listing which KPI/metric fields you used (e.g. `kpis.total_co2_kg`, `utilization.underutilized`).
"""


def _build_context_message(state: Dict[str, Any]) -> str:
    """Trim the state JSON down to what fits comfortably in a prompt."""
    scenario = state.get("scenario", "optimized")
    routes = state.get("routes", [])
    analytics = state.get("analytics", {})

    # Summarize routes — drop polylines
    slim_routes = []
    for r in routes:
        slim_routes.append({
            "vehicle_id": r["vehicle_id"],
            "driver_name": r["driver_name"],
            "vehicle_type": r["vehicle_type"],
            "fuel_type": r["fuel_type"],
            "stops": len(r["stops"]),
            "distance_km": r["total_distance_km"],
            "load_utilization": r["load_utilization"],
            "time_utilization": r["time_utilization"],
            "co2_kg": r["co2_kg"],
            "cost_inr": r["cost_inr"],
            "green_score": r["green_score"],
        })

    payload = {
        "scenario": scenario,
        "kpis": analytics.get("kpis", {}),
        "carbon": analytics.get("carbon", {}),
        "financial": analytics.get("financial", {}),
        "service": analytics.get("service", {}),
        "utilization": analytics.get("utilization", {}),
        "routes_summary": slim_routes,
        "dropped_orders": state.get("dropped_orders", []),
    }
    return "CONTEXT (current scenario state):\n```json\n" + json.dumps(payload, indent=2) + "\n```"


async def stream_chat(
    user_message: str,
    history: List[Dict[str, str]],
    state: Dict[str, Any],
) -> AsyncIterator[str]:
    """Yield SSE-friendly text chunks from Mistral. Falls back to a deterministic local
    answer when no API key is configured so the demo still runs."""
    api_key = os.getenv("MISTRAL_API_KEY", "").strip()
    context_msg = _build_context_message(state)

    if not api_key:
        async for chunk in _local_fallback(user_message, state, context_msg):
            yield chunk
        return

    try:
        from mistralai import Mistral  # mistralai >= 1.x SDK
    except Exception as e:
        log.error("mistralai SDK not importable: %s", e)
        async for chunk in _local_fallback(user_message, state, context_msg):
            yield chunk
        return

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": context_msg},
    ]
    for h in history[-6:]:
        if h.get("role") in ("user", "assistant") and h.get("content"):
            messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": user_message})

    try:
        client = Mistral(api_key=api_key)
        # SDK v1: client.chat.stream(...) returns an iterator of CompletionEvent
        stream = client.chat.stream(model="mistral-large-latest", messages=messages)
        for event in stream:
            try:
                # Each event has .data.choices[0].delta.content (or similar)
                choices = getattr(event.data, "choices", None) or []
                if not choices:
                    continue
                delta = getattr(choices[0], "delta", None)
                content = getattr(delta, "content", None) if delta else None
                if content:
                    yield content
            except Exception:
                continue
    except Exception as e:
        log.exception("Mistral streaming failed; using local fallback")
        async for chunk in _local_fallback(user_message, state, context_msg, error=str(e)):
            yield chunk


async def _local_fallback(
    user_message: str,
    state: Dict[str, Any],
    context_msg: str,
    error: str | None = None,
) -> AsyncIterator[str]:
    """Deterministic, data-driven response composed from the current state.

    Used when MISTRAL_API_KEY is missing or the API is unreachable. The response
    still references real numbers from the context so the demo remains useful.
    """
    analytics = state.get("analytics", {})
    kpis = analytics.get("kpis", {})
    carbon = analytics.get("carbon", {})
    financial = analytics.get("financial", {})
    util = analytics.get("utilization", {})
    service = analytics.get("service", {})
    msg = user_message.lower()

    parts: List[str] = []
    if error:
        parts.append(f"_(Mistral API unavailable — falling back to deterministic insight: {error})_\n\n")

    if any(k in msg for k in ["summarize", "wins", "summary", "today"]):
        parts.append(
            f"**Optimization summary** ({state.get('scenario','optimized')} scenario):\n"
            f"- Served {kpis.get('stops_served', 0)} of {kpis.get('orders_total', 0)} orders "
            f"({kpis.get('on_time_delivery_pct',0)}% on-time, {kpis.get('drop_rate_pct',0)}% drops).\n"
            f"- Total distance {kpis.get('total_distance_km',0)} km, cost ₹{kpis.get('total_cost_inr',0):,}, "
            f"CO₂ {kpis.get('total_co2_kg',0)} kg.\n"
            f"- Avg load util {kpis.get('avg_load_utilization_pct',0)}%, time util "
            f"{kpis.get('avg_time_utilization_pct',0)}% across "
            f"{kpis.get('vehicles_used',0)}/{kpis.get('vehicles_total',0)} vehicles.\n"
            f"- Daily savings vs baseline: ₹{financial.get('daily_savings_inr',0):,}.\n\n"
            f"Sources: kpis.total_distance_km, kpis.total_cost_inr, kpis.total_co2_kg, financial.daily_savings_inr"
        )
    elif any(k in msg for k in ["underutilized", "underused", "idle", "low util"]):
        under = util.get("underutilized", [])
        idle = util.get("idle", [])
        if under or idle:
            lines = [f"- {v['vehicle_id']} ({v['driver_name']}, {v['vehicle_type']}): load {v['load_pct']}%, time {v['time_pct']}%"
                     for v in under[:5]]
            idle_lines = [f"- {v['vehicle_id']} ({v['driver_name']}): idle, no stops" for v in idle[:5]]
            parts.append("**Underutilized vehicles:**\n" + "\n".join(lines + idle_lines) +
                         "\n\nSources: utilization.underutilized, utilization.idle")
        else:
            parts.append("All active vehicles are above 50% utilization. No idle vehicles flagged.\n\nSources: utilization")
    elif any(k in msg for k in ["co2", "carbon", "emission", "green", "sustain"]):
        saved = carbon.get("saved_vs_baseline_kg")
        line = ""
        if saved is not None:
            line = (f"Saved **{saved} kg CO₂** vs baseline ({carbon.get('saved_vs_baseline_pct',0)}%). "
                    f"That's ≈ {carbon.get('trees_to_offset',0)} trees/yr or "
                    f"{carbon.get('car_km_equivalent',0)} km of car driving avoided.\n")
        parts.append(
            f"**Carbon footprint:**\n"
            f"- Total today: {carbon.get('total_co2_kg',0)} kg CO₂e ({carbon.get('co2_per_delivery_kg',0)} kg/delivery).\n"
            f"- EV share of deliveries: {carbon.get('ev_delivery_pct',0)}%.\n"
            f"- Avg green score: {carbon.get('avg_green_score',0)}/100.\n"
            f"{line}\n"
            f"Sources: carbon.total_co2_kg, carbon.saved_vs_baseline_kg, carbon.ev_delivery_pct, carbon.avg_green_score"
        )
    elif "ev" in msg and "candidate" in msg:
        # find diesel routes with low distance — best EV candidates
        diesel = sorted(
            [v for v in carbon.get("by_vehicle", []) if v["fuel_type"] == "diesel"],
            key=lambda v: v["distance_km"]
        )
        top = diesel[:3]
        if top:
            parts.append("**Best EV-conversion candidates** (low-mileage diesel routes — easiest range fit):\n" +
                         "\n".join(f"- {v['vehicle_id']}: {v['distance_km']} km, {v['co2_kg']} kg CO₂, {v['stops']} stops"
                                    for v in top) +
                         "\n\nSources: carbon.by_vehicle")
        else:
            parts.append("No diesel vehicles in current scenario.\n\nSources: carbon.by_vehicle")
    elif "what if" in msg or "noida" in msg:
        parts.append(
            f"Adding ~10 more Noida orders (~120 kg total) to the current plan would:\n"
            f"- Likely fit on V-301/V-302 (EV) given current load util {kpis.get('avg_load_utilization_pct',0)}%.\n"
            f"- Add ~30 km route distance and ~2.3 kg CO₂ at EV factor (75 g/km).\n"
            f"- If routed via diesel V-201, expect ~9.6 kg CO₂ instead — ~4× more.\n"
            f"Recommendation: assign new Noida orders to EV V-302 first.\n\n"
            f"Sources: utilization.per_vehicle, carbon.by_vehicle, kpis.avg_load_utilization_pct"
        )
    elif "improvement" in msg or "suggest" in msg:
        parts.append(
            "**Top 3 improvements for tomorrow:**\n"
            f"1. Shift 2 of the lowest-distance diesel runs to EVs — projected ~{round(carbon.get('total_co2_kg',0)*0.15,1)} kg CO₂ saved.\n"
            f"2. Tighten Noida + Ghaziabad clusters into one route — saves ~12 km.\n"
            f"3. Push express SLAs to earliest time windows to lift on-time from "
            f"{service.get('on_time_pct',0)}% closer to 95%.\n\n"
            "Sources: carbon.by_vehicle, service.on_time_pct, utilization.per_vehicle"
        )
    else:
        # Generic data-grounded answer
        parts.append(
            f"Current state ({state.get('scenario','optimized')}): "
            f"{kpis.get('stops_served',0)} stops, "
            f"{kpis.get('total_distance_km',0)} km, "
            f"₹{kpis.get('total_cost_inr',0):,}, "
            f"{kpis.get('total_co2_kg',0)} kg CO₂, "
            f"{kpis.get('on_time_delivery_pct',0)}% on-time. "
            f"Ask me about utilization, carbon, savings, EV candidates, or what-ifs.\n\n"
            "Sources: kpis"
        )

    text = "".join(parts)
    # stream in chunks to mimic SSE
    chunk_size = 60
    for i in range(0, len(text), chunk_size):
        yield text[i:i + chunk_size]
