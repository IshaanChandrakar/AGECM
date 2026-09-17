// Thin REST client for the AGECM backend. Uses the Vite proxy (/api -> :8080).

import type {
  Node, Alert, ConsensusEvent, NetworkEvent, FrontEstimation,
} from "../types";

async function get<T>(path: string): Promise<T> {
  const r = await fetch(path);
  if (!r.ok) throw new Error(`${path} -> ${r.status}`);
  return r.json();
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const r = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : "{}",
  });
  if (!r.ok) throw new Error(`${path} -> ${r.status}`);
  return r.json();
}

export const api = {
  health: () => get<{ status: string }>("/api/health"),
  nodes: () => get<Node[]>("/api/nodes"),
  alerts: () => get<Alert[]>("/api/alerts"),
  consensus: () => get<ConsensusEvent[]>("/api/consensus"),
  network: () => get<NetworkEvent[]>("/api/network"),
  front: () => get<FrontEstimation>("/api/front-estimation"),
  startRun: (scenario: string, nodeCount: number) =>
    post<{ runId: number }>("/api/simulation/start", { scenario, nodeCount }),
  stopRun: (runId: number) => post("/api/simulation/stop", { runId }),
  reset: () => post("/api/simulation/reset"),
};
