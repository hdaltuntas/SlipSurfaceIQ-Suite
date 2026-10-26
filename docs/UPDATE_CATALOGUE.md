# Release Catalogue and the Update Flow

The Suite learns about new module releases from a release catalogue, and
installs them module by module. This document is the operator's guide: the
catalogue format, where to publish it, and how to rehearse the flow locally.

## The catalogue

A catalogue is a JSON object, one record per module key. The Suite checks for
updates **in the background when its native GUI starts**. It also has a
`Güncellemeleri kontrol et / Check updates` button in the persistent toolbar.
The update checker tries these sources, in order:

1. `~/.slipsurface/index.json` — an optional explicit user override;
2. `./slipsurface-index.json` — an optional local testing catalogue;
3. The **public GitHub version file** on `main`:
   `https://raw.githubusercontent.com/hdaltuntas/SlipSurfaceIQ-Suite/main/module-versions.json`.

GitHub Actions updates `module-versions.json` on every published module
version bump. It mirrors `module-updates/index.json`, whose original URL
remains available for older clients. **There is no need to download or
manually copy a JSON file** in a Suite shell with online checking.

The HTTPS request has a short timeout and a 64 KiB response size limit; it never
runs on the Qt GUI thread. Offline startup is allowed. Set
`SLIPSURFACE_DISABLE_UPDATE_CHECK=1` to disable the automatic lookup.
For a public update check, the newest valid version per module wins across
local and published catalogues; a local entry wins ties. This prevents a stale
`slipsurface-index.json` (for example, Rock 2026.0.1) from hiding a newer
GitHub Rock 2026.0.2 package. Offline checks still use the local catalogue
alone.

**Compatibility:** Older Suite shell versions only search the two local paths.
To enable fully automatic GitHub checks, existing users must upgrade their
Suite shell once (by updating the source checkout). After that, independently
published module updates are discovered and installed via the cards. A new Suite source checkout that already bundles Rock v2026.0.2 correctly
shows `v2026.0.2`, not an upgrade badge for the same version. To test
`2026.0.1 → 2026.0.2`, the **installed Rock module** must truly be
`2026.0.1` and the Suite shell must have the online update checker.
Adding a new file to GitHub cannot retrofit an older shell that never
contacts GitHub.

A record names the new release and where its archive lives:

```json
{
    "pile": {
        "version": "1.0.1",
        "changelog": "Socket side resistance correlations added.",
        "requires_core": ">=0.1.0",
        "url": "https://example.com/pile-1.0.1.zip",
        "sha256": "<published SHA-256 hex digest of the archive>"
    }
}
```

| Field | Meaning |
| --- | --- |
| `version` | the new release; shown only if newer than the installed one |
| `changelog` | shown on the update badge tooltip |
| `requires_core` | the core the release needs; incompatible cores see a warning badge instead of a button |
| `url` | HTTPS release ZIP, or a local file URL for offline tests |
| `sha256` | Required 64-character hexadecimal SHA-256 digest of the exact archive bytes |

## Publishing a release

1. Bump **only the edited module's** `slipsurface/<key>/app.json` version.
   Suite product version and core API version remain independent.
2. Merge the tested source changes to `main`. The
   `.github/workflows/publish-module-updates.yml` workflow validates the
   complete Python/Qt test suite before packaging changed module manifests.
3. The workflow runs `scripts/publish_module_updates.py` to create
   `module-updates/<key>-<version>.zip`, compute its SHA-256 hash and
   update both `module-versions.json` (the root version file) and
   `module-updates/index.json` (legacy alias). The workflow commits the
   version files and the module archive together to `main`.
   Re-publishing an existing same-version ZIP leaves its bytes unchanged.
4. Existing users' Suite launchers fetch the public catalogue asynchronously
   on startup and refresh the module cards. The `Güncelle / Update` button
   installs **only that module**. The Suite executable and other modules
   remain untouched.

For manual/offline publication use `python scripts/build_module_dist.py rock`
and place a trusted JSON catalogue in one of the local override paths.

No Windows EXE/installer is created and **no GitHub Release is published**;
only a separately versioned Python module archive is committed to the project.
If the publisher workflow fails (or repository write permissions are restricted),
the catalogue **does not automatically exist** until the failure is fixed.

## What the user sees

The launchpad shows a banner and one badge per module with a newer release,
plus a Güncelle button on the module's card. Clicking it downloads the
archive, checks it against the catalogue (same key, same version, a
compatible core, verified SHA-256 checksum, safe paths and bounded extraction) and unpacks it into `~/.slipsurface/apps/<key>/`.
The Suite installation is never modified; other modules are untouched; and
`slipsurface.installer.uninstall(key)` returns the module to the bundled
release.

## Rehearsing locally

`python scripts/demo_update.py` performs the entire flow offline: it builds
a patch-bumped archive of one module (`--key wall` chooses another), writes
`~/.slipsurface/index.json` pointing at it through a `file://` URL, and the
Suite offers and installs the update exactly as it would over the network.
`python scripts/demo_update.py --revert` removes the demonstration
catalogue afterwards.

## Security and installation boundaries

Updates execute Python code with the current user permissions. Only use a
catalogue whose author and hosting are trusted. SHA-256 verifies that the
archive matches that catalogue; it does **not** authenticate an untrusted
catalogue. Remote archives require HTTPS, and the importer rejects ZIP path
traversal, symlinks, case-folding collisions, oversized entries and excessive
unpacked data. A module with an open editor must be saved before update, and
an ongoing calculation prevents replacement. The prior module is restored if
the new module cannot be moved into place.

The Suite itself remains a Python-source desktop application launched using
`python main.py`. Optional per-module ZIP updates are **not** Windows EXE
or installer distribution packages.

## Activation failures and Windows validation

Before replacing a live release, a candidate ZIP is extracted into a temporary
folder and its `Session` import, application contract, and metadata are checked
in a separate Python interpreter with a bounded timeout. The working module
remains untouched when this preflight fails.

The PySide6 update flow then retains the previous installed module until the
new native editor can be opened successfully. Success discards the backup;
failure automatically restores the former release (or the original bundled
module for a first-time user installation). User project files must be saved
before starting any update.

Incompatible module versions are excluded from the launchable catalogue and
listed on the home dashboard together with their required core version.

The Windows CI pipeline installs `requirements-dev.txt`, compiles sources,
runs all pytest regressions and opens module pages with Qt offscreen mode.
The app continues to be launched using only `python main.py`. Windows EXE
production and releases are deliberately excluded.
