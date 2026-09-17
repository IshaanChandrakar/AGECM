"""
Adaptive radio configuration (SIMULATED).

Maps a node state to simulated LoRa-style parameters (spreading factor, Tx
power, routing mode) and to the adaptive sampling interval. These are SOFTWARE
VALUES only — no SX1276 hardware transmits at these settings.

  NORMAL   : low sampling, SF12, 14 dBm, neighbour-only routing
  WARNING  : higher sampling, intermediate radio, cluster/gateway reporting
  CRITICAL : 10 Hz, SF9, 20 dBm, multi-hop gateway forwarding, immediate alert
"""

from config import RADIO_CONFIG, SAMPLING_INTERVAL


class AdaptiveRadio:
    def __init__(self, node_id):
        self.node_id = node_id
        self.apply("NORMAL")

    def apply(self, state):
        cfg = RADIO_CONFIG.get(state, RADIO_CONFIG["NORMAL"])
        self.spreading_factor = cfg["spreading_factor"]
        self.tx_power_dbm = cfg["tx_power_dbm"]
        self.routing_mode = cfg["routing"]
        self.sampling_interval = SAMPLING_INTERVAL.get(state, 60.0)
        return self

    def as_dict(self):
        return {
            "spreading_factor": self.spreading_factor,
            "tx_power_dbm": self.tx_power_dbm,
            "routing_mode": self.routing_mode,
            "sampling_interval": self.sampling_interval,
        }
