"""Per-module release installation: download one application archive, unpack it, make it win.

A release archive is a plain ZIP built by ``scripts/build_module_dist.py``
from one application directory. Its layout is::

    <key>-<version>/                 (a single top folder, or entries at the root)
        app.json                     the manifest of the new release
        slipsurface_<key>/           the application package, importable as-is

``install_release`` downloads the archive named in a release catalogue
record, checks it against the catalogue and against this core's version,
and unpacks it into the user applications directory
(``~/.slipsurface/apps/<key>/`` by default). From the next discovery pass
onward the installed release overrides the bundled module of the same key,
without touching the Suite installation itself — no write access to the
program directory, no pip, no restart of the shell beyond refreshing the
catalogue.

The whole module is standard-library only and Qt-free, and the download
step is injectable so the installer is fully testable offline.
"""
from __future__ import annotations

import io
import json
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from slipsurface import CORE_VERSION
from slipsurface.registry import USER_APPS_DIR, load_manifest
from slipsurface.versioning import is_compatible

__all__ = [
    "InstallError",
    "install_release",
    "uninstall",
    "installed_keys",
    "download",
]

#: Refuse archives larger than this before reading them into memory
MAX_ARCHIVE_BYTES = 512 * 1024 * 1024


class InstallError(RuntimeError):
    """A release that cannot be downloaded, unpacked or accepted."""


def download(url: str, timeout: float = 30.0) -> bytes:
    """Read a release archive into memory, refusing unbounded responses."""
    request = urllib.request.Request(url, headers={"User-Agent": "SlipSurfaceIQ-Suite"})
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
        data = response.read(MAX_ARCHIVE_BYTES + 1)
    if len(data) > MAX_ARCHIVE_BYTES:
        raise InstallError(f"release archive is larger than {MAX_ARCHIVE_BYTES} bytes: {url}")
    return data


def _check_archive_names(archive: zipfile.ZipFile) -> None:
    for name in archive.namelist():
        candidate = Path(name)
        if candidate.is_absolute() or ".." in candidate.parts or name.startswith("\\"):
            raise InstallError(f"unsafe path in release archive: {name}")


def _locate_manifest(archive: zipfile.ZipFile) -> tuple[dict, str]:
    """Find the manifest inside the archive and its root directory.

    Accepted layouts: ``app.json`` at the archive root, or inside one single
    top-level folder. Everything unpacks relative to that root.
    """
    names = archive.namelist()
    if "app.json" in names:
        root = ""
    else:
        tops = sorted({name.split("/", 1)[0] for name in names if name.strip()})
        if len(tops) != 1:
            raise InstallError("release archive must contain app.json at its root or in one folder")
        root = f"{tops[0]}/"
    try:
        data = archive.read(f"{root}app.json")
        manifest = load_manifest(json.loads(data.decode("utf-8")))
    except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise InstallError(f"release archive has no valid app.json: {error}") from error
    return manifest, root


def _extract(archive: zipfile.ZipFile, root: str, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    for name in archive.namelist():
        if not name.startswith(root):
            continue
        relative = name[len(root):]
        if not relative or relative.endswith("/"):
            continue
        target = destination.joinpath(*relative.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        with archive.open(name) as source, open(target, "wb") as sink:
            shutil.copyfileobj(source, sink)


def install_release(
    record,
    apps_root: Path | str | None = None,
    core: str = CORE_VERSION,
    fetch=None,
) -> dict:
    """Download and install one release; returns its validated manifest.

    ``record`` is the release-catalogue entry: ``key``, ``version`` and
    ``url`` are required, ``requires_core`` optional. The archive must
    describe exactly the key and version the catalogue announced, and the
    release must accept this core version. Installation replaces any
    previously installed release of the same key atomically enough for a
    single-user desktop tool: the new tree is unpacked beside the old one
    and swapped in, and the old tree is deleted afterwards.
    """
    if not isinstance(record, dict):
        raise InstallError("release record must be a mapping")
    key = str(record.get("key", "")).strip()
    version = str(record.get("version", "")).strip()
    url = str(record.get("url", "")).strip()
    if not key or not version or not url:
        raise InstallError("release record needs key, version and url")
    if not is_compatible(core, record.get("requires_core", "")):
        raise InstallError(f"release {key} {version} needs a newer core than {core}")

    archive_bytes = (fetch or download)(url)
    root_dir = Path(apps_root) if apps_root is not None else USER_APPS_DIR
    destination = root_dir / key

    with tempfile.TemporaryDirectory(prefix=f"slipsurface-{key}-") as staging:
        staged = Path(staging) / "release"
        try:
            with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
                _check_archive_names(archive)
                manifest, root = _locate_manifest(archive)
                if manifest["key"] != key:
                    raise InstallError(
                        f"release archive describes {manifest['key']!r}, not {key!r}"
                    )
                if manifest["version"] != version:
                    raise InstallError(
                        f"release archive is {manifest['version']}, catalogue announced {version}"
                    )
                if not is_compatible(core, manifest.get("requires_core", "")):
                    raise InstallError(
                        f"release {key} {version} needs a newer core than {core}"
                    )
                _extract(archive, root, staged)
        except zipfile.BadZipFile as error:
            raise InstallError(f"release archive is not a valid ZIP: {error}") from error

        root_dir.mkdir(parents=True, exist_ok=True)
        previous = None
        if destination.exists():
            previous = destination.with_name(f"{key}.previous")
            if previous.exists():
                shutil.rmtree(previous)
            destination.rename(previous)
        try:
            staged.rename(destination)
        except OSError:
            if previous is not None:
                previous.rename(destination)
            raise
        if previous is not None:
            shutil.rmtree(previous, ignore_errors=True)
    return manifest


def uninstall(key: str, apps_root: Path | str | None = None) -> bool:
    """Remove an installed release; the bundled module becomes active again."""
    root_dir = Path(apps_root) if apps_root is not None else USER_APPS_DIR
    destination = root_dir / key
    if not destination.is_dir():
        return False
    shutil.rmtree(destination, ignore_errors=True)
    return not destination.exists()


def installed_keys(apps_root: Path | str | None = None) -> list[str]:
    """Keys of the releases currently installed in the user directory."""
    root_dir = Path(apps_root) if apps_root is not None else USER_APPS_DIR
    if not root_dir.is_dir():
        return []
    return sorted(
        directory.name
        for directory in root_dir.iterdir()
        if (directory / "app.json").is_file()
    )
