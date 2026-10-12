from osc7501 import State, encode


def test_working_is_the_state_only_sequence() -> None:
    assert encode("working") == "\x1b]7501;state=working\x1b\\"
    assert encode(State.WORKING) == "\x1b]7501;state=working\x1b\\"
