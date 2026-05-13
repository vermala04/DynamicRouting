"""Carbon accounting constants & helpers for the CEVA France POC.

Emission factors are operational planning assumptions for a French last-mile fleet.
They should be calibrated with CEVA telematics and carrier sustainability data before
production use.
"""
from __future__ import annotations
import os
from typing import Dict

# grams CO2e per km
EMISSION_FACTORS_G_PER_KM: Dict[str, int] = {
    "small_van": 210,       # diesel LCV, France urban duty cycle
    "medium_truck": 520,    # diesel MCV / rigid truck
    "ev": 20,               # France low-carbon grid planning factor
}

# Carbon shadow price for multi-objective optimization (€ per tonne).
# Keep the variable name stable to avoid changing optimizer API contracts.
CARBON_PRICE_INR_PER_TONNE = float(os.getenv("CARBON_PRICE_EUR_PER_TONNE", "90"))

# Equivalency constants
TREE_KG_CO2_PER_YEAR = 21.0      # one mature tree absorbs ~21 kg CO2/yr
CAR_G_CO2_PER_KM = 120.0         # avg passenger car planning factor, France g CO2/km

# Energy/fuel reference numbers (for "fuel used" reporting)
DIESEL_KM_PER_LITRE = {"small_van": 9.0, "medium_truck": 5.0}
EV_KWH_PER_KM = 0.22             # ~220 Wh/km for a small EV van


def co2_kg_for_route(vehicle_type: str, distance_km: float) -> float:
    """Return route CO2e in kilograms."""
    g_per_km = EMISSION_FACTORS_G_PER_KM.get(vehicle_type, 250)
    return (g_per_km * distance_km) / 1000.0


def fuel_or_energy_for_route(vehicle_type: str, distance_km: float) -> float:
    """Litres of diesel or kWh of electricity used on this route."""
    if vehicle_type == "ev":
        return distance_km * EV_KWH_PER_KM
    kpl = DIESEL_KM_PER_LITRE.get(vehicle_type, 7.0)
    return distance_km / max(kpl, 0.1)


def trees_equivalent(co2_kg: float) -> float:
    """How many mature trees would absorb this CO2 in one year."""
    return co2_kg / TREE_KG_CO2_PER_YEAR if co2_kg > 0 else 0.0


def car_km_equivalent(co2_kg: float) -> float:
    """Equivalent km of average car driving."""
    return (co2_kg * 1000.0) / CAR_G_CO2_PER_KM if co2_kg > 0 else 0.0


def green_score(vehicle_type: str, co2_kg: float, distance_km: float) -> float:
    """0–100 score where higher is greener.

    Combines fuel type and per-km emission intensity. EVs get a base boost.
    """
    if distance_km <= 0:
        return 100.0
    intensity = co2_kg * 1000.0 / distance_km  # g/km
    # Map 0 g/km → 100, 320 g/km → 0
    raw = max(0.0, 100.0 - (intensity / 320.0) * 100.0)
    if vehicle_type == "ev":
        raw = min(100.0, raw + 10.0)
    return round(raw, 1)
