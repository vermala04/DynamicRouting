import React, { useEffect, useState } from "react";
import { api } from "../api";

interface Finding {
  area: string;
  finding: string;
  recommendation: string;
}

interface ArchitecturePayload {
  platform: string;
  region: string;
  control_tower: string;
  phase_1_findings: Finding[];
  target_architecture: string[];
  incremental_roadmap: string[];
  ai_governance: {
    selected_pattern_from_reference: string;
    mistral_model: string;
    allowed_responsibilities: string[];
    blocked_responsibilities: string[];
    rag_scope: string[];
  };
}

const ArchitectureTab: React.FC = () => {
  const [data, setData] = useState<ArchitecturePayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .architecture()
      .then((payload) => {
        if (!cancelled) setData(payload);
      })
      .catch((e: any) => {
        if (!cancelled) setError(e?.message || String(e));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (error) {
    return <div className="text-sm text-ceva-red">Architecture assessment unavailable: {error}</div>;
  }

  if (!data) {
    return <div className="text-sm text-ceva-grayText">Loading architecture assessment…</div>;
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
        <div className="rounded-md border border-ceva-grayMid p-3 bg-ceva-gray">
          <div className="text-[11px] uppercase tracking-wide text-ceva-grayText">Platform</div>
          <div className="text-sm font-bold text-ceva-black">{data.platform}</div>
        </div>
        <div className="rounded-md border border-ceva-grayMid p-3 bg-ceva-gray">
          <div className="text-[11px] uppercase tracking-wide text-ceva-grayText">Region</div>
          <div className="text-sm font-bold text-ceva-black">{data.region}</div>
        </div>
        <div className="rounded-md border border-ceva-grayMid p-3 bg-ceva-gray">
          <div className="text-[11px] uppercase tracking-wide text-ceva-grayText">AI pattern selected</div>
          <div className="text-sm font-bold text-ceva-red">{data.ai_governance.selected_pattern_from_reference}</div>
        </div>
      </div>

      <section>
        <h3 className="text-sm font-bold text-ceva-black mb-2">Phase 1 assessment</h3>
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-3">
          {data.phase_1_findings.map((item) => (
            <div key={item.area} className="rounded-md border border-ceva-grayMid p-3 bg-white">
              <div className="text-sm font-bold text-ceva-black">{item.area}</div>
              <p className="text-xs text-ceva-grayText mt-1">{item.finding}</p>
              <p className="text-xs text-ceva-black mt-2"><b>Incremental improvement:</b> {item.recommendation}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <div>
          <h3 className="text-sm font-bold text-ceva-black mb-2">Improved target architecture</h3>
          <ol className="space-y-2">
            {data.target_architecture.map((item, idx) => (
              <li key={item} className="flex gap-2 text-sm text-ceva-black">
                <span className="ceva-pill bg-ceva-navy text-white h-6 min-w-6 justify-center">{idx + 1}</span>
                <span>{item}</span>
              </li>
            ))}
          </ol>
        </div>
        <div>
          <h3 className="text-sm font-bold text-ceva-black mb-2">Mistral AI governance boundary</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="rounded-md border border-ceva-grayMid p-3">
              <div className="text-xs font-bold text-ceva-green mb-2">Allowed</div>
              <ul className="list-disc ml-4 text-xs text-ceva-black space-y-1">
                {data.ai_governance.allowed_responsibilities.map((item) => <li key={item}>{item}</li>)}
              </ul>
            </div>
            <div className="rounded-md border border-ceva-grayMid p-3">
              <div className="text-xs font-bold text-ceva-red mb-2">Blocked</div>
              <ul className="list-disc ml-4 text-xs text-ceva-black space-y-1">
                {data.ai_governance.blocked_responsibilities.map((item) => <li key={item}>{item}</li>)}
              </ul>
            </div>
          </div>
          <div className="mt-3 rounded-md border border-ceva-grayMid p-3 bg-ceva-gray">
            <div className="text-xs font-bold text-ceva-black mb-2">RAG retrieval scope</div>
            <div className="flex flex-wrap gap-1.5">
              {data.ai_governance.rag_scope.map((item) => (
                <span key={item} className="ceva-pill bg-white text-ceva-black border border-ceva-grayMid">{item}</span>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section>
        <h3 className="text-sm font-bold text-ceva-black mb-2">Incremental roadmap</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-2">
          {data.incremental_roadmap.map((item) => (
            <div key={item} className="rounded-md border border-ceva-grayMid p-3 text-xs text-ceva-black bg-white">
              {item}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};

export default ArchitectureTab;
