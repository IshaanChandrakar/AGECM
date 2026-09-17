// Shared types mirroring the Spring Boot API responses.

export type State = "NORMAL" | "WARNING" | "CRITICAL" | "FAULT";

export interface Node {
  nodeId: string;
  state: State;
  tiltRate: number | null;
  displacementVelocity: number | null;
  vibration: number | null;
  consensusConfidence: number | null;
  samplingInterval: number | null;
  spreadingFactor: number | null;
  txPowerDbm: number | null;
  nextHop: string | null;
  lastSequence: number | null;
  lastSeen: string | null;
}

export interface Telemetry {
  id: number;
  nodeId: string;
  timestamp: string;
  tiltRate: number;
  displacementVelocity: number;
  vibration: number;
  state: State;
  consensusConfidence: number | null;
  sequence: number;
}

export interface Alert {
  id: number;
  nodeId: string;
  state: State;
  sequence: number | null;
  active: boolean;
  createdAt: string;
}

export interface ConsensusEvent {
  id: number;
  requestingNode: string;
  responders: string;
  repliesReceived: number;
  corroborating: number;
  confidence: number | null;
  sequence: number;
}

export interface NetworkEvent {
  id: number;
  relayNode: string;
  originNode: string;
  nextHop: string;
  hopCount: number;
  delivered: boolean;
  sequence: number;
}

export interface FrontEstimation {
  active: boolean;
  directionX?: number;
  directionY?: number;
  bearingDeg?: number;
  progressionSpeed?: number;
  supportingNodes?: string;
}
