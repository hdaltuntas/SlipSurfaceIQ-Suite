"""Isolated pre-install smoke probe for one unpacked application release.

This module runs in a *new Python interpreter* before the current release is
replaced. A crashed or invalid plugin cannot displace the working version.
It is a compatibility check, not a sandbox: use only trusted release sources.
"""
from __future__ import annotations

import importlib
import inspect
import sys
from pathlib import Path

from slipsurface.contract import satisfies_contract


def probe(directory: Path, key: str) -> None:
    directory = directory.resolve()
    sys.path.insert(0, str(directory))
    path = f"slipsurface_{key}.web.session"
    module = importlib.import_module(path)
    module_file = Path(module.__file__).resolve()
    if not module_file.is_relative_to(directory):
        raise RuntimeError(f"{path} was imported from the wrong location")
    factory = module.Session
    parameters = inspect.signature(factory).parameters
    kwargs = {"lang": "tr"} if "lang" in parameters else (
        {"language": "tr"} if "language" in parameters else {}
    )
    session = factory(**kwargs)
    if not satisfies_contract(session):
        raise RuntimeError("session does not implement the Suite application contract")
    metadata = session.meta()
    if not isinstance(metadata, dict):
        raise RuntimeError("session.meta() must return a mapping")
    if not isinstance(metadata.get("schema"), dict):
        raise RuntimeError("session.meta() must expose a schema mapping")
    if not isinstance(metadata.get("defaults"), dict):
        raise RuntimeError("session.meta() must expose a defaults mapping")


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        raise SystemExit("usage: python -m slipsurface.release_probe <folder> <key>")
    probe(Path(args[0]), args[1])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
