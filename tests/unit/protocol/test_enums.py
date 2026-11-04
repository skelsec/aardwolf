"""UnknownValueEnum pseudo-member behaviour."""

import pickle

import pytest

from aardwolf.protocol.enums import UnknownValueEnum


pytestmark = pytest.mark.unit


class SAMPLE(UnknownValueEnum):
    FIRST = 1
    SECOND = 2


def test_known_values_resolve_to_members():
    assert SAMPLE(1) is SAMPLE.FIRST


def test_unknown_value_keeps_raw_value_and_is_cached():
    member = SAMPLE(0x1234)
    assert isinstance(member, SAMPLE)
    assert member.value == 0x1234
    assert member.name == "UNKNOWN_0x1234"
    assert SAMPLE(0x1234) is member
    assert pickle.loads(pickle.dumps(member)) is member


def test_unknown_values_are_not_listed_as_members():
    SAMPLE(0x77)
    assert list(SAMPLE) == [SAMPLE.FIRST, SAMPLE.SECOND]
    assert "UNKNOWN_0x0077" not in SAMPLE.__members__


@pytest.mark.parametrize("value", ["1", 1.5, None, False])
def test_non_integer_values_are_rejected(value):
    with pytest.raises(ValueError):
        SAMPLE(value)
