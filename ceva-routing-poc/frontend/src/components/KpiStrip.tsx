import React from "react";
import { LineChart, Line, ResponsiveContainer } from "recharts";
import type { Kpis } from "../types";
import { CEVA, fmtINR, fmtNum } from "../theme";

interface Props {
  optimized: Kpis | null;
  baseline: Kpis | null;
}

interface CardSpec {
  title: string;
  value: string;
  delta?: { pct: number; goodWhenLower: boolean };
  spark: number[];
}

function delta(opt: number, base: number, goodWhenLower: boolean) {
  if (!base || !isFinite(base)) return undefined;
  const pct = ((opt - base) / base) * 100;
  return { pct: Number(pct.toFixed(1)), goodWhenLower };
}

const Card: React.FC<{ spec: CardSpec }> = ({ spec }) => {
  const d = spec.delta;
  let dColor = "text-ceva-grayText";
  let dArrow = "";
  if (d) {
    const isImproved = d.goodWhenLower ? d.pct < 0 : d.pct > 0;
    dColor = isImproved ? "text-ceva-green" : d.pct === 0 ? "text-ceva-grayText" : "text-ceva-red";
    dArrow = d.pct < 0 ? "↓" : d.pct > 0 ? "↑" : "·";
  }
  return (
    <div className="ceva-card p-4 flex flex-col gap-2 min-w-0">
      <div className="text-[11px] uppercase tracking-wide text-ceva-grayText font-semibold">{spec.title}</div>
      <div className="flex items-end justify-between gap-2">
        <div className="text-2xl font-bold text-ceva-black truncate">{spec.value}</div>
        {d !== undefined && (
          <div className={`text-xs font-bold ${dColor} whitespace-nowrap`}>
            {dArrow} {Math.abs(d.pct)}%
          </div>
        )}
      </div>
      <div className="h-7">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={spec.spark.map((v, i) => ({ i, v }))}>
            <Line
              type="monotone"
              dataKey="v"
              stroke={CEVA.red}
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

const sparkBetween = (a: number, b: number) => {
  // smooth fake sparkline from a→b for visual interest
  const n = 8;
  return Array.from({ length: n }, (_, i) => {
    const t = i / (n - 1);
    const noise = Math.sin(i * 1.3) * Math.abs(b - a) * 0.05;
    return a + (b - a) * t + noise;
  });
};

const KpiStrip: React.FC<Props> = ({ optimized, baseline }) => {
  if (!optimized) {
    return <div className="text-ceva-grayText text-sm">Loading KPIs…</div>;
  }
  const o = optimized;
  const b = baseline || optimized;

  const cards: CardSpec[] = [
    {
      title: "Total Distance",
      value: `${fmtNum(o.total_distance_km, 1)} km`,
      delta: delta(o.total_distance_km, b.total_distance_km, true),
      spark: sparkBetween(b.total_distance_km, o.total_distance_km),
    },
    {
      title: "Total Cost",
      value: fmtINR(o.total_cost_inr),
      delta: delta(o.total_cost_inr, b.total_cost_inr, true),
      spark: sparkBetween(b.total_cost_inr, o.total_cost_inr),
    },
    {
      title: "CO₂ Emitted",
      value: `${fmtNum(o.total_co2_kg, 1)} kg`,
      delta: delta(o.total_co2_kg, b.total_co2_kg, true),
      spark: sparkBetween(b.total_co2_kg, o.total_co2_kg),
    },
    {
      title: "Avg Vehicle Util.",
      value: `${fmtNum(o.avg_load_utilization_pct, 1)}%`,
      delta: delta(o.avg_load_utilization_pct, b.avg_load_utilization_pct, false),
      spark: sparkBetween(b.avg_load_utilization_pct, o.avg_load_utilization_pct),
    },
    {
      title: "On-Time Delivery",
      value: `${fmtNum(o.on_time_delivery_pct, 1)}%`,
      delta: delta(o.on_time_delivery_pct, b.on_time_delivery_pct, false),
      spark: sparkBetween(b.on_time_delivery_pct, o.on_time_delivery_pct),
    },
    {
      title: "Vehicles Used",
      value: `${o.vehicles_used} / ${o.vehicles_total}`,
      delta: delta(o.vehicles_used, b.vehicles_used, true),
      spark: sparkBetween(b.vehicles_used, o.vehicles_used),
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
      {cards.map((c) => (
        <Card key={c.title} spec={c} />
      ))}
    </div>
  );
};

export default KpiStrip;
