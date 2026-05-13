import React, { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { api } from "../api";

interface Props {
  open: boolean;
  onClose: () => void;
  scenario: "baseline" | "optimized";
}

interface Msg {
  role: "user" | "assistant";
  content: string;
  sources?: string[];
}

const SUGGESTED = [
  "Summarize today's optimization wins",
  "Which vehicles are underutilized?",
  "How much CO₂ did we save and what's the equivalent?",
  "What if I add 10 more orders to Noida?",
  "Which routes can I shift to EV to maximize green score?",
];

const extractSources = (text: string): string[] => {
  const m = text.match(/Sources?:\s*([^\n]+)/i);
  if (!m) return [];
  return m[1].split(/[,;]/).map((s) => s.trim()).filter(Boolean).slice(0, 8);
};

const CoPilotChat: React.FC<Props> = ({ open, onClose, scenario }) => {
  const [msgs, setMsgs] = useState<Msg[]>([
    {
      role: "assistant",
      content:
        "Hello — I'm the CEVA Logistics Co-Pilot, powered by Mistral AI. I can analyze today's routes, utilization, carbon, and savings. Try a suggested question below.",
    },
  ]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const scrollerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollerRef.current) {
      scrollerRef.current.scrollTop = scrollerRef.current.scrollHeight;
    }
  }, [msgs, streaming]);

  const send = async (text: string) => {
    const userMsg: Msg = { role: "user", content: text };
    const next: Msg[] = [...msgs, userMsg, { role: "assistant", content: "" }];
    setMsgs(next);
    setInput("");
    setStreaming(true);

    let acc = "";
    await api.chat(
      text,
      msgs.map((m) => ({ role: m.role, content: m.content })),
      scenario,
      (delta) => {
        acc += delta;
        setMsgs((curr) => {
          const copy = curr.slice();
          copy[copy.length - 1] = { role: "assistant", content: acc };
          return copy;
        });
      },
      () => {
        setStreaming(false);
        setMsgs((curr) => {
          const copy = curr.slice();
          const last = copy[copy.length - 1];
          copy[copy.length - 1] = { ...last, sources: extractSources(last.content) };
          return copy;
        });
      },
      (err) => {
        setStreaming(false);
        setMsgs((curr) => {
          const copy = curr.slice();
          copy[copy.length - 1] = { role: "assistant", content: `_Chat error:_ ${err}` };
          return copy;
        });
      }
    );
  };

  return (
    <div
      className={`fixed inset-y-0 right-0 w-full sm:w-[440px] bg-white border-l border-ceva-grayMid shadow-cardLg z-50 transform transition-transform duration-300 ${
        open ? "translate-x-0" : "translate-x-full"
      } flex flex-col`}
      aria-hidden={!open}
    >
      <div className="px-4 py-3 border-b border-ceva-grayMid flex items-center gap-2">
        <div className="w-8 h-8 rounded-md bg-ceva-red flex items-center justify-center text-white font-extrabold text-sm">AI</div>
        <div className="flex-1">
          <div className="text-sm font-bold text-ceva-black">CEVA Co-Pilot</div>
          <div className="text-[11px] text-ceva-grayText">Powered by Mistral AI · scenario: <b>{scenario}</b></div>
        </div>
        <button onClick={onClose} className="ceva-btn-ghost text-xs px-2 py-1">Close</button>
      </div>

      <div ref={scrollerRef} className="flex-1 overflow-y-auto p-4 space-y-3 bg-ceva-gray">
        {msgs.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[88%] rounded-md px-3 py-2 text-sm shadow-card chat-md ${
                m.role === "user"
                  ? "bg-ceva-red text-white"
                  : "bg-white text-ceva-black border border-ceva-grayMid"
              }`}
            >
              {m.role === "assistant" ? (
                <ReactMarkdown>{m.content || (streaming ? "…" : "")}</ReactMarkdown>
              ) : (
                <div className="whitespace-pre-wrap">{m.content}</div>
              )}
              {m.sources && m.sources.length > 0 && (
                <div className="mt-2 pt-2 border-t border-ceva-grayMid">
                  <div className="text-[10px] uppercase tracking-wide text-ceva-grayText mb-1">Cited KPIs</div>
                  <div className="flex flex-wrap gap-1">
                    {m.sources.map((s, j) => (
                      <span key={j} className="ceva-pill bg-ceva-gray text-ceva-black border border-ceva-grayMid">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="px-4 pt-2 border-t border-ceva-grayMid bg-white">
        <div className="flex flex-wrap gap-1.5 mb-2">
          {SUGGESTED.map((s) => (
            <button
              key={s}
              onClick={() => !streaming && send(s)}
              disabled={streaming}
              className="text-[11px] px-2 py-1 rounded-md border border-ceva-grayMid text-ceva-black bg-white hover:bg-ceva-gray disabled:opacity-50"
            >
              {s}
            </button>
          ))}
        </div>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (!input.trim() || streaming) return;
            send(input.trim());
          }}
          className="flex items-center gap-2 pb-3"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask the Co-Pilot…"
            className="flex-1 border border-ceva-grayMid rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ceva-red"
          />
          <button type="submit" disabled={streaming || !input.trim()} className="ceva-btn-primary text-sm py-2">
            Send
          </button>
        </form>
      </div>
    </div>
  );
};

export default CoPilotChat;
