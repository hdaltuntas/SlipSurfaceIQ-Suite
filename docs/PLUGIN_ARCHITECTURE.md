# Application Architecture: Contract, Manifests and Updates

The Suite is one repository with one launcher and ten applications, but it is
laid out so that every application could later live in its own repository
without the shell — or any other application — noticing. Nothing about the
split has to be decided now; this document describes the machinery that makes
both layouts work the same way.

## Layering

    slipsurface/                the core: contract, registry, versioning
        contract.py            what an application must provide
        registry.py            how applications are discovered
        versioning.py          semantic-version comparison (stdlib only)
        apps.py                the discovered catalogue, as the shell sees it
        <key>/app.json         one manifest per application
        <key>/web/session.py   the application's session adapter
        desktop/               the launcher: shell, launchpad, updater, theme

The rule that keeps the layers independent: `contract.py`, `registry.py`,
`versioning.py` and `apps.py` never import application code and never import
PySide6. Discovery reads data files and entry points only, so a broken or
half-installed application can never prevent the launcher from starting.

## The contract

`slipsurface.contract` defines `AppSession`, the frozen surface between the
shell and an application session: `meta`, `analyse`, `plot`, `report`,
`project_file` and `load_project` are required; `set_language` and `set_theme`
are optional. The contract is checked by duck typing
(`satisfies_contract`); an application subclasses nothing. Applications must
treat the contract as immutable between core major versions.

## The manifest

Every application carries an `app.json` next to its code:

```json
{
    "key": "pile",
    "name": "Pile",
    "tr": "Kazık",
    "group": "Foundations",
    "description": "Axial capacity, group and socket assessment",
    "description_tr": "Kazıkların eksenel kapasitesi, grup etkisi ve soket analizi.",
    "version": "1.0.0",
    "requires_core": ">=0.1.0",
    "order": 7,
    "session": "slipsurface.pile.web.session"
}
```

Required fields are validated by `registry.load_manifest`; unknown fields are
preserved and ignored, so a newer application can carry extra metadata that an
older shell skips. `requires_core` accepts comma-separated AND clauses over
`>=`, `<=`, `>`, `<`, `==`, `!=` and is checked against
`slipsurface.CORE_VERSION`.

## Discovery order

`registry.discover()` merges two sources:

1. Bundled manifests: every `slipsurface/<key>/app.json`.
2. Installed plugins: any distribution registering an entry point in the
   `slipsurface.apps` group whose value resolves to a callable returning the
   manifest.

On a duplicate `key` the installed plugin wins — an installed application
always overrides the bundled one with the same key. The result is sorted by
`order`, then `key`, so the launchpad is stable regardless of the filesystem
or entry-point order. A manifest that fails validation is skipped rather than
allowed to break start-up.

`apps.py` wraps the discovered manifests in the `App` value object and keeps
the historical API (`APPS`, `keys()`, `get()`, `catalogue()`) unchanged.

## Installing one application on its own

To ship an application as a standalone, optional package:

1. Move the application package (e.g. `pile/`) into its own distribution with
   its own `app.json` and its own version history.
2. Depend on the core package and pin `requires_core` to the contract it was
   written against.
3. Register the manifest in `pyproject.toml`:

   ```toml
   [project.entry-points."slipsurface.apps"]
   pile = "slipsurface_pile:manifest"
   ```

4. `pip install slipsurface-pile` — the next start of the Suite picks it up
   with no configuration, and `pip uninstall` removes it cleanly.

An application whose dependencies are not installed is simply never
discovered; the shell does not need a plugin to be present.

## Version control and updates

Three version families are kept in step:

| Family | Where | Meaning |
| --- | --- | --- |
| Core | `slipsurface.CORE_VERSION` | contract, registry and versioning |
| Suite | `slipsurface.__version__` | the launcher and the desktop shell |
| Application | each `app.json` `version` | one per application, independently |

A release catalogue is a JSON file listing newer releases:

```json
{
    "pile": {
        "version": "1.1.0",
        "changelog": "Socket side resistance correlations added.",
        "requires_core": ">=0.1.0"
    }
}
```

At start-up the shell calls `desktop.updater.load_available_updates()`, which
looks for `~/.slipsurface/index.json` and then `./slipsurface-index.json`,
compares every catalogue record against the installed manifests and returns
one `AppUpdate` per application with a newer release. The launchpad then
shows a banner plus one badge per application. A release that needs a newer
core than this Suite carries is still shown, but flagged as incompatible
(`core_ok` false) instead of offering an update that cannot run. A missing,
unreadable or malformed catalogue is not an error; the Suite starts quietly
with no updates, because an offline machine is the normal case.

Today the catalogue is read-only: installing an update still means installing
the newer distribution. The download-and-replace step can be added behind
this same interface without touching the shell.

## When to actually split repositories

Keep one repository while the applications share the core, ship together and
are developed by the same person; the logical separation above already gives
selective installation and independent application versions. Split an
application into its own repository only when at least one of these becomes
true:

- a different licence must apply to that application;
- a different release cadence or a separate maintainer is needed;
- the application must be installed on its own, without the Suite, at the
  repository level (e.g. a licence-gated distribution).

In every case the split requires no shell changes: the application keeps its
`app.json`, registers the same entry point and is discovered exactly like a
bundled one.
