"""Synthetic CEVA France last-mile dataset generator.

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
    "depot_id": "DEP-FR-RSY-01",
    "name": "CEVA Roissy-CDG France Hub",
    "address": "14 Rue du Meunier, 95700 Roissy-en-France, France",
    "lat": 49.0097,
    "lon": 2.5479,
}

# Realistic France / Île-de-France delivery clusters: (area, lat, lon, postcode)
FRANCE_AREAS = [
    ("Paris 8e - Champs-Élysées", 48.8698, 2.3078, "75008"),
    ("Paris 12e - Bercy", 48.8386, 2.3822, "75012"),
    ("Paris 15e - Vaugirard", 48.8412, 2.3003, "75015"),
    ("La Défense", 48.8924, 2.2369, "92400"),
    ("Boulogne-Billancourt", 48.8397, 2.2399, "92100"),
    ("Saint-Denis", 48.9362, 2.3574, "93200"),
    ("Aubervilliers", 48.9146, 2.3822, "93300"),
    ("Bobigny", 48.9086, 2.4397, "93000"),
    ("Créteil", 48.7904, 2.4556, "94000"),
    ("Rungis MIN", 48.7537, 2.3500, "94150"),
    ("Massy", 48.7309, 2.2713, "91300"),
    ("Versailles", 48.8014, 2.1301, "78000"),
    ("Cergy", 49.0361, 2.0631, "95000"),
    ("Argenteuil", 48.9472, 2.2467, "95100"),
    ("Marne-la-Vallée", 48.8591, 2.5987, "77700"),
    ("Meaux", 48.9603, 2.8883, "77100"),
    ("Melun", 48.5393, 2.6607, "77000"),
    ("Compiègne", 49.4179, 2.8261, "60200"),
]

FRENCH_FIRST_NAMES = [
    "Camille", "Julien", "Sophie", "Nicolas", "Claire", "Thomas", "Élodie", "Antoine",
    "Léa", "Maxime", "Manon", "Hugo", "Chloé", "Lucas", "Inès", "Mathieu",
    "Sarah", "Romain", "Amandine", "Mehdi", "Nadia", "Yanis", "Océane", "Baptiste",
    "Karim", "Anaïs", "Louis", "Mélanie", "Arthur", "Fatima",
]
FRENCH_LAST_NAMES = [
    "Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit", "Durand",
    "Leroy", "Moreau", "Simon", "Laurent", "Lefebvre", "Michel", "Garcia",
    "David", "Bertrand", "Roux", "Vincent", "Fournier",
]

DRIVER_NAMES = [
    "Jean Martin", "Sabrina Laurent", "Karim Benali", "Luc Moreau",
    "Éric Dubois", "Nadia Robert", "Hugo Petit", "Mélanie Fournier",
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
         "driver_name": "Jean Martin", "base_cost_per_km": 0.72,
         "co2_grams_per_km": 210, "avg_speed_kmh": 34.0},
        {"vehicle_id": "V-102", "type": "small_van", "fuel_type": "diesel",
         "capacity_kg": 500, "max_stops": 12, "shift_start": 8 * 60, "shift_end": 18 * 60,
         "driver_name": "Sabrina Laurent", "base_cost_per_km": 0.72,
         "co2_grams_per_km": 210, "avg_speed_kmh": 34.0},
        {"vehicle_id": "V-103", "type": "small_van", "fuel_type": "diesel",
         "capacity_kg": 500, "max_stops": 12, "shift_start": 9 * 60, "shift_end": 19 * 60,
         "driver_name": "Karim Benali", "base_cost_per_km": 0.72,
         "co2_grams_per_km": 210, "avg_speed_kmh": 34.0},
        # 3 medium trucks (diesel)
        {"vehicle_id": "V-201", "type": "medium_truck", "fuel_type": "diesel",
         "capacity_kg": 1200, "max_stops": 18, "shift_start": 8 * 60, "shift_end": 18 * 60,
         "driver_name": "Luc Moreau", "base_cost_per_km": 1.15,
         "co2_grams_per_km": 520, "avg_speed_kmh": 32.0},
        {"vehicle_id": "V-202", "type": "medium_truck", "fuel_type": "diesel",
         "capacity_kg": 1200, "max_stops": 18, "shift_start": 8 * 60, "shift_end": 18 * 60,
         "driver_name": "Éric Dubois", "base_cost_per_km": 1.15,
         "co2_grams_per_km": 520, "avg_speed_kmh": 32.0},
        {"vehicle_id": "V-203", "type": "medium_truck", "fuel_type": "diesel",
         "capacity_kg": 1200, "max_stops": 18, "shift_start": 9 * 60, "shift_end": 19 * 60,
         "driver_name": "Nadia Robert", "base_cost_per_km": 1.15,
         "co2_grams_per_km": 520, "avg_speed_kmh": 32.0},
        # 2 EVs
        {"vehicle_id": "V-301", "type": "ev", "fuel_type": "electric",
         "capacity_kg": 800, "max_stops": 14, "shift_start": 8 * 60, "shift_end": 18 * 60,
         "driver_name": "Hugo Petit", "base_cost_per_km": 0.32,
         "co2_grams_per_km": 20, "avg_speed_kmh": 36.0},
        {"vehicle_id": "V-302", "type": "ev", "fuel_type": "electric",
         "capacity_kg": 800, "max_stops": 14, "shift_start": 9 * 60, "shift_end": 19 * 60,
         "driver_name": "Mélanie Fournier", "base_cost_per_km": 0.32,
         "co2_grams_per_km": 20, "avg_speed_kmh": 36.0},
    ]


def build_orders(n: int = 50, rng: random.Random | None = None) -> List[Dict[str, Any]]:
    rng = rng or random.Random(SEED)
    orders: List[Dict[str, Any]] = []
    for i in range(n):
        area_name, alat, alon, pin = rng.choice(FRANCE_AREAS)
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
        cust = f"{rng.choice(FRENCH_FIRST_NAMES)} {rng.choice(FRENCH_LAST_NAMES)}"
        orders.append({
            "order_id": f"ORD-{1000 + i}",
            "customer_name": cust,
            "address": f"{rng.randint(1, 250)} Rue de la Logistique, {area_name} {pin}, France",
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
