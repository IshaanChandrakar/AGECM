"""
Routing / neighbour table with static two-hop next-hop selection.

Dynamic multi-hop route selection is PARTIAL (Review 3 work). Here routes are
deterministic/static: each node has a preconfigured next hop toward the gateway,
giving paths of at most two hops (node -> relay -> gateway). The interface
(`next_hop`) is shaped so a dynamic selector can replace the static table later.
"""

from config import GATEWAY_ID


class Router:
    def __init__(self, node_id):
        self.node_id = node_id
        # neighbour_id -> True (reachable). Simple neighbour table.
        self.neighbours = {}
        # static next hop toward the gateway; None means "direct to gateway".
        self._next_hop = GATEWAY_ID

    def add_neighbour(self, neighbour_id):
        self.neighbours[neighbour_id] = True

    def set_static_next_hop(self, next_hop):
        """Preconfigure the deterministic route toward the gateway."""
        self._next_hop = next_hop

    def next_hop(self):
        """
        Current next hop toward the gateway. Static today; a dynamic selector
        (Review 3) could pick the best neighbour from link metrics here.
        """
        return self._next_hop

    def neighbour_ids(self):
        return list(self.neighbours.keys())
