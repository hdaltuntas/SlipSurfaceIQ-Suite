"""The application catalogue, built from discovered manifests instead of a hard-coded list.

Every application — bundled or installed as a plugin — carries an
``app.json`` manifest next to its code. ``slipsurface.registry`` reads those
manifests; this module wraps each of them in the ``App`` value object the
desktop shell already consumes. The public surface (``APPS``, ``keys()``,
``get()``, ``catalogue()``) is unchanged, so no caller has to care that the
catalogue is now dynamic.
"""
from __future__ import annotations

from dataclasses import dataclass

from slipsurface.registry import discover

#: The ``importlib.metadata`` group a standalone application registers under
ENTRY_POINT_GROUP = "slipsurface.apps"

#: Fields of a manifest that map straight onto the catalogue entry
_FIELDS = ("key", "name", "tr", "group", "description", "description_tr")


@dataclass(frozen=True)
class App:
    """One application as the launchpad and the shell see it."""

    key: str
    name: str
    tr: str
    group: str
    description: str
    description_tr: str = ""
    version: str = "1.0.0"
    requires_core: str = ""


def _from_manifest(manifest: dict) -> App:
    return App(
        **{field: manifest[field] for field in _FIELDS},
        version=manifest.get("version", "1.0.0"),
        requires_core=manifest.get("requires_core", ""),
    )


APPS = tuple(_from_manifest(manifest) for manifest in discover())

_BY_KEY = {app.key: app for app in APPS}


def keys() -> list[str]:
    return list(_BY_KEY)


def get(key: str) -> App:
    return _BY_KEY[key]


def catalogue() -> tuple[App, ...]:
    return APPS
