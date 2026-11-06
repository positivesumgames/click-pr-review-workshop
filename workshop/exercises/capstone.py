"""Learner-owned extension: implement a new gate and its tests, not another model vote."""


def additional_gate(packet, evidence):
    """Return (passed: bool, reason: str). Choose and document your own measurable policy."""
    raise NotImplementedError("Choose one new failure mode and implement its gate")
