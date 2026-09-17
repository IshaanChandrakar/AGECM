import { useState } from "react";
import { api } from "../services/api";

const SCENARIOS = [
  "normal", "gradual_subsidence", "sudden_subsidence", "vibration_noise",
  "single_node_fault", "multi_node_correlated_event", "recovery",
];

export default function SimulationControls({ onReset }: { onReset: () => void }) {
  const [scenario, setScenario] = useState("gradual_subsidence");
  const [nodes, setNodes] = useState(6);
  const [runId, setRunId] = useState<number | null>(null);
  const [msg, setMsg] = useState("");

  const start = async () => {
    const r = await api.startRun(scenario, nodes);
    setRunId(r.runId);
    setMsg(`Run #${r.runId} recorded. Now launch the engine (see command below).`);
  };
  const stop = async () => {
    if (runId != null) await api.stopRun(runId);
    setMsg(`Run #${runId} stopped.`);
  };
  const reset = async () => {
    await api.reset();
    setRunId(null);
    setMsg("Live tables cleared.");
    onReset();
  };

  return (
    <div className="panel">
      <h2>Simulation</h2>
      <div className="controls">
        <label>Scenario
          <select value={scenario} onChange={(e) => setScenario(e.target.value)}>
            {SCENARIOS.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </label>
        <label>Nodes
          <input type="number" min={2} max={12} value={nodes}
                 onChange={(e) => setNodes(Number(e.target.value))} style={{ width: 70 }} />
        </label>
        <button className="primary" onClick={start}>Start run</button>
        <button onClick={stop} disabled={runId == null}>Stop</button>
        <button className="warn" onClick={reset}>Reset</button>
      </div>
      {msg && <div className="hint">{msg}</div>}
      <div className="hint">
        The dashboard records the run and clears data; the AGECM engine runs
        separately. Launch it with:
        <br />
        <code className="small">
          cd python-engine &amp;&amp; python main.py --scenario {scenario} --nodes {nodes} --backend http://localhost:8080
        </code>
      </div>
    </div>
  );
}
