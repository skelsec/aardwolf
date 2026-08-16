"""Reusable readers and validators for the known-failure registry."""

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set, Tuple

import yaml


KNOWN_FAILURE_PATTERN = re.compile(r"KF-[0-9]{4}")


@dataclass(frozen=True)
class CanonicalTest:
    path: Path
    function_name: str
    parameter_id: Optional[str]


def load_registry(path: Path) -> Mapping[str, Any]:
    registry = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(registry, dict):
        raise AssertionError("known-failure registry must be a mapping")
    return registry


def active_entries(registry: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    entries = registry.get("known_failures")
    if not isinstance(entries, list):
        raise AssertionError("known_failures must be a list")
    return entries


def parse_canonical_test(repository_root: Path, nodeid: str) -> CanonicalTest:
    try:
        relative_path, test_name = nodeid.split("::", 1)
    except ValueError:
        raise AssertionError(
            "canonical_test must contain a path and test name: {!r}".format(
                nodeid
            )
        )

    parameter_id = None
    if "[" in test_name:
        test_name, parameter_id = test_name.split("[", 1)
        parameter_id = parameter_id.rstrip("]")

    return CanonicalTest(
        path=repository_root / relative_path,
        function_name=test_name,
        parameter_id=parameter_id,
    )


def find_test_function(canonical: CanonicalTest) -> Tuple[str, ast.AST]:
    source = canonical.path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(canonical.path))
    matches = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == canonical.function_name
    ]
    if len(matches) != 1:
        raise AssertionError(
            "{} must define {!r} exactly once".format(
                canonical.path, canonical.function_name
            )
        )
    return source, matches[0]


def xfail_declarations(function: ast.AST) -> Iterable[ast.Call]:
    decorators = getattr(function, "decorator_list", ())
    for decorator in decorators:
        for node in ast.walk(decorator):
            if not isinstance(node, ast.Call):
                continue
            called = node.func
            if isinstance(called, ast.Attribute) and called.attr == "xfail":
                yield node


def strict_xfail_ids(function: ast.AST) -> Set[str]:
    ids: Set[str] = set()
    for call in xfail_declarations(function):
        strict = next(
            (
                keyword.value
                for keyword in call.keywords
                if keyword.arg == "strict"
            ),
            None,
        )
        if not (
            isinstance(strict, ast.Constant)
            and strict.value is True
        ):
            continue
        for node in ast.walk(call):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                ids.update(KNOWN_FAILURE_PATTERN.findall(node.value))
    return ids


def referenced_ids(test_root: Path) -> Dict[str, Set[Path]]:
    references: Dict[str, Set[Path]] = {}
    for path in test_root.rglob("test_*.py"):
        source = path.read_text(encoding="utf-8")
        for known_failure_id in KNOWN_FAILURE_PATTERN.findall(source):
            references.setdefault(known_failure_id, set()).add(path)
    return references


def relationship_graph(
    entries: Iterable[Mapping[str, Any]]
) -> Dict[str, Set[str]]:
    return {
        str(entry["id"]): set(entry["blocks"])
        for entry in entries
    }


def find_cycle(graph: Mapping[str, Set[str]]) -> Optional[List[str]]:
    visited: Set[str] = set()
    active: Set[str] = set()
    route: List[str] = []

    def visit(node: str) -> Optional[List[str]]:
        if node in active:
            index = route.index(node)
            return route[index:] + [node]
        if node in visited:
            return None

        visited.add(node)
        active.add(node)
        route.append(node)
        for child in graph.get(node, ()):
            cycle = visit(child)
            if cycle is not None:
                return cycle
        route.pop()
        active.remove(node)
        return None

    for node in graph:
        cycle = visit(node)
        if cycle is not None:
            return cycle
    return None
