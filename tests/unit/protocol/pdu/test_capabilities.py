"""Capability-set wrappers and individual capability codecs."""

import pytest

from aardwolf.protocol.pdu.capabilities import CAPSTYPE, TS_CAPS_SET
from aardwolf.protocol.pdu.capabilities.bitmap import TS_BITMAP_CAPABILITYSET
from aardwolf.protocol.pdu.capabilities.control import TS_CONTROL_CAPABILITYSET
from aardwolf.protocol.pdu.capabilities.font import TS_FONT_CAPABILITYSET
from aardwolf.protocol.pdu.capabilities.general import (
    EXTRAFLAG,
    OSMAJORTYPE,
    OSMINORTYPE,
    TS_GENERAL_CAPABILITYSET,
)
from aardwolf.protocol.pdu.capabilities.input import INPUT_FLAG, TS_INPUT_CAPABILITYSET
from aardwolf.protocol.pdu.capabilities.multifragmentupdate import (
    TS_MULTIFRAGMENTUPDATE_CAPABILITYSET,
)
from aardwolf.protocol.pdu.capabilities.pointer import TS_POINTER_CAPABILITYSET
from aardwolf.protocol.pdu.capabilities.share import TS_SHARE_CAPABILITYSET
from aardwolf.protocol.pdu.capabilities.sound import SOUND_FLAG, TS_SOUND_CAPABILITYSET
from aardwolf.protocol.pdu.capabilities.virtualchannel import (
    VCCAPS,
    TS_VIRTUALCHANNEL_CAPABILITYSET,
)


pytestmark = pytest.mark.unit


def round_trip_capability(capability):
    wrapped = TS_CAPS_SET.from_capability(capability)
    parsed = TS_CAPS_SET.from_bytes(wrapped.to_bytes())
    assert parsed.capabilitySetType == wrapped.capabilitySetType
    assert parsed.capability.to_bytes() == capability.to_bytes()
    return parsed


def test_general_capability_round_trip():
    capability = TS_GENERAL_CAPABILITYSET()
    capability.osMajorType = OSMAJORTYPE.WINDOWS
    capability.osMinorType = OSMINORTYPE.WINDOWS_NT
    capability.extraFlags = EXTRAFLAG.FASTPATH_OUTPUT_SUPPORTED
    capability.refreshRectSupport = True
    capability.suppressOutputSupport = True
    parsed = round_trip_capability(capability)
    assert parsed.capabilitySetType == CAPSTYPE.GENERAL
    assert parsed.capability.refreshRectSupport is True


def test_bitmap_capability_round_trip():
    capability = TS_BITMAP_CAPABILITYSET()
    capability.preferredBitsPerPixel = 16
    capability.desktopWidth = 1024
    capability.desktopHeight = 768
    parsed = round_trip_capability(capability)
    assert parsed.capabilitySetType == CAPSTYPE.BITMAP
    assert parsed.capability.desktopWidth == 1024


def test_share_sound_font_pointer_control_round_trips():
    round_trip_capability(TS_SHARE_CAPABILITYSET())
    sound = TS_SOUND_CAPABILITYSET()
    sound.soundFlags = SOUND_FLAG.BEEPS
    round_trip_capability(sound)
    round_trip_capability(TS_FONT_CAPABILITYSET())
    pointer = TS_POINTER_CAPABILITYSET()
    pointer.colorPointerFlag = True
    round_trip_capability(pointer)
    round_trip_capability(TS_CONTROL_CAPABILITYSET())


def test_input_capability_round_trip():
    capability = TS_INPUT_CAPABILITYSET()
    capability.inputFlags = INPUT_FLAG.SCANCODES | INPUT_FLAG.MOUSEX | INPUT_FLAG.UNICODE
    capability.keyboardLayout = 1033
    parsed = round_trip_capability(capability)
    assert parsed.capabilitySetType == CAPSTYPE.INPUT
    assert INPUT_FLAG.UNICODE in parsed.capability.inputFlags
    assert parsed.capability.keyboardLayout == 1033


def test_virtual_channel_capability_with_chunk_size():
    capability = TS_VIRTUALCHANNEL_CAPABILITYSET()
    capability.flags = VCCAPS.COMPR_SC
    capability.VCChunkSize = 1600
    parsed = round_trip_capability(capability)
    assert parsed.capability.VCChunkSize == 1600


def test_virtual_channel_capability_without_chunk_size():
    capability = TS_VIRTUALCHANNEL_CAPABILITYSET()
    capability.flags = VCCAPS.NO_COMPR
    parsed = round_trip_capability(capability)
    assert parsed.capability.VCChunkSize is None


def test_multifragment_capability_round_trip():
    capability = TS_MULTIFRAGMENTUPDATE_CAPABILITYSET()
    capability.MaxRequestSize = 65535
    parsed = round_trip_capability(capability)
    assert parsed.capabilitySetType == CAPSTYPE.MULTIFRAGMENTUPDATE
    assert parsed.capability.MaxRequestSize == 65535
