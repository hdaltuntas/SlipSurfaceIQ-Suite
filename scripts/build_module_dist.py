"""Build one release archive per application module.

Usage:

    python scripts/build_module_dist.py                 # every module
    python scripts/build_module_dist.py pile wall      # just some modules

For each module the script writes ``dist/<key>-<version>.zip`` (the version
comes from the module's ``app.json``). The archive layout is what
``slipsurface.installer`` accepts:

    <key>-<version>/
        app.json                       session rewritten to the plugin package
        slipsurface_<key>/             the module package, byte for byte

Inside the archive the module package is renamed to ``slipsurface_<key>``
and the manifest's ``session`` field points at it, so the release installs
into ``~/.slipsurface/apps/<key>/`` and overrides the bundled module
without touching the Suite installation. The script also prints the
release-catalogue entry to paste into ``slipsurface-index.json`` — fill in
the real download URL.

Standard library only; run from the repository root.
"""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODULES = (
    "kinematic", "rock", "bearing", "settle", "correlation",
    "liquefaction", "pile", "spwa", "msew", "wall",
)
SKIP_DIRS = {"__pycache__", ".git"}


def build(key: str, out_dir: Path, version: str | None = None) -> Path:
    """Write ``<out_dir>/<key>-<version>.zip`` and return its path.

    ``version`` overrides the manifest version inside the archive only — the
    source ``app.json`` stays untouched. ``scripts/demo_update.py`` uses this
    to build a demonstration (or test) release without editing the tree.
    """
    source = ROOT / "slipsurface" / key
    manifest_path = source / "app.json"
    if not manifest_path.is_file():
        raise SystemExit(f"no manifest for {key!r}: {manifest_path} is missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    version = version or manifest["version"]

    manifest = dict(manifest)
    manifest["version"] = version
    manifest["session"] = f"slipsurface_{key}.web.session"

    out_dir.mkdir(parents=True, exist_ok=True)
    archive_path = out_dir / f"{key}-{version}.zip"
    top = f"{key}-{version}"
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(f"{top}/app.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        for path in sorted(source.rglob("*")):
            if path.is_dir() or any(part in SKIP_DIRS for part in path.parts):
                continue
            relative = path.relative_to(source)
            if relative == Path("app.json"):
                continue
            archive.write(path, f"{top}/slipsurface_{key}/" + relative.as_posix())
    return archive_path


def main(argv: list[str]) -> int:
    keys = [argument for argument in argv[1:] if not argument.startswith("-")]
    if any(argument in ("-h", "--help") for argument in argv):
        print(__doc__)
        return 0
    for key in keys or list(MODULES):
        if key not in MODULES:
            print(f"unknown module: {key}", file=sys.stderr)
            return 2
        archive = build(key, ROOT / "dist")
        manifest = json.loads((ROOT / "slipsurface" / key / "app.json").read_text(encoding="utf-8"))
        print(f"built {archive}")
        print("  catalogue entry:")
        print(json.dumps({
            key: {
                "version": manifest["version"],
                "changelog": "",
                "requires_core": manifest["requires_core"],
                "url": f"https://example.com/{archive.name}",
            }
        }, ensure_ascii=False, indent=2))
        print("  demonstration flow: python scripts/demo_update.py" + (f" --key {key}" if keys else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
