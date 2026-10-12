"""Build one OSC 7501 report. This module does not write to a terminal."""

import base64
import re
import unicodedata
from enum import StrEnum

_APP = re.compile(r"[A-Za-z0-9_.+-]{1,32}")
_ID_BYTES = 128
_ID_SEGMENTS = 8
_MSG_BYTES = 2048
_TITLE_BYTES = 192
_SEQUENCE_BYTES = 4096


class State(StrEnum):
    IDLE = "idle"
    WORKING = "working"
    DONE = "done"
    BLOCKED = "blocked"
    ERROR = "error"
    CLEAR = "clear"


class Kind(StrEnum):
    PERMISSION = "permission"
    QUESTION = "question"
    AUTH = "auth"


def encode(
    state: str,
    *,
    msg: str | None = None,
    title: str | None = None,
    app: str | None = None,
    id: str | None = None,
    kind: str | None = None,
    progress: int | None = None,
) -> str:
    """Return one report. The terminator is ST.

    ``re.fullmatch`` is required for ``app`` and each ``id`` segment.
    ``re.match`` with ``$`` also matches before a trailing newline.

    Control characters in ``msg`` and ``title`` are replaced with a space.
    A terminal discards the whole report when those fields decode to a control.
    """
    try:
        parsed = State(state)
    except ValueError:
        raise ValueError(f"unknown state: {state!r}") from None

    if parsed is State.CLEAR and any(
        value is not None for value in (msg, title, app, kind, progress)
    ):
        raise ValueError("clear accepts only id")

    parsed_kind: Kind | None = None
    if kind is not None:
        if parsed is not State.BLOCKED:
            raise ValueError("kind is only valid with blocked")
        try:
            parsed_kind = Kind(kind)
        except ValueError:
            raise ValueError(f"unknown kind: {kind!r}") from None

    if progress is not None:
        if parsed not in (State.WORKING, State.BLOCKED):
            raise ValueError("progress is only valid with working or blocked")
        # bool is a subclass of int. True would otherwise encode as progress=1.
        if isinstance(progress, bool) or not isinstance(progress, int) or not 0 <= progress <= 100:
            raise ValueError(f"invalid progress: {progress!r}")

    if app is not None and _APP.fullmatch(app) is None:
        raise ValueError(f"invalid app: {app!r}")
    if id is not None:
        _check_id(id)

    pairs = [f"state={parsed.value}"]
    if id is not None:
        pairs.append(f"id={id}")
    if parsed_kind is not None:
        pairs.append(f"kind={parsed_kind.value}")
    if progress is not None:
        pairs.append(f"progress={progress}")
    if app is not None:
        pairs.append(f"app={app}")
    if title is not None and (encoded := _text(title, _TITLE_BYTES)) is not None:
        pairs.append(f"title={encoded}")
    if msg is not None and (encoded := _text(msg, _MSG_BYTES)) is not None:
        pairs.append(f"msg={encoded}")

    sequence = f"\x1b]7501;{':'.join(pairs)}\x1b\\"
    if len(sequence.encode("ascii")) > _SEQUENCE_BYTES:
        raise ValueError("sequence longer than 4096 bytes")
    return sequence


def _check_id(record_id: str) -> None:
    if len(record_id.encode("utf-8")) > _ID_BYTES:
        raise ValueError("id longer than 128 bytes")
    segments = record_id.split("/")
    if len(segments) > _ID_SEGMENTS:
        raise ValueError("id has more than 8 segments")
    for segment in segments:
        if _APP.fullmatch(segment) is None:
            raise ValueError(f"invalid id segment: {segment!r}")


def _text(text: str, limit: int) -> str | None:
    cleaned = "".join(" " if unicodedata.category(char) == "Cc" else char for char in text)
    raw = cleaned.encode("utf-8", errors="replace")
    if len(raw) > limit:
        raw = raw[:limit].decode("utf-8", errors="ignore").encode("utf-8")
    if not raw:
        return None
    return base64.b64encode(raw).decode("ascii")
