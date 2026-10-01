"""Slow-path input events and input PDU wrapping."""

import pytest

from aardwolf.protocol.T128.inputeventpdu import TS_INPUT_PDU_DATA
from aardwolf.protocol.T128.share import PDUTYPE2, STREAM_TYPE, CompType, TS_SHARECONTROLHEADER, TS_SHAREDATAHEADER, PDUTYPE
from aardwolf.protocol.pdu.input import INPUT_EVENT, TS_INPUT_EVENT
from aardwolf.protocol.pdu.input.keyboard import KBDFLAGS, TS_KEYBOARD_EVENT
from aardwolf.protocol.pdu.input.mouse import PTRFLAGS, TS_POINTER_EVENT
from aardwolf.protocol.pdu.input.sync import TS_SYNC, TS_SYNC_EVENT
from aardwolf.protocol.pdu.input.unicode import TS_UNICODE_KEYBOARD_EVENT


pytestmark = pytest.mark.unit


def test_keyboard_event_round_trip():
    event = TS_KEYBOARD_EVENT()
    event.keyboardFlags = KBDFLAGS(0)
    event.keyCode = 0x1C
    parsed = TS_KEYBOARD_EVENT.from_bytes(event.to_bytes())
    assert parsed.keyCode == 0x1C
    assert parsed.to_bytes() == event.to_bytes()


def test_keyboard_release_extended_flag():
    event = TS_KEYBOARD_EVENT()
    event.keyboardFlags = KBDFLAGS.RELEASE | KBDFLAGS.EXTENDED
    event.keyCode = 0x1D
    parsed = TS_KEYBOARD_EVENT.from_bytes(event.to_bytes())
    assert KBDFLAGS.RELEASE in parsed.keyboardFlags
    assert KBDFLAGS.EXTENDED in parsed.keyboardFlags


def test_mouse_event_round_trip():
    event = TS_POINTER_EVENT()
    event.pointerFlags = PTRFLAGS.MOVE | PTRFLAGS.DOWN | PTRFLAGS.BUTTON1
    event.xPos = 100
    event.yPos = 200
    parsed = TS_POINTER_EVENT.from_bytes(event.to_bytes())
    assert parsed.xPos == 100
    assert parsed.yPos == 200
    assert PTRFLAGS.BUTTON1 in parsed.pointerFlags
    assert parsed.to_bytes() == event.to_bytes()


def test_unicode_event_round_trip():
    event = TS_UNICODE_KEYBOARD_EVENT()
    event.keyboardFlags = KBDFLAGS(0)
    event.unicodeCode = "A"
    parsed = TS_UNICODE_KEYBOARD_EVENT.from_bytes(event.to_bytes())
    assert parsed.unicodeCode == "A"
    assert parsed.to_bytes() == event.to_bytes()


def test_sync_event_round_trip():
    event = TS_SYNC_EVENT()
    event.pad2Octets = b"\x00\x00"
    event.toggleFlags = TS_SYNC.CAPS_LOCK | TS_SYNC.NUM_LOCK
    parsed = TS_SYNC_EVENT.from_bytes(event.to_bytes())
    assert TS_SYNC.CAPS_LOCK in parsed.toggleFlags
    assert parsed.to_bytes() == event.to_bytes()


def test_input_event_wrapper_round_trip():
    keyboard = TS_KEYBOARD_EVENT()
    keyboard.keyboardFlags = KBDFLAGS(0)
    keyboard.keyCode = 30
    wrapped = TS_INPUT_EVENT.from_input(keyboard)
    parsed = TS_INPUT_EVENT.from_bytes(wrapped.to_bytes())
    assert parsed.messageType == INPUT_EVENT.SCANCODE
    assert parsed.input.keyCode == 30
    assert parsed.to_bytes() == wrapped.to_bytes()


def test_input_pdu_data_body_round_trip():
    keyboard = TS_KEYBOARD_EVENT()
    keyboard.keyboardFlags = KBDFLAGS.RELEASE
    keyboard.keyCode = 16
    event = TS_INPUT_EVENT.from_input(keyboard)
    pdu = TS_INPUT_PDU_DATA()
    pdu.slowPathInputEvents = [event]
    body = pdu.to_bytes()

    header = TS_SHAREDATAHEADER()
    header.shareControlHeader = TS_SHARECONTROLHEADER()
    header.shareControlHeader.totalLength = 18 + len(body)
    header.shareControlHeader.pduType = PDUTYPE.DATAPDU
    header.shareControlHeader.pduVersion = 1
    header.shareControlHeader.pduSource = 1004
    header.shareID = 0x000103EA
    header.streamID = STREAM_TYPE.MED
    header.uncompressedLength = len(body) + 4
    header.pduType2 = PDUTYPE2.INPUT
    header.compressedType = CompType(0)
    header.compressedLength = 0

    parsed = TS_INPUT_PDU_DATA.from_bytes(header.to_bytes() + body)
    assert parsed.numEvents == 1
    assert parsed.slowPathInputEvents[0].input.keyCode == 16
