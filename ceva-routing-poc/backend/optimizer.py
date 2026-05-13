"""OR-Tools VRP optimizer with capacity + time windows + carbon-aware cost.

Also exposes `naive_static_route()` — a simple round-robin / nearest-neighbor
baseline used to demonstrate the lift from optimization.
"""
from __future__ import annotations
import math
from typing import List, Dict, Any, Tuple

from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from carbon import (
    co2_kg_for_route, fuel_or_energy_for_route, green_score,
    CARBON_PRICE_INR_PER_TONNE,
)


# ---------- Helpers ----------
def _all_coords(depot: Dict[str, Any], orders: List[Dict[str, Any]]) -> List[Tuple[float, float]]:
    coords = [(depot["lat"], depot["lon"])]
    coords.extend((o["lat"], o["lon"]) for o in orders)
    return coords


def _build_stops_for_route(
    depot: Dict[str, Any],
    vehicle: Dict[str, Any],
    visited_orders: List[Dict[str, Any]],
    distance_km: List[List[float]],
    time_min: List[List[float]],
    order_index_map: Dict[str, int],
) -> Dict[str, Any]:
    """Walk a fixed sequence of orders for one vehicle, computing ETAs/loads/distance."""
    stops: List[Dict[str, Any]] = []
    cum_load = 0.0
    cum_dist = 0.0
    current_node = 0  # depot index
    current_time = vehicle["shift_start"]

    for seq, order in enumerate(visited_orders, start=1):
        next_node = order_index_map[order["order_id"]]
        leg_km = distance_km[current_node][next_node]
        leg_min = time_min[current_node][next_node]
        cum_dist += leg_km
        arrival = current_time + leg_min
        # Wait for the time window if early
        if arrival < order["time_window_start"]:
            arrival = order["time_window_start"]
        on_time = arrival <= order["time_window_end"]
        cum_load += order["weight_kg"]
        stops.append({
            "seq": seq,
            "order_id": order["order_id"],
            "customer_name": order["customer_name"],
            "address": order["address"],
            "lat": order["lat"],
            "lon": order["lon"],
            "weight_kg": order["weight_kg"],
            "eta_min": int(arrival),
            "cumulative_load_kg": round(cum_load, 1),
            "cumulative_distance_km": round(cum_dist, 2),
            "priority": order["priority"],
            "on_time": on_time,
        })
        # Service time, then move on
        current_time = arrival + order["service_time_min"]
        current_node = next_node

    # Return to depot
    if visited_orders:
        leg_km_back = distance_km[current_node][0]
        leg_min_back = time_min[current_node][0]
        cum_dist += leg_km_back
        current_time += leg_min_back

    total_time = max(0, int(current_time - vehicle["shift_start"]))
    shift_minutes = max(1, vehicle["shift_end"] - vehicle["shift_start"])

    co2 = co2_kg_for_route(vehicle["type"], cum_dist)
    fuel_or_energy = fuel_or_energy_for_route(vehicle["type"], cum_dist)
    cost = cum_dist * vehicle["base_cost_per_km"]
    polyline = [[depot["lat"], depot["lon"]]] + [[s["lat"], s["lon"]] for s in stops]
    if visited_orders:
        polyline.append([depot["lat"], depot["lon"]])

    return {
        "vehicle_id": vehicle["vehicle_id"],
        "driver_name": vehicle["driver_name"],
        "vehicle_type": vehicle["type"],
        "fuel_type": vehicle["fuel_type"],
        "capacity_kg": vehicle["capacity_kg"],
        "stops": stops,
        "total_distance_km": round(cum_dist, 2),
        "total_time_min": total_time,
        "total_load_kg": round(cum_load, 1),
        "load_utilization": round(cum_load / vehicle["capacity_kg"], 3) if vehicle["capacity_kg"] else 0.0,
        "time_utilization": round(total_time / shift_minutes, 3),
        "stop_utilization": round(len(stops) / vehicle["max_stops"], 3) if vehicle["max_stops"] else 0.0,
        "co2_kg": round(co2, 2),
        "fuel_or_energy": round(fuel_or_energy, 2),
        "cost_inr": round(cost, 2),
        "green_score": green_score(vehicle["type"], co2, cum_dist),
        "polyline": polyline,
    }


