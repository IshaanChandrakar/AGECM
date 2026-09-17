import type { Node } from "../types";

const f = (v: number | null, d = 3) => (v == null ? "—" : v.toFixed(d));

export default function NodeTable({ nodes }: { nodes: Node[] }) {
  const sorted = [...nodes].sort((a, b) => a.nodeId.localeCompare(b.nodeId));
  return (
    <div className="panel full">
      <h2>Node table</h2>
      <div style={{ overflowX: "auto" }}>
        <table>
          <thead>
            <tr>
              <th>Node</th><th>State</th><th>Tilt rate</th><th>Disp. vel.</th>
              <th>Vibration</th><th>Consensus C</th><th>Sampling</th>
              <th>SF</th><th>Tx dBm</th><th>Next hop</th><th>Seq</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((n) => (
              <tr key={n.nodeId}>
                <td>{n.nodeId}</td>
                <td><span className={`badge ${n.state}`}>{n.state}</span></td>
                <td className="num">{f(n.tiltRate)}</td>
                <td className="num">{f(n.displacementVelocity)}</td>
                <td className="num">{f(n.vibration)}</td>
                <td className="num">{n.consensusConfidence == null ? "undef" : f(n.consensusConfidence, 2)}</td>
                <td className="num">{f(n.samplingInterval, 1)}s</td>
                <td className="num">{n.spreadingFactor ?? "—"}</td>
                <td className="num">{n.txPowerDbm ?? "—"}</td>
                <td>{n.nextHop ?? "—"}</td>
                <td className="num">{n.lastSequence ?? "—"}</td>
              </tr>
            ))}
            {sorted.length === 0 && (
              <tr><td colSpan={11} className="muted">No nodes yet — start the Python engine.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
