"""Build one demonstration module release and publish a local catalogue.

The demonstration is the real update flow, end to end, with no server: it
builds a release archive for one module with a patch-version bump (the
module code itself is unchanged, so the demo is always safe), writes a
release catalogue that points at the archive through a ``file://`` URL, and
the Suite then offers — and performs — the update exactly as it would over
the network:

    python scripts/demo_update.py               # demo release for pile
    python scripts/demo_update.py --key wall    # any other module
    python scripts/demo_update.py --revert       # revert pile catalogue and module

What happens on the screen:

1. Launch the Suite (``python main.py``). The launchpad shows the module's
   card with an update badge and a Güncelle button.
2. Click the button and confirm. The archive is downloaded, checked and
   unpacked into ``~/.slipsurface/apps/<key>/``; the catalogue, the module
   list and the card are refreshed, and the card now carries the new
   version number.
3. ``--revert`` (or ``slipsurface.installer.uninstall``) returns the
   module to the bundled release at any time.

The catalogue is written to ``~/.slipsurface/index.json``; an existing file
is preserved as ``index.json.bak`` and restored by ``--revert``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from build_module_dist import MODULES, build  # noqa: E402
from slipsurface.versioning import parse  # noqa: E402

CATALOGUE = Path.home() / ".slipsurface" / "index.json"


def _next_patch(version: str) -> str:
    major, minor, patch = parse(version)
    return f"{major}.{minor}.{patch + 1}"


def _revert(key: str) -> int:
    """Restore the prior catalogue and undo an identified local demo install."""
    import urllib.parse
    import urllib.request

    from slipsurface.installer import uninstall, installed_keys
    from slipsurface.registry import USER_APPS_DIR

    if CATALOGUE.exists():
        try:
            records = json.loads(CATALOGUE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            records = {}
        record = records.get(key, {}) if isinstance(records, dict) else {}
        url = record.get("url", "") if isinstance(record, dict) else ""
        parsed = urllib.parse.urlsplit(url)
        demo_path = Path(urllib.request.url2pathname(parsed.path)).resolve()
        if (
            parsed.scheme == "file"
            and demo_path.is_relative_to((ROOT / "dist").resolve())
            and key in installed_keys(USER_APPS_DIR)
        ):
            manifest_file = USER_APPS_DIR / key / "app.json"
            try:
                installed = json.loads(manifest_file.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                installed = {}
            if installed.get("version") == record.get("version"):
                uninstall(key, apps_root=USER_APPS_DIR)
                print(f"removed demonstration module {key}")

    backup = CATALOGUE.with_name(f"{CATALOGUE.name}.bak")
    if CATALOGUE.exists():
        CATALOGUE.unlink()
        print(f"removed {CATALOGUE}")
    if backup.exists():
        backup.replace(CATALOGUE)
        print(f"restored {backup}")
    print("the Suite will show no updates on its next start")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--key", default="pile", choices=MODULES,
                        help="module to publish a demonstration release for")
    parser.add_argument("--revert", action="store_true",
                        help="remove the demonstration catalogue and restore any backup")
    parser.add_argument("--changelog", default="",
                        help="one line shown on the update tooltip")
    arguments = parser.parse_args(argv)

    if arguments.revert:
        return _revert(arguments.key)

    manifest = json.loads(
        (ROOT / "slipsurface" / arguments.key / "app.json").read_text(encoding="utf-8")
    )
    demo_version = _next_patch(manifest["version"])
    archive = build(arguments.key, ROOT / "dist", version=demo_version)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()

    record = {
        arguments.key: {
            "version": demo_version,
            "changelog": arguments.changelog
            or f"Demonstration release {demo_version} for the update flow.",
            "requires_core": manifest["requires_core"],
            "url": archive.resolve().as_uri(),
            "sha256": digest,
        }
    }

    CATALOGUE.parent.mkdir(parents=True, exist_ok=True)
    if CATALOGUE.exists():
        CATALOGUE.replace(CATALOGUE.with_name(f"{CATALOGUE.name}.bak"))
    CATALOGUE.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8")

    print(f"built  {archive}")
    print(f"index  {CATALOGUE}")
    print(json.dumps(record, ensure_ascii=False, indent=2))
    print()
    print("next: launch the Suite (python main.py), open the module's card,")
    print("      click Güncelle and confirm; --revert undoes the demonstration.")
    print()
    print("for a real release, publish the archive (e.g. a GitHub release) and")
    print("replace the url with the download address:")
    print(json.dumps({
        arguments.key: {
            "version": demo_version,
            "changelog": "…",
            "requires_core": manifest["requires_core"],
            "url": f"https://github.com/hdaltuntas/SlipSurfaceIQ-Suite/"
                   f"releases/download/v{demo_version}/{archive.name}",
            "sha256": digest,
        }
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
