"""Report terminal program status with OSC 7501."""

from osc7501.encode import Kind, State, encode
from osc7501.terminal import (
    Detection,
    Job,
    Support,
    blocked,
    clear,
    detect,
    done,
    error,
    idle,
    parse_reply,
    query,
    working,
)

__all__ = [
    "Detection",
    "Job",
    "Kind",
    "State",
    "Support",
    "blocked",
    "clear",
    "detect",
    "done",
    "encode",
    "error",
    "idle",
    "parse_reply",
    "query",
    "working",
]
