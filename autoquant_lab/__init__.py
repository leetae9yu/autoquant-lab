"""Local namespace bridge for the src-layout autoquant_lab package."""

from __future__ import annotations

from pathlib import Path


_SRC_PACKAGE = Path(__file__).resolve().parents[1] / "src" / "autoquant_lab"
if _SRC_PACKAGE.is_dir():
    src_package_path = str(_SRC_PACKAGE)
    if src_package_path not in __path__:
        __path__.append(src_package_path)

del Path
del _SRC_PACKAGE
