"""The frozen contract between the Suite shell and an application module.

An application is discoverable and installable on its own only if the shell
can rely on a stable surface. This module is that surface: it says, in one
place, which members a session adapter must provide and which are optional.
Applications must treat it as immutable between core major versions; the
``requires_core`` field of their ``app.json`` says which core they need.

The contract is deliberately narrow. Specialist operations an application
offers beyond it — the pile rock-socket analysis, the MSEW layer generator,
the wall dimension suggester, the correlation exports, the kinematic
screening and equilibrium modes — stay private to their session and are
surfaced by the shell through guarded feature calls, never through the
contract itself.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

__all__ = ["AppSession", "satisfies_contract", "REQUIRED_METHODS", "OPTIONAL_METHODS"]

#: The members every session adapter must provide
REQUIRED_METHODS = ("meta", "analyse", "plot", "report", "project_file", "load_project")

#: The members the shell calls when an application provides them
OPTIONAL_METHODS = ("set_language", "set_theme")


@runtime_checkable
class AppSession(Protocol):
    """The surface of one application, as the Suite shell consumes it.

    ``meta`` returns the form schema, the default values and the figure
    catalogue; ``analyse`` runs one analysis and returns its results as a
    plain mapping; ``plot`` renders one figure to PNG bytes; ``report``
    writes a PDF to a path; ``project_file`` and ``load_project`` serialize
    and restore the module's project state.
    """

    def meta(self) -> dict: ...

    def analyse(self, values: dict) -> dict: ...

    def plot(self, target: str, kind: str) -> bytes: ...

    def report(self, kind: str, path: str) -> None: ...

    def project_file(self, values: dict) -> dict: ...

    def load_project(self, payload: dict) -> dict: ...


def satisfies_contract(session) -> bool:
    """Whether an object provides every required member of ``AppSession``.

    Method presence only: this is a duck-type check, so an application's
    adapter does not have to subclass anything, and the check itself never
    imports application code.
    """
    return all(callable(getattr(session, name, None)) for name in REQUIRED_METHODS)
