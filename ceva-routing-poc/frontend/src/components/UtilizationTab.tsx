import React from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid } from "recharts";
import type { Utilization } from "../types";
import { CEVA, ROUTE_COLORS, fmtNum } from "../theme";

interface Props {
  data: Utilization;
  onSelectVehicle: (vid: string) => void;
}

const UtilizationTab: React.FC<Props> = ({ data, onSelectVehicle }) => {
  const chartData = data.per_vehicle.map((v) => ({
    name: v.vehicle_id,
    Load: v.load_pct,
    Time: v.time_pct,
    Stops: v.stop_pct,
  }));

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <div className="ceva-card p-4 lg:col-span-2">
        <div className="text-sm font-bold text-ceva-black mb-3">Per-vehicle Utilization (%)</div>
        <div style={{ height: 60 + 36 * Math.max(chartData.length, 1) }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} layout="vertical" margin={{ left: 10, right: 30 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={CEVA.grayMid} />
              <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11, fill: CEVA.grayText }} />
              <YAxis type="category" dataKey="name" width={70} tick={{ fontSize: 11, fill: CEVA.black, fontWeight: 600 }} />
              <Tooltip />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="Load" fill={CEVA.red} />
              <Bar dataKey="Time" fill={CEVA.navy} />
              <Bar dataKey="Stops" fill={CEVA.amber} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="flex flex-col gap-4">
        <div className="ceva-card p-4">
          <div className="text-sm font-bold text-ceva-black mb-2">Idle Vehicles</div>
          {data.idle.length === 0 ? (
            <div className="text-xs text-ceva-grayText">All vehicles dispatched ✓</div>
          ) : (
            <ul className="space-y-1">
              {data.idle.map((v) => (
                <li key={v.vehicle_id} className="flex items-center justify-between text-sm">
                  <button
                    className="font-semibold text-ceva-red hover:underline"
                    onClick={() => onSelectVehicle(v.vehicle_id)}
                  >
                    {v.vehicle_id}
                  </button>
                  <span className="text-xs text-ceva-grayText">{v.driver_name} · {v.vehicle_type}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="ceva-card p-4">
          <div className="text-sm font-bold text-ceva-black mb-2">Underutilized (load &lt; 50% & time &lt; 50%)</div>
          {data.underutilized.length === 0 ? (
            <div className="text-xs text-ceva-grayText">No underutilized vehicles ✓</div>
          ) : (
            <ul className="space-y-1.5">
              {data.underutilized.map((v) => (
                <li key={v.vehicle_id} className="flex items-center justify-between gap-2 text-sm">
                  <button
                    className="font-semibold text-ceva-amber hover:underline"
                    onClick={() => onSelectVehicle(v.vehicle_id)}
                  >
                    {v.vehicle_id}
                  </button>
                  <span className="text-xs text-ceva-grayText flex-1 truncate">{v.driver_name}</span>
                  <span className="text-xs">L {fmtNum(v.load_pct, 0)}% · T {fmtNum(v.time_pct, 0)}%</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="ceva-card p-4">
          <div className="text-sm font-bold text-ceva-black mb-2">Active Fleet</div>
          <ul className="space-y-1">
            {data.per_vehicle.map((v, i) => (
              <li key={v.vehicle_id} className="flex items-center justify-between text-sm">
                <span className="flex items-center gap-2">
                  <span
                    className="w-3 h-3 rounded-sm"
                    style={{ background: ROUTE_COLORS[i % ROUTE_COLORS.length] }}
                  />
                  <button
                    className="font-semibold text-ceva-black hover:underline"
                    onClick={() => onSelectVehicle(v.vehicle_id)}
                  >
                    {v.vehicle_id}
                  </button>
                  {v.fuel_type === "electric" && <span className="ceva-pill bg-ceva-green text-white">EV</span>}
                </span>
                <span className="text-xs text-ceva-grayText">{v.stops} stops · {fmtNum(v.distance_km, 1)} km</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};

export default UtilizationTab;
