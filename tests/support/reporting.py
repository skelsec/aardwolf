#!/usr/bin/env python3
"""Create secret-minimal summaries from pytest JUnit and failure registries."""

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ElementTree
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

import yaml


KNOWN_FAILURE_PATTERN = re.compile(r"\bKF-[0-9]{4}\b")
ALLOWED_STATUSES = {"confirmed", "planned", "resolved"}
ALLOWED_CLASSIFICATIONS = {
    "production_defect",
    "planned_feature",
    "environment",
}


class ReportError(Exception):
    """An input report could not be summarized safely."""


@dataclass(frozen=True)
class TestCounts:
    passed: int = 0
    skipped: int = 0
    xfailed: int = 0
    failed: int = 0

    @property
    def total(self) -> int:
        return self.passed + self.skipped + self.xfailed + self.failed

    def add(self, other: "TestCounts") -> "TestCounts":
        return TestCounts(
            passed=self.passed + other.passed,
            skipped=self.skipped + other.skipped,
            xfailed=self.xfailed + other.xfailed,
            failed=self.failed + other.failed,
        )

    def as_dict(self) -> Mapping[str, int]:
        return {
            "total": self.total,
            "passed": self.passed,
            "skipped": self.skipped,
            "xfailed": self.xfailed,
            "failed": self.failed,
        }


@dataclass(frozen=True)
class JUnitSummary:
    counts: TestCounts
    xfailed_ids: Tuple[str, ...]
    skipped_ids: Tuple[str, ...]
    failed_ids: Tuple[str, ...]

    def add(self, other: "JUnitSummary") -> "JUnitSummary":
        return JUnitSummary(
            counts=self.counts.add(other.counts),
            xfailed_ids=tuple(sorted(set(self.xfailed_ids) | set(other.xfailed_ids))),
            skipped_ids=tuple(sorted(set(self.skipped_ids) | set(other.skipped_ids))),
            failed_ids=tuple(sorted(set(self.failed_ids) | set(other.failed_ids))),
        )


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _known_failure_ids(element: ElementTree.Element) -> Set[str]:
    text = " ".join(
        list(element.attrib.values())
        + [item for item in element.itertext() if item]
    )
    return set(KNOWN_FAILURE_PATTERN.findall(text))


def summarize_junit(path: Path) -> JUnitSummary:
    """Count testcase outcomes without retaining names or diagnostic text."""
    try:
        root = ElementTree.parse(str(path)).getroot()
    except (ElementTree.ParseError, OSError):
        raise ReportError("invalid or unreadable JUnit XML")

    counts = TestCounts()
    xfailed_ids: Set[str] = set()
    skipped_ids: Set[str] = set()
    failed_ids: Set[str] = set()

    for testcase in root.iter():
        if _local_name(testcase.tag) != "testcase":
            continue
        children = {
            _local_name(child.tag): child
            for child in testcase
            if _local_name(child.tag) in {"error", "failure", "skipped"}
        }
        failed = children.get("failure")
        if failed is None:
            failed = children.get("error")
        skipped = children.get("skipped")

        if failed is not None:
            counts = counts.add(TestCounts(failed=1))
            failed_ids.update(_known_failure_ids(failed))
        elif skipped is not None:
            skip_type = skipped.attrib.get("type", "").lower()
            if skip_type == "pytest.xfail":
                counts = counts.add(TestCounts(xfailed=1))
                xfailed_ids.update(_known_failure_ids(skipped))
            else:
                counts = counts.add(TestCounts(skipped=1))
                skipped_ids.update(_known_failure_ids(skipped))
        else:
            counts = counts.add(TestCounts(passed=1))

    return JUnitSummary(
        counts=counts,
        xfailed_ids=tuple(sorted(xfailed_ids)),
        skipped_ids=tuple(sorted(skipped_ids)),
        failed_ids=tuple(sorted(failed_ids)),
    )


def summarize_junit_files(paths: Iterable[Path]) -> JUnitSummary:
    summary = JUnitSummary(TestCounts(), (), (), ())
    seen = False
    for path in paths:
        seen = True
        summary = summary.add(summarize_junit(path))
    if not seen:
        raise ReportError("at least one JUnit XML input is required")
    return summary


