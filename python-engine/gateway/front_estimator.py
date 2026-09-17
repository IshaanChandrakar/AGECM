"""
Linear front-estimation prototype (Review 2).

Given node positions and the times each node first escalated to WARNING/CRITICAL,
estimate the direction and progression speed of the subsidence front with a
simple linear (least-squares) fit. This is a PROTOTYPE — graph-based prediction
is Review 3 work; no graph neural network is used here.

Method
------
Each supporting node contributes a point (x, y, t_escalation). We fit escalation
time as a linear function of position:  t ≈ a*x + b*y + c.
The gradient (a, b) points in the direction of increasing escalation time, so the
front travels along -(a, b) (earlier-escalating nodes are where the front has
already passed). Front speed ≈ 1 / |(a, b)|  (position units per second).
"""

import math


class FrontEstimator:
    def __init__(self, positions):
        # positions: {node_id: (x, y)}
        self.positions = positions

    def estimate(self, escalations):
        """
        escalations: {node_id: t_first_escalation}. Needs >= 2 supporting nodes.
        Returns a dict describing the estimate, or {'active': False, ...}.
        """
        pts = [(self.positions[n][0], self.positions[n][1], t)
               for n, t in escalations.items() if n in self.positions]

        if len(pts) < 2:
            return {"active": False, "reason": "insufficient supporting nodes",
                    "supporting_nodes": list(escalations.keys())}

        if len(pts) == 2:
            return self._two_point(pts, escalations)
        return self._least_squares(pts, escalations)

    def _two_point(self, pts, escalations):
        (x0, y0, t0), (x1, y1, t1) = pts[0], pts[1]
        dx, dy, dt = x1 - x0, y1 - y0, (t1 - t0)
        dist = math.hypot(dx, dy)
        if dist == 0 or dt == 0:
            return {"active": False, "reason": "degenerate geometry",
                    "supporting_nodes": list(escalations.keys())}
        # Front moves from the earlier node toward the later node.
        sign = 1.0 if dt > 0 else -1.0
        dir_x, dir_y = sign * dx / dist, sign * dy / dist
        speed = dist / abs(dt)
        return self._result(dir_x, dir_y, speed, escalations)

    def _least_squares(self, pts, escalations):
        # Fit t = a*x + b*y + c via normal equations (3x3 solve).
        n = len(pts)
        Sx = sum(p[0] for p in pts); Sy = sum(p[1] for p in pts)
        Sxx = sum(p[0] * p[0] for p in pts); Syy = sum(p[1] * p[1] for p in pts)
        Sxy = sum(p[0] * p[1] for p in pts)
        St = sum(p[2] for p in pts)
        Sxt = sum(p[0] * p[2] for p in pts); Syt = sum(p[1] * p[2] for p in pts)

        # Normal-equation matrix A * [a,b,c] = rhs
        A = [[Sxx, Sxy, Sx],
             [Sxy, Syy, Sy],
             [Sx,  Sy,  n]]
        rhs = [Sxt, Syt, St]
        sol = _solve3(A, rhs)
        if sol is None:
            # Collinear nodes (e.g. a straight line) make the 2-D fit singular.
            # Fall back to a 1-D regression of t against the dominant axis.
            return self._one_d(pts, escalations)
        a, b, _ = sol
        grad = math.hypot(a, b)
        if grad == 0:
            return {"active": False, "reason": "no spatial gradient",
                    "supporting_nodes": list(escalations.keys())}
        # Front travels toward increasing t: direction = +(a, b)/|.|
        dir_x, dir_y = a / grad, b / grad
        speed = 1.0 / grad
        return self._result(dir_x, dir_y, speed, escalations)

    def _one_d(self, pts, escalations):
        """Regress t on distance along the dominant spatial axis (collinear nodes)."""
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        span_x = max(xs) - min(xs); span_y = max(ys) - min(ys)
        axis = 0 if span_x >= span_y else 1
        pos = [p[axis] for p in pts]
        ts = [p[2] for p in pts]
        n = len(pts)
        mp = sum(pos) / n; mt = sum(ts) / n
        num = sum((pos[i] - mp) * (ts[i] - mt) for i in range(n))
        den = sum((pos[i] - mp) ** 2 for i in range(n))
        if den == 0 or num == 0:
            return {"active": False, "reason": "no spatial gradient",
                    "supporting_nodes": list(escalations.keys())}
        slope = num / den                 # dt/d(pos): s per position unit
        speed = 1.0 / abs(slope)
        sign = 1.0 if slope > 0 else -1.0
        dir_x, dir_y = (sign, 0.0) if axis == 0 else (0.0, sign)
        return self._result(dir_x, dir_y, speed, escalations)

    @staticmethod
    def _result(dir_x, dir_y, speed, escalations):
        bearing = (math.degrees(math.atan2(dir_y, dir_x)) + 360) % 360
        return {
            "active": True,
            "direction_x": round(dir_x, 4),
            "direction_y": round(dir_y, 4),
            "bearing_deg": round(bearing, 1),
            "progression_speed": round(speed, 4),
            "supporting_nodes": list(escalations.keys()),
            "escalation_times": {k: round(v, 2) for k, v in escalations.items()},
        }


def _solve3(A, b):
    """Gaussian elimination for a 3x3 system. Returns None if singular."""
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for col in range(3):
        piv = max(range(col, 3), key=lambda r: abs(M[r][col]))
        if abs(M[piv][col]) < 1e-12:
            return None
        M[col], M[piv] = M[piv], M[col]
        pv = M[col][col]
        M[col] = [x / pv for x in M[col]]
        for r in range(3):
            if r != col:
                f = M[r][col]
                M[r] = [x - f * y for x, y in zip(M[r], M[col])]
    return [M[0][3], M[1][3], M[2][3]]
