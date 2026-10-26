"""Publish independently versioned module ZIPs and their GitHub catalogue.

Only invoke from the trusted repository publishing workflow after tests pass.
This writes source-module archives, not Windows installers or GitHub Releases.

Usage: python scripts/publish_module_updates.py rock [pile ...]
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scripts.build_module_dist import MODULES, build  # noqa: E402
from slipsurface.versioning import parse  # noqa: E402

PUBLISHED = ROOT / "module-updates"
# Stable human-readable index at the repository root, mirrored in the
# original path for existing clients.
ROOT_INDEX = ROOT / "module-versions.json"
PUBLIC_ROOT = (
    "https://raw.githubusercontent.com/hdaltuntas/"
    "SlipSurfaceIQ-Suite/main/module-updates"
)


def publish(keys: list[str]) -> dict:
    if not keys:
        raise ValueError("specify at least one independently updated module")
    PUBLISHED.mkdir(parents=True, exist_ok=True)
    index_path = PUBLISHED / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else {}
    if not isinstance(index, dict):
        raise ValueError("module update index is not a JSON object")

    for key in sorted(set(keys)):
        if key not in MODULES:
            raise ValueError(f"unknown module key: {key}")
        manifest = json.loads(
            (ROOT / "slipsurface" / key / "app.json").read_text(encoding="utf-8")
        )
        version = manifest["version"]
        parse(version)
        archive = PUBLISHED / f"{key}-{version}.zip"
        # Published releases are immutable: never silently rebuild the same
        # version from later source edits.
        if not archive.exists():
            build(key, PUBLISHED)
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        index[key] = {
            "version": version,
            "changelog": (
                "Bearing 2026.0.1: corrected zero lower bounds in engineering input fields."
                if key == "bearing" and version == "2026.0.1"
                else "Rock Mass 2026.0.2: independent update-card verification; no numerical changes."
                if key == "rock" and version == "2026.0.2"
                else ("Rock Mass 2026.0.1: Hoek–Brown D input range (0–1) corrected."
                      if key == "rock" and version == "2026.0.1"
                      else f"{key} {version} module update")
            ),
            "requires_core": manifest["requires_core"],
            "url": f"{PUBLIC_ROOT}/{archive.name}",
            "sha256": digest,
        }
    published_json = json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    index_path.write_text(published_json, encoding="utf-8")
    ROOT_INDEX.write_text(published_json, encoding="utf-8")
    return index


def main(argv: list[str]) -> int:
    index = publish(argv[1:])
    for key in argv[1:]:
        print(json.dumps({key: index[key]}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
