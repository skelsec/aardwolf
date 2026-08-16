"""Safety fixtures for explicitly enabled VNC interoperability tests."""

from pathlib import Path

import pytest

from tests.interop._lab import load_profile, require_reachable


@pytest.fixture(scope="session")
def vnc_profile(request):
    if not request.config.getoption("--run-vnc"):
        pytest.skip("requires explicit --run-vnc opt-in")
    profile = load_profile(
        "AARDWOLF_VNC_PROFILE",
        Path(__file__).with_name("profile.example.yml"),
    )
    require_reachable(profile)
    return profile
