"""Write an OSC 7501 report to a terminal, and read a support reply."""

import os
import sys
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import IO, Any

from osc7501.encode import Kind, State, encode

_ESC = 0x1B
_BEL = 0x07
_CAN = 0x18
_SUB = 0x1A
_GROUND = "ground"
_ESCAPE = "esc"
_OSC = "osc"
_OSC_ESC = "osc-esc"
_CSI = "csi"
_REPLY_PREFIX = b"7501;?"
_BODY_LIMIT = 4096

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
        if sequence == self._last_bytes:
            return False
        wrote = _write(sequence, self._stream, self._enabled)
        # A raised write stops above, so a failed report does not count as sent.
        self._last_state = State(state)
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


class Detection(Enum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"


_DEFAULT_STATES = frozenset(state.value for state in State if state is not State.CLEAR)
_DEFAULT_KINDS = frozenset(kind.value for kind in Kind)


@dataclass(frozen=True)
class Support:
    result: Detection
    states: frozenset[str]
    kinds: frozenset[str]

    @property
    def supported(self) -> bool:
        return self.result is Detection.SUPPORTED


def detect(*, timeout: float = 0.2) -> Support:
    """Ask ``/dev/tty`` whether it supports OSC 7501.

    Call this before reading input. Keystrokes typed during the wait can be
    consumed, and a reply that arrives after the timeout can leak into later
    input. Emit paths never call this.
    """
    try:
        import select
        import termios
    except ImportError:
        return _unknown()
    try:
        fd = os.open("/dev/tty", os.O_RDWR | os.O_NOCTTY)
    except OSError:
        return _unknown()
    try:
        try:
            old = termios.tcgetattr(fd)
        except termios.error:
            return _unknown()
        new = [old[0], old[1], old[2], old[3], old[4], old[5], list(old[6])]
        new[3] &= ~(termios.ICANON | termios.ECHO | termios.ISIG | termios.IEXTEN)
        new[0] &= ~(termios.IXON | termios.ICRNL)
        new[6][termios.VMIN] = 0
        new[6][termios.VTIME] = 1
        termios.tcsetattr(fd, termios.TCSANOW, new)
        try:
            os.write(fd, query().encode("ascii"))
            os.write(fd, b"\x1b[c")
            reader = _ReplyReader()
            deadline = time.monotonic() + timeout
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                ready, _, _ = select.select([fd], [], [], remaining)
                if not ready:
                    break
                chunk = os.read(fd, 256)
                if not chunk:
                    break
                reader.feed(chunk)
                if reader._done:
                    break
            return _support_from(reader)
        finally:
            termios.tcsetattr(fd, termios.TCSANOW, old)
    finally:
        os.close(fd)


def _unknown() -> Support:
    return Support(Detection.UNKNOWN, frozenset(), frozenset())


def _support_from(reader: "_ReplyReader") -> Support:
    if reader._result is Detection.SUPPORTED and reader.reply is not None:
        parsed = parse_reply(reader.reply)
        if parsed is not None:
            return parsed
    if reader._result is Detection.SUPPORTED:
        return Support(Detection.SUPPORTED, _DEFAULT_STATES, _DEFAULT_KINDS)
    return Support(reader._result, frozenset(), frozenset())


def query() -> str:
    """The feature-detection query, ``OSC 7501 ; ? ST``."""
    return "\x1b]7501;?\x1b\\"


def parse_reply(sequence: str) -> Support | None:
    """Parse one support reply. Anything else, including DA1, returns ``None``."""
    if sequence.endswith("\x1b\\"):
        body = sequence[: -2]
    elif sequence.endswith("\x07"):
        body = sequence[: -1]
    else:
        return None
    if not body.startswith("\x1b]7501;?"):
        return None
    rest = body[len("\x1b]7501;?") :]
    if rest.startswith(":"):
        rest = rest[1:]
    elif rest != "":
        return None

    states: frozenset[str] | None = None
    kinds: frozenset[str] | None = None
    for pair in rest.split(":") if rest else ():
        if "=" not in pair:
            continue
        key, value = pair.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key == "states":
            states = _csv(value)
        elif key == "kinds":
            kinds = _csv(value)
    return Support(
        result=Detection.SUPPORTED,
        states=_DEFAULT_STATES if states is None else states,
        kinds=_DEFAULT_KINDS if kinds is None else kinds,
    )


def _csv(value: str) -> frozenset[str]:
    return frozenset(part.strip() for part in value.split(",") if part.strip())


class _ReplyReader:
    """Streaming scan for a 7501 support reply and the following DA1 reply.

    DA1 is a CSI whose first parameter byte is ``?`` and whose final byte is ``c``.
    OSC ends on BEL or ST. CAN and SUB cancel. ESC restarts a sequence.
    """

    def __init__(self) -> None:
        self._state = _GROUND
        self._buf = bytearray()
        self._overflow = False
        self._csi_first = 0
        self._result = Detection.UNKNOWN
        self._done = False
        self.reply: str | None = None

    def feed(self, data: bytes) -> tuple[Detection, bool]:
        for byte in data:
            if self._done:
                break
            self._feed_byte(byte)
        return self._result, self._done

    def _feed_byte(self, byte: int) -> None:
        if self._state == _GROUND:
            if byte == _ESC:
                self._state = _ESCAPE
            return
        if self._state == _ESCAPE:
            self._after_esc(byte)
            return
        if self._state == _OSC:
            if byte == _BEL:
                self._end_osc(b"\x07")
            elif byte == _ESC:
                self._state = _OSC_ESC
            elif byte in (_CAN, _SUB):
                self._state = _GROUND
                self._buf.clear()
                self._overflow = False
            elif len(self._buf) < _BODY_LIMIT:
                self._buf.append(byte)
            else:
                self._overflow = True
            return
        if self._state == _OSC_ESC:
            if byte == ord("\\"):
                self._end_osc(b"\x1b\\")
            else:
                self._after_esc(byte)
            return
        if byte == _ESC:
            self._state = _ESCAPE
        elif byte in (_CAN, _SUB):
            self._state = _GROUND
        elif 0x40 <= byte <= 0x7E:
            if byte == ord("c") and self._csi_first == ord("?"):
                if self._result is Detection.UNKNOWN:
                    self._result = Detection.UNSUPPORTED
                self._done = True
            self._state = _GROUND
        elif 0x20 <= byte <= 0x3F:
            if self._csi_first == 0:
                self._csi_first = byte
        else:
            self._state = _GROUND

    def _after_esc(self, byte: int) -> None:
        if byte == ord("]"):
            self._buf.clear()
            self._overflow = False
            self._state = _OSC
        elif byte == ord("["):
            self._csi_first = 0
            self._state = _CSI
        elif byte == _ESC:
            self._state = _ESCAPE
        else:
            self._state = _GROUND

    def _end_osc(self, terminator: bytes) -> None:
        self._state = _GROUND
        body = bytes(self._buf)
        self._buf.clear()
        overflow = self._overflow
        self._overflow = False
        if overflow or self._result is not Detection.UNKNOWN or not body.startswith(_REPLY_PREFIX):
            return
        self._result = Detection.SUPPORTED
        self.reply = "\x1b]" + body.decode("ascii") + terminator.decode("ascii")


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
