"""Secret-safe profile loading for disposable RDP and VNC labs."""

from __future__ import annotations

import os
import socket
from pathlib import Path
from typing import Any, Mapping, Optional

import pytest
import yaml


def _required(mapping: Mapping[str, Any], key: str, section: str) -> Any:
    value = mapping.get(key)
    if value in (None, ""):
        raise pytest.UsageError(
            "interop profile field {}.{} is required".format(section, key)
        )
    return value


class LabProfile:
    """Resolved live target settings without a credential-bearing repr."""

    def __init__(self, path: Path, document: Mapping[str, Any]) -> None:
        if document.get("schema_version") != 1:
            raise pytest.UsageError("unsupported interop profile schema")

        target = document.get("target") or {}
        authentication = document.get("authentication") or {}
        overrides = document.get("environment_overrides") or {}
        safety = document.get("safety") or {}

        self.path = path
        self.name = str(_required(document, "name", "root"))
        self.host = str(
            self._environment_value(
                overrides, "host", _required(target, "host", "target")
            )
        )
        port = self._environment_value(
            overrides, "port", _required(target, "port", "target")
        )
        try:
            self.port = int(port)
        except (TypeError, ValueError):
            raise pytest.UsageError("interop profile port must be an integer")

        username_environment = _required(
            authentication, "username_environment", "authentication"
        )
        password_environment = _required(
            authentication, "password_environment", "authentication"
        )
        self.username = os.environ.get(
            str(username_environment),
            str(
                _required(
                    authentication,
                    "test_only_default_username",
                    "authentication",
                )
            ),
        )
        self.password = os.environ.get(
            str(password_environment),
            str(
                _required(
                    authentication,
                    "test_only_default_password",
                    "authentication",
                )
            ),
        )
        self.disposable = safety.get("disposable") is True
        self.capabilities = {
            str(value) for value in document.get("capabilities", [])
        }

    def __repr__(self) -> str:
        return "LabProfile(name={!r}, host={!r}, port={!r})".format(
            self.name, self.host, self.port
        )

    @staticmethod
    def _environment_value(overrides: Mapping[str, Any], name: str, default: Any) -> Any:
        environment_name = overrides.get(name)
        if environment_name:
            return os.environ.get(str(environment_name), default)
        return default

    def require_capability(self, name: str) -> None:
        if name not in self.capabilities:
            pytest.skip(
                "interop profile does not declare capability {!r}".format(name)
            )


def load_profile(environment_name: str, example_path: Path) -> LabProfile:
    configured = os.environ.get(environment_name)
    path = Path(configured).expanduser() if configured else example_path
    if not path.is_file():
        pytest.skip("interop profile is not available")
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise pytest.UsageError("interop profile must be a mapping")
    return LabProfile(path, document)


def require_reachable(profile: LabProfile, timeout: float = 2.0) -> None:
    try:
        connection = socket.create_connection(
            (profile.host, profile.port), timeout=timeout
        )
    except OSError:
        pytest.skip("interop target is not reachable")
    else:
        connection.close()
