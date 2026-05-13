import React from "react";
import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts";
import type { ServiceMetrics } from "../types";
import { CEVA, fmtNum, minutesToHHMM } from "../theme";

interface Props { data: ServiceMetrics }

const PRIORITY_LABEL: Record<string, string> = {
  express: "Express",
  urgent: "Urgent",
  normal: "Normal",
};

const ServiceTab: React.FC<Props> = ({ data }) => {
  const onTime = Math.max(0, Math.min(100, data.on_time_pct));
  const gauge = [
    { name: "ot", value: onTime },
    { name: "rest", value: 100 - onTime },
  ];
  const color = onTime >= 95 ? CEVA.green : onTime >= 80 ? CEVA.amber : CEVA.red;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <div className="ceva-card p-5">
        <div className="text-sm font-bold text-ceva-black mb-2">On-Time Delivery</div>
        <div className="relative h-44">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={gauge}
                dataKey="value"
                startAngle={180}
                endAngle={0}
                innerRadius={55}
                outerRadius={80}
                stroke="none"
              >
                <Cell fill={color} />
                <Cell fill={CEVA.grayMid} />
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <div className="text-3xl font-extrabold" style={{ color }}>{fmtNum(onTime, 1)}%</div>
            <div className="text-[11px] text-ceva-grayText -mt-1">on-time</div>
          </div>
        </div>
      </div>

      <div className="ceva-card p-5 lg:col-span-2">
        <div className="text-sm font-bold text-ceva-black mb-3">SLA compliance by priority</div>
        <div className="space-y-3">
          {Object.entries(data.sla_compliance_pct_by_priority).map(([k, v]) => (
            <div key={k}>
              <div className="flex items-center justify-between text-sm mb-1">
                <span className="font-semibold">{PRIORITY_LABEL[k] || k}</span>
                <span className={v >= 95 ? "text-ceva-green font-bold" : v >= 80 ? "text-ceva-amber font-bold" : "text-ceva-red font-bold"}>
                  {fmtNum(v, 1)}%
                </span>
              </div>
              <div className="h-2 bg-ceva-grayMid rounded-md overflow-hidden">
                <div
                  className="h-full rounded-md"
                  style={{
                    width: `${Math.max(0, Math.min(100, v))}%`,
                    background: v >= 95 ? CEVA.green : v >= 80 ? CEVA.amber : CEVA.red,
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="ceva-card p-5 lg:col-span-3">
        <div className="text-sm font-bold text-ceva-black mb-2">
          Time-window violations <span className="text-ceva-grayText font-normal">({data.violations_count})</span>
        </div>
        {data.violations_count === 0 ? (
          <div className="text-xs text-ceva-grayText">No violations — every stop within its time window ✓</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-[11px] uppercase text-ceva-grayText border-b border-ceva-grayMid">
                <tr>
                  <th className="text-left py-2">Vehicle</th>
                  <th className="text-left py-2">Order</th>
                  <th className="text-left py-2">Customer</th>
                  <th className="text-left py-2">Priority</th>
                  <th className="text-right py-2">ETA</th>
                </tr>
              </thead>
              <tbody>
                {data.time_window_violations.slice(0, 50).map((v, i) => (
                  <tr key={i} className="border-b border-ceva-gray">
                    <td className="py-1.5 font-semibold">{v.vehicle_id}</td>
                    <td className="py-1.5">{v.order_id}</td>
                    <td className="py-1.5">{v.customer_name}</td>
                    <td className="py-1.5">
                      <span
                        className="ceva-pill"
                        style={{
                          background:
                            v.priority === "express" ? CEVA.red : v.priority === "urgent" ? CEVA.amber : CEVA.grayMid,
                          color: v.priority === "normal" ? CEVA.black : "white",
                        }}
                      >
                        {v.priority}
                      </span>
                    </td>
                    <td className="py-1.5 text-right tabular-nums">{minutesToHHMM(v.eta_min)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default ServiceTab;
