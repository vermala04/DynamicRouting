// Shared types mirroring the backend Pydantic models.

export interface Depot {
  depot_id: string;
  name: string;
  address: string;
  lat: number;
  lon: number;
}

export interface Vehicle {
  vehicle_id: string;
  type: "small_van" | "medium_truck" | "ev";
  fuel_type: "diesel" | "electric";
  capacity_kg: number;
  max_stops: number;
  shift_start: number;
  shift_end: number;
  driver_name: string;
  base_cost_per_km: number;
  co2_grams_per_km: number;
  avg_speed_kmh: number;
}

export interface Order {
  order_id: string;
  customer_name: string;
  address: string;
  lat: number;
  lon: number;
  weight_kg: number;
  time_window_start: number;
  time_window_end: number;
  priority: "normal" | "urgent" | "express";
  service_time_min: number;
  sla_minutes: number;
}

export interface Stop {
  seq: number;
  order_id: string;
  customer_name: string;
  address: string;
  lat: number;
  lon: number;
  weight_kg: number;
  eta_min: number;
  cumulative_load_kg: number;
  cumulative_distance_km: number;
  priority: string;
  on_time: boolean;
}

export interface Route {
  vehicle_id: string;
  driver_name: string;
  vehicle_type: string;
  fuel_type: string;
  capacity_kg: number;
  stops: Stop[];
  total_distance_km: number;
  total_time_min: number;
  total_load_kg: number;
  load_utilization: number;
  time_utilization: number;
  stop_utilization: number;
  co2_kg: number;
  fuel_or_energy: number;
  cost_inr: number;
  green_score: number;
  polyline: [number, number][];
}

export interface Kpis {
  total_distance_km: number;
  total_time_min: number;
  total_co2_kg: number;
  total_cost_inr: number;
  total_load_kg: number;
  vehicles_total: number;
  vehicles_used: number;
  stops_served: number;
  orders_total: number;
  orders_dropped: number;
  drop_rate_pct: number;
  on_time_delivery_pct: number;
  avg_load_utilization_pct: number;
  avg_time_utilization_pct: number;
  avg_stop_utilization_pct: number;
  cost_per_delivery_inr: number;
  cost_per_km_inr: number;
  cost_per_kg_inr: number;
}

export interface UtilEntry {
  vehicle_id: string;
  driver_name: string;
  vehicle_type: string;
  fuel_type: string;
  load_pct: number;
  time_pct: number;
  stop_pct: number;
  stops: number;
  distance_km: number;
}
export interface Utilization {
  per_vehicle: UtilEntry[];
  idle: UtilEntry[];
  underutilized: UtilEntry[];
}

export interface CarbonByVehicle {
  vehicle_id: string;
  vehicle_type: string;
  fuel_type: string;
  co2_kg: number;
  distance_km: number;
  stops: number;
  green_score: number;
}
export interface Carbon {
  total_co2_kg: number;
  co2_per_delivery_kg: number;
  co2_per_km_g: number;
  co2_per_kg_shipped_g: number;
  by_type_kg: Record<string, number>;
  by_vehicle: CarbonByVehicle[];
  ev_delivery_pct: number;
  diesel_delivery_pct: number;
  ev_deliveries: number;
  diesel_deliveries: number;
  avg_green_score: number;
  trees_to_offset: number;
  car_km_equivalent: number;
  saved_vs_baseline_kg: number | null;
  saved_vs_baseline_pct: number | null;
  emission_factors_g_per_km: Record<string, number>;
}

export interface Financial {
  daily_savings_inr: number;
  monthly_savings_inr: number;
  annual_savings_inr: number;
  co2_saved_kg_daily?: number;
  co2_saved_tonnes_annual: number;
  cost_per_delivery_baseline?: number;
  cost_per_delivery_optimized?: number;
  extrapolation: {
    depots?: number;
    annual_savings_inr?: number;
    annual_savings_cr?: number;
    annual_co2_saved_tonnes?: number;
  };
}

export interface ServiceMetrics {
  on_time_pct: number;
  sla_compliance_pct_by_priority: Record<string, number>;
  time_window_violations: Array<{
    vehicle_id: string;
    order_id: string;
    customer_name: string;
    priority: string;
    eta_min: number;
  }>;
  violations_count: number;
}

export interface OptimizationComparison {
  optimized: number;
  baseline: number | null;
  delta: number | null;
  delta_pct: number | null;
  unit: string;
  improved: boolean | null;
}

export interface RouteReasoning {
  vehicle_id: string;
  driver_name: string;
  stops: number;
  distance_km: number;
  cost_eur: number;
  co2_kg: number;
  green_score: number;
  reasons: string[];
}

export interface OptimizationReasoning {
  summary: string;
  optimizer: string;
  selected_objective: string;
  baseline_reference: string | null;
  comparisons: Record<string, OptimizationComparison>;
  why_optimized: string[];
  route_reasoning: RouteReasoning[];
  dropped_order_ids: string[];
  generated_from: string[];
}

export interface Analytics {
  kpis: Kpis;
  utilization: Utilization;
  carbon: Carbon;
  financial: Financial;
  service: ServiceMetrics;
  optimization_reasoning: OptimizationReasoning;
}

export interface ScenarioResult {
  scenario: string;
  routes: Route[];
  dropped_orders: string[];
  kpis: Kpis;
  analytics: Analytics;
}
