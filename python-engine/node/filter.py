"""
Moving-average filter for edge smoothing of a raw sensor stream.

Simple, explainable, O(1) per sample using a running sum over a fixed window.
"""

from collections import deque


class MovingAverageFilter:
    def __init__(self, window):
        self.window = window
        self._buf = deque(maxlen=window)
        self._sum = 0.0

    def update(self, value):
        """Add a value, return the current moving average."""
        if len(self._buf) == self.window:
            self._sum -= self._buf[0]     # value about to be evicted
        self._buf.append(value)
        self._sum += value
        return self._sum / len(self._buf)

    def reset(self):
        self._buf.clear()
        self._sum = 0.0
