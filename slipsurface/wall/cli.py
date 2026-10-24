"""Command line interface."""

from __future__ import annotations

import argparse
import json
import sys

from . import APP_NAME, __version__

#: Default port of the local interface (the family counts up from 8777)
PORT = 8785


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="slipsurface-wall",
        description="Cantilever reinforced concrete retaining walls: earth pressure by "
                    "Rankine, Coulomb, at rest and the trial wedge; sliding, overturning, "
                    "eccentricity, bearing capacity by Terzaghi, Meyerhof, Hansen, Vesić and "
                    "EN 1997-1, global stability by Bishop and Fellenius; the earthquake of "
                    "TBDY 2018; the reinforced concrete design of TS 500, the bars, the "
                    "reinforcement drawing (DXF) and the bar bending schedule.")
    parser.add_argument("--version", action="version", version=f"{APP_NAME} {__version__}")
    # Running the program with no subcommand means "web", so the top level
    # carries that subcommand's defaults: without them the bare `slipsurface-wall`
    # would reach serve() with a Namespace that has no host, port or language.
    parser.set_defaults(host="127.0.0.1", port=PORT, lang="en", no_browser=False)
    sub = parser.add_subparsers(dest="command")

    web = sub.add_parser("web", help="start the interface in a browser")
    web.add_argument("--port", type=int, default=PORT)
    web.add_argument("--host", default="127.0.0.1")
    web.add_argument("--lang", default="en", choices=["en", "tr"])
    web.add_argument("--no-browser", action="store_true")

    run = sub.add_parser("run", help="analyse a project file and print the results")
    run.add_argument("project", help="path to a .lwall / .json project file")
    run.add_argument("-o", "--out", default=None,
                     help="write a report here (.pdf / .html / .docx)")
    run.add_argument("--dxf", default=None, help="write the reinforcement drawing here (.dxf)")
    run.add_argument("--lang", default="en", choices=["en", "tr"])

    example = sub.add_parser("example", help="write a starter project file")
    example.add_argument("-o", "--out", default="project.lwall")

    args = parser.parse_args(argv)
    command = args.command or "web"
    try:
        return _dispatch(command, args)
    except (ValueError, RuntimeError, OSError) as exc:
        # The analysis refuses impossible input with a sentence worth reading
        # (a backslope steeper than the backfill, a footing thicker than the
        # wall, an unreadable project file). A traceback would bury it, so
        # only unexpected failures keep theirs.
        print(f"{APP_NAME}: {exc}", file=sys.stderr)
        return 1


def _dispatch(command: str, args) -> int:
    """Runs one command; raises on anything that goes wrong."""
    if command == "web":
        from .web.server import serve
        serve(host=args.host, port=args.port, open_browser=not args.no_browser,
              lang=args.lang)
        return 0

    from . import forms

    if command == "example":
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(forms.project_file(forms.defaults()), fh, indent=2, ensure_ascii=False)
        print(args.out)
        return 0

    with open(args.project, encoding="utf-8") as fh:
        data = json.load(fh)

    from .web.session import Session
    session = Session(lang=args.lang)
    values = session.load_project(data)["values"]
    result = session.analyse(values)
    print(result["text"])
    if args.out:
        fmt = args.out.lower().rsplit(".", 1)[-1]
        print(session.report(fmt if fmt in ("pdf", "html", "docx") else "pdf", args.out))
    if args.dxf:
        with open(args.dxf, "wb") as fh:
            fh.write(session.dxf())
        print(args.dxf)
    return 0


if __name__ == "__main__":
    sys.exit(main())
