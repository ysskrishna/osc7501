"""Write an OSC 7501 report to a terminal."""

import sys
import threading
from typing import IO, Any

from osc7501.encode import State, encode

_lock = threading.Lock()


def idle(
    *,
    msg: str | None = None,
    title: str | None = None,
    app: str | None = None,
    id: str | None = None,
    stream: IO[str] | None = None,
    enabled: bool | None = None,
) -> bool:
    return _send(State.IDLE, msg=msg, title=title, app=app, id=id, stream=stream, enabled=enabled)


def done(
    *,
    msg: str | None = None,
    title: str | None = None,
    app: str | None = None,
    id: str | None = None,
    stream: IO[str] | None = None,
    enabled: bool | None = None,
) -> bool:
    return _send(State.DONE, msg=msg, title=title, app=app, id=id, stream=stream, enabled=enabled)


def error(
    *,
    msg: str | None = None,
    title: str | None = None,
    app: str | None = None,
    id: str | None = None,
    stream: IO[str] | None = None,
    enabled: bool | None = None,
) -> bool:
    return _send(State.ERROR, msg=msg, title=title, app=app, id=id, stream=stream, enabled=enabled)


def blocked(
    *,
    kind: str | None = None,
    msg: str | None = None,
    title: str | None = None,
    app: str | None = None,
    id: str | None = None,
    progress: int | None = None,
    stream: IO[str] | None = None,
    enabled: bool | None = None,
) -> bool:
    return _send(
        State.BLOCKED,
        kind=kind,
        msg=msg,
        title=title,
        app=app,
        id=id,
        progress=progress,
        stream=stream,
        enabled=enabled,
    )


def clear(
    *,
    id: str | None = None,
    stream: IO[str] | None = None,
    enabled: bool | None = None,
) -> bool:
    return _send(State.CLEAR, id=id, stream=stream, enabled=enabled)


def _send(
    state: str,
    *,
    msg: str | None = None,
    title: str | None = None,
    app: str | None = None,
    id: str | None = None,
    kind: str | None = None,
    progress: int | None = None,
    stream: IO[str] | None = None,
    enabled: bool | None = None,
) -> bool:
    sequence = encode(
        state,
        msg=msg,
        title=title,
        app=app,
        id=id,
        kind=kind,
        progress=progress,
    )
    return _write(sequence, sys.stderr if stream is None else stream, enabled)


def _write(sequence: str, stream: Any, enabled: bool | None) -> bool:
    if enabled is None:
        isatty = getattr(stream, "isatty", None)
        enabled = bool(isatty()) if isatty is not None else False
    if not enabled:
        return False
    with _lock:
        stream.write(sequence)
        flush = getattr(stream, "flush", None)
        if flush is not None:
            flush()
    return True