def load_registry_state(path: Path) -> Mapping[str, Tuple[str, str]]:
    """Load only stable, non-diagnostic registry fields used for comparisons."""
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        raise ReportError("invalid or unreadable known-failure registry")
    if not isinstance(document, dict):
        raise ReportError("invalid known-failure registry structure")
    entries = document.get("known_failures")
    if not isinstance(entries, list):
        raise ReportError("invalid known-failure registry structure")

    state: Dict[str, Tuple[str, str]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise ReportError("invalid known-failure registry entry")
        identifier = entry.get("id")
        status = entry.get("status")
        classification = entry.get("classification")
        if (
            not isinstance(identifier, str)
            or KNOWN_FAILURE_PATTERN.fullmatch(identifier) is None
            or status not in ALLOWED_STATUSES
            or classification not in ALLOWED_CLASSIFICATIONS
            or identifier in state
        ):
            raise ReportError("invalid known-failure registry entry")
        state[identifier] = (status, classification)
    return state


def compare_registries(
    current: Mapping[str, Tuple[str, str]],
    baseline: Mapping[str, Tuple[str, str]],
) -> Mapping[str, Any]:
    current_ids = set(current)
    baseline_ids = set(baseline)
    shared = current_ids & baseline_ids
    status_changed = [
        {"id": identifier, "from": baseline[identifier][0], "to": current[identifier][0]}
        for identifier in sorted(shared)
        if current[identifier][0] != baseline[identifier][0]
    ]
    classification_changed = [
        {"id": identifier, "from": baseline[identifier][1], "to": current[identifier][1]}
        for identifier in sorted(shared)
        if current[identifier][1] != baseline[identifier][1]
    ]
    return {
        "available": True,
        "added": sorted(current_ids - baseline_ids),
        "removed": sorted(baseline_ids - current_ids),
        "status_changed": status_changed,
        "classification_changed": classification_changed,
    }


def build_report(
    junit: JUnitSummary,
    registry: Optional[Mapping[str, Tuple[str, str]]] = None,
    baseline_registry: Optional[Mapping[str, Tuple[str, str]]] = None,
) -> Mapping[str, Any]:
    registry_ids = set(registry or {})
    observed_ids = (
        set(junit.xfailed_ids)
        | set(junit.skipped_ids)
        | set(junit.failed_ids)
    )
    changes: Mapping[str, Any] = {"available": False}
    if registry is not None and baseline_registry is not None:
        changes = compare_registries(registry, baseline_registry)

    return {
        "schema_version": 1,
        "counts": junit.counts.as_dict(),
        "known_failures": {
            "xfailed": list(junit.xfailed_ids),
            "skipped": list(junit.skipped_ids),
            "failed": list(junit.failed_ids),
            "unregistered": sorted(observed_ids - registry_ids)
            if registry is not None
            else [],
        },
        "registry_changes": changes,
    }


def _format_ids(values: Sequence[str]) -> str:
    return ", ".join(values) if values else "none"


def render_markdown(report: Mapping[str, Any]) -> str:
    counts = report["counts"]
    known = report["known_failures"]
    changes = report["registry_changes"]
    lines = [
        "## aardwolf test report",
        "",
        "- Total: **{}**".format(counts["total"]),
        "- Passed: **{}**".format(counts["passed"]),
        "- Skipped: **{}**".format(counts["skipped"]),
        "- Xfailed: **{}**".format(counts["xfailed"]),
        "- Failed: **{}**".format(counts["failed"]),
        "",
        "Known-failure observations:",
        "",
        "- Xfailed IDs: {}".format(_format_ids(known["xfailed"])),
        "- Skipped IDs: {}".format(_format_ids(known["skipped"])),
        "- Failed IDs: {}".format(_format_ids(known["failed"])),
        "- Unregistered IDs: {}".format(_format_ids(known["unregistered"])),
    ]
    if changes["available"]:
        status_ids = [item["id"] for item in changes["status_changed"]]
        classification_ids = [
            item["id"] for item in changes["classification_changed"]
        ]
        lines.extend(
            [
                "",
                "Known-failure registry changes:",
                "",
                "- Added: {}".format(_format_ids(changes["added"])),
                "- Removed: {}".format(_format_ids(changes["removed"])),
                "- Status changed: {}".format(_format_ids(status_ids)),
                "- Classification changed: {}".format(
                    _format_ids(classification_ids)
                ),
            ]
        )
    return "\n".join(lines) + "\n"


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Summarize JUnit outcomes and known-failure changes without "
            "copying testcase names or diagnostic text."
        )
    )
    parser.add_argument(
        "--junit",
        action="append",
        required=True,
        metavar="PATH",
        help="JUnit XML input; repeat for multiple test invocations",
    )
    parser.add_argument("--registry", metavar="PATH")
    parser.add_argument("--baseline-registry", metavar="PATH")
    parser.add_argument("--json-output", required=True, metavar="PATH")
    parser.add_argument("--markdown-output", required=True, metavar="PATH")
    return parser


def run(arguments: argparse.Namespace) -> Mapping[str, Any]:
    junit = summarize_junit_files(Path(path) for path in arguments.junit)
    registry = (
        load_registry_state(Path(arguments.registry))
        if arguments.registry
        else None
    )
    baseline = (
        load_registry_state(Path(arguments.baseline_registry))
        if arguments.baseline_registry
        else None
    )
    if baseline is not None and registry is None:
        raise ReportError("a baseline registry requires a current registry")

    report = build_report(junit, registry, baseline)
    markdown = render_markdown(report)
    _write_text(
        Path(arguments.json_output),
        json.dumps(report, indent=2, sort_keys=True) + "\n",
    )
    _write_text(Path(arguments.markdown_output), markdown)
    print(markdown, end="")
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        run(arguments)
    except ReportError as error:
        print("report generation failed: {}".format(error), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