# ---------- Naive baseline ----------
def naive_static_route(
    depot: Dict[str, Any],
    vehicles: List[Dict[str, Any]],
    orders: List[Dict[str, Any]],
    distance_km: List[List[float]],
    time_min: List[List[float]],
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Round-robin orders to vehicles by priority then nearest-neighbor sequence per vehicle."""
    order_index_map = {o["order_id"]: i + 1 for i, o in enumerate(orders)}
    # Priority weight: express > urgent > normal
    prio_w = {"express": 0, "urgent": 1, "normal": 2}
    sorted_orders = sorted(orders, key=lambda o: (prio_w[o["priority"]], o["order_id"]))

    buckets: Dict[str, List[Dict[str, Any]]] = {v["vehicle_id"]: [] for v in vehicles}
    bucket_load: Dict[str, float] = {v["vehicle_id"]: 0.0 for v in vehicles}
    bucket_count: Dict[str, int] = {v["vehicle_id"]: 0 for v in vehicles}
    veh_by_id = {v["vehicle_id"]: v for v in vehicles}
    dropped: List[str] = []

    veh_cycle = [v["vehicle_id"] for v in vehicles]
    idx = 0
    for o in sorted_orders:
        placed = False
        # Try up to len(vehicles) round-robin slots
        for _ in range(len(veh_cycle)):
            vid = veh_cycle[idx % len(veh_cycle)]
            idx += 1
            v = veh_by_id[vid]
            if (bucket_load[vid] + o["weight_kg"] <= v["capacity_kg"]
                    and bucket_count[vid] + 1 <= v["max_stops"]):
                buckets[vid].append(o)
                bucket_load[vid] += o["weight_kg"]
                bucket_count[vid] += 1
                placed = True
                break
        if not placed:
            dropped.append(o["order_id"])

    # Sequence within each bucket: nearest neighbor from depot
    routes: List[Dict[str, Any]] = []
    for v in vehicles:
        bucket = buckets[v["vehicle_id"]]
        if not bucket:
            routes.append(_build_stops_for_route(depot, v, [], distance_km, time_min, order_index_map))
            continue
        remaining = bucket[:]
        sequence: List[Dict[str, Any]] = []
        current = 0  # depot
        while remaining:
            best_idx, best_d = 0, float("inf")
            for i, o in enumerate(remaining):
                d = distance_km[current][order_index_map[o["order_id"]]]
                if d < best_d:
                    best_d = d
                    best_idx = i
            picked = remaining.pop(best_idx)
            sequence.append(picked)
            current = order_index_map[picked["order_id"]]
        routes.append(_build_stops_for_route(depot, v, sequence, distance_km, time_min, order_index_map))

    return routes, dropped


# ---------- OR-Tools optimizer ----------
def optimize(
    depot: Dict[str, Any],
    vehicles: List[Dict[str, Any]],
    orders: List[Dict[str, Any]],
    distance_km: List[List[float]],
    time_min: List[List[float]],
    time_limit_seconds: int = 8,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Run capacitated VRPTW with carbon-aware cost. Returns (routes, dropped_order_ids)."""
    n_orders = len(orders)
    n_nodes = n_orders + 1            # 0 = depot
    n_vehicles = len(vehicles)
    order_index_map = {o["order_id"]: i + 1 for i, o in enumerate(orders)}

    manager = pywrapcp.RoutingIndexManager(n_nodes, n_vehicles, 0)
    routing = pywrapcp.RoutingModel(manager)

    # ---- Cost: distance × per-km cost + carbon shadow price ----
    # We register one cost callback per vehicle so per-km costs (and emissions) match the vehicle.
    def make_cost_cb(v_idx: int):
        v = vehicles[v_idx]
        per_km = v["base_cost_per_km"]
        # carbon cost per km in INR: g/km / 1e6 * carbon_price (INR/tonne)
        carbon_per_km = (v["co2_grams_per_km"] / 1_000_000.0) * CARBON_PRICE_INR_PER_TONNE

        def cb(from_index, to_index):
            i = manager.IndexToNode(from_index)
            j = manager.IndexToNode(to_index)
            d = distance_km[i][j]
            return int((d * per_km + d * carbon_per_km) * 100)  # cents
        return cb

    for v_idx in range(n_vehicles):
        cb = make_cost_cb(v_idx)
        cb_idx = routing.RegisterTransitCallback(cb)
        routing.SetArcCostEvaluatorOfVehicle(cb_idx, v_idx)

    # ---- Distance dimension (for vehicle max range / global constraints) ----
    def dist_cb(from_index, to_index):
        i = manager.IndexToNode(from_index)
        j = manager.IndexToNode(to_index)
        return int(distance_km[i][j] * 1000)  # metres

    dist_cb_idx = routing.RegisterTransitCallback(dist_cb)
    routing.AddDimension(dist_cb_idx, 0, 500_000, True, "Distance")  # 500 km cap per vehicle

    # ---- Capacity dimension ----
    demands = [0] + [int(round(o["weight_kg"])) for o in orders]

    def demand_cb(from_index):
        i = manager.IndexToNode(from_index)
        return demands[i]

    demand_cb_idx = routing.RegisterUnaryTransitCallback(demand_cb)
    capacities = [int(v["capacity_kg"]) for v in vehicles]
    routing.AddDimensionWithVehicleCapacity(demand_cb_idx, 0, capacities, True, "Capacity")

    # ---- Stops dimension (max stops per vehicle) ----
    def stop_cb(from_index):
        i = manager.IndexToNode(from_index)
        return 0 if i == 0 else 1

    stop_cb_idx = routing.RegisterUnaryTransitCallback(stop_cb)
    max_stops = [int(v["max_stops"]) for v in vehicles]
    routing.AddDimensionWithVehicleCapacity(stop_cb_idx, 0, max_stops, True, "Stops")

    # ---- Time dimension (with service time + windows) ----
    service_time = [0] + [int(o["service_time_min"]) for o in orders]

    def time_cb(from_index, to_index):
        i = manager.IndexToNode(from_index)
        j = manager.IndexToNode(to_index)
        return int(round(time_min[i][j])) + service_time[i]

    time_cb_idx = routing.RegisterTransitCallback(time_cb)
    horizon = 24 * 60
    routing.AddDimension(time_cb_idx, 30, horizon, False, "Time")
    time_dim = routing.GetDimensionOrDie("Time")

    # Vehicle shift windows
    for v_idx, v in enumerate(vehicles):
        start = routing.Start(v_idx)
        end = routing.End(v_idx)
        time_dim.CumulVar(start).SetRange(int(v["shift_start"]), int(v["shift_end"]))
        time_dim.CumulVar(end).SetRange(int(v["shift_start"]), int(v["shift_end"]))

    # Order time windows (allow waiting => use SetRange on cumul)
    for i, o in enumerate(orders):
        node_idx = manager.NodeToIndex(i + 1)
        tw_s = int(o["time_window_start"])
        tw_e = int(o["time_window_end"])
        time_dim.CumulVar(node_idx).SetRange(tw_s, tw_e)

    # Allow drops with priority-aware penalties. Without disjunctions, OR-Tools requires
    # all orders to be visited which can render the problem infeasible.
    drop_penalty = {"express": 1_000_000, "urgent": 500_000, "normal": 80_000}
    for i, o in enumerate(orders):
        node_idx = manager.NodeToIndex(i + 1)
        routing.AddDisjunction([node_idx], drop_penalty[o["priority"]])

    # Search
    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    params.time_limit.seconds = max(1, int(time_limit_seconds))

    solution = routing.SolveWithParameters(params)

    routes: List[Dict[str, Any]] = []
    visited_nodes: set[int] = set()

    if solution is None:
        # Fall back to naive if solver couldn't find anything
        return naive_static_route(depot, vehicles, orders, distance_km, time_min)

    for v_idx, v in enumerate(vehicles):
        index = routing.Start(v_idx)
        sequence: List[Dict[str, Any]] = []
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            if node != 0:
                sequence.append(orders[node - 1])
                visited_nodes.add(node)
            index = solution.Value(routing.NextVar(index))
        routes.append(_build_stops_for_route(depot, v, sequence, distance_km, time_min, order_index_map))

    dropped = [o["order_id"] for i, o in enumerate(orders) if (i + 1) not in visited_nodes]
    return routes, dropped
