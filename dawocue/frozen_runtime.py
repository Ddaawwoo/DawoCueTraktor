from __future__ import annotations

import sys
import tempfile
from pathlib import Path


def configure_frozen_numba_cache() -> None:
    """Make Numba caching work when package sources live inside a PyInstaller EXE."""
    if not getattr(sys, "frozen", False):
        return

    from numba.core import caching, config

    cache_root = Path(tempfile.gettempdir()) / "DawoCueTraktor-numba-cache"
    cache_root.mkdir(parents=True, exist_ok=True)
    config.CACHE_DIR = str(cache_root)

    class FrozenExecutableCacheLocator(caching.UserProvidedCacheLocator):
        @classmethod
        def from_function(cls, py_func, py_file):
            locator = cls(py_func, py_file)
            try:
                locator.ensure_cache_path()
            except OSError:
                return None
            return locator

    caching.CacheImpl._locator_classes.insert(0, FrozenExecutableCacheLocator)
