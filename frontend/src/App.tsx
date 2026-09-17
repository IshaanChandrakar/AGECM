import { useEffect, useRef, useState } from "react";
import { api } from "./services/api";
import { connect } from "./services/ws";
import type {
  Node, Alert, ConsensusEvent, NetworkEvent, FrontEstimation, Telemetry,
} from "./types";
import StatusBar from "./components/StatusBar";
import NodeTable from "./components/NodeTable";
import Alerts from "./components/Alerts";
import Consensus from "./components/Consensus";
import NetworkView from "./components/NetworkView";
import FrontEstimationView from "./components/FrontEstimationView";
import SimulationControls from "./components/SimulationControls";
import SensorGraphs, { History } from "./components/SensorGraphs";

const HISTORY_LEN = 60;

export default function App() {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [consensus, setConsensus] = useState<ConsensusEvent[]>([]);
  const [network, setNetwork] = useState<NetworkEvent[]>([]);
  const [front, setFront] = useState<FrontEstimation>({ active: false });
  const [connected, setConnected] = useState(false);
  const [history, setHistory] = useState<History>({ tilt: [], disp: [], vib: [] });

  // Buffer WS telemetry between polls to build the mean sensor series.
  const buffer = useRef<Telemetry[]>([]);

  const refresh = async () => {
    try {
      const [n, a, c, net, f] = await Promise.all([
        api.nodes(), api.alerts(), api.consensus(), api.network(), api.front(),
      ]);
      setNodes(n); setAlerts(a); setConsensus(c); setNetwork(net); setFront(f);
    } catch { /* backend may be down; keep last state */ }
  };

  useEffect(() => {
    refresh();
    const client = connect({
      telemetry: (t: Telemetry) => { if (t && t.nodeId) buffer.current.push(t); },
      alerts: () => refresh(),
      front: (f: FrontEstimation) => setFront(f),
      onStatus: setConnected,
    });

    const poll = setInterval(refresh, 2000);

    // Every second, collapse buffered telemetry into one mean point per series.
    const tick = setInterval(() => {
      const b = buffer.current;
      buffer.current = [];
      if (b.length === 0) return;
      const mean = (sel: (t: Telemetry) => number) =>
        b.reduce((s, t) => s + (sel(t) || 0), 0) / b.length;
      setHistory((h) => ({
        tilt: [...h.tilt, mean((t) => t.tiltRate)].slice(-HISTORY_LEN),
        disp: [...h.disp, mean((t) => t.displacementVelocity)].slice(-HISTORY_LEN),
        vib: [...h.vib, mean((t) => t.vibration)].slice(-HISTORY_LEN),
      }));
    }, 1000);

    return () => { clearInterval(poll); clearInterval(tick); client.deactivate(); };
  }, []);

  const onReset = () => {
    setHistory({ tilt: [], disp: [], vib: [] });
    buffer.current = [];
    refresh();
  };

  return (
    <div className="app">
      <header className="top">
        <div>
          <h1>AGECM — Adaptive Geotechnical Edge-Consensus Mesh</h1>
          <div className="sub">
            Real-time mine subsidence monitoring · simulated sensors &amp; network · college prototype
          </div>
        </div>
      </header>

      <div className="grid">
        <StatusBar nodes={nodes} connected={connected} />
        <NodeTable nodes={nodes} />
        <SensorGraphs history={history} />
        <Alerts alerts={alerts} />
        <Consensus events={consensus} />
        <NetworkView nodes={nodes} events={network} />
        <FrontEstimationView front={front} />
        <SimulationControls onReset={onReset} />
      </div>
    </div>
  );
}
