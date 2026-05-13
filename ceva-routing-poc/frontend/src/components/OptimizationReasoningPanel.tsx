import React from "react";
import type { OptimizationReasoning } from "../types";
import { fmtINR, fmtNum } from "../theme";

interface Props {
  reasoning?: OptimizationReasoning;
  scenario: "baseline" | "optimized";
}

const LABELS: Record<string, string> = {
  distance: "Distance",
  cost: "Cost",
  co2: "CO₂",
  on_time: "On-time",
  drops: "Dropped",
};

const formatComparisonValue = (name: string, value: number | null, unit: string) => {
  if (value === null) return "—";
  if (name === "cost") return fmtINR(value);
  if (unit === "pct") return `${fmtNum(value, 1)}%`;
  return `${fmtNum(value, name === "drops" ? 0 : 1)} ${unit}`;
};

const ComparisonCard: React.FC<{ name: string; item: OptimizationReasoning["comparisons"][string] }> = ({ name, item }) => {
  const improved = item.improved === true;
  const worsened = item.improved === false && item.delta !== 0;
  const color = improved ? "text-ceva-green" : worsened ? "text-ceva-red" : "text-ceva-grayText";
  const sign = item.delta === null || item.delta === 0 ? "·" : item.delta < 0 ? "↓" : "↑";

  return (
    <div className="rounded-md border border-ceva-grayMid bg-white p-3">
      <div className="text-[11px] uppercase tracking-wide text-ceva-grayText font-semibold">{LABELS[name] ?? name}</div>
      <div className="mt-1 text-sm font-bold text-ceva-black">
        {formatComparisonValue(name, item.optimized, item.unit)}
      </div>
      <div className={`mt-1 text-xs font-semibold ${color}`}>
        {item.baseline === null ? "No baseline reference" : `${sign} ${formatComparisonValue(name, Math.abs(item.delta ?? 0), item.unit)} (${Math.abs(item.delta_pct ?? 0)}%) vs baseline`}
      </div>
    </div>
  );
};

const OptimizationReasoningPanel: React.FC<Props> = ({ reasoning, scenario }) => {
  if (!reasoning) return null;

  return (
    <section className="ceva-card overflow-hidden">
      <div className="px-4 py-3 border-b border-ceva-grayMid flex flex-col lg:flex-row lg:items-center gap-2">
        <div className="flex-1">
          <div className="text-[11px] uppercase tracking-wide text-ceva-grayText font-semibold">Optimization rationale</div>
          <h2 className="text-lg font-extrabold text-ceva-black">What changed and why this route plan was selected</h2>
        </div>
        <div className="flex flex-wrap gap-2">
          <span className="ceva-pill bg-ceva-navy text-white">{reasoning.optimizer}</span>
          <span className="ceva-pill bg-ceva-gray text-ceva-black border border-ceva-grayMid">Scenario: {scenario}</span>
        </div>
      </div>

      <div className="p-4 grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="xl:col-span-2 space-y-4">
          <div>
            <p className="text-sm text-ceva-black font-semibold">{reasoning.summary}</p>
            <p className="text-xs text-ceva-grayText mt-1"><b>Objective:</b> {reasoning.selected_objective}</p>
            {reasoning.baseline_reference && (
              <p className="text-xs text-ceva-grayText mt-1"><b>Reference:</b> {reasoning.baseline_reference}</p>
            )}
          </div>

          <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
            {Object.entries(reasoning.comparisons).map(([name, item]) => (
              <ComparisonCard key={name} name={name} item={item} />
            ))}
          </div>

          <div className="rounded-md bg-ceva-gray border border-ceva-grayMid p-3">
            <div className="text-sm font-bold text-ceva-black mb-2">Why optimized</div>
            <ul className="list-disc pl-5 space-y-1 text-sm text-ceva-black">
              {reasoning.why_optimized.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        </div>

        <div className="space-y-3">
          <div className="text-sm font-bold text-ceva-black">Route-level reasoning</div>
          <div className="space-y-2 max-h-[360px] overflow-y-auto pr-1">
            {reasoning.route_reasoning.map((route) => (
              <div key={route.vehicle_id} className="rounded-md border border-ceva-grayMid bg-white p-3">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <div className="text-sm font-bold text-ceva-black">{route.vehicle_id}</div>
                    <div className="text-[11px] text-ceva-grayText">{route.driver_name}</div>
                  </div>
                  <span className="ceva-pill bg-ceva-gray text-ceva-black border border-ceva-grayMid">Green {fmtNum(route.green_score, 1)}</span>
                </div>
                <div className="grid grid-cols-3 gap-2 mt-2 text-[11px] text-ceva-grayText">
                  <span>{route.stops} stops</span>
                  <span>{fmtNum(route.distance_km, 1)} km</span>
                  <span>{fmtNum(route.co2_kg, 1)} kg CO₂</span>
                </div>
                <ul className="list-disc pl-4 mt-2 space-y-1 text-xs text-ceva-black">
                  {route.reasons.map((reason) => (
                    <li key={reason}>{reason}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
          <div className="text-[11px] text-ceva-grayText">
            Generated from: {reasoning.generated_from.join(", ")}
          </div>
        </div>
      </div>
    </section>
  );
};

export default OptimizationReasoningPanel;
