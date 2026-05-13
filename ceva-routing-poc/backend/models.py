"""Pydantic models for CEVA Dynamic Routing POC."""
from __future__ import annotations
from typing import List, Optional, Literal, Any, Dict
from pydantic import BaseModel, Field


# ---------- Domain ----------
class Depot(BaseModel):
    depot_id: str
    name: str
    address: str
    lat: float
    lon: float


class Vehicle(BaseModel):
    vehicle_id: str
    type: Literal["small_van", "medium_truck", "ev"]
    fuel_type: Literal["diesel", "electric"]
    capacity_kg: int
    max_stops: int
    shift_start: int  # minutes from 00:00
    shift_end: int
    driver_name: str
    base_cost_per_km: float  # EUR; field name kept stable for API compatibility
    co2_grams_per_km: int
    avg_speed_kmh: float


class Order(BaseModel):
    order_id: str
    customer_name: str
    address: str
    lat: float
    lon: float
    weight_kg: float
    time_window_start: int  # minutes from 00:00
    time_window_end: int
    priority: Literal["normal", "urgent", "express"]
    service_time_min: int
    sla_minutes: int


class Stop(BaseModel):
    seq: int
    order_id: str
    customer_name: str
    address: str
    lat: float
    lon: float
    weight_kg: float
    eta_min: int  # minutes from 00:00
    cumulative_load_kg: float
    cumulative_distance_km: float
    priority: str
    on_time: bool


class Route(BaseModel):
    vehicle_id: str
    driver_name: str
    vehicle_type: str
    fuel_type: str
    capacity_kg: int
    stops: List[Stop]
    total_distance_km: float
    total_time_min: int
    total_load_kg: float
    load_utilization: float  # 0..1
    time_utilization: float  # 0..1
    stop_utilization: float  # 0..1
    co2_kg: float
    fuel_or_energy: float
    cost_inr: float
    green_score: float  # 0..100
    polyline: List[List[float]]  # [[lat, lon], ...]


class ScenarioResult(BaseModel):
    scenario: str  # "baseline" | "optimized"
    routes: List[Route]
    dropped_orders: List[str]
    kpis: Dict[str, Any]
    analytics: Dict[str, Any]


class DisruptionPayload(BaseModel):
    type: Literal["new_order", "vehicle_breakdown", "traffic_block"]
    payload: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = Field(default_factory=list)
    scenario: Optional[str] = "optimized"
