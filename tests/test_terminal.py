import asyncio

import pytest

from osc7501 import State, blocked, clear, done, encode, working


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


_WORKING = "\x1b]7501;state=working:app=make:msg=QnVpbGRpbmcgZG9jcw==\x1b\\"
_BLOCKED = "\x1b]7501;state=blocked:kind=question:app=make:msg=T3ZlcndyaXRlIGNvbmZpZy50b21sPw==\x1b\\"
_DONE = "\x1b]7501;state=done:app=make:msg=RG9jcyBidWlsdA==\x1b\\"


def test_job_writes_the_spec_example() -> None:
    stream = _Stream(tty=True)
    with working(app="make", msg="Building docs", stream=stream) as job:
        job.blocked(kind="question", msg="Overwrite config.toml?")
        job.done(msg="Docs built")
    assert stream.buf == [_WORKING, _BLOCKED, _DONE]


def test_job_repeats_identity_and_exit_omits_msg() -> None:
    stream = _Stream(tty=True)
    with working(app="make", id="build/test", title="Docs", msg="Building docs", stream=stream) as job:
        assert job.update(progress=40) is True
    assert stream.buf[1] == encode("working", app="make", id="build/test", title="Docs", progress=40)
    assert stream.buf[2] == encode("done", app="make", id="build/test", title="Docs")


def test_job_skips_a_repeat() -> None:
    stream = _Stream(tty=True)
    job = working(msg="Building docs", stream=stream)
    assert job.update(msg="Building docs") is False
    for _ in range(10_000):
        job.update(msg="Building docs")
    assert stream.buf == [encode("working", msg="Building docs")]
    for progress in range(101):
        assert job.update(msg="Building docs", progress=progress) is True
    assert len(stream.buf) == 102
    assert job.update(msg="Building docs", progress=100) is False
    assert len(stream.buf) == 102


@pytest.mark.parametrize(
    ("exc", "state"),
    [
        (None, "done"),
        (SystemExit(0), "done"),
        (SystemExit(), "done"),
        (SystemExit(1), "error"),
        (SystemExit("fail"), "error"),
        (KeyboardInterrupt(), "idle"),
        (RuntimeError("boom"), "error"),
        (asyncio.CancelledError(), "idle"),
    ],
)
def test_exit_mapping(exc: BaseException | None, state: str) -> None:
    stream = _Stream(tty=True)
    try:
        with working(app="make", stream=stream):
            if exc is not None:
                raise exc
    except BaseException:
        if exc is None:
            raise
    assert stream.buf[-1] == encode(state, app="make")
    assert len(stream.buf) == 2


def test_disabled_exit_still_records_the_final_state() -> None:
    stream = _Stream(tty=False)
    with working(app="make", stream=stream) as job:
        pass
    assert stream.buf == []
    assert job._last_state is State.DONE
