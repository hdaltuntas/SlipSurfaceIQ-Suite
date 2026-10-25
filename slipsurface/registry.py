"""Discovery of application manifests: bundled first, installed plugins second.

An application is described by a manifest (``app.json``). Manifests are the
only thing the shell reads before it knows anything about an application's
code, so this module is standard-library only and never imports application
code. Two sources are merged:

    bundled    every ``slipsurface/<key>/app.json`` shipped with the Suite
    installed  plugins that register a ``slipsurface.apps`` entry point

On a key collision the installed plugin wins, so an installed application
always overrides the bundled one with the same key. The result is sorted by
(``order``, ``key``) and is deterministic on every run.
"""
from __future__ import annotations

import json
from importlib.metadata import entry_points
from pathlib import Path
from typing import Callable

from slipsurface.versioning import VersionError, is_compatible, parse

__all__ = [
    "ManifestError",
    "REQUIRED_FIELDS",
    "ENTRY_POINT_GROUP",
    "load_manifest",
    "discover",
]

#: The ``importlib.metadata`` group a plugin registers its manifest under
ENTRY_POINT_GROUP = "slipsurface.apps"

#: Every manifest must carry these fields, with usable values
REQUIRED_FIELDS = (
    "key",
    "name",
    "tr",
    "group",
    "description",
    "description_tr",
    "version",
)


class ManifestError(ValueError):
    """A manifest that is missing, unreadable or not a valid application."""


def load_manifest(data) -> dict:
    """Validate one manifest mapping (already decoded from JSON or a plugin).

    Unknown fields are preserved, so a newer application can carry extra
    metadata that older shells simply ignore. Returns the same mapping.
    """
    if not isinstance(data, dict):
        raise ManifestError("manifest must be a JSON object")
    for field in REQUIRED_FIELDS:
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ManifestError(f"manifest field {field!r} is missing or empty")
    if not data["key"].isidentifier():
        raise ManifestError(f"manifest key {data['key']!r} is not an identifier")
    try:
        parse(data["version"])
    except VersionError as error:
        raise ManifestError(f"manifest version is invalid: {error}") from error
    try:
        is_compatible("0.0.0", data.get("requires_core", ""))
    except VersionError as error:
        raise ManifestError(f"manifest requires_core is invalid: {error}") from error
    return data


def _entry_point_manifests() -> list[dict]:
    """Manifests of applications installed as plugins.

    A plugin registers an entry point in the ``slipsurface.apps`` group whose
    value resolves to a callable returning the manifest mapping, e.g.::

        [project.entry-points."slipsurface.apps"]
        pile = "slipsurface_pile:manifest"

    A plugin that is broken must not take down discovery, so every entry
    point that fails to load or validate is skipped.
    """
    manifests: list[dict] = []
    for point in entry_points(group=ENTRY_POINT_GROUP):
        try:
            factory: Callable = point.load()
            manifest = load_manifest(factory())
        except Exception:  # noqa: BLE001 - a bad plugin must not break discovery
            continue
        manifests.append(manifest)
    return manifests


def _bundled_manifests() -> list[dict]:
    """Manifests of the applications shipped inside the Suite package."""
    manifests: list[dict] = []
    package = Path(__file__).parent
    for directory in sorted(package.iterdir()):
        manifest_path = directory / "app.json"
        if not manifest_path.is_file():
            continue
        try:
            manifest = load_manifest(json.loads(manifest_path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError, ManifestError):
            continue
        manifests.append(manifest)
    return manifests


def discover() -> list[dict]:
    """Every installed application manifest, bundled ones plus plugins.

    Duplicate keys collapse in favour of the entry-point (installed)
    manifest, and the result is sorted by ``order`` then ``key`` so the
    launchpad is stable whichever way the manifests were read.
    """
    merged: dict[str, dict] = {}
    for manifest in _bundled_manifests() + _entry_point_manifests():
        merged[manifest["key"]] = manifest
    return sorted(
        merged.values(),
        key=lambda manifest: (manifest.get("order", 1000), manifest["key"]),
    )
