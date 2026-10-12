import pytest

from osc7501 import Kind, State, encode


def test_working_is_the_state_only_sequence() -> None:
    assert encode("working") == "\x1b]7501;state=working\x1b\\"
    assert encode(State.WORKING) == "\x1b]7501;state=working\x1b\\"


def test_pair_order_is_state_id_kind_progress_app() -> None:
    sequence = encode("blocked", id="build/test", kind="question", progress=40, app="make")
    assert sequence == "\x1b]7501;state=blocked:id=build/test:kind=question:progress=40:app=make\x1b\\"


def test_progress_is_emitted_for_working() -> None:
    assert encode("working", progress=40) == "\x1b]7501;state=working:progress=40\x1b\\"
    assert encode("blocked", kind=Kind.PERMISSION, progress=0) == (
        "\x1b]7501;state=blocked:kind=permission:progress=0\x1b\\"
    )
    assert encode("blocked", kind="auth", progress=100).endswith("progress=100\x1b\\")


@pytest.mark.parametrize(
    "kwargs",
    [
        {"state": "done", "progress": 40},
        {"state": "working", "progress": True},
        {"state": "working", "progress": False},
        {"state": "working", "progress": -1},
        {"state": "working", "progress": 101},
        {"state": "working", "progress": 0.5},
        {"state": "idle", "kind": "permission"},
        {"state": "blocked", "kind": "nope"},
        {"state": "nope"},
        {"state": "working", "app": "make\n"},
        {"state": "working", "app": ""},
        {"state": "working", "app": "x" * 33},
        {"state": "working", "id": "x=y"},
        {"state": "working", "id": "a//b"},
        {"state": "working", "id": "/a"},
        {"state": "working", "id": "a/"},
        {"state": "working", "id": "/".join(["a"] * 9)},
        {"state": "working", "id": "a" * 129},
        {"state": "clear", "app": "make"},
        {"state": "clear", "progress": 1},
        {"state": "clear", "kind": "question"},
    ],
)
def test_invalid_identity_raises(kwargs: dict[str, object]) -> None:
    state = kwargs.pop("state")
    with pytest.raises(ValueError):
        encode(state, **kwargs)  # type: ignore[arg-type]


def test_newline_in_app_does_not_match_the_end_anchor() -> None:
    with pytest.raises(ValueError):
        encode("working", app="make\n")
