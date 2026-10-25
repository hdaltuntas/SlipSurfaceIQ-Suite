"""The application catalogue, built from discovered manifests instead of a hard-coded list.

Every application — bundled, entry-point installed or unpacked as a release
archive — carries an ``app.json`` manifest. ``slipsurface.registry`` reads
those manifests; this module wraps each of them in the ``App`` value object
the desktop shell consumes. The public surface (``APPS``, ``keys()``,
``get()``, ``catalogue()``, ``refresh()``) is unchanged for callers that
already used it, so nothing has to care that the catalogue is dynamic.
"""
from __future__ import annotations

from dataclasses import dataclass

from slipsurface import CORE_VERSION
from slipsurface.versioning import is_compatible

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
    session: str = ""
    compatible: bool = True


def _from_manifest(manifest: dict) -> App:
    return App(
        **{field: manifest[field] for field in _FIELDS},
        version=manifest.get("version", "1.0.0"),
        requires_core=manifest.get("requires_core", ""),
        session=manifest.get("session", ""),
        compatible=is_compatible(CORE_VERSION, manifest.get("requires_core", "")),
    )


def _catalogue() -> tuple[App, ...]:
    return tuple(_from_manifest(manifest) for manifest in discover())


APPS = _catalogue()

_BY_KEY = {app.key: app for app in APPS}


def keys() -> list[str]:
    return list(_BY_KEY)


def get(key: str) -> App:
    return _BY_KEY[key]


def catalogue() -> tuple[App, ...]:
    return APPS


def refresh() -> None:
    """Re-read every manifest source and rebuild the catalogue.

    Called after a module release has been installed (or uninstalled), so
    the launchpad, the navigator and new module pages all see the new
    versions without a restart. Pages already open keep their loaded code;
    the shell drops them on refresh and reloads on next open.
    """
    global APPS, _BY_KEY
    APPS = _catalogue()
    _BY_KEY = {app.key: app for app in APPS}


def session_path(key: str) -> str:
    """The dotted import path of an application's session module.

    Bundled applications live at ``slipsurface.<key>.web.session``; a
    release installed into the user directory says where its session is in
    its manifest, and that value wins.
    """
    session = get(key).session
    return session or f"slipsurface.{key}.web.session"


def forms_path(key: str) -> str:
    """The dotted import path of an application's forms module."""
    session = get(key).session
    if not session:
        return f"slipsurface.{key}.forms"
    return f"{session.removesuffix('.web.session')}.forms"
