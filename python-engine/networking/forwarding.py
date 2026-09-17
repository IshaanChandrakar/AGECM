"""
Two-hop forwarding with TTL and duplicate detection.

A relay node forwards packets toward the gateway, decrementing TTL and
incrementing hop_count. Duplicates are dropped using a (node_id, sequence) seen
set, so the same telemetry is not forwarded twice.
"""

from config import GATEWAY_ID
from networking.packet import FORWARD


class Forwarder:
    def __init__(self, node_id):
        self.node_id = node_id
        self._seen = set()      # (origin_node_id, sequence) already handled

    def _is_duplicate(self, packet):
        key = (packet.node_id, packet.sequence)
        if key in self._seen:
            return True
        self._seen.add(key)
        return False

    def forward(self, packet, router, logger=None, now=0.0):
        """
        Forward one packet one hop toward the gateway.

        Returns a dict describing the network event, or None if dropped
        (duplicate or TTL expired). When next hop is the gateway, delivered=True.
        """
        if self._is_duplicate(packet):
            return None
        if packet.ttl <= 0:
            if logger:
                logger.ttl_expired(self.node_id, packet.node_id, packet.sequence, now)
            return None

        packet.ttl -= 1
        packet.hop_count += 1
        packet.packet_type = FORWARD if packet.hop_count > 0 else packet.packet_type

        nxt = router.next_hop()
        delivered = nxt == GATEWAY_ID
        packet.next_hop = nxt

        if logger:
            logger.forward(self.node_id, packet.node_id, nxt, packet.hop_count, now)

        return {
            "relay_node": self.node_id,
            "origin_node": packet.node_id,
            "next_hop": nxt,
            "hop_count": packet.hop_count,
            "ttl": packet.ttl,
            "sequence": packet.sequence,
            "delivered": delivered,
            "timestamp": now,
        }
