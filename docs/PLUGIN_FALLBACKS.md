# Resilient plugin discovery

Applications are discovered from bundled manifests, Python distribution entry points,
and per-user installed module updates.

External modules receive a generic engineering icon and a neutral workspace profile
when their key has no built-in visual customization. No source code is executed
while reading a user-folder manifest.

The native frontend must not assert that the catalogue has exactly ten modules:
ten are bundled, but plugin entry points and installed modules can add more.
Their session must implement the documented `AppSession` contract. The UI
should display a recoverable error for an invalid module rather than crash.

Bundled engineering modules retain their own SVG symbols and localized panels.

## Incompatible core handling

Every discovered manifest retains its required core version and carries a
`compatible` flag in the application catalogue. The native launcher shows
incompatible applications with an explicit warning and a disabled Open action.
The sidebar also disables their entries. Direct attempts to open an incompatible
module are blocked before importing its code.

This makes incompatible releases visible for diagnosis while preventing a
module compiled against another core contract from running unexpectedly.
