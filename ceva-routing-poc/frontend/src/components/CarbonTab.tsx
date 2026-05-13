import React from "react";
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, Legend,
} from "recharts";
import type { Carbon } from "../types";
import { CEVA, fmtNum } from "../theme";

interface Props {
  optimized: Carbon;
  baseline?: Carbon | null;
}

const TYPE_COLORS: Record<string, string> = {
  ev: CEVA.green,
  small_van: CEVA.amber,
  medium_truck: CEVA.red,
};

const CarbonTab: React.FC<Props> = ({ optimized, baseline }) => {
  const saved = optimized.saved_vs_baseline_kg ?? 0;
  const savedPct = optimized.saved_vs_baseline_pct ?? 0;

  const donut = Object.entries(optimized.by_type_kg).map(([k, v]) => ({ name: k, value: v }));

  // Per-delivery comparison
  const baselinePerDel = baseline?.co2_per_delivery_kg ?? null;
  const compare = [
    { name: "Baseline", co2: baselinePerDel ?? 0 },
    { name: "Optimized", co2: optimized.co2_per_delivery_kg },
  ];

  // Green Score gauge — render as a half-circle via PieChart trick
  const score = Math.max(0, Math.min(100, optimized.avg_green_score));
  const gaugeData = [
    { name: "score", value: score },
    { name: "rest", value: 100 - score },
  ];
  const gaugeColor = score >= 70 ? CEVA.green : score >= 40 ? CEVA.amber : CEVA.red;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <div className="ceva-card p-5 flex flex-col gap-3">
        <div className="text-xs uppercase tracking-wide font-semibold text-ceva-grayText">CO₂ saved today</div>
        <div className="text-4xl font-extrabold text-ceva-green">
          {saved >= 0 ? "−" : "+"}{fmtNum(Math.abs(saved), 1)} kg
        </div>
        <div className="text-xs text-ceva-grayText">{savedPct >= 0 ? "Reduction" : "Increase"} of {Math.abs(savedPct)}% vs baseline</div>
        <div className="border-t border-ceva-grayMid mt-2 pt-3 grid grid-cols-2 gap-3 text-sm">
          <div>
            <div className="text-[11px] text-ceva-grayText">Total CO₂e</div>
            <div className="font-bold">{fmtNum(optimized.total_co2_kg, 1)} kg</div>
          </div>
          <div>
            <div className="text-[11px] text-ceva-grayText">Per delivery</div>
            <div className="font-bold">{fmtNum(optimized.co2_per_delivery_kg, 2)} kg</div>
          </div>
          <div>
            <div className="text-[11px] text-ceva-grayText">Per km</div>
            <div className="font-bold">{fmtNum(optimized.co2_per_km_g, 0)} g</div>
          </div>
          <div>
            <div className="text-[11px] text-ceva-grayText">Per kg shipped</div>
            <div className="font-bold">{fmtNum(optimized.co2_per_kg_shipped_g, 1)} g</div>
          </div>
        </div>
      </div>

      <div className="ceva-card p-5">
        <div className="text-sm font-bold text-ceva-black mb-2">Emissions by vehicle type</div>
        <div className="h-44">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={donut}
                dataKey="value"
                nameKey="name"
                innerRadius={45}
                outerRadius={70}
                paddingAngle={2}
              >
                {donut.map((d, i) => (
                  <Cell key={i} fill={TYPE_COLORS[d.name] || CEVA.navy} />
                ))}
              </Pie>
              <Tooltip />
              <Legend wrapperStyle={{ fontSize: 11 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="text-xs text-ceva-grayText mt-2">
          EV share of deliveries: <span className="font-bold text-ceva-green">{fmtNum(optimized.ev_delivery_pct, 1)}%</span>
          &nbsp;·&nbsp; Diesel: <span className="font-bold">{fmtNum(optimized.diesel_delivery_pct, 1)}%</span>
        </div>
      </div>

      <div className="ceva-card p-5">
        <div className="text-sm font-bold text-ceva-black mb-2">Avg Green Score</div>
        <div className="relative h-44">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={gaugeData}
                dataKey="value"
                startAngle={180}
                endAngle={0}
                innerRadius={55}
                outerRadius={80}
                stroke="none"
              >
                <Cell fill={gaugeColor} />
                <Cell fill={CEVA.grayMid} />
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <div className="text-3xl font-extrabold" style={{ color: gaugeColor }}>{fmtNum(score, 0)}</div>
            <div className="text-[11px] text-ceva-grayText -mt-1">/ 100</div>
          </div>
        </div>
        <div className="text-xs text-ceva-grayText text-center -mt-1">
          {score >= 70 ? "Excellent" : score >= 40 ? "Good — room to improve" : "Needs attention"}
        </div>
      </div>

      <div className="ceva-card p-5 lg:col-span-2">
        <div className="text-sm font-bold text-ceva-black mb-2">CO₂ per delivery (baseline vs optimized)</div>
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={compare}>
              <CartesianGrid strokeDasharray="3 3" stroke={CEVA.grayMid} />
              <XAxis dataKey="name" tick={{ fontSize: 12, fill: CEVA.black }} />
              <YAxis tick={{ fontSize: 11, fill: CEVA.grayText }} unit=" kg" />
              <Tooltip />
              <Bar dataKey="co2" name="kg CO₂ / delivery">
                {compare.map((d, i) => (
                  <Cell key={i} fill={i === 0 ? CEVA.red : CEVA.green} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="ceva-card p-5">
        <div className="text-sm font-bold text-ceva-black mb-2">Equivalencies</div>
        <ul className="space-y-3 text-sm">
          <li className="flex items-center gap-3">
            <span className="text-2xl">🌳</span>
            <div>
              <div className="font-bold">{fmtNum(optimized.trees_to_offset, 1)} trees</div>
              <div className="text-xs text-ceva-grayText">needed to absorb today's emissions in 1 year</div>
            </div>
          </li>
          <li className="flex items-center gap-3">
            <span className="text-2xl">🚗</span>
            <div>
              <div className="font-bold">{fmtNum(optimized.car_km_equivalent, 0)} km</div>
              <div className="text-xs text-ceva-grayText">equivalent passenger-car driving</div>
            </div>
          </li>
          <li className="flex items-center gap-3">
            <span className="text-2xl">⚡</span>
            <div>
              <div className="font-bold">{fmtNum(optimized.ev_delivery_pct, 1)}% zero-emission</div>
              <div className="text-xs text-ceva-grayText">share of deliveries done by EVs</div>
            </div>
          </li>
        </ul>
      </div>
    </div>
  );
};

export default CarbonTab;
