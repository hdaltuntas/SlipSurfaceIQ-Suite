"""Verified single-module installation with path checks and rollback.

The caller must provide SHA-256 for a trusted release catalogue. A digest
protects bytes in transit but does not make unknown Python code trustworthy.
"""
from __future__ import annotations

import hashlib
import io
import json
import logging
import re
import shutil
import stat
import tempfile
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath, PureWindowsPath

from slipsurface import CORE_VERSION
from slipsurface.registry import USER_APPS_DIR, load_manifest
from slipsurface.versioning import is_compatible

__all__ = ["InstallError", "install_release", "uninstall", "installed_keys", "download"]

LOG = logging.getLogger(__name__)

MAX_ARCHIVE_BYTES = 512 * 1024 * 1024
MAX_UNPACKED_BYTES = 1024 * 1024 * 1024
MAX_ENTRY_BYTES = 256 * 1024 * 1024
MAX_ENTRIES = 20000
MAX_MANIFEST_BYTES = 65536
_SAFE_KEY = re.compile(r"[a-z][a-z0-9_]*\Z")
_SHA256 = re.compile(r"[0-9a-fA-F]{64}\Z")


class InstallError(RuntimeError):
    """Unsafe or incompatible module release."""


def _key(value: object) -> str:
    if not isinstance(value, str) or not _SAFE_KEY.fullmatch(value):
        raise InstallError(f"invalid application key: {value!r}")
    return value


def _url(value: object) -> str:
    url = str(value or "").strip()
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in ("https", "file"):
        raise InstallError("release URL must use HTTPS or an explicit local file URL")
    if parsed.scheme == "https" and not parsed.hostname:
        raise InstallError("HTTPS release URL must specify a host")
    if parsed.scheme == "file" and parsed.netloc not in ("", "localhost"):
        raise InstallError("file URL must refer to a local path")
    if parsed.username or parsed.password:
        raise InstallError("release URL cannot contain user credentials")
    return url


def download(url: str, timeout: float = 30.0) -> bytes:
    """Download bounded bytes from HTTPS or an intentional offline file URL."""
    request = urllib.request.Request(_url(url), headers={"User-Agent": "SlipSurfaceIQ-Suite"})
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
        data = response.read(MAX_ARCHIVE_BYTES + 1)
    if len(data) > MAX_ARCHIVE_BYTES:
        raise InstallError("compressed release archive exceeds size limit")
    return data


def _check_archive_names(archive: zipfile.ZipFile) -> None:
    infos = archive.infolist()
    if len(infos) > MAX_ENTRIES:
        raise InstallError("release archive contains too many entries")
    unpacked = 0
    seen = set()
    for info in infos:
        name = info.filename
        parts = PurePosixPath(name).parts
        if (
            not name or "\x00" in name or "\\" in name
            or name.startswith("/") or PureWindowsPath(name).is_absolute()
            or ":" in name or any(part in ("", ".", "..") for part in name.rstrip("/").split("/"))
        ):
            raise InstallError(f"unsafe path in release archive: {name!r}")
        folded = "/".join(parts).casefold()
        if folded in seen:
            raise InstallError(f"duplicate release archive entry: {name}")
        seen.add(folded)
        kind = stat.S_IFMT(info.external_attr >> 16)
        if kind not in (0, stat.S_IFREG, stat.S_IFDIR):
            raise InstallError(f"symlinks and special files are not allowed: {name}")
        if info.file_size > MAX_ENTRY_BYTES:
            raise InstallError(f"oversized file in release archive: {name}")
        unpacked += info.file_size
        if unpacked > MAX_UNPACKED_BYTES:
            raise InstallError("release archive expands beyond size limit")


