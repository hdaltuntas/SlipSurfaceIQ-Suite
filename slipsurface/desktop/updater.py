"""Version comparison between installed applications and a release catalogue.

This module is deliberately free of Qt, so the version logic can be tested
and reused headlessly. The desktop shell calls ``load_available_updates``
once at start-up and passes the result to the launchpad, which shows one
update badge per application that has a newer release.

A release catalogue is a JSON mapping of application keys to release
records, e.g.::

    {
        "pile": {
            "version": "1.1.0",
            "changelog": "Socket side resistance correlations added.",
            "requires_core": ">=0.1.0"
        }
    }

The Suite looks for one at ``~/.slipsurface/index.json`` and then
``./slipsurface-index.json``; if neither exists it starts quietly with no
updates, because an offline machine is the normal case.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from slipsurface import CORE_VERSION
from slipsurface.apps import App, catalogue
from slipsurface.versioning import compare, is_compatible

__all__ = ["AppUpdate", "read_index", "check", "load_available_updates"]

#: Where a downloaded release catalogue is expected, in lookup order
INDEX_PATHS = (
    Path.home() / ".slipsurface" / "index.json",
    Path("slipsurface-index.json"),
)


@dataclass(frozen=True)
class AppUpdate:
    """The comparison of one installed application against the catalogue."""

    key: str
    installed: str
    latest: str
    changelog: str = ""
    requires_core: str = ""
    core_ok: bool = True

    @property
    def update_available(self) -> bool:
        return compare(self.installed, self.latest) < 0


def read_index(path) -> dict:
    """Read and minimally validate a release catalogue file."""
    records = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(records, dict):
        raise ValueError("release catalogue must be a JSON object")
    return records


def _record_version(record) -> str:
    if isinstance(record, str):
        return record
    if isinstance(record, dict):
        return record.get("version", "")
    return ""


def check(index: dict, apps: tuple[App, ...] = None, core: str = CORE_VERSION) -> dict:
    """Update info per application key, for every app the catalogue mentions.

    Only entries with a usable version are considered. An application whose
    catalogue release needs a newer core than this Suite carries is still
    reported, but with ``core_ok`` false, so the interface can say so
    instead of offering an update that cannot run.
    """
    if apps is None:
        apps = catalogue()
    updates: dict[str, AppUpdate] = {}
    for app in apps:
        record = index.get(app.key)
        latest = _record_version(record)
        if not latest or compare(app.version, latest) >= 0:
            continue
        requires_core = record.get("requires_core", "") if isinstance(record, dict) else ""
        updates[app.key] = AppUpdate(
            key=app.key,
            installed=app.version,
            latest=latest,
            changelog=record.get("changelog", "") if isinstance(record, dict) else "",
            requires_core=requires_core,
            core_ok=is_compatible(core, requires_core),
        )
    return updates


def load_available_updates() -> dict:
    """Updates shown on the launchpad; empty when no catalogue is available.

    Never raises: a missing, unreadable or malformed catalogue must not
    stop the Suite from starting.
    """
    for path in INDEX_PATHS:
        try:
            return check(read_index(path))
        except (OSError, ValueError, json.JSONDecodeError):
            continue
    return {}
