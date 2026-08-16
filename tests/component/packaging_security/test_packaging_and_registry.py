"""Packaging metadata and known-failure registry integrity."""

from pathlib import Path

import pytest
import tomllib

from tests.component.packaging_security._known_failures import (
    active_entries,
    find_cycle,
    find_test_function,
    load_registry,
    parse_canonical_test,
    relationship_graph,
    strict_xfail_ids,
)
from tests.support import reporting


pytestmark = pytest.mark.component

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
REGISTRY_PATH = REPOSITORY_ROOT / "tests" / "known_failures.yml"


def test_pyproject_declares_native_extensions_and_scripts():
    document = tomllib.loads(
        (REPOSITORY_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    scripts = document["project"]["scripts"]
    assert scripts["ardpscan"] == "aardwolf.examples.scanners.__main__:main"
    modules = document["tool"]["setuptools"]["py-modules"]
    assert "librlers" in modules
    rust_targets = [
        item["target"] for item in document["tool"]["setuptools-rust"]["ext-modules"]
    ]
    assert "aardwolf._rle" in rust_targets
    assert "aardwolf._bulk" in rust_targets


def test_librlers_reexports_native_rle():
    import aardwolf._rle
    import librlers

    assert librlers.bitmap_decompress is aardwolf._rle.bitmap_decompress
    assert librlers.decode_rre is aardwolf._rle.decode_rre


def test_known_failure_registry_schema_and_uniqueness():
    registry = load_registry(REGISTRY_PATH)
    entries = active_entries(registry)
    assert registry["schema_version"] == 1
    ids = [entry["id"] for entry in entries]
    assert ids == sorted(ids)
    assert len(ids) == len(set(ids))
    required = set(registry["schema"]["entry_required"])
    for entry in entries:
        assert required <= set(entry)


def test_known_failure_blocker_graph_is_acyclic():
    entries = active_entries(load_registry(REGISTRY_PATH))
    cycle = find_cycle(relationship_graph(entries))
    assert cycle is None


def test_known_failure_canonical_tests_are_strict_xfails():
    entries = active_entries(load_registry(REGISTRY_PATH))
    for entry in entries:
        canonical = parse_canonical_test(REPOSITORY_ROOT, entry["canonical_test"])
        _source, function = find_test_function(canonical)
        assert entry["id"] in strict_xfail_ids(function)


def test_reporting_summarizes_junit_without_hostnames(tmp_path):
    junit = tmp_path / "junit.xml"
    junit.write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<testsuite tests="2" failures="0" skipped="0">
  <testcase classname="tests.unit.example" name="test_pass" time="0.01"/>
  <testcase classname="tests.unit.example" name="test_skip" time="0.00">
    <skipped type="pytest.skip" message="requires explicit --run-xrdp"/>
  </testcase>
</testsuite>
""",
        encoding="utf-8",
    )
    json_output = tmp_path / "summary.json"
    markdown_output = tmp_path / "summary.md"
    report = reporting.run(
        reporting.build_parser().parse_args(
            [
                "--junit",
                str(junit),
                "--registry",
                str(REGISTRY_PATH),
                "--json-output",
                str(json_output),
                "--markdown-output",
                str(markdown_output),
            ]
        )
    )
    assert report["counts"]["passed"] == 1
    assert report["counts"]["skipped"] == 1
    markdown = markdown_output.read_text(encoding="utf-8")
    assert "aardwolf test report" in markdown
    assert "10.0.0." not in markdown
    assert "password" not in markdown.lower()
