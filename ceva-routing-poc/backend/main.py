"""FastAPI app for CEVA Dynamic Routing & Logistics Intelligence POC."""
from __future__ import annotations
import os
import copy
import json
import asyncio
import logging
import random
from typing import List, Dict, Any, Optional, Tuple

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

load_dotenv()  # picks up .env if present

import data_generator
import optimizer
import analytics as analytics_mod
import carbon as carbon_mod
from distance import build_matrices
from llm import stream_chat
from models import DisruptionPayload, ChatRequest

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("ceva.api")

app = FastAPI(title="CEVA Dynamic Routing POC", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Global state ----------
class State:
    depot: Dict[str, Any] = {}
    vehicles: List[Dict[str, Any]] = []
    orders: List[Dict[str, Any]] = []  # mutable working copy
    original_orders: List[Dict[str, Any]] = []
    original_vehicles: List[Dict[str, Any]] = []
    distance_km: List[List[float]] = []
    time_min: List[List[float]] = []
    last_baseline: Optional[Dict[str, Any]] = None
    last_optimized: Optional[Dict[str, Any]] = None
    use_osrm: bool = True


STATE = State()


# ---------- Lifecycle ----------
@app.on_event("startup")
def _startup() -> None:
    data = data_generator.generate(regenerate=False)
    STATE.depot = data["depot"]
    STATE.vehicles = data["vehicles"]
    STATE.orders = list(data["orders"])
    STATE.original_orders = copy.deepcopy(data["orders"])
    STATE.original_vehicles = copy.deepcopy(data["vehicles"])
    STATE.use_osrm = os.getenv("USE_OSRM", "1") not in ("0", "false", "False")
    _rebuild_matrices()
    log.info("Loaded %d orders, %d vehicles. OSRM=%s", len(STATE.orders), len(STATE.vehicles), STATE.use_osrm)


def _rebuild_matrices() -> None:
    coords: List[Tuple[float, float]] = [(STATE.depot["lat"], STATE.depot["lon"])]
    coords.extend((o["lat"], o["lon"]) for o in STATE.orders)
    avg_speed = sum(v["avg_speed_kmh"] for v in STATE.vehicles) / max(len(STATE.vehicles), 1)
    STATE.distance_km, STATE.time_min = build_matrices(coords, avg_speed_kmh=avg_speed, use_osrm=STATE.use_osrm)


# ---------- Helpers ----------
def _run_baseline() -> Dict[str, Any]:
    routes, dropped = optimizer.naive_static_route(
        STATE.depot, STATE.vehicles, STATE.orders, STATE.distance_km, STATE.time_min
    )
    kpis = analytics_mod.compute_kpis(routes, dropped, len(STATE.orders))
    a = analytics_mod.full_analytics(routes, dropped, len(STATE.orders), baseline_routes=None, baseline_kpis=None)
    result = {
        "scenario": "baseline",
        "routes": routes,
        "dropped_orders": dropped,
        "kpis": kpis,
        "analytics": a,
    }
    STATE.last_baseline = result
    return result


def _run_optimized() -> Dict[str, Any]:
    if STATE.last_baseline is None:
        _run_baseline()
    routes, dropped = optimizer.optimize(
        STATE.depot, STATE.vehicles, STATE.orders, STATE.distance_km, STATE.time_min
    )
    kpis = analytics_mod.compute_kpis(routes, dropped, len(STATE.orders))
    a = analytics_mod.full_analytics(
        routes, dropped, len(STATE.orders),
        baseline_routes=STATE.last_baseline["routes"],
        baseline_kpis=STATE.last_baseline["kpis"],
    )
    result = {
        "scenario": "optimized",
        "routes": routes,
        "dropped_orders": dropped,
        "kpis": kpis,
        "analytics": a,
    }
    STATE.last_optimized = result
    return result


# ---------- Endpoints ----------
@app.get("/")
def root():
    return {"service": "CEVA Dynamic Routing POC", "status": "ok", "endpoints": [
        "/api/data", "/api/baseline", "/api/optimize", "/api/disrupt",
        "/api/analytics", "/api/carbon", "/api/utilization", "/api/chat", "/api/reset"
    ]}


@app.get("/api/data")
def get_data():
    return {
        "depot": STATE.depot,
        "vehicles": STATE.vehicles,
        "orders": STATE.orders,
        "carbon_factors": carbon_mod.EMISSION_FACTORS_G_PER_KM,
    }


@app.post("/api/baseline")
def post_baseline():
    return _run_baseline()


@app.post("/api/optimize")
def post_optimize():
    return _run_optimized()


@app.post("/api/disrupt")
def post_disrupt(d: DisruptionPayload):
    """Inject a disruption and re-optimize."""
    if d.type == "new_order":
        # New urgent order in Noida by default
        payload = d.payload or {}
        new_id = payload.get("order_id") or f"ORD-{2000 + len(STATE.orders)}"
        new_order = {
            "order_id": new_id,
            "customer_name": payload.get("customer_name", "Aditya Reddy"),
            "address": payload.get("address", "Plot 99, Noida Sec 62, 201309"),
            "lat": payload.get("lat", 28.6271 + random.uniform(-0.01, 0.01)),
            "lon": payload.get("lon", 77.3716 + random.uniform(-0.01, 0.01)),
            "weight_kg": payload.get("weight_kg", 35.0),
            "time_window_start": payload.get("time_window_start", 12 * 60),
            "time_window_end": payload.get("time_window_end", 14 * 60),
            "priority": payload.get("priority", "urgent"),
            "service_time_min": payload.get("service_time_min", 8),
            "sla_minutes": payload.get("sla_minutes", 90),
        }
        STATE.orders.append(new_order)
        _rebuild_matrices()
        result = _run_optimized()
        return {"disruption": "new_order", "added_order": new_order, "result": result}

    if d.type == "vehicle_breakdown":
        payload = d.payload or {}
        vid = payload.get("vehicle_id")
        if not vid:
            # Drop the largest truck
            largest = max(STATE.vehicles, key=lambda v: v["capacity_kg"])
            vid = largest["vehicle_id"]
        before = len(STATE.vehicles)
        STATE.vehicles = [v for v in STATE.vehicles if v["vehicle_id"] != vid]
        if len(STATE.vehicles) == before:
            raise HTTPException(404, f"Vehicle {vid} not found")
        result = _run_optimized()
        return {"disruption": "vehicle_breakdown", "removed_vehicle_id": vid, "result": result}

    if d.type == "traffic_block":
        # Simulate NH-48 corridor block: add 80% travel-time penalty between any
        # pair where one node is in the Gurugram cluster (lat<28.55 & lon<77.15)
        payload = d.payload or {}
        factor = float(payload.get("factor", 1.8))
        coords: List[Tuple[float, float]] = [(STATE.depot["lat"], STATE.depot["lon"])]
        coords.extend((o["lat"], o["lon"]) for o in STATE.orders)

        def in_corridor(c):
            return c[0] < 28.55 and c[1] < 77.15

        for i in range(len(coords)):
            for j in range(len(coords)):
                if i == j:
                    continue
                if in_corridor(coords[i]) or in_corridor(coords[j]):
                    STATE.time_min[i][j] *= factor
                    STATE.distance_km[i][j] *= 1.15  # detour adds km too
        result = _run_optimized()
        return {"disruption": "traffic_block", "corridor": "NH-48 / Gurugram", "factor": factor, "result": result}

    raise HTTPException(400, f"Unknown disruption type: {d.type}")


@app.get("/api/analytics")
def get_analytics():
    if STATE.last_optimized is None:
        _run_optimized()
    return STATE.last_optimized["analytics"]


@app.get("/api/carbon")
def get_carbon():
    if STATE.last_optimized is None:
        _run_optimized()
    base = STATE.last_baseline["routes"] if STATE.last_baseline else None
    return analytics_mod.carbon_breakdown(STATE.last_optimized["routes"], base)


@app.get("/api/utilization")
def get_utilization():
    if STATE.last_optimized is None:
        _run_optimized()
    return analytics_mod.utilization_breakdown(STATE.last_optimized["routes"])


@app.post("/api/chat")
async def post_chat(req: ChatRequest):
    # Use the latest scenario the user asked for, fall back to optimized.
    state_block: Dict[str, Any]
    if req.scenario == "baseline" and STATE.last_baseline:
        state_block = STATE.last_baseline
    elif STATE.last_optimized:
        state_block = STATE.last_optimized
    elif STATE.last_baseline:
        state_block = STATE.last_baseline
    else:
        state_block = _run_optimized()

    async def event_gen():
        try:
            async for chunk in stream_chat(req.message, req.history, state_block):
                yield f"data: {json.dumps({'delta': chunk})}\n\n"
                await asyncio.sleep(0)  # cooperative yield
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            log.exception("chat error")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream")


@app.post("/api/reset")
def post_reset():
    STATE.orders = copy.deepcopy(STATE.original_orders)
    STATE.vehicles = copy.deepcopy(STATE.original_vehicles)
    STATE.last_baseline = None
    STATE.last_optimized = None
    _rebuild_matrices()
    return {"status": "reset", "orders": len(STATE.orders), "vehicles": len(STATE.vehicles)}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
