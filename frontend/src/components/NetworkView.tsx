import type { Node, NetworkEvent } from "../types";

// Simple network view: each node -> its next hop toward the gateway, plus recent
// forwarding events. Static two-hop routing (dynamic routing is Review 3 work).
export default function NetworkView({ nodes, events }: { nodes: Node[]; events: NetworkEvent[] }) {
  const sorted = [...nodes].sort((a, b) => a.nodeId.localeCompare(b.nodeId));
  return (
    <div className="panel">
      <h2>Network (two-hop, static routes)</h2>
      <table>
        <thead><tr><th>Node</th><th>Route to gateway</th></tr></thead>
        <tbody>
          {sorted.map((n) => (
            <tr key={n.nodeId}>
              <td>{n.nodeId}</td>
              <td className="small">
                {n.nextHop === "gateway"
                  ? `${n.nodeId} → gateway`
                  : `${n.nodeId} → ${n.nextHop} → gateway`}
              </td>
            </tr>
          ))}
          {sorted.length === 0 && (
            <tr><td colSpan={2} className="muted">No nodes yet.</td></tr>
          )}
        </tbody>
      </table>
      <div className="hint">
        Recent forwards: {events.slice(0, 5).map((e) =>
          `${e.originNode}→${e.nextHop}${e.delivered ? "✓" : ""}`).join("  ") || "—"}
      </div>
    </div>
  );
}