def _locate_manifest(archive: zipfile.ZipFile) -> tuple[dict, str]:
    names = archive.namelist()
    if "app.json" in names:
        root = ""
    else:
        tops = sorted({name.split("/", 1)[0] for name in names})
        if len(tops) != 1:
            raise InstallError("release archive must contain one top-level directory")
        root = f"{tops[0]}/"
    if any(not name.startswith(root) for name in names):
        raise InstallError("release archive contains files outside its root")
    try:
        entry = archive.getinfo(f"{root}app.json")
        if entry.file_size > MAX_MANIFEST_BYTES:
            raise InstallError("release manifest is too large")
        data = archive.read(entry)
        manifest = load_manifest(json.loads(data.decode("utf-8")))
    except (KeyError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise InstallError(f"invalid release manifest: {error}") from error
    return manifest, root


def _extract(archive: zipfile.ZipFile, root: str, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    total = 0
    for info in archive.infolist():
        if not info.filename.startswith(root):
            raise InstallError(f"release path escapes root: {info.filename}")
        relative = info.filename[len(root):].rstrip("/")
        if not relative:
            continue
        target = destination.joinpath(*relative.split("/"))
        if info.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        count = 0
        with archive.open(info) as source, open(target, "xb") as sink:
            while True:
                chunk = source.read(1024 * 1024)
                if not chunk:
                    break
                count += len(chunk)
                total += len(chunk)
                if count > MAX_ENTRY_BYTES or total > MAX_UNPACKED_BYTES:
                    raise InstallError("extracted release exceeds size limit")
                sink.write(chunk)


def _check_layout(archive: zipfile.ZipFile, root: str, key: str) -> None:
    """Allow only ``app.json`` and the ``slipsurface_<key>`` package at the top.

    The installed directory goes onto the front of ``sys.path``, so any other
    top-level module could shadow the standard library or the Suite.
    """
    package = f"slipsurface_{key}"
    for name in archive.namelist():
        relative = name[len(root):]
        if not relative or relative == "app.json":
            continue
        if relative.split("/", 1)[0] != package or relative == package:
            raise InstallError(f"unexpected top-level entry in release archive: {name}")


def _is_stale_backup(backup: Path, destination: Path, key: str) -> bool:
    """Whether ``backup`` is the leftover copy of a release replaced earlier.

    That is the case only when a live release sits at ``destination`` and the
    backup holds a manifest of the same key; anything else is left alone.
    """
    if not (destination / "app.json").is_file():
        return False
    try:
        manifest = json.loads((backup / "app.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return isinstance(manifest, dict) and manifest.get("key") == key


def install_release(
    record, apps_root: Path | str | None = None, core: str = CORE_VERSION, fetch=None
) -> dict:
    """Verify a release then replace one user-installed module with rollback."""
    if not isinstance(record, dict):
        raise InstallError("release record must be a mapping")
    key = _key(record.get("key"))
    version = str(record.get("version") or "").strip()
    url = _url(record.get("url"))
    digest = record.get("sha256")
    if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
        raise InstallError("release catalogue must provide a 64-character SHA-256 checksum")
    if not is_compatible(core, record.get("requires_core", "")):
        raise InstallError(
            f"release {key} {version} requires core {record.get('requires_core')!r}, "
            f"this Suite has {core}"
        )
    archive_bytes = (fetch or download)(url)
    if not isinstance(archive_bytes, bytes) or len(archive_bytes) > MAX_ARCHIVE_BYTES:
        raise InstallError("release payload is not bounded bytes")
    if hashlib.sha256(archive_bytes).hexdigest() != digest.lower():
        raise InstallError("release archive checksum does not match the catalogue")

    root_dir = Path(apps_root) if apps_root is not None else USER_APPS_DIR
    destination = root_dir / key
    backup = root_dir / f"{key}.previous"
    try:
        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
            _check_archive_names(archive)
            manifest, root = _locate_manifest(archive)
            if manifest["key"] != key:
                raise InstallError(f"release describes {manifest['key']!r}, not {key!r}")
            if manifest["version"] != version:
                raise InstallError("release version differs from the catalogue")
            if not is_compatible(core, manifest.get("requires_core", "")):
                raise InstallError("release manifest requires an incompatible core")
            if manifest.get("session") != f"slipsurface_{key}.web.session":
                raise InstallError("release manifest must name the module session")
            required = {
                f"{root}slipsurface_{key}/__init__.py",
                f"{root}slipsurface_{key}/web/session.py",
            }
            if not required.issubset(archive.namelist()):
                raise InstallError("release archive lacks expected Python package files")
            _check_layout(archive, root, key)
            root_dir.mkdir(parents=True, exist_ok=True)
            if destination.is_symlink() or backup.is_symlink():
                raise InstallError("cannot replace symbolic links")
            if backup.exists() and _is_stale_backup(backup, destination, key):
                shutil.rmtree(backup, ignore_errors=True)
            if backup.exists():
                raise InstallError("previous backup exists; resolve it before updating")
            with tempfile.TemporaryDirectory(prefix=f".{key}-staging-", dir=root_dir) as temp:
                staged = Path(temp) / "release"
                _extract(archive, root, staged)
                had_previous = destination.exists()
                if had_previous:
                    destination.rename(backup)
                try:
                    staged.rename(destination)
                except OSError:
                    if had_previous:
                        backup.rename(destination)
                    raise
                if had_previous:
                    # The new release is live: failing to delete the old copy
                    # (a locked file, say) must not report the update as failed.
                    # A leftover backup is never discovered as a module and is
                    # cleared before the next update.
                    try:
                        shutil.rmtree(backup)
                    except OSError:
                        LOG.warning("could not remove the previous release at %s", backup)
    except (zipfile.BadZipFile, EOFError) as error:
        raise InstallError(f"invalid release ZIP: {error}") from error
    return manifest


def uninstall(key: str, apps_root: Path | str | None = None) -> bool:
    """Remove only a validated application directory below the app root."""
    key = _key(key)
    root_dir = Path(apps_root) if apps_root is not None else USER_APPS_DIR
    destination = root_dir / key
    if destination.is_symlink():
        raise InstallError("cannot uninstall a symbolic link")
    if not destination.is_dir():
        return False
    shutil.rmtree(destination)
    return not destination.exists()


def installed_keys(apps_root: Path | str | None = None) -> list[str]:
    root_dir = Path(apps_root) if apps_root is not None else USER_APPS_DIR
    if not root_dir.is_dir():
        return []
    return sorted(
        directory.name for directory in root_dir.iterdir()
        if _SAFE_KEY.fullmatch(directory.name)
        and not directory.is_symlink()
        and (directory / "app.json").is_file()
    )
