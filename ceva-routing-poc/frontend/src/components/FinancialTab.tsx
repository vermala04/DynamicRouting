import React from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from "recharts";
import type { Financial } from "../types";
import { CEVA, fmtINR, fmtNum } from "../theme";

interface Props { data: Financial }

const FinancialTab: React.FC<Props> = ({ data }) => {
  const compare = [
    { name: "Baseline", value: data.cost_per_delivery_baseline ?? 0 },
    { name: "Optimized", value: data.cost_per_delivery_optimized ?? 0 },
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <div className="ceva-card p-5">
        <div className="text-xs uppercase tracking-wide font-semibold text-ceva-grayText">Daily Savings</div>
        <div className="text-3xl font-extrabold text-ceva-green mt-1">{fmtINR(data.daily_savings_inr)}</div>
        <div className="text-xs text-ceva-grayText mt-1">vs naive baseline (today)</div>
        <div className="border-t border-ceva-grayMid mt-4 pt-3 grid grid-cols-2 gap-3 text-sm">
          <div>
            <div className="text-[11px] text-ceva-grayText">Monthly</div>
            <div className="font-bold">{fmtINR(data.monthly_savings_inr)}</div>
          </div>
          <div>
            <div className="text-[11px] text-ceva-grayText">Annual</div>
            <div className="font-bold">{fmtINR(data.annual_savings_inr)}</div>
          </div>
        </div>
      </div>

      <div className="ceva-card p-5">
        <div className="text-xs uppercase tracking-wide font-semibold text-ceva-grayText">CO₂ Saved Annually</div>
        <div className="text-3xl font-extrabold text-ceva-green mt-1">{fmtNum(data.co2_saved_tonnes_annual, 1)} t</div>
        <div className="text-xs text-ceva-grayText mt-1">at current daily savings × 312 days</div>
        <div className="border-t border-ceva-grayMid mt-4 pt-3 text-sm">
          <div className="text-[11px] text-ceva-grayText">CO₂ saved today</div>
          <div className="font-bold">{fmtNum(data.co2_saved_kg_daily ?? 0, 1)} kg</div>
        </div>
      </div>

      <div className="ceva-card p-5 bg-gradient-to-br from-white to-ceva-gray">
        <div className="text-xs uppercase tracking-wide font-semibold text-ceva-grayText">ROI Extrapolation</div>
        <div className="mt-2 space-y-1.5 text-sm">
          <div className="flex justify-between">
            <span>Across {data.extrapolation.depots ?? 10} depots × 312 days</span>
          </div>
          <div className="text-2xl font-extrabold text-ceva-red">
            {fmtINR(data.extrapolation.annual_savings_inr ?? 0)}
            <span className="text-sm text-ceva-grayText font-semibold ml-1">
              (~€{fmtNum(((data.extrapolation.annual_savings_inr ?? 0) / 1_000_000), 2)}M)
            </span>
          </div>
          <div className="font-bold text-ceva-green">
            + {fmtNum(data.extrapolation.annual_co2_saved_tonnes ?? 0, 1)} t CO₂/yr
          </div>
        </div>
      </div>

      <div className="ceva-card p-5 lg:col-span-2">
        <div className="text-sm font-bold text-ceva-black mb-2">Cost per delivery</div>
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={compare}>
              <CartesianGrid strokeDasharray="3 3" stroke={CEVA.grayMid} />
              <XAxis dataKey="name" tick={{ fontSize: 12, fill: CEVA.black }} />
              <YAxis tick={{ fontSize: 11, fill: CEVA.grayText }} tickFormatter={(v) => `€${v}`} />
              <Tooltip formatter={(v: number) => fmtINR(v)} />
              <Bar dataKey="value" name="€ / delivery">
                {compare.map((d, i) => (
                  <Cell key={i} fill={i === 0 ? CEVA.red : CEVA.green} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="ceva-card p-5">
        <div className="text-sm font-bold text-ceva-black mb-2">Notes</div>
        <ul className="text-xs text-ceva-grayText space-y-1.5 list-disc pl-4">
          <li>Working days assumed: 26/month, 312/year.</li>
          <li>Extrapolation assumes uniform performance across 10 France regional depots.</li>
          <li>Carbon shadow price: €90/tonne (already priced into optimization cost).</li>
        </ul>
      </div>
    </div>
  );
};

export default FinancialTab;
