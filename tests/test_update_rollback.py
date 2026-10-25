"""Regression tests for safe live-module activation and rollback."""
from __future__ import annotations

import hashlib
import io
import json
import zipfile

import pytest

from slipsurface.installer import (
    InstallError,
    finalize_release,
    install_release,
    installed_keys,
    rollback_release,
)
from slipsurface.registry import discover

WORKING_SESSION = """class Session:
    def __init__(self, lang="tr"):
        self.lang = lang
    def meta(self):
        return {"schema": {}, "defaults": {}}
    def analyse(self, values):
        return {"ok": True}
    def plot(self, target, kind):
        return b""
    def report(self, fmt, path):
        return path
    def project_file(self, values):
        return values
    def load_project(self, payload):
        return {"ok": True, "values": payload}
"""


def package(version="1.1.0", source=WORKING_SESSION):
    manifest = {
        "key": "pile", "name": "Pile", "tr": "Kazık", "group": "Foundations",
        "description": "Pile analysis", "description_tr": "Kazık analizi",
        "version": version, "requires_core": ">=0.1.0",
        "session": "slipsurface_pile.web.session",
    }
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("release/app.json", json.dumps(manifest))
        archive.writestr("release/slipsurface_pile/__init__.py", "")
        archive.writestr("release/slipsurface_pile/web/__init__.py", "")
        archive.writestr("release/slipsurface_pile/web/session.py", source)
    raw = stream.getvalue()
    return raw, {
        "key": "pile", "version": version, "url": "https://example.com/pile.zip",
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def install(root, version="1.1.0", source=WORKING_SESSION, retain=False):
    raw, record = package(version, source)
    return install_release(record, apps_root=root, retain_backup=retain, fetch=lambda _: raw)


def version_at(root):
    return json.loads((root / "pile" / "app.json").read_text(encoding="utf-8"))["version"]


def test_preflight_rejects_import_error_without_replacing_existing(tmp_path):
    root = tmp_path / "apps"
    install(root)
    with pytest.raises(InstallError, match="candidate module cannot start"):
        install(root, "1.2.0", 'raise RuntimeError("bad version")\n')
    assert version_at(root) == "1.1.0"
    assert not (root / "pile.previous").exists()


def test_preflight_rejects_missing_session_contract(tmp_path):
    with pytest.raises(InstallError, match="candidate module cannot start"):
        install(tmp_path / "apps", source="class Session: pass\n")
    assert installed_keys(tmp_path / "apps") == []


def test_previous_release_restored_after_failed_native_activation(tmp_path):
    root = tmp_path / "apps"
    install(root)
    install(root, "1.2.0", retain=True)
    assert version_at(root) == "1.2.0"
    assert (root / "pile.previous" / "app.json").is_file()
    rollback_release("pile", apps_root=root, expected_version="1.2.0")
    assert version_at(root) == "1.1.0"
    assert not (root / "pile.previous").exists()


def test_successful_activation_finalizes_only_matching_version(tmp_path):
    root = tmp_path / "apps"
    install(root)
    install(root, "1.2.0", retain=True)
    with pytest.raises(InstallError, match="changed since update"):
        finalize_release("pile", apps_root=root, expected_version="9.0.0")
    assert (root / "pile.previous").exists()
    finalize_release("pile", apps_root=root, expected_version="1.2.0")
    assert version_at(root) == "1.2.0"
    assert not (root / "pile.previous").exists()


def test_failed_first_user_update_returns_to_bundled_module(tmp_path):
    root = tmp_path / "apps"
    install(root, retain=True)
    rollback_release("pile", apps_root=root, expected_version="1.1.0")
    assert installed_keys(root) == []
    assert {item["key"]: item["version"] for item in discover(root)}["pile"] == "1.0.0"


def test_preflight_timeout_never_replaces_working_release(tmp_path, monkeypatch):
    from slipsurface import installer

    root = tmp_path / "apps"
    install(root)

    def timeout(*args, **kwargs):
        raise installer.subprocess.TimeoutExpired(cmd="python", timeout=0.01)

    monkeypatch.setattr(installer.subprocess, "run", timeout)
    with pytest.raises(InstallError, match="could not finish"):
        install(root, "1.2.0")
    assert version_at(root) == "1.1.0"
