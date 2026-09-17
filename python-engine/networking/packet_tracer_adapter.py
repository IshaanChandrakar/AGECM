"""
Packet Tracer integration adapter (local JSON/file bridge).

Cisco Packet Tracer cannot be assumed to talk to localhost freely, so the
GUARANTEED integration path is a local file bridge:

    bridge/incoming   <- telemetry JSON produced for / by the network layer
    bridge/outgoing   -> AGECM CONTROL responses for the network layer
    bridge/processed  <- incoming files moved here after handling

Duplicate processing is prevented with a (node_id, sequence) processed set and
by moving handled files into bridge/processed. The rest of the system works
whether or not Packet Tracer is running — this adapter is optional.
"""

import json
import os
import shutil


class PacketTracerAdapter:
    def __init__(self, incoming, outgoing, processed, logger=None):
        self.incoming = incoming
        self.outgoing = outgoing
        self.processed = processed
        self._log = logger
        self._seen = set()      # (node_id, sequence)
        for d in (incoming, outgoing, processed):
            os.makedirs(d, exist_ok=True)

    def write_telemetry(self, packet):
        """Drop one telemetry packet into bridge/incoming as JSON."""
        fname = f"{packet.node_id}_{packet.sequence}.json"
        path = os.path.join(self.incoming, fname)
        with open(path, "w") as f:
            json.dump(packet.to_dict(), f, indent=2)
        return path

    def read_incoming(self):
        """
        Read and return new telemetry dicts from bridge/incoming, skipping any
        already processed (by node_id+sequence). Handled files are moved to
        bridge/processed to avoid reprocessing.
        """
        out = []
        for name in sorted(os.listdir(self.incoming)):
            if not name.endswith(".json"):
                continue
            path = os.path.join(self.incoming, name)
            try:
                with open(path) as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError):
                continue
            key = (data.get("node_id"), data.get("sequence"))
            if key in self._seen:
                continue
            self._seen.add(key)
            out.append(data)
            shutil.move(path, os.path.join(self.processed, name))
            if self._log:
                self._log.bridge_read(data.get("node_id"), data.get("sequence"))
        return out

    def write_control(self, node_id, sequence, control):
        """Place an AGECM CONTROL response into bridge/outgoing."""
        payload = {"packet_type": "CONTROL", "node_id": node_id,
                   "sequence": sequence, **control}
        path = os.path.join(self.outgoing, f"control_{node_id}_{sequence}.json")
        with open(path, "w") as f:
            json.dump(payload, f, indent=2)
        return path
