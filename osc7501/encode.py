"""Build one OSC 7501 report. This module does not write to a terminal."""

from enum import StrEnum


class State(StrEnum):
    IDLE = "idle"
    WORKING = "working"
    DONE = "done"
    BLOCKED = "blocked"
    ERROR = "error"
    CLEAR = "clear"


def encode(state: str) -> str:
    """Return a state-only report. The terminator is ST."""
    try:
        parsed = State(state)
    except ValueError:
        raise ValueError(f"unknown state: {state!r}") from None
    return f"\x1b]7501;state={parsed.value}\x1b\\"
