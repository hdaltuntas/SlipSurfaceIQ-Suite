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
    "version": "2026.0.0",
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

`registry.discover()` merges three sources:

1. Bundled manifests: every `slipsurface/<key>/app.json`.
2. Installed plugins: any distribution registering an entry point in the
   `slipsurface.apps` group whose value resolves to a callable returning the
   manifest.
3. Release archives unpacked into the user applications directory
   (`~/.slipsurface/apps` by default, overridable with the
   `SLIPSURFACE_APPS_DIR` environment variable).

On a duplicate `key` the most local source wins — an unpacked release
always overrides the entry-point and bundled versions of the same key. The
result is sorted by `order`, then `key`, so the launchpad is stable
regardless of the filesystem or entry-point order. A manifest that fails
validation is skipped rather than allowed to break start-up.

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
        "requires_core": ">=0.1.0",
        "sha256": "<sha256-hex-digest>"
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

## Module-by-module updates

A catalogue record that carries a `url` is not only announced but
installable: the launchpad card shows an install button, and the shell
installs that one module without touching any other module or the Suite
installation itself.

The flow, end to end:

1. Develop one module, bump its `app.json` `version`, run
   `python scripts/build_module_dist.py <key>`. The script writes
   `dist/<key>-<version>.zip`, a standard-library ZIP with this layout:

   ```text
   <key>-<version>/
       app.json                  session rewritten to slipsurface_<key>.web.session
       slipsurface_<key>/        the module package, byte for byte
   ```

   It also prints the catalogue entry to paste into the release index —
   fill in the real download URL and publish the archive (a GitHub release
   works well).

2. Publish the catalogue. `~/.slipsurface/index.json` maps every module to
   its newest release; a record with `url`, `version`, `changelog`, `requires_core` and
   `sha256` is required for installation.

3. On the user's machine the shell compares versions, shows the badge and
   the button, and on confirmation calls
   `slipsurface.installer.install_release(record)`: it downloads the
   archive, checks it against the catalogue (same key, same version, a core
   this Suite satisfies, matching SHA-256, no unsafe paths, nothing at the
   top level but `app.json` and `slipsurface_<key>/`), and unpacks it into the user
   applications directory `~/.slipsurface/apps/<key>/`, replacing any
   previously installed release. The Suite directory itself is never
   written to, so no administrator rights are needed.

4. The shell then rebuilds the catalogue (`apps.refresh()`), drops the
   cached imports and the open page of that one module, and the next open
   imports the new release's session from its manifest `session` field —
   `slipsurface_pile.web.session` for an installed release, while bundled
   modules keep importing `slipsurface.<key>.web.session`.

Because discovery puts the installed release above the bundled module of
the same key, a module that was never updated simply keeps running from the
Suite installation, and `installer.uninstall(key)` rolls a module back to
the bundled version at any time.

Two conventions make the relocation work and both are already in place:

- Modules address the shared core absolutely (`from slipsurface.common
  import factors`), never relatively across the package boundary.
- Modules address their own code relatively (`from ..engine import ...`),
  so the package works unchanged under the `slipsurface_<key>` name.

The operator's side of the flow — catalogue format, publishing, and a
script that rehearses the whole update offline — is documented separately
in `docs/UPDATE_CATALOGUE.md` (`python scripts/demo_update.py`).

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

## Tested separation and fallback contracts

The per-module archive builder rewrites the old parent-relative version alias
in each application initializer to the module release version. This is
necessary because installed plugins use a top-level `slipsurface_<key>`
package, not the bundled `slipsurface.<key>` namespace.

The native launcher accepts new manifest keys and displays a generic icon and
workspace profile if an app does not yet have a custom design. Applications
must provide the methods in `slipsurface.contract.AppSession`; Kinematic
also supports this shared contract while keeping its specialist calls.

The desktop launcher is still started solely by `python main.py`.

## Preflight and two-phase activation

The release installer first validates the SHA-256 digest, archive structure and
core compatibility. Before any live module directory is changed, it extracts
the candidate to a staging directory and launches a fresh isolated Python
interpreter to import the candidate's actual `Session`, instantiate it,
verify `AppSession` methods, and inspect its editable schema/defaults.
Import errors and timeouts leave the working release intact.

For updates started from PySide6, `install_release(..., retain_backup=True)`
holds the previous user-installed module as `<key>.previous` until the native
`ModulePage` successfully initializes. A good activation calls
`finalize_release`; a failure invokes `rollback_release`. If no previous
user-installation exists, rollback removes the candidate and uses the original
bundled module. User project JSON files are saved outside the module directory.

`registry.discover()` excludes manifests whose `requires_core` constraint
is incompatible with `slipsurface.CORE_VERSION`, and
`registry.incompatible_modules()` supplies their names and required core
versions for the launchpad warning. Incompatible releases do not add their
Python code to `sys.path`.

Native Linux and Windows source validation runs the numerical regressions and
offscreen Qt tests; no Windows executable or distribution installer is built.

Note that Python plug-in releases still execute code with the current user's
permissions; use a trusted release catalogue. SHA-256 is an integrity check,
not publisher authentication.

## Product versions from 2026 onwards

The Suite and each shipped application start from **2026.0.0**. Subsequent
patch/minor releases are **per module**; updating Pile never increments the
Bearing version. Module packages use `module_version(__file__)` to read the
bundled `app.json` or, for a relocated user release, its parent manifest.
The launcher reads `slipsurface.__version__`. **CORE_VERSION remains 0.1.0**
as the separately maintained plugin ABI constraint; `requires_core` must
not be confused with the calendar-year product version.
