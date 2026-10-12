import base64

import pytest

from osc7501 import Kind, State, encode


@pytest.mark.parametrize("state", ["idle", "working", "done", "blocked", "error", "clear"])
def test_each_state_is_a_state_only_sequence(state: str) -> None:
    assert encode(state) == f"\x1b]7501;state={state}\x1b\\"


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
        {"state": "working", "id": "a" * 33},
        {"state": "working", "id": "with space"},
        {"state": "working", "id": "x;y"},
        {"state": "working", "id": "x:y"},
        {"state": "working", "id": "東京"},
        {"state": "working", "id": "/".join(["a" * 32] * 4)},
        {"state": "working", "progress": float("nan")},
        {"state": "working", "progress": float("inf")},
        {"state": "clear", "app": "make"},
        {"state": "clear", "progress": 1},
        {"state": "clear", "kind": "question"},
        {"state": "clear", "msg": "done"},
        {"state": "clear", "title": "label"},
    ],
)
def test_invalid_identity_raises(kwargs: dict[str, object]) -> None:
    state = kwargs.pop("state")
    with pytest.raises(ValueError):
        encode(state, **kwargs)  # type: ignore[arg-type]


def test_newline_in_app_does_not_match_the_end_anchor() -> None:
    with pytest.raises(ValueError):
        encode("working", app="make\n")


def test_clear_with_an_id_addresses_that_record() -> None:
    assert encode("clear", id="build/test") == "\x1b]7501;state=clear:id=build/test\x1b\\"


def test_terraform_approval_example() -> None:
    message = "Apply 3 to add, 1 to change, 0 to destroy?"
    sequence = encode("blocked", kind="permission", app="terraform", msg=message)
    assert sequence == (
        "\x1b]7501;state=blocked:kind=permission:app=terraform:"
        "msg=QXBwbHkgMyB0byBhZGQsIDEgdG8gY2hhbmdlLCAwIHRvIGRlc3Ryb3k/\x1b\\"
    )
    assert _decoded_fields(sequence)[0] == message


def test_c1_controls_in_text_become_spaces() -> None:
    sequence = encode("working", msg="a\x85b\x9fc")
    assert _decoded_fields(sequence)[0] == "a b c"


def test_msg_and_title_are_base64() -> None:
    sequence = encode("working", app="make", msg="Building docs", title="Docs")
    assert sequence == (
        "\x1b]7501;state=working:app=make:title=RG9jcw==:msg=QnVpbGRpbmcgZG9jcw==\x1b\\"
    )


def test_controls_in_text_become_spaces() -> None:
    sequence = encode("working", msg="a\x7fb\nc", title="\n")
    msg, title = _decoded_fields(sequence)
    assert msg == "a b c"
    assert title == " "


def test_msg_cuts_on_a_code_point_boundary() -> None:
    sequence = encode("working", msg="é" * 2048)
    decoded = _decoded_fields(sequence)[0]
    assert decoded is not None
    assert len(decoded.encode("utf-8")) <= 2048
    assert decoded == "é" * 1024


def test_empty_text_is_omitted() -> None:
    assert encode("working", msg="") == "\x1b]7501;state=working\x1b\\"


def test_lone_surrogate_is_replaced() -> None:
    # str.encode(..., errors="replace") writes "?" for a lone surrogate.
    decoded = _decoded_fields(encode("working", msg="\ud800"))[0]
    assert decoded == "?"


def test_largest_legal_report_stays_under_4096_bytes() -> None:
    record_id = "/".join(("a" * 32, "b" * 32, "c" * 32, "d" * 29))
    assert len(record_id.encode("utf-8")) == 128
    sequence = encode(
        "blocked",
        id=record_id,
        kind="permission",
        progress=100,
        app="a" * 32,
        title="b" * 192,
        msg="c" * 2048,
    )
    assert len(sequence.encode("ascii")) < 4096


def _decoded_fields(sequence: str) -> tuple[str | None, str | None]:
    body = sequence.removeprefix("\x1b]7501;").removesuffix("\x1b\\")
    found: dict[str, str] = {}
    for pair in body.split(":"):
        key, value = pair.split("=", 1)
        if key in {"msg", "title"}:
            found[key] = base64.b64decode(value).decode("utf-8")
    return found.get("msg"), found.get("title")
