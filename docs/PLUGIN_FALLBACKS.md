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
