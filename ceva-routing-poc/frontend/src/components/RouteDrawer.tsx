import React from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import type { Route } from "../types";
import { CEVA, fmtNum, fmtINR, minutesToHHMM } from "../theme";

interface Props {
  route: Route | null;
  onClose: () => void;
}

const RouteDrawer: React.FC<Props> = ({ route, onClose }) => {
  if (!route) return null;
  const isEv = route.fuel_type === "electric";
  const loadCurve = route.stops.map((s) => ({ seq: s.seq, load: s.cumulative_load_kg }));

  return (
    <div className="fixed inset-y-0 left-0 w-full sm:w-[460px] bg-white border-r border-ceva-grayMid shadow-cardLg z-40 transform transition-transform duration-300 flex flex-col">
      <div className="px-4 py-3 border-b border-ceva-grayMid flex items-center gap-2">
        <div className="text-sm font-bold text-ceva-black">
          {route.vehicle_id}
          <span className="ml-2 ceva-pill" style={{ background: isEv ? CEVA.green : CEVA.navy, color: "white" }}>
            {route.vehicle_type}{isEv ? " · EV" : ""}
          </span>
        </div>
        <button onClick={onClose} className="ml-auto ceva-btn-ghost text-xs px-2 py-1">Close</button>
      </div>

      <div className="p-4 space-y-4 overflow-y-auto">
        <div className="grid grid-cols-2 gap-3 text-sm">
          <Stat label="Driver" value={route.driver_name} />
          <Stat label="Fuel" value={route.fuel_type} />
          <Stat label="Stops" value={`${route.stops.length}`} />
          <Stat label="Load" value={`${fmtNum(route.total_load_kg, 1)} / ${route.capacity_kg} kg`} />
          <Stat label="Distance" value={`${fmtNum(route.total_distance_km, 2)} km`} />
          <Stat label="Time" value={`${Math.floor(route.total_time_min / 60)}h ${route.total_time_min % 60}m`} />
          <Stat label="CO₂e" value={`${fmtNum(route.co2_kg, 2)} kg`} />
          <Stat label="Cost" value={fmtINR(route.cost_inr)} />
          <Stat
            label="Green Score"
            value={`${route.green_score} / 100`}
            color={route.green_score >= 70 ? CEVA.green : route.green_score >= 40 ? CEVA.amber : CEVA.red}
          />
          <Stat label={isEv ? "Energy" : "Fuel"} value={`${fmtNum(route.fuel_or_energy, 2)} ${isEv ? "kWh" : "L"}`} />
        </div>

        {loadCurve.length > 0 && (
          <div className="ceva-card p-3">
            <div className="text-xs font-bold text-ceva-black mb-1">Cumulative Load (kg)</div>
            <div className="h-32">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={loadCurve}>
                  <CartesianGrid strokeDasharray="3 3" stroke={CEVA.grayMid} />
                  <XAxis dataKey="seq" tick={{ fontSize: 10, fill: CEVA.grayText }} />
                  <YAxis tick={{ fontSize: 10, fill: CEVA.grayText }} />
                  <Tooltip />
                  <Line type="monotone" dataKey="load" stroke={CEVA.red} strokeWidth={2} dot />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        <div className="ceva-card">
          <div className="text-xs font-bold text-ceva-black p-3 border-b border-ceva-grayMid">Stops</div>
          {route.stops.length === 0 ? (
            <div className="p-3 text-xs text-ceva-grayText">No stops assigned to this vehicle.</div>
          ) : (
            <ol className="divide-y divide-ceva-grayMid">
              {route.stops.map((s) => (
                <li key={s.order_id} className="px-3 py-2 text-sm flex items-start gap-2">
                  <div className="w-7 h-7 rounded-full bg-ceva-red text-white text-xs font-bold flex items-center justify-center flex-shrink-0 mt-0.5">
                    {s.seq}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-semibold truncate">{s.customer_name}</div>
                    <div className="text-xs text-ceva-grayText truncate">{s.address}</div>
                    <div className="text-[11px] mt-0.5 flex flex-wrap gap-x-3 gap-y-0.5">
                      <span>ETA <b>{minutesToHHMM(s.eta_min)}</b></span>
                      <span>{fmtNum(s.weight_kg, 1)} kg</span>
                      <span>cum {fmtNum(s.cumulative_distance_km, 1)} km</span>
                      <span
                        className={s.on_time ? "text-ceva-green font-bold" : "text-ceva-red font-bold"}
                      >
                        {s.on_time ? "on time" : "LATE"}
                      </span>
                    </div>
                  </div>
                </li>
              ))}
            </ol>
          )}
        </div>
      </div>
    </div>
  );
};

const Stat: React.FC<{ label: string; value: string; color?: string }> = ({ label, value, color }) => (
  <div className="bg-ceva-gray rounded-md px-3 py-2">
    <div className="text-[10px] uppercase tracking-wide text-ceva-grayText font-semibold">{label}</div>
    <div className="font-bold" style={color ? { color } : undefined}>{value}</div>
  </div>
);

export default RouteDrawer;
