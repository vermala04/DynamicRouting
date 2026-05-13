"""Synthetic CEVA Delhi NCR last-mile dataset generator.

Run: python data_generator.py [--regenerate]
"""
from __future__ import annotations
import json
import math
import random
import argparse
from pathlib import Path
from typing import List, Dict, Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SEED = 42

DEPOT = {
    "depot_id": "DEP-DEL-01",
    "name": "CEVA Delhi NCR Hub",
    "address": "CEVA Logistics Hub, Mahipalpur, New Delhi 110037",
    "lat": 28.6139,
    "lon": 77.2090,
}

# Realistic Delhi-NCR delivery clusters: (area, lat, lon, pin)
NCR_AREAS = [
    ("Saket",                28.5245, 77.2066, "110017"),
    ("Dwarka Sec 12",        28.5921, 77.0460, "110078"),
    ("Rohini Sec 7",         28.7196, 77.1186, "110085"),
    ("Noida Sec 62",         28.6271, 77.3716, "201309"),
    ("Noida Sec 18",         28.5708, 77.3260, "201301"),
    ("Gurugram Cyber City",  28.4949, 77.0890, "122002"),
    ("Gurugram Sec 56",      28.4231, 77.1027, "122011"),
    ("Karol Bagh",           28.6519, 77.1909, "110005"),
    ("Lajpat Nagar",         28.5670, 77.2436, "110024"),
    ("Faridabad Sec 21",     28.4089, 77.3178, "121001"),
    ("Ghaziabad Vasundhara", 28.6644, 77.3729, "201012"),
    ("Vasant Kunj",          28.5200, 77.1588, "110070"),
    ("Mayur Vihar",          28.6086, 77.2949, "110091"),
    ("Pitampura",            28.7041, 77.1325, "110034"),
    ("Janakpuri",            28.6219, 77.0878, "110058"),
    ("Greater Kailash",      28.5494, 77.2425, "110048"),
    ("Connaught Place",      28.6315, 77.2167, "110001"),
    ("Mehrauli",             28.5239, 77.1855, "110030"),
]

INDIAN_FIRST_NAMES = [
    "Rahul", "Priya", "Amit", "Sneha", "Vikram", "Anjali", "Rohan", "Pooja",
    "Arjun", "Neha", "Karan", "Divya", "Sanjay", "Kavita", "Manish", "Ritu",
    "Suresh", "Meera", "Deepak", "Anita", "Nikhil", "Shreya", "Ravi", "Tanvi",
    "Aditya", "Isha", "Vivek", "Riya", "Ankit", "Pallavi",
]
INDIAN_LAST_NAMES = [
    "Sharma", "Patel", "Singh", "Verma", "Gupta", "Kumar", "Rao", "Iyer",
    "Reddy", "Nair", "Joshi", "Mehta", "Khanna", "Kapoor", "Malhotra",
    "Chopra", "Bansal", "Agarwal", "Saxena", "Mishra",
]

DRIVER_NAMES = [
    "Rakesh Yadav", "Suresh Kumar", "Mohan Lal", "Devendra Singh",
    "Bhupinder Negi", "Vinod Pandey", "Harish Chand", "Ramesh Bisht",
]


def _rand_jitter(lat: float, lon: float, km: float, rng: random.Random) -> tuple[float, float]:
    """Add a uniform jitter up to `km` kilometres around (lat, lon)."""
    # 1 deg lat ≈ 111 km
    dlat = (rng.uniform(-1, 1) * km) / 111.0
    dlon = (rng.uniform(-1, 1) * km) / (111.0 * math.cos(math.radians(lat)))
    return lat + dlat, lon + dlon


