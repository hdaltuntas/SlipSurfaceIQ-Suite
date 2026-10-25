# Release Catalogue and the Update Flow

The Suite learns about new module releases from a release catalogue, and
installs them module by module. This document is the operator's guide: the
catalogue format, where to publish it, and how to rehearse the flow locally.

## The catalogue

A catalogue is a JSON object, one record per module key. Two locations are
checked at start-up, in order:

1. `~/.slipsurface/index.json` — the user's catalogue;
2. `./slipsurface-index.json` — a catalogue next to the working directory.

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

1. Bump the module's `slipsurface/<key>/app.json` `version` and commit it.
2. Build the archive: `python scripts/build_module_dist.py <key>` writes
   `dist/<key>-<version>.zip` and prints the catalogue entry to paste.
3. Host the archive anywhere the user's machine can reach — a GitHub
   release, a company file server, an object store — and set the record's
   `url` to its download address.
4. Publish the catalogue at one of the two lookup locations above. A
   static JSON file on the same server as the archives is usually enough.

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

## Candidate verification and rollback

SHA-256 and ZIP layout checks run before extraction. After extraction, the
Suite launches a separate Python interpreter against the staged package and
verifies that its actual `Session` can be imported and instantiated, satisfies
the shared module contract, and supplies schema/default metadata. A failed
preflight leaves the existing module untouched.

During desktop installation, the former installed release is retained under
`<key>.previous` until a new PySide6 module page has been successfully
created. An unsuccessful first launch restores the previous installed release.
If this was the first user-specific installation, rollback instead removes the
override to expose the bundled version. Successful activation removes the
backup; an already working release is kept if backup cleanup is temporarily
blocked by the operating system.

Preflight is intentionally a structural smoke check, not a guarantee that all
future numerical calculations or third-party dependencies will be error-free.
Trustworthy source and independent engineering verification are still required.

Windows users continue running `python main.py`. The Windows CI workflow
validates the source application; it does **not** package or publish an EXE.
