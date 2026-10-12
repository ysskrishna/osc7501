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


def working(
    *,
    msg: str | None = None,
    title: str | None = None,
    app: str | None = None,
    id: str | None = None,
    progress: int | None = None,
    stream: IO[str] | None = None,
    enabled: bool | None = None,
) -> "Job":
    """Write ``working`` immediately and return a handle for later reports."""
    job = Job(
        app=app,
        id=id,
        title=title,
        stream=sys.stderr if stream is None else stream,
        enabled=enabled,
    )
    job.update(msg=msg, progress=progress)
    return job


def clear(
    *,
    id: str | None = None,
    stream: IO[str] | None = None,
    enabled: bool | None = None,
) -> bool:
    return _send(State.CLEAR, id=id, stream=stream, enabled=enabled)


class Job:
    """One task. Repeats ``app``, ``id``, and ``title`` because a report replaces the record."""

    def __init__(
        self,
        *,
        app: str | None,
        id: str | None,
        title: str | None,
        stream: Any,
        enabled: bool | None,
    ) -> None:
        self._app = app
        self._id = id
        self._title = title
        self._stream = stream
        self._enabled = enabled
        self._last_state: State | None = None
        self._last_bytes: str | None = None

    def __enter__(self) -> "Job":
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: object) -> bool:
        if self._last_state not in (State.WORKING, State.BLOCKED):
            return False
        if exc_type is None:
            self.done()
        elif issubclass(exc_type, SystemExit):
            code = exc.code if isinstance(exc, SystemExit) else None
            if code in (0, None):
                self.done()
            else:
                self.error()
        elif issubclass(exc_type, KeyboardInterrupt):
            self.idle()
        elif issubclass(exc_type, Exception):
            self.error()
        else:
            # asyncio.CancelledError and other non-Exception BaseExceptions.
            self.idle()
        return False

    def update(self, *, progress: int | None = None, msg: str | None = None) -> bool:
        return self._emit(State.WORKING, progress=progress, msg=msg)

    def blocked(
        self,
        *,
        kind: str | None = None,
        msg: str | None = None,
        progress: int | None = None,
    ) -> bool:
        return self._emit(State.BLOCKED, kind=kind, msg=msg, progress=progress)

    def done(self, *, msg: str | None = None) -> bool:
        return self._emit(State.DONE, msg=msg)

    def error(self, *, msg: str | None = None) -> bool:
        return self._emit(State.ERROR, msg=msg)

    def idle(self, *, msg: str | None = None) -> bool:
        return self._emit(State.IDLE, msg=msg)

    def _emit(
        self,
        state: str,
        *,
        msg: str | None = None,
        kind: str | None = None,
        progress: int | None = None,
    ) -> bool:
        sequence = encode(
            state,
            msg=msg,
            title=self._title,
            app=self._app,
            id=self._id,
            kind=kind,
            progress=progress,
        )
        self._last_state = State(state)
        if sequence == self._last_bytes:
            return False
        wrote = _write(sequence, self._stream, self._enabled)
        if wrote:
            self._last_bytes = sequence
        return wrote


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
