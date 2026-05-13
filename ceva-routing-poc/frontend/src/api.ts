import type { Depot, Vehicle, Order, ScenarioResult, Analytics, Carbon, Utilization } from "./types";

const BASE = "/api";

async function jsonReq<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${txt}`);
  }
  return res.json();
}

export const api = {
  data: () => jsonReq<{ depot: Depot; vehicles: Vehicle[]; orders: Order[] }>("/data"),
  baseline: () => jsonReq<ScenarioResult>("/baseline", { method: "POST" }),
  optimize: () => jsonReq<ScenarioResult>("/optimize", { method: "POST" }),
  reset: () => jsonReq<{ status: string }>("/reset", { method: "POST" }),
  analytics: () => jsonReq<Analytics>("/analytics"),
  carbon: () => jsonReq<Carbon>("/carbon"),
  utilization: () => jsonReq<Utilization>("/utilization"),
  disrupt: (type: "new_order" | "vehicle_breakdown" | "traffic_block", payload?: any) =>
    jsonReq<{ disruption: string; result: ScenarioResult; [k: string]: any }>("/disrupt", {
      method: "POST",
      body: JSON.stringify({ type, payload }),
    }),

  /** Stream chat. onDelta is called with each text chunk. */
  async chat(
    message: string,
    history: { role: string; content: string }[],
    scenario: string,
    onDelta: (delta: string) => void,
    onDone: () => void,
    onError: (err: string) => void
  ): Promise<void> {
    try {
      const res = await fetch(`${BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, history, scenario }),
      });
      if (!res.ok || !res.body) throw new Error(`${res.status} ${res.statusText}`);
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        const lines = buf.split("\n\n");
        buf = lines.pop() || "";
        for (const block of lines) {
          const line = block.trim();
          if (!line.startsWith("data:")) continue;
          const payload = line.slice(5).trim();
          if (!payload) continue;
          try {
            const obj = JSON.parse(payload);
            if (obj.delta) onDelta(obj.delta);
            if (obj.error) onError(obj.error);
            if (obj.done) onDone();
          } catch {
            // ignore parse errors on partial frames
          }
        }
      }
      onDone();
    } catch (e: any) {
      onError(e?.message || String(e));
    }
  },
};
