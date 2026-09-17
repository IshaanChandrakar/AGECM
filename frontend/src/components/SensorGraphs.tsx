import Sparkline from "./Sparkline";

export interface History {
  tilt: number[];
  disp: number[];
  vib: number[];
}

// Aggregate sensor graphs: the mean series across all nodes over recent samples.
export default function SensorGraphs({ history }: { history: History }) {
  return (
    <div className="panel full">
      <h2>Sensor graphs (mesh mean, recent samples)</h2>
      <div className="legend">
        <span className="l-tilt">tilt rate dθ/dt</span>
        <span className="l-disp">disp. velocity dd/dt</span>
        <span className="l-vib">vibration A_vib</span>
      </div>
      <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
        <div>
          <div className="small muted">tilt rate</div>
          <Sparkline data={history.tilt} color="var(--critical)" />
        </div>
        <div>
          <div className="small muted">disp. velocity</div>
          <Sparkline data={history.disp} color="var(--accent)" />
        </div>
        <div>
          <div className="small muted">vibration</div>
          <Sparkline data={history.vib} color="var(--warning)" />
        </div>
      </div>
    </div>
  );
}
