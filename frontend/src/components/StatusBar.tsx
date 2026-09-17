import type { Node } from "../types";

export default function StatusBar({ nodes, connected }: { nodes: Node[]; connected: boolean }) {
  const count = (s: string) => nodes.filter((n) => n.state === s).length;
  return (
    <div className="panel full">
      <h2>System status</h2>
      <div className="statusrow">
        <div className="stat"><div className="k">Nodes</div><div className="v">{nodes.length}</div></div>
        <div className="stat"><div className="k">Normal</div><div className="v" style={{ color: "var(--normal)" }}>{count("NORMAL")}</div></div>
        <div className="stat"><div className="k">Warning</div><div className="v" style={{ color: "var(--warning)" }}>{count("WARNING")}</div></div>
        <div className="stat"><div className="k">Critical</div><div className="v" style={{ color: "var(--critical)" }}>{count("CRITICAL")}</div></div>
        <div className="stat"><div className="k">Fault</div><div className="v" style={{ color: "var(--fault)" }}>{count("FAULT")}</div></div>
        <div className="stat">
          <div className="k">Live feed</div>
          <div className="v small">
            <span className={`dot ${connected ? "on" : "off"}`} />
            {connected ? "connected" : "offline"}
          </div>
        </div>
      </div>
    </div>
  );
}
