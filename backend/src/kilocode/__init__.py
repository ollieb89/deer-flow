"""Kilocode integration module.

Provides client and utilities for interacting with the kilocode AI Gateway.
"""

# Use lazy imports so that running `python -m src.kilocode.model_fetcher`
# doesn't trigger the RuntimeWarning caused by the module already being
# registered in sys.modules when the package __init__ is loaded.

__all__ = [
    "KilocodeClient",
    "ModelFetcher",
    "fetch_models",
    "dry_run_fetch",
]


def __getattr__(name: str):
    if name == "KilocodeClient":
        from .client import KilocodeClient
        return KilocodeClient
    if name in ("ModelFetcher", "fetch_models", "dry_run_fetch"):
        import importlib
        mod = importlib.import_module(".model_fetcher", package=__name__)
        return getattr(mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
