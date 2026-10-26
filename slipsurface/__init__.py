"""SlipSurfaceIQ Suite: native Python geotechnical desktop software."""
__version__ = "2026.0.0"

#: The version of the shared core — the engineering library, the application
#: contract (``slipsurface.contract``) and the manifest registry — that every
#: application declares in its ``app.json`` ``requires_core`` field.
CORE_VERSION = "0.1.0"

#: The CORE_VERSION is an independent API contract number, not a product version.
APP_NAME = "SlipSurfaceIQ Suite"
__all__ = ["__version__", "CORE_VERSION", "APP_NAME"]