def build_vehicles() -> List[Dict[str, Any]]:
    return [
        # 3 small vans (diesel)
        {"vehicle_id": "V-101", "type": "small_van", "fuel_type": "diesel",
         "capacity_kg": 500, "max_stops": 12, "shift_start": 8 * 60, "shift_end": 18 * 60,
         "driver_name": "Rakesh Yadav", "base_cost_per_km": 14.0,
         "co2_grams_per_km": 250, "avg_speed_kmh": 26.0},
        {"vehicle_id": "V-102", "type": "small_van", "fuel_type": "diesel",
         "capacity_kg": 500, "max_stops": 12, "shift_start": 8 * 60, "shift_end": 18 * 60,
         "driver_name": "Suresh Kumar", "base_cost_per_km": 14.0,
         "co2_grams_per_km": 250, "avg_speed_kmh": 26.0},
        {"vehicle_id": "V-103", "type": "small_van", "fuel_type": "diesel",
         "capacity_kg": 500, "max_stops": 12, "shift_start": 9 * 60, "shift_end": 19 * 60,
         "driver_name": "Mohan Lal", "base_cost_per_km": 14.0,
         "co2_grams_per_km": 250, "avg_speed_kmh": 26.0},
        # 3 medium trucks (diesel)
        {"vehicle_id": "V-201", "type": "medium_truck", "fuel_type": "diesel",
         "capacity_kg": 1200, "max_stops": 18, "shift_start": 8 * 60, "shift_end": 18 * 60,
         "driver_name": "Devendra Singh", "base_cost_per_km": 22.0,
         "co2_grams_per_km": 320, "avg_speed_kmh": 24.0},
        {"vehicle_id": "V-202", "type": "medium_truck", "fuel_type": "diesel",
         "capacity_kg": 1200, "max_stops": 18, "shift_start": 8 * 60, "shift_end": 18 * 60,
         "driver_name": "Bhupinder Negi", "base_cost_per_km": 22.0,
         "co2_grams_per_km": 320, "avg_speed_kmh": 24.0},
        {"vehicle_id": "V-203", "type": "medium_truck", "fuel_type": "diesel",
         "capacity_kg": 1200, "max_stops": 18, "shift_start": 9 * 60, "shift_end": 19 * 60,
         "driver_name": "Vinod Pandey", "base_cost_per_km": 22.0,
         "co2_grams_per_km": 320, "avg_speed_kmh": 24.0},
        # 2 EVs
        {"vehicle_id": "V-301", "type": "ev", "fuel_type": "electric",
         "capacity_kg": 800, "max_stops": 14, "shift_start": 8 * 60, "shift_end": 18 * 60,
         "driver_name": "Harish Chand", "base_cost_per_km": 9.0,
         "co2_grams_per_km": 75, "avg_speed_kmh": 28.0},
        {"vehicle_id": "V-302", "type": "ev", "fuel_type": "electric",
         "capacity_kg": 800, "max_stops": 14, "shift_start": 9 * 60, "shift_end": 19 * 60,
         "driver_name": "Ramesh Bisht", "base_cost_per_km": 9.0,
         "co2_grams_per_km": 75, "avg_speed_kmh": 28.0},
    ]


def build_orders(n: int = 50, rng: random.Random | None = None) -> List[Dict[str, Any]]:
    rng = rng or random.Random(SEED)
    orders: List[Dict[str, Any]] = []
    for i in range(n):
        area_name, alat, alon, pin = rng.choice(NCR_AREAS)
        lat, lon = _rand_jitter(alat, alon, 1.5, rng)
        weight = round(rng.uniform(5, 200), 1)
        prio = rng.choices(
            ["normal", "urgent", "express"], weights=[0.7, 0.2, 0.1]
        )[0]
        # time windows
        start_hour = rng.choice([9, 10, 11, 12, 13, 14, 15])
        window_hours = rng.choice([2, 3, 4])
        tw_start = start_hour * 60
        tw_end = tw_start + window_hours * 60
        sla = {"normal": 240, "urgent": 120, "express": 90}[prio]
        service = rng.choice([5, 8, 10, 12])
        cust = f"{rng.choice(INDIAN_FIRST_NAMES)} {rng.choice(INDIAN_LAST_NAMES)}"
        orders.append({
            "order_id": f"ORD-{1000 + i}",
            "customer_name": cust,
            "address": f"{rng.randint(1, 250)}, {area_name}, Delhi NCR {pin}",
            "lat": round(lat, 6),
            "lon": round(lon, 6),
            "weight_kg": weight,
            "time_window_start": tw_start,
            "time_window_end": tw_end,
            "priority": prio,
            "service_time_min": service,
            "sla_minutes": sla,
        })
    return orders


def generate(regenerate: bool = False) -> Dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    depot_p = DATA_DIR / "depot.json"
    veh_p = DATA_DIR / "vehicles.json"
    ord_p = DATA_DIR / "synthetic_orders.json"

    if not regenerate and depot_p.exists() and veh_p.exists() and ord_p.exists():
        return {
            "depot": json.loads(depot_p.read_text()),
            "vehicles": json.loads(veh_p.read_text()),
            "orders": json.loads(ord_p.read_text()),
        }

    rng = random.Random(SEED)
    vehicles = build_vehicles()
    orders = build_orders(50, rng)

    depot_p.write_text(json.dumps(DEPOT, indent=2))
    veh_p.write_text(json.dumps(vehicles, indent=2))
    ord_p.write_text(json.dumps(orders, indent=2))
    return {"depot": DEPOT, "vehicles": vehicles, "orders": orders}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--regenerate", action="store_true")
    args = ap.parse_args()
    out = generate(regenerate=args.regenerate)
    print(f"Generated: 1 depot, {len(out['vehicles'])} vehicles, {len(out['orders'])} orders")
    print(f"Files in: {DATA_DIR}")
