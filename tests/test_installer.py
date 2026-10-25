"""Per-module release installation: archive layout, precedence and rollback."""
import hashlib
import io
import json
import sys
import zipfile

import pytest

from slipsurface import installer
from slipsurface.desktop.updater import AppUpdate, check
from slipsurface.installer import (
    InstallError,
    confirm_release,
    install_release,
    installed_keys,
    rollback_release,
    uninstall,
)
from slipsurface.registry import discover

EXPECTED_ORDER = [
    "kinematic", "rock", "bearing", "settle", "correlation",
    "liquefaction", "pile", "spwa", "msew", "wall",
]


def _manifest(key="pile", version="1.1.0", requires_core=">=0.1.0"):
    return {
        "key": key,
        "name": "Pile",
        "tr": "Kazık",
        "group": "Foundations",
        "description": "Axial capacity, group and socket assessment",
        "description_tr": "Kazıkların eksenel kapasitesi, grup etkisi ve soket analizi.",
        "version": version,
        "requires_core": requires_core,
        "order": 7,
        "session": f"slipsurface_{key}.web.session",
    }


VALID_SESSION = """class Session:
    def __init__(self, lang="tr"):
        self.lang = lang
    def meta(self):
        return {"schema": {"project": {"groups": []}}, "defaults": {"title": "demo"}}
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


def _archive_bytes(manifest, top="release", source=VALID_SESSION):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(f"{top}/app.json", json.dumps(manifest))
        archive.writestr(f"{top}/slipsurface_{manifest['key']}/__init__.py", "")
        archive.writestr(f"{top}/slipsurface_{manifest['key']}/web/session.py", source)
    return buffer.getvalue()


def _record(key="pile", version="1.1.0", url="https://example.com/pile-1.1.0.zip",
            requires_core=">=0.1.0", sha256=None):
    if sha256 is None:
        sha256 = hashlib.sha256(_archive_bytes(_manifest(
            key=key, version=version, requires_core=requires_core
        ))).hexdigest()
    return {
        "key": key, "version": version, "url": url,
        "requires_core": requires_core, "sha256": sha256,
    }


def test_install_release_unpacks_and_reports_the_manifest(tmp_path):
    apps = tmp_path / "apps"
    manifest = install_release(
        _record(), apps_root=apps, fetch=lambda url: _archive_bytes(_manifest())
    )
    assert manifest["key"] == "pile" and manifest["version"] == "1.1.0"
    assert (apps / "pile" / "app.json").is_file()
    assert (apps / "pile" / "slipsurface_pile" / "web" / "session.py").is_file()
    assert installed_keys(apps) == ["pile"]
    # A second install replaces the first in place.
    manifest = install_release(
        _record(version="1.2.0", url="https://example.com/pile-1.2.0.zip"), apps_root=apps,
        fetch=lambda url: _archive_bytes(_manifest(version="1.2.0")),
    )
    assert manifest["version"] == "1.2.0"
    assert installed_keys(apps) == ["pile"]
    assert not (apps / "pile.previous").exists()


def test_installed_release_overrides_the_bundled_module(tmp_path):
    apps = tmp_path / "apps"
    assert [m["key"] for m in discover(apps)] == EXPECTED_ORDER
    install_release(
        _record(), apps_root=apps, fetch=lambda url: _archive_bytes(_manifest())
    )
    manifests = {m["key"]: m for m in discover(apps)}
    assert manifests["pile"]["version"] == "1.1.0"
    assert manifests["pile"]["session"] == "slipsurface_pile.web.session"
    assert [m["key"] for m in discover(apps)] == EXPECTED_ORDER  # order preserved
    assert uninstall("pile", apps_root=apps) is True
    manifests = {m["key"]: m for m in discover(apps)}
    assert manifests["pile"]["version"] == "1.0.0"  # bundled again
    assert uninstall("pile", apps_root=apps) is False


def test_install_rejects_mismatched_key_version_and_core(tmp_path):
    apps = tmp_path / "apps"
    try:
        install_release(
            _record(), apps_root=apps, fetch=lambda url: _archive_bytes(_manifest(key="rock"))
        )
        raise AssertionError("a key mismatch must be refused")
    except InstallError:
        pass
    try:
        install_release(
            _record(version="1.5.0"), apps_root=apps,
            fetch=lambda url: _archive_bytes(_manifest(version="1.1.0")),
        )
        raise AssertionError("a version mismatch must be refused")
    except InstallError:
        pass
    try:
        install_release(
            _record(requires_core=">=9.0.0"), apps_root=apps,
            fetch=lambda url: _archive_bytes(_manifest(requires_core=">=9.0.0")),
        )
        raise AssertionError("an incompatible core must be refused")
    except InstallError:
        pass
    assert installed_keys(apps) == []


def test_install_rejects_unsafe_archive_paths(tmp_path):
    apps = tmp_path / "apps"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("app.json", json.dumps(_manifest()))
        archive.writestr("../escape.py", "print('bad')")
    try:
        install_release(_record(sha256=hashlib.sha256(buffer.getvalue()).hexdigest()),
                        apps_root=apps, fetch=lambda url: buffer.getvalue())
        raise AssertionError("unsafe paths must be refused")
    except InstallError:
        pass
    assert installed_keys(apps) == []


def test_updater_carries_the_download_url():
    updates = check({
        "pile": {"version": "1.1.0", "url": "https://example.com/pile-1.1.0.zip"},
        "rock": "1.1.0",
    })
    assert updates["pile"].url == "https://example.com/pile-1.1.0.zip"
    assert updates["rock"].url == ""
    assert AppUpdate("pile", "1.0.0", "1.0.0").update_available is False


def test_download_reads_file_urls(tmp_path):
    archive_path = tmp_path / "pile-1.0.9.zip"
    archive_path.write_bytes(_archive_bytes(_manifest(version="1.0.9")))
    data = installer.download(archive_path.resolve().as_uri())
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        manifest = json.loads(archive.read("release/app.json"))
    assert manifest["version"] == "1.0.9"
    # Full offline flow: catalogue record -> real download -> install.
    installed = install_release(
        {"key": "pile", "version": "1.0.9", "url": archive_path.resolve().as_uri(),
         "requires_core": ">=0.1.0",
         "sha256": hashlib.sha256(data).hexdigest()},
        apps_root=tmp_path / "apps",
    )
    assert installed["version"] == "1.0.9"


def test_key_validation_blocks_directory_escape(tmp_path):
    for invalid in ("..", "../", "../../", ".", "/tmp", r"..\escape", "pile/../wall",
                    "__dict__", "PILE", "π", ""):
        with pytest.raises(InstallError):
            uninstall(invalid, apps_root=tmp_path)
        with pytest.raises(InstallError):
            install_release(_record(key=invalid), apps_root=tmp_path,
                            fetch=lambda _: _archive_bytes(_manifest()))
    assert not list(tmp_path.iterdir())


def test_sha256_required_and_mismatch_does_not_replace_existing(tmp_path):
    data = _archive_bytes(_manifest())
    root = tmp_path / "apps"
    installed = install_release(_record(), apps_root=root, fetch=lambda _: data)
    assert installed["version"] == "1.1.0"
    old_manifest = (root / "pile" / "app.json").read_bytes()
    with pytest.raises(InstallError, match="SHA-256"):
        install_release({**_record(), "sha256": ""}, apps_root=root,
                        fetch=lambda _: data)
    with pytest.raises(InstallError, match="checksum"):
        install_release(_record(version="1.2.0"), apps_root=root,
                        fetch=lambda _: data)
    assert (root / "pile" / "app.json").read_bytes() == old_manifest


def test_rejects_zip_symlink_and_case_collisions(tmp_path):
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as stream:
        stream.writestr("app.json", json.dumps(_manifest()))
        stream.writestr("slipsurface_pile/__init__.py", "")
        stream.writestr("slipsurface_pile/web/session.py", "class Session: pass")
        entry = zipfile.ZipInfo("symlink")
        entry.create_system = 3
        entry.external_attr = (0o120777 << 16)
        stream.writestr(entry, "../../etc/passwd")
    data = archive.getvalue()
    with pytest.raises(InstallError, match="symlinks"):
        install_release(_record(sha256=hashlib.sha256(data).hexdigest()),
                        apps_root=tmp_path, fetch=lambda _: data)

    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as stream:
        stream.writestr("app.json", json.dumps(_manifest()))
        stream.writestr("SAME.TXT", "A")
        stream.writestr("same.txt", "B")
    data = archive.getvalue()
    with pytest.raises(InstallError, match="duplicate"):
        install_release(_record(sha256=hashlib.sha256(data).hexdigest()),
                        apps_root=tmp_path, fetch=lambda _: data)


def test_existing_release_backup_is_not_silently_destroyed(tmp_path):
    root = tmp_path / "apps"
    root.mkdir()
    backup = root / "pile.previous"
    backup.mkdir()
    (backup / "user_work.json").write_text("important")
    data = _archive_bytes(_manifest())
    with pytest.raises(InstallError, match="backup"):
        install_release(_record(), apps_root=root, fetch=lambda _: data)
    assert (backup / "user_work.json").read_text() == "important"


def test_missing_code_is_refused_before_installation(tmp_path):
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as stream:
        stream.writestr("app.json", json.dumps(_manifest()))
    data = payload.getvalue()
    with pytest.raises(InstallError, match="lacks expected"):
        install_release(_record(sha256=hashlib.sha256(data).hexdigest()),
                        apps_root=tmp_path, fetch=lambda _: data)


def test_unverified_http_url_is_refused(tmp_path):
    with pytest.raises(InstallError, match="HTTPS"):
        install_release(_record(url="http://example.com/archive.zip"), apps_root=tmp_path)


def _installed_dir(root, name, version):
    directory = root / name
    (directory / "slipsurface_pile" / "web").mkdir(parents=True)
    (directory / "app.json").write_text(json.dumps(_manifest(version=version)))
    return directory


def test_leftover_backup_never_shadows_the_live_release(tmp_path):
    root = tmp_path / "apps"
    live = _installed_dir(root, "pile", "2.0.0")
    stale = _installed_dir(root, "pile.previous", "1.0.0")
    try:
        manifests = {m["key"]: m for m in discover(root)}
        assert manifests["pile"]["version"] == "2.0.0"
        assert str(stale) not in sys.path
    finally:
        if str(live) in sys.path:
            sys.path.remove(str(live))


def test_installed_release_comes_first_on_sys_path(tmp_path):
    root = tmp_path / "apps"
    live = _installed_dir(root, "pile", "2.0.0")
    try:
        discover(root)
        assert sys.path[0] == str(live)
    finally:
        sys.path.remove(str(live))


def test_release_directory_with_extra_modules_is_ignored(tmp_path):
    root = tmp_path / "apps"
    live = _installed_dir(root, "pile", "2.0.0")
    (live / "json.py").write_text("raise SystemExit('shadowed')")
    manifests = {m["key"]: m for m in discover(root)}
    assert manifests["pile"]["version"] == "1.0.0"  # the bundled module
    assert str(live) not in sys.path


def test_release_archive_with_extra_top_level_module_is_refused(tmp_path):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("release/app.json", json.dumps(_manifest()))
        archive.writestr("release/slipsurface_pile/__init__.py", "")
        archive.writestr("release/slipsurface_pile/web/session.py", "class Session: pass")
        archive.writestr("release/json.py", "raise SystemExit('shadowed')")
    data = buffer.getvalue()
    with pytest.raises(InstallError, match="unexpected top-level"):
        install_release(_record(sha256=hashlib.sha256(data).hexdigest()),
                        apps_root=tmp_path, fetch=lambda _: data)
    assert installed_keys(tmp_path) == []


def test_failed_backup_cleanup_still_reports_success(tmp_path, monkeypatch):
    root = tmp_path / "apps"
    install_release(_record(), apps_root=root, fetch=lambda _: _archive_bytes(_manifest()))
    real_rmtree = installer.shutil.rmtree

    def locked(path, *args, **kwargs):
        if str(path).endswith(".previous") and not kwargs.get("ignore_errors"):
            raise PermissionError("file in use")
        return real_rmtree(path, *args, **kwargs)

    monkeypatch.setattr(installer.shutil, "rmtree", locked)
    manifest = install_release(
        _record(version="1.2.0"), apps_root=root,
        fetch=lambda _: _archive_bytes(_manifest(version="1.2.0")),
    )
    assert manifest["version"] == "1.2.0"
    assert (root / "pile.previous").is_dir()
    monkeypatch.setattr(installer.shutil, "rmtree", real_rmtree)
    # The leftover copy does not block the next update.
    manifest = install_release(
        _record(version="1.3.0"), apps_root=root,
        fetch=lambda _: _archive_bytes(_manifest(version="1.3.0")),
    )
    assert manifest["version"] == "1.3.0"
    assert not (root / "pile.previous").exists()


def test_one_malformed_catalogue_record_does_not_hide_the_others():
    updates = check({
        "pile": {"version": "9.0.0"},
        "rock": {"version": "latest"},
        "wall": {"version": "9.0.0", "requires_core": "~1.0"},
    })
    assert set(updates) == {"pile"}


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))


def test_candidate_probe_rejects_broken_session_before_replacing_working_release(tmp_path):
    root = tmp_path / "apps"
    good = _archive_bytes(_manifest())
    install_release(_record(), apps_root=root, fetch=lambda _: good)
    old_manifest = (root / "pile" / "app.json").read_bytes()
    broken = _archive_bytes(_manifest(version="1.2.0"), source="raise RuntimeError('broken')\n")
    with pytest.raises(InstallError, match="candidate module failed validation"):
        install_release(
            _record(version="1.2.0", sha256=hashlib.sha256(broken).hexdigest()),
            apps_root=root, fetch=lambda _: broken,
        )
    assert (root / "pile" / "app.json").read_bytes() == old_manifest
    assert not (root / "pile.previous").exists()


def test_retained_backup_is_restored_if_first_launch_fails(tmp_path):
    root = tmp_path / "apps"
    install_release(_record(), apps_root=root, fetch=lambda _: _archive_bytes(_manifest()))
    install_release(
        _record(version="1.2.0"), apps_root=root,
        fetch=lambda _: _archive_bytes(_manifest(version="1.2.0")),
        keep_backup=True,
    )
    assert (root / "pile.previous" / "app.json").is_file()
    assert "1.2.0" in (root / "pile" / "app.json").read_text()
    rollback_release("pile", apps_root=root)
    assert "1.1.0" in (root / "pile" / "app.json").read_text()
    assert not (root / "pile.previous").exists()


def test_confirmed_update_removes_backup_after_first_launch(tmp_path):
    root = tmp_path / "apps"
    install_release(_record(), apps_root=root, fetch=lambda _: _archive_bytes(_manifest()))
    install_release(
        _record(version="1.2.0"), apps_root=root,
        fetch=lambda _: _archive_bytes(_manifest(version="1.2.0")),
        keep_backup=True,
    )
    confirm_release("pile", apps_root=root)
    assert not (root / "pile.previous").exists()
    assert "1.2.0" in (root / "pile" / "app.json").read_text()


def test_first_installed_override_rolls_back_to_bundled_module(tmp_path):
    root = tmp_path / "apps"
    install_release(
        _record(), apps_root=root, fetch=lambda _: _archive_bytes(_manifest()),
        keep_backup=True,
    )
    rollback_release("pile", apps_root=root)
    assert installed_keys(root) == []
    assert not (root / "pile").exists()
