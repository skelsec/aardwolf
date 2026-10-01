"""Safety fixtures for explicitly enabled xrdp interoperability tests."""

from pathlib import Path

import pytest

from tests.interop._lab import load_profile, require_reachable


@pytest.fixture(scope="session")
def xrdp_profile(request):
    if not request.config.getoption("--run-xrdp"):
        pytest.skip("requires explicit --run-xrdp opt-in")
    profile = load_profile(
        "AARDWOLF_XRDP_PROFILE",
        Path(__file__).with_name("profile.example.yml"),
    )
    require_reachable(profile)
    return profile
