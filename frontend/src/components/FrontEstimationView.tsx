import type { FrontEstimation } from "../types";

export default function FrontEstimationView({ front }: { front: FrontEstimation }) {
  return (
    <div className="panel">
      <h2>Front estimation (linear prototype)</h2>
      {front.active ? (
        <div>
          <div className="statusrow">
            <div className="stat">
              <div className="k">Bearing</div>
              <div className="v">{front.bearingDeg?.toFixed(0)}°</div>
            </div>
            <div className="stat">
              <div className="k">Speed</div>
              <div className="v">{front.progressionSpeed?.toFixed(2)}</div>
            </div>
          </div>
          <div className="hint">
            Direction vector: ({front.directionX?.toFixed(2)}, {front.directionY?.toFixed(2)})
          </div>
          <div className="hint">Supporting nodes: {front.supportingNodes || "—"}</div>
        </div>
      ) : (
        <div className="muted">
          Not active — needs ≥2 nodes escalating at different positions/times.
          <div className="hint">Graph-based prediction is Review 3 work.</div>
        </div>
      )}
    </div>
  );
}
