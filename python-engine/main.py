"""
AGECM engine entry point.

Examples
--------
    python main.py --scenario gradual_subsidence --nodes 6
    python main.py --scenario single_node_fault --nodes 5 --duration 90
    python main.py --scenario gradual_subsidence --backend http://localhost:8080
    python main.py --scenario gradual_subsidence --mode packet_tracer

Runs fully offline by default (PURE_PYTHON_SIMULATION). --backend streams
telemetry to Spring Boot; --mode packet_tracer also writes the local file bridge.
"""

import argparse
import json

from config import MODE_PURE, MODE_PACKET_TRACER
from logger import EventLogger
from backend_client import BackendClient
from simulation.scenarios import SCENARIOS
from simulation.simulation_engine import SimulationEngine


def parse_args():
    p = argparse.ArgumentParser(description="AGECM edge-consensus mesh simulator")
    p.add_argument("--scenario", default="gradual_subsidence", choices=SCENARIOS)
    p.add_argument("--nodes", type=int, default=6)
    p.add_argument("--duration", type=float, default=120.0, help="simulated seconds")
    p.add_argument("--dt", type=float, default=1.0, help="base timestep (s)")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--mode", default=MODE_PURE,
                   choices=[MODE_PURE, MODE_PACKET_TRACER])
    p.add_argument("--backend", default=None,
                   help="Spring Boot base URL, e.g. http://localhost:8080")
    p.add_argument("--quiet", action="store_true", help="suppress per-event log lines")
    return p.parse_args()


def main():
    args = parse_args()
    logger = EventLogger(echo=not args.quiet)

    backend = None
    run_id = None
    if args.backend:
        backend = BackendClient(args.backend, logger=logger)
        run_id = backend.start_run(args.scenario, args.nodes)

    engine = SimulationEngine(
        scenario=args.scenario, node_count=args.nodes, duration=args.duration,
        dt=args.dt, seed=args.seed, logger=logger, mode=args.mode,
        backend_client=backend, run_id=run_id,
    )
    summary = engine.run()

    if backend and run_id is not None:
        backend.stop_run(run_id)

    print("\n=== AGECM run summary ===")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
