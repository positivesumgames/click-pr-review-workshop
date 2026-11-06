"""Deliberately unsafe learner starter. Never used by the live readiness workflow."""


def ready(snapshot):
    """What evidence does this ignore? Repair the function; preserve its boolean interface."""
    return all(check["conclusion"] == "success" for check in snapshot["checks"])
