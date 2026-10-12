import pytest

from osc7501 import Detection, detect, parse_reply, query
from osc7501.terminal import _ReplyReader

_DA1 = b"\x1b[?62;22;52c"
_REPLY_ST = b"\x1b]7501;?\x1b\\"
_REPLY_BEL = b"\x1b]7501;?\x07"

_CASES = [
    ("7501 then DA1", _REPLY_ST + _DA1, Detection.SUPPORTED, True),
    ("7501 only so far", _REPLY_ST, Detection.SUPPORTED, False),
    ("DA1 only", _DA1, Detection.UNSUPPORTED, True),
    ("DA1 then 7501", _DA1 + _REPLY_ST, Detection.UNSUPPORTED, True),
    ("BEL reply", _REPLY_BEL + _DA1, Detection.SUPPORTED, True),
    ("extra pairs", b"\x1b]7501;?:version=2:x=y\x1b\\" + _DA1, Detection.SUPPORTED, True),
    (
        "garbage interleaved",
        b"abc\x1b[1;1R\x1b]0;t\axyz" + _REPLY_ST + b"\x1b[2Jq" + _DA1,
        Detection.SUPPORTED,
        True,
    ),
    ("other OSC", b"\x1b]7502;?\x07" + _DA1, Detection.UNSUPPORTED, True),
    ("report is not a reply", b"\x1b]7501;state=idle\x07" + _DA1, Detection.UNSUPPORTED, True),
    ("DA2 is not DA1", b"\x1b[>1;10;0c", Detection.UNKNOWN, False),
    ("DA1 without question mark", b"\x1b[62c", Detection.UNKNOWN, False),
    ("other CSI", b"\x1b[?1;2$y", Detection.UNKNOWN, False),
    ("nothing", b"", Detection.UNKNOWN, False),
    ("ESC restarts OSC", b"\x1b]7501\x1b]7501;?\x07" + _DA1, Detection.SUPPORTED, True),
    ("CAN cancels", b"\x1b]7501;?\x18\x07" + _DA1, Detection.UNSUPPORTED, True),
    ("minimal DA1", b"\x1b[?c", Detection.UNSUPPORTED, True),
    ("input after done ignored", _DA1 + _REPLY_ST, Detection.UNSUPPORTED, True),
]


@pytest.mark.parametrize(("name", "data", "result", "done"), _CASES)
def test_reply_reader_whole_and_byte_by_byte(
    name: str, data: bytes, result: Detection, done: bool
) -> None:
    assert _ReplyReader().feed(data) == (result, done)
    reader = _ReplyReader()
    for index in range(len(data)):
        seen = reader.feed(data[index : index + 1])
    if data:
        assert seen == (result, done)


def test_states_and_kinds_are_kept() -> None:
    reader = _ReplyReader()
    reader.feed(b"\x1b]7501;?:states=idle,working:kinds=permission\x1b\\")
    parsed = parse_reply(reader.reply or "")
    assert parsed is not None
    assert parsed.states == frozenset({"idle", "working"})
    assert parsed.kinds == frozenset({"permission"})
    assert parsed.supported is True


def test_missing_lists_mean_the_fixed_defaults() -> None:
    parsed = parse_reply(query())
    assert parsed is not None
    assert parsed.result is Detection.SUPPORTED
    assert parsed.states == frozenset({"idle", "working", "done", "blocked", "error"})
    assert parsed.kinds == frozenset({"permission", "question", "auth"})


def test_a_repeated_key_keeps_the_last_value() -> None:
    parsed = parse_reply("\x1b]7501;?:states=idle:states=working\x1b\\")
    assert parsed is not None
    assert parsed.states == frozenset({"working"})


def test_detect_without_a_tty(monkeypatch: pytest.MonkeyPatch) -> None:
    def _open(*_args: object, **_kwargs: object) -> int:
        raise OSError("no tty")

    monkeypatch.setattr("osc7501.terminal.os.open", _open)
    found = detect(timeout=0.01)
    assert found.result is Detection.UNKNOWN
    assert found.supported is False
    assert found.states == frozenset()
    assert found.kinds == frozenset()


def test_parse_reply_rejects_da1_and_a_report() -> None:
    assert parse_reply("\x1b[?1;2c") is None
    assert parse_reply("\x1b]7501;state=working\x1b\\") is None
