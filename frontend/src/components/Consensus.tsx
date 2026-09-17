import type { ConsensusEvent } from "../types";

export default function Consensus({ events }: { events: ConsensusEvent[] }) {
  const recent = events.slice(0, 12);
  return (
    <div className="panel">
      <h2>Consensus</h2>
      <table>
        <thead>
          <tr><th>Requester</th><th>Responders</th><th>Corrob.</th><th>C</th></tr>
        </thead>
        <tbody>
          {recent.map((e) => (
            <tr key={e.id}>
              <td>{e.requestingNode}</td>
              <td className="small">{e.responders || "—"}</td>
              <td className="num">{e.corroborating}/{e.repliesReceived}</td>
              <td className="num">{e.confidence == null ? "undef" : e.confidence.toFixed(2)}</td>
            </tr>
          ))}
          {recent.length === 0 && (
            <tr><td colSpan={4} className="muted">No consensus rounds yet.</td></tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
