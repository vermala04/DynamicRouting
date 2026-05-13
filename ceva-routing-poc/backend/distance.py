"""Distance + travel-time matrix helpers.

Tries OSRM public demo for realistic road distance/time. Falls back to a
Haversine + average-speed estimator when OSRM is unreachable, so the POC
still runs offline.
"""
from __future__ import annotations
import math
import logging
from typing import List, Tuple, Optional

import httpx

OSRM_BASE = "https://router.project-osrm.org"
log = logging.getLogger("ceva.distance")


def haversine_km(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    """Great-circle distance in kilometres between (lat,lon) tuples."""
    R = 6371.0
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def _osrm_table(coords: List[Tuple[float, float]], timeout: float = 6.0) -> Optional[Tuple[List[List[float]], List[List[float]]]]:
    """Hit OSRM /table for distances+durations. Returns (dist_km, time_min) matrices or None."""
    if not coords:
        return None
    pts = ";".join(f"{lon:.6f},{lat:.6f}" for lat, lon in coords)
    url = f"{OSRM_BASE}/table/v1/driving/{pts}?annotations=distance,duration"
    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.get(url)
            r.raise_for_status()
            data = r.json()
        if data.get("code") != "Ok":
            return None
        dist_m = data["distances"]
        dur_s = data["durations"]
        n = len(coords)
        dist_km = [[(dist_m[i][j] or 0.0) / 1000.0 for j in range(n)] for i in range(n)]
        time_min = [[(dur_s[i][j] or 0.0) / 60.0 for j in range(n)] for i in range(n)]
        return dist_km, time_min
    except Exception as e:  # network / timeout / DNS
        log.warning("OSRM unavailable, falling back to Haversine: %s", e)
        return None


def build_matrices(
    coords: List[Tuple[float, float]],
    avg_speed_kmh: float = 28.0,
    use_osrm: bool = True,
) -> Tuple[List[List[float]], List[List[float]]]:
    """Return (distance_km, time_min) NxN matrices for the given coords."""
    if use_osrm:
        result = _osrm_table(coords)
        if result is not None:
            return result
    # Fallback: Haversine * 1.35 detour factor + constant avg speed
    n = len(coords)
    dist = [[0.0] * n for _ in range(n)]
    time = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            d = haversine_km(coords[i], coords[j]) * 1.35
            dist[i][j] = d
            time[i][j] = (d / max(avg_speed_kmh, 1.0)) * 60.0
    return dist, time
