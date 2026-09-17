import type { Alert } from "../types";

export default function Alerts({ alerts }: { alerts: Alert[] }) {
  const recent = alerts.slice(0, 12);
  return (
    <div className="panel">
      <h2>Alerts</h2>
      <table>
        <thead><tr><th>Node</th><th>State</th><th>Seq</th><th>When</th></tr></thead>
        <tbody>
          {recent.map((a) => (
            <tr key={a.id}>
              <td>{a.nodeId}</td>
              <td><span className={`badge ${a.state}`}>{a.state}</span></td>
              <td className="num">{a.sequence ?? "—"}</td>
              <td className="small muted">{new Date(a.createdAt).toLocaleTimeString()}</td>
            </tr>
          ))}
          {recent.length === 0 && (
            <tr><td colSpan={4} className="muted">No alerts.</td></tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
