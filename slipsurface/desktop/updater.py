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
            "requires_core": ">=0.1.0",
            "url": "https://example.com/pile-1.1.0.zip"
        }
    }

The Suite looks for one at ``~/.slipsurface/index.json`` and then
``./slipsurface-index.json``; if neither exists it starts quietly with no
updates, because an offline machine is the normal case.
"""
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from slipsurface import CORE_VERSION
from slipsurface.apps import App, catalogue
from slipsurface.versioning import VersionError, compare, is_compatible

__all__ = ["AppUpdate", "read_index", "read_published_index", "check",
           "load_available_updates"]

#: Where a downloaded release catalogue is expected, in lookup order
INDEX_PATHS = (
    Path.home() / ".slipsurface" / "index.json",
    Path("slipsurface-index.json"),
)

# Trusted project-controlled, public repository path; no API token required.
PUBLISHED_INDEX = (
    "https://raw.githubusercontent.com/hdaltuntas/"
    "SlipSurfaceIQ-Suite/main/module-updates/index.json"
)
MAX_INDEX_BYTES = 64 * 1024
LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class AppUpdate:
    """The comparison of one installed application against the catalogue."""

    key: str
    installed: str
    latest: str
    changelog: str = ""
    requires_core: str = ""
    core_ok: bool = True
    url: str = ""
    sha256: str = ""

    @property
    def update_available(self) -> bool:
        return compare(self.installed, self.latest) < 0


def read_index(path) -> dict:
    """Read and minimally validate a release catalogue file."""
    records = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(records, dict):
        raise ValueError("release catalogue must be a JSON object")
    return records


def read_published_index(url: str = PUBLISHED_INDEX, timeout: float = 5.0) -> dict:
    """Fetch a bounded public catalogue over HTTPS, never Qt's GUI thread."""
    if not url.startswith("https://"):
        raise ValueError("release catalogue must use HTTPS")
    request = urllib.request.Request(
        url, headers={"User-Agent": "SlipSurfaceIQ-Suite-UpdateChecker"}
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        if not response.geturl().startswith("https://"):
            raise ValueError("release catalogue redirected to insecure URL")
        data = response.read(MAX_INDEX_BYTES + 1)
    if len(data) > MAX_INDEX_BYTES:
        raise ValueError("release catalogue exceeds size limit")
    records = json.loads(data.decode("utf-8"))
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
        # A malformed record is skipped on its own, so it cannot hide the
        # valid updates of every other application in the same catalogue.
        try:
            if not latest or compare(app.version, latest) >= 0:
                continue
            requires_core = record.get("requires_core", "") if isinstance(record, dict) else ""
            core_ok = is_compatible(core, requires_core)
        except VersionError:
            continue
        updates[app.key] = AppUpdate(
            key=app.key,
            installed=app.version,
            latest=latest,
            changelog=record.get("changelog", "") if isinstance(record, dict) else "",
            requires_core=requires_core,
            core_ok=core_ok,
            url=record.get("url", "") if isinstance(record, dict) else "",
            sha256=record.get("sha256", "") if isinstance(record, dict) else "",
        )
    return updates


def load_available_updates(include_remote: bool = False) -> dict:
    """Choose the newest valid release per module from local and public indexes.

    The local-only path is fast and works offline. Public checks run on a Qt
    worker thread. An older local catalogue must not suppress newer GitHub
    updates (notably after previous offline trials).
    """
    local_index = {}
    for path in INDEX_PATHS:
        try:
            local_index = read_index(path)
            break
        except (OSError, ValueError, json.JSONDecodeError):
            continue
    if not include_remote:
        return check(local_index)
    try:
        public_index = read_published_index()
    except (OSError, ValueError, UnicodeDecodeError, urllib.error.URLError):
        LOG.info("Remote module catalogue unavailable", exc_info=True)
        return check(local_index)

    merged = dict(public_index)
    for key, local_record in local_index.items():
        local_version = _record_version(local_record)
        public_version = _record_version(public_index.get(key))
        try:
            # Keep local releases for offline/demo tests if equally new or
            # newer. Ignore older/stale or malformed local records.
            if local_version and (
                not public_version or compare(local_version, public_version) >= 0
            ):
                merged[key] = local_record
        except VersionError:
            continue
    return check(merged)
