import React, { Suspense, lazy, useEffect, useMemo, useState } from "react";
import TopBar from "./components/TopBar";
import KpiStrip from "./components/KpiStrip";
import MapView from "./components/MapView";
import DisruptionPanel from "./components/DisruptionPanel";
import CoPilotChat from "./components/CoPilotChat";
import OptimizationReasoningPanel from "./components/OptimizationReasoningPanel";
import { api } from "./api";
import type { Depot, ScenarioResult } from "./types";

const UtilizationTab = lazy(() => import("./components/UtilizationTab"));
const CarbonTab = lazy(() => import("./components/CarbonTab"));
const FinancialTab = lazy(() => import("./components/FinancialTab"));
const ServiceTab = lazy(() => import("./components/ServiceTab"));
const ArchitectureTab = lazy(() => import("./components/ArchitectureTab"));
const RouteDrawer = lazy(() => import("./components/RouteDrawer"));

type TabKey = "utilization" | "carbon" | "financial" | "service" | "architecture";

const TABS: { key: TabKey; label: string }[] = [
  { key: "utilization", label: "Utilization" },
  { key: "carbon", label: "Carbon Footprint" },
  { key: "financial", label: "Financial Impact" },
  { key: "service", label: "Service Quality" },
  { key: "architecture", label: "Architecture & AI Governance" },
];

const App: React.FC = () => {
  const [depot, setDepot] = useState<Depot | null>(null);
  const [baseline, setBaseline] = useState<ScenarioResult | null>(null);
  const [optimized, setOptimized] = useState<ScenarioResult | null>(null);
  const [scenario, setScenario] = useState<"baseline" | "optimized">("optimized");
  const [view, setView] = useState<"single" | "side">("single");
  const [tab, setTab] = useState<TabKey>("utilization");
  const [chatOpen, setChatOpen] = useState(false);
  const [selectedVehicleId, setSelectedVehicleId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initial data load + first run
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        setLoading(true);
        const data = await api.data();
        if (cancelled) return;
        setDepot(data.depot);
        const b = await api.baseline();
        if (cancelled) return;
        setBaseline(b);
        const o = await api.optimize();
        if (cancelled) return;
        setOptimized(o);
      } catch (e: any) {
        setError(e?.message || String(e));
      } finally {
        setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const runOptimization = async () => {
    setLoading(true);
    setError(null);
    try {
      const b = await api.baseline();
      setBaseline(b);
      const o = await api.optimize();
      setOptimized(o);
      setScenario("optimized");
    } catch (e: any) {
      setError(e?.message || String(e));
    } finally {
      setLoading(false);
    }
  };

  const reset = async () => {
    setLoading(true);
    try {
      await api.reset();
      const b = await api.baseline();
      setBaseline(b);
      const o = await api.optimize();
      setOptimized(o);
      setSelectedVehicleId(null);
    } finally {
      setLoading(false);
    }
  };

  const inject = async (type: "new_order" | "vehicle_breakdown" | "traffic_block") => {
    setLoading(true);
    try {
      const res = await api.disrupt(type);
      setOptimized(res.result);
      setScenario("optimized");
    } catch (e: any) {
      setError(e?.message || String(e));
    } finally {
      setLoading(false);
    }
  };

  const current = scenario === "baseline" ? baseline : optimized;

  const selectedRoute = useMemo(() => {
    if (!selectedVehicleId || !current) return null;
    return current.routes.find((r) => r.vehicle_id === selectedVehicleId) || null;
  }, [selectedVehicleId, current]);

  return (
    <div className="min-h-screen flex flex-col">
      <TopBar
        scenario={scenario}
        onScenarioChange={setScenario}
        onOptimize={runOptimization}
        onReset={reset}
        loading={loading}
      />

      <main className="flex-1 max-w-[1600px] w-full mx-auto p-4 lg:p-6 space-y-4">
        {error && (
          <div className="ceva-card p-3 text-sm text-ceva-red">
            <b>Error:</b> {error}
          </div>
        )}

        <KpiStrip
          optimized={current?.kpis ?? null}
          baseline={baseline?.kpis ?? null}
        />

        {current?.analytics?.optimization_reasoning && (
          <OptimizationReasoningPanel
            reasoning={current.analytics.optimization_reasoning}
            scenario={scenario}
          />
        )}

        <DisruptionPanel onInject={inject} view={view} onViewChange={setView} loading={loading} />

        {depot && current && (
          <MapView
            depot={depot}
            routes={current.routes}
            baselineRoutes={baseline?.routes}
            view={view}
            onSelectRoute={(vid) => setSelectedVehicleId(vid)}
          />
        )}

        {/* Analytics tabs */}
        <div className="ceva-card">
          <div className="flex items-center gap-1 px-3 pt-2 border-b border-ceva-grayMid overflow-x-auto">
            {TABS.map((t) => (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className={`ceva-tab ${tab === t.key ? "ceva-tab-active" : ""}`}
              >
                {t.label}
              </button>
            ))}
            <div className="ml-auto pr-2 py-2 text-[11px] text-ceva-grayText">
              Showing: <b className="text-ceva-black">{scenario}</b>
            </div>
          </div>
          <div className="p-4">
            <Suspense fallback={<div className="text-sm text-ceva-grayText">Loading panel…</div>}>
              {!current?.analytics ? (
                <div className="text-sm text-ceva-grayText">Loading analytics…</div>
              ) : tab === "utilization" ? (
                <UtilizationTab data={current.analytics.utilization} onSelectVehicle={setSelectedVehicleId} />
              ) : tab === "architecture" ? (
                <ArchitectureTab />
              ) : tab === "carbon" ? (
                <CarbonTab
                  optimized={current.analytics.carbon}
                  baseline={baseline?.analytics?.carbon}
                />
              ) : tab === "financial" ? (
                <FinancialTab data={current.analytics.financial} />
              ) : (
                <ServiceTab data={current.analytics.service} />
              )}
            </Suspense>
          </div>
        </div>

        <footer className="text-center text-[11px] text-ceva-grayText py-6">
          CEVA Logistics France Control Tower POC | Confidential | © 2026
        </footer>
      </main>

      {/* Floating Co-Pilot button */}
      <button
        onClick={() => setChatOpen(true)}
        className="fixed bottom-6 right-6 z-40 ceva-btn-primary rounded-full !p-0 w-14 h-14 shadow-cardLg"
        aria-label="Open Co-Pilot"
        title="CEVA Co-Pilot"
      >
        <span className="text-lg font-extrabold">AI</span>
      </button>

      <CoPilotChat open={chatOpen} onClose={() => setChatOpen(false)} scenario={scenario} />

      <Suspense fallback={null}>
        {selectedRoute && (
          <RouteDrawer route={selectedRoute} onClose={() => setSelectedVehicleId(null)} />
        )}
      </Suspense>
    </div>
  );
};

export default App;
