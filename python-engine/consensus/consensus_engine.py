"""
Consensus engine (simulated).

Implements the AGECM request/reply mechanism inside one process. The requesting
node's engine sends a CONSENSUS_REQUEST to a set of neighbour nodes, collects
replies that arrive within the 2-second response window, and computes:

    C = corroborating_replies / replies_received

Rules (report):
  * If fewer than MIN_REPLIES neighbours respond, C is UNDEFINED (returns None).
    The node may escalate to WARNING but must NOT become CRITICAL on this alone.
  * The engine does not wait indefinitely; replies past the window are ignored.

A neighbour corroborates if its own tilt rate exceeds CORROBORATION_TILT, i.e.
it independently observes deformation rather than isolated noise.
"""

from config import CONSENSUS_WINDOW_S, MIN_REPLIES, CORROBORATION_TILT
from consensus.messages import ConsensusRequest, ConsensusReply


class ConsensusEngine:
    def __init__(self, node_id, logger=None):
        self.node_id = node_id
        self._log = logger

    def request(self, sequence, features, state, neighbours, now):
        """
        Run one consensus round.

        neighbours: list of (neighbour_id, neighbour_features) reachable now.
                    A neighbour with features=None is unreachable / silent.
        Returns (C or None, ConsensusEvent-dict) for logging/persistence.
        """
        req = ConsensusRequest(
            node_id=self.node_id,
            sequence=sequence,
            timestamp=now,
            tilt_rate=features.tilt_rate,
            displacement_velocity=features.displacement_velocity,
            vibration=features.vibration,
            state=state,
        )
        if self._log:
            self._log.consensus_request(self.node_id, sequence, now)

        replies = []
        for nid, nfeat in neighbours:
            if nfeat is None:
                # No reply within the window (timeout). Logged, not counted.
                if self._log:
                    self._log.consensus_timeout(self.node_id, nid, sequence, now)
                continue
            corroborated = nfeat.tilt_rate >= CORROBORATION_TILT
            reply = ConsensusReply(
                node_id=nid,
                request_node_id=self.node_id,
                sequence=sequence,
                timestamp=now + CONSENSUS_WINDOW_S,
                corroborated=corroborated,
                tilt_rate=nfeat.tilt_rate,
            )
            replies.append(reply)
            if self._log:
                self._log.consensus_reply(self.node_id, nid, corroborated, sequence, now)

        replies_received = len(replies)
        corroborating = sum(1 for r in replies if r.corroborated)

        if replies_received < MIN_REPLIES:
            c = None                       # undefined
        else:
            c = corroborating / replies_received

        if self._log:
            self._log.consensus_result(self.node_id, c, sequence, now)

        event = {
            "requesting_node": self.node_id,
            "responders": [r.node_id for r in replies],
            "replies_received": replies_received,
            "corroborating": corroborating,
            "confidence": c,
            "sequence": sequence,
            "timestamp": now,
        }
        return c, event
