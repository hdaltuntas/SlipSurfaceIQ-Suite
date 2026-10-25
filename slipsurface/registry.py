"""Discovery of application manifests: bundled, installed plugins, user apps.

An application is described by a manifest (``app.json``). Manifests are the
only thing the shell reads before it knows anything about an application's
code, so this module is standard-library only and never imports application
code. Three sources are merged, weakest first:

    bundled    every ``slipsurface/<key>/app.json`` shipped with the Suite
    plugin     distributions registering a ``slipsurface.apps`` entry point
    installed  release archives unpacked under the user applications
               directory (``~/.slipsurface/apps`` by default), each with an
               ``app.json`` and an importable ``slipsurface_<key>`` package

On a key collision the later, more local source wins: a release installed
into the user directory always overrides the entry-point and bundled
versions of the same key. The result is sorted by ``order``, then ``key`` and
is deterministic on every run.

A release installed under the user applications directory carries its
package next to its manifest, so its parent directory is appended to
``sys.path`` once, at discovery time, to make ``slipsurface_<key>`` importable.
"""
from __future__ import annotations

import json
import os
import re
import sys
from importlib.metadata import entry_points
from pathlib import Path
from typing import Callable

from slipsurface.versioning import VersionError, is_compatible, parse

__all__ = [
    "ManifestError",
    "REQUIRED_FIELDS",
    "ENTRY_POINT_GROUP",
    "USER_APPS_DIR",
    "load_manifest",
    "discover",
]

#: The ``importlib.metadata`` group a plugin registers its manifest under
ENTRY_POINT_GROUP = "slipsurface.apps"
_KEY = re.compile(r"[a-z][a-z0-9_]*\Z")

#: Where per-module release archives are unpacked; an environment override
#: exists for tests and portable installations.
USER_APPS_DIR = Path(
    os.environ.get("SLIPSURFACE_APPS_DIR")
    or (Path.home() / ".slipsurface" / "apps")
)

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
    if not _KEY.fullmatch(data["key"]):
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


def _installed_manifests(apps_root: Path | None = None) -> list[dict]:
    """Manifests of module releases installed into the user directory.

    Each subdirectory that carries an ``app.json`` is one installed release:
    the manifest next to an importable ``slipsurface_<key>`` package. The
    subdirectory is appended to ``sys.path`` so the shell can import the
    application's session from the manifest's ``session`` field.
    """
    root = Path(apps_root) if apps_root is not None else USER_APPS_DIR
    manifests: list[dict] = []
    if not root.is_dir():
        return manifests
    for directory in sorted(root.iterdir()):
        manifest_path = directory / "app.json"
        if not manifest_path.is_file():
            continue
        try:
            manifest = load_manifest(json.loads(manifest_path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError, ManifestError):
            continue
        key = manifest["key"]
        if manifest.get("session") != f"slipsurface_{key}.web.session":
            continue
        if directory.is_symlink():
            continue
        location = str(directory)
        if location not in sys.path:
            sys.path.append(location)
        manifests.append(manifest)
    return manifests


def discover(apps_root: Path | str | None = None) -> list[dict]:
    """Every application manifest, bundled ones plus every installed source.

    Duplicate keys collapse in favour of the most local manifest (installed
    releases first, entry points second, bundled last), and the result is
    sorted by ``order`` then ``key`` so the launchpad is stable whichever
    way the manifests were read.
    """
    merged: dict[str, dict] = {}
    for manifest in (
        _bundled_manifests()
        + _entry_point_manifests()
        + _installed_manifests(apps_root)
    ):
        merged[manifest["key"]] = manifest
    return sorted(
        merged.values(),
        key=lambda manifest: (manifest.get("order", 1000), manifest["key"]),
    )
