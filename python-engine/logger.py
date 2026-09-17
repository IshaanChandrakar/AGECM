"""
Readable AGECM event logger.

Produces the demonstration-style log lines described in the report, e.g.

    [12.42] node_03 NORMAL -> WARNING
    [12.45] node_03 CONSENSUS_REQUEST seq=81
    [12.71] node_02 CONSENSUS_REPLY corroborated=true
    [12.73] node_03 consensus C=1.00
    [12.74] node_03 WARNING -> CRITICAL
    [12.75] node_03 sampling=10Hz SF=9 Tx=20dBm
    [12.76] gateway received ALERT from node_03

Lines print to stdout and are kept in memory for tests / evidence.
"""


class EventLogger:
    def __init__(self, echo=True):
        self.echo = echo
        self.lines = []

    def _emit(self, line):
        self.lines.append(line)
        if self.echo:
            print(line)

    @staticmethod
    def _ts(t):
        return f"[{t:6.2f}]"

    def state_change(self, node_id, old, new, t, c=None):
        self._emit(f"{self._ts(t)} {node_id} {old} -> {new}")

    def consensus_request(self, node_id, seq, t):
        self._emit(f"{self._ts(t)} {node_id} CONSENSUS_REQUEST seq={seq}")

    def consensus_reply(self, req_node, resp_node, corroborated, seq, t):
        val = "true" if corroborated else "false"
        self._emit(f"{self._ts(t)} {resp_node} CONSENSUS_REPLY corroborated={val}")

    def consensus_timeout(self, req_node, resp_node, seq, t):
        self._emit(f"{self._ts(t)} {resp_node} CONSENSUS_TIMEOUT seq={seq}")

    def consensus_result(self, node_id, c, seq, t):
        cval = "undefined" if c is None else f"{c:.2f}"
        self._emit(f"{self._ts(t)} {node_id} consensus C={cval}")

    def radio_change(self, node_id, radio, t):
        hz = 1.0 / radio.sampling_interval if radio.sampling_interval else 0
        self._emit(f"{self._ts(t)} {node_id} sampling={hz:.3g}Hz "
                   f"SF={radio.spreading_factor} Tx={radio.tx_power_dbm}dBm")

    def forward(self, relay, origin, nxt, hop, t):
        self._emit(f"{self._ts(t)} {relay} FORWARD origin={origin} -> {nxt} hop={hop}")

    def ttl_expired(self, relay, origin, seq, t):
        self._emit(f"{self._ts(t)} {relay} TTL_EXPIRED origin={origin} seq={seq}")

    def alert(self, node_id, state, t):
        self._emit(f"{self._ts(t)} gateway received ALERT from {node_id} state={state}")

    def bridge_read(self, node_id, seq):
        self._emit(f"[bridge] read {node_id} seq={seq}")
