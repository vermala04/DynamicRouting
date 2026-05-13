import React, { useState } from "react";

interface Props {
  onInject: (type: "new_order" | "vehicle_breakdown" | "traffic_block") => void;
  view: "single" | "side";
  onViewChange: (v: "single" | "side") => void;
  loading: boolean;
}

const OPTIONS = [
  { value: "new_order", label: "New Urgent Order" },
  { value: "vehicle_breakdown", label: "Vehicle Breakdown" },
  { value: "traffic_block", label: "Traffic Block on NH-48" },
] as const;

const DisruptionPanel: React.FC<Props> = ({ onInject, view, onViewChange, loading }) => {
  const [type, setType] = useState<typeof OPTIONS[number]["value"]>("new_order");
  return (
    <div className="ceva-card p-3 flex items-center gap-3 flex-wrap">
      <div className="text-sm font-bold text-ceva-black">Disruption Lab</div>
      <select
        value={type}
        onChange={(e) => setType(e.target.value as any)}
        className="border border-ceva-grayMid rounded-md px-2 py-1.5 text-sm bg-white"
      >
        {OPTIONS.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
      <button
        onClick={() => onInject(type)}
        disabled={loading}
        className="ceva-btn-primary text-sm py-1.5"
      >
        {loading ? "Re-optimizing…" : "Inject"}
      </button>

      <div className="ml-auto inline-flex rounded-md overflow-hidden border border-ceva-grayMid">
        {(["single", "side"] as const).map((v) => (
          <button
            key={v}
            onClick={() => onViewChange(v)}
            className={`px-3 py-1.5 text-xs font-semibold ${
              view === v ? "bg-ceva-navy text-white" : "bg-white text-ceva-black hover:bg-ceva-gray"
            }`}
          >
            {v === "single" ? "Single" : "Side-by-side"}
          </button>
        ))}
      </div>
    </div>
  );
};

export default DisruptionPanel;
