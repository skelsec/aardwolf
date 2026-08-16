"""Keyboard layout manager lookups for the default US layout."""

import pytest

from aardwolf.keyboard.layoutmanager import KeyboardLayoutManager


pytestmark = pytest.mark.unit


def test_enus_layout_maps_ascii_letters():
    manager = KeyboardLayoutManager()
    layout = manager.get_layout_by_shortname("enus")
    assert layout is not None
    scancode, modifiers = layout.char_to_scancode("a")
    assert scancode is not None
    assert int(modifiers) == 0
    shifted, shift_modifiers = layout.char_to_scancode("A")
    assert shifted is not None
    assert int(shift_modifiers) != 0 or shifted != scancode


def test_unknown_shortname_returns_none():
    manager = KeyboardLayoutManager()
    assert manager.get_layout_by_shortname("not-a-layout") is None


def test_klid_and_name_iterators_include_us():
    manager = KeyboardLayoutManager()
    shortnames = set(manager.get_shortnames())
    assert "enus" in shortnames
    names = set(manager.get_names())
    assert any("US" in name or "United States" in name for name in names)
