"""Shared collection policy for the staged aardwolf test suite."""

from typing import Iterable, Set, Tuple

import pytest


_OPT_IN_MARKERS: Tuple[Tuple[str, str], ...] = (
    ("xrdp", "--run-xrdp"),
    ("vnc", "--run-vnc"),
    ("slow", "--run-slow"),
    ("destructive", "--run-destructive"),
    ("privileged", "--run-privileged"),
    ("quarantine", "--run-quarantine"),
)


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("aardwolf safety gates")
    for marker, option in _OPT_IN_MARKERS:
        group.addoption(
            option,
            action="store_true",
            default=False,
            help="run tests marked {!r}".format(marker),
        )
    group.addoption(
        "--capability",
        action="append",
        default=[],
        metavar="NAME",
        help="declare an available target capability; may be repeated",
    )


def _required_capabilities(item: pytest.Item) -> Iterable[str]:
    for marker in item.iter_markers(name="capability"):
        if not marker.args:
            raise pytest.UsageError(
                "{}: capability marker requires at least one name".format(
                    item.nodeid
                )
            )
        for capability in marker.args:
            if not isinstance(capability, str):
                raise pytest.UsageError(
                    "{}: capability names must be strings".format(item.nodeid)
                )
            yield capability


def pytest_collection_modifyitems(
    config: pytest.Config, items: Iterable[pytest.Item]
) -> None:
    available_capabilities: Set[str] = set(config.getoption("capability"))

    for item in items:
        for marker, option in _OPT_IN_MARKERS:
            if item.get_closest_marker(marker) and not config.getoption(option):
                item.add_marker(
                    pytest.mark.skip(
                        reason="requires explicit {} opt-in".format(option)
                    )
                )

        missing = set(_required_capabilities(item)) - available_capabilities
        if missing:
            item.add_marker(
                pytest.mark.skip(
                    reason="missing capabilities: {}".format(
                        ", ".join(sorted(missing))
                    )
                )
            )
