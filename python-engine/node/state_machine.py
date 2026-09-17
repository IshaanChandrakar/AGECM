"""
AGECM 4-state machine: NORMAL, WARNING, CRITICAL, FAULT.

Report rules implemented:
  NORMAL   : dθ/dt < θ_min and no sufficient anomaly evidence
  WARNING  : θ_min <= dθ/dt < θ_crit, or moderate evidence
  CRITICAL : dθ/dt >= θ_crit  AND  sufficient consensus evidence
  FAULT    : local anomaly exists but neighbours do not corroborate it

Key constraint: insufficient neighbour evidence must NOT auto-produce CRITICAL.
A strong local anomaly with no/low corroboration -> FAULT (not CRITICAL).

Escalation uses the two-consecutive-samples rule: a candidate stronger state
must be seen on two consecutive ready samples before it is committed.
Recovery to NORMAL requires the below-threshold condition to hold for the
30-second recovery dwell.
"""

from config import (
    THETA_MIN, THETA_CRIT, C_MED,
    CONSECUTIVE_SAMPLES, RECOVERY_DWELL_S,
)

NORMAL, WARNING, CRITICAL, FAULT = "NORMAL", "WARNING", "CRITICAL", "FAULT"


class StateMachine:
    def __init__(self, node_id, logger=None):
        self.node_id = node_id
        self.state = NORMAL
        self._log = logger
        self._candidate = NORMAL
        self._candidate_count = 0
        self._below_since = None      # time below θ_min started (for recovery)

    def sufficient_consensus(self, c):
        """C is sufficient only if defined and >= C_MED."""
        return c is not None and c >= C_MED

    def classify(self, features, consensus_confidence):
        """
        Return the *candidate* state implied by this sample alone.
        Consensus is only used to gate CRITICAL vs FAULT.
        """
        r = features.tilt_rate
        if r >= THETA_CRIT:
            # Strong local anomaly. CRITICAL only with sufficient corroboration,
            # otherwise FAULT (anomaly not confirmed by neighbours).
            return CRITICAL if self.sufficient_consensus(consensus_confidence) else FAULT
        if r >= THETA_MIN:
            return WARNING
        return NORMAL

    def update(self, features, consensus_confidence=None):
        """
        Advance the machine one ready sample. Returns the (possibly new) state.
        Applies the two-consecutive-samples rule for escalation and the
        recovery dwell for de-escalation to NORMAL.
        """
        if not features.ready:
            return self.state

        candidate = self.classify(features, consensus_confidence)
        t = features.t

        # Track how long tilt rate has stayed below θ_min (recovery timer).
        if features.tilt_rate < THETA_MIN:
            if self._below_since is None:
                self._below_since = t
        else:
            self._below_since = None

        rank = {NORMAL: 0, WARNING: 1, FAULT: 2, CRITICAL: 3}

        if rank[candidate] > rank[self.state]:
            # Escalation: require two consecutive matching candidates.
            if candidate == self._candidate:
                self._candidate_count += 1
            else:
                self._candidate = candidate
                self._candidate_count = 1
            if self._candidate_count >= CONSECUTIVE_SAMPLES:
                self._transition(candidate, t, consensus_confidence)
                self._candidate_count = 0
        elif rank[candidate] < rank[self.state]:
            # De-escalation. Return to NORMAL only after the recovery dwell.
            if candidate == NORMAL:
                if self._below_since is not None and (t - self._below_since) >= RECOVERY_DWELL_S:
                    self._transition(NORMAL, t, consensus_confidence)
                    self._candidate = NORMAL
                    self._candidate_count = 0
            else:
                # Drop toward an intermediate state immediately (e.g. CRITICAL->WARNING).
                self._transition(candidate, t, consensus_confidence)
                self._candidate = candidate
                self._candidate_count = 0
        else:
            self._candidate = candidate
            self._candidate_count = 0

        return self.state

    def _transition(self, new_state, t, c):
        if new_state == self.state:
            return
        old = self.state
        self.state = new_state
        if self._log:
            self._log.state_change(self.node_id, old, new_state, t, c)
