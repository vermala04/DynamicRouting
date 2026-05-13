import React from "react";

interface Props {
  scenario: "baseline" | "optimized";
  onScenarioChange: (s: "baseline" | "optimized") => void;
  onOptimize: () => void;
  onReset: () => void;
  loading: boolean;
}

const TopBar: React.FC<Props> = ({ scenario, onScenarioChange, onOptimize, onReset, loading }) => {
  return (
    <header className="bg-white border-b border-ceva-grayMid sticky top-0 z-30 shadow-card">
      <div className="max-w-[1600px] mx-auto px-6 py-3 flex items-center gap-6 flex-wrap">
        <div className="flex items-center gap-3">
          <div className="text-3xl font-extrabold tracking-tight text-ceva-red leading-none">CEVA</div>
          <div className="hidden md:flex flex-col leading-tight">
            <span className="text-sm font-bold text-ceva-black">Dynamic Routing Intelligence</span>
            <span className="text-[11px] text-ceva-grayText">France last-mile control tower · Roissy-CDG</span>
          </div>
        </div>

        <div className="ml-auto flex items-center gap-2 flex-wrap">
          <div className="inline-flex rounded-md overflow-hidden border border-ceva-grayMid">
            {(["baseline", "optimized"] as const).map((s) => (
              <button
                key={s}
                onClick={() => onScenarioChange(s)}
                className={`px-3 py-1.5 text-sm font-semibold transition-colors ${
                  scenario === s
                    ? "bg-ceva-black text-white"
                    : "bg-white text-ceva-black hover:bg-ceva-gray"
                }`}
              >
                {s === "baseline" ? "Baseline" : "Optimized"}
              </button>
            ))}
          </div>

          <button onClick={onOptimize} disabled={loading} className="ceva-btn-primary">
            {loading ? "Optimizing…" : "Run Optimization"}
          </button>
          <button onClick={onReset} className="ceva-btn-ghost">Reset</button>

          <span className="ceva-pill bg-ceva-navy text-white">
            <span className="w-1.5 h-1.5 rounded-full bg-ceva-amber inline-block" />
            Mistral AI · RAG Pipeline
          </span>
        </div>
      </div>
    </header>
  );
};

export default TopBar;
