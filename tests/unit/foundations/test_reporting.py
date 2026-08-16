"""Reporting helper unit coverage."""

from pathlib import Path

import pytest

from tests.support.reporting import (
    ReportError,
    build_report,
    load_registry_state,
    summarize_junit,
)


pytestmark = pytest.mark.unit


def test_summarize_junit_counts_xfail(tmp_path):
    path = tmp_path / "junit.xml"
    path.write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<testsuite tests="1">
  <testcase classname="t" name="n">
    <skipped type="pytest.xfail" message="KF-0001: example"/>
  </testcase>
</testsuite>
""",
        encoding="utf-8",
    )
    summary = summarize_junit(path)
    assert summary.counts.xfailed == 1
    assert "KF-0001" in summary.xfailed_ids


def test_load_registry_state_rejects_invalid_document(tmp_path):
    path = tmp_path / "bad.yml"
    path.write_text("not: valid: registry\n", encoding="utf-8")
    with pytest.raises(ReportError):
        load_registry_state(path)


def test_build_report_without_registry():
    from tests.support.reporting import JUnitSummary, TestCounts

    report = build_report(JUnitSummary(TestCounts(passed=1), (), (), ()))
    assert report["counts"]["passed"] == 1
    assert report["known_failures"]["unregistered"] == []
