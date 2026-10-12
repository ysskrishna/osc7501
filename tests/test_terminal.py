import pytest

from osc7501 import blocked, clear, done, encode


class _Stream:
    def __init__(self, *, tty: bool) -> None:
        self.tty = tty
        self.buf: list[str] = []
        self.flushed = False

    def write(self, data: str) -> int:
        self.buf.append(data)
        return len(data)

    def isatty(self) -> bool:
        return self.tty

    def flush(self) -> None:
        self.flushed = True

    @property
    def text(self) -> str:
        return "".join(self.buf)


def test_a_pipe_receives_nothing() -> None:
    stream = _Stream(tty=False)
    assert done(msg="Built", stream=stream) is False
    assert stream.buf == []
    assert stream.flushed is False


def test_enabled_writes_even_when_the_stream_is_not_a_tty() -> None:
    stream = _Stream(tty=False)
    assert done(app="make", msg="Docs built", stream=stream, enabled=True) is True
    assert stream.text == encode("done", app="make", msg="Docs built")
    assert stream.flushed is True


def test_disabled_still_rejects_a_bad_progress() -> None:
    stream = _Stream(tty=True)
    with pytest.raises(ValueError):
        blocked(progress=101, stream=stream, enabled=False)
    assert stream.buf == []


def test_write_errors_propagate() -> None:
    class _Boom:
        def write(self, data: str) -> int:
            raise OSError("closed")

        def isatty(self) -> bool:
            return True

    with pytest.raises(OSError, match="closed"):
        done(stream=_Boom(), enabled=True)


def test_a_tty_is_the_default_gate() -> None:
    stream = _Stream(tty=True)
    assert clear(stream=stream) is True
    assert stream.text == encode("clear")
