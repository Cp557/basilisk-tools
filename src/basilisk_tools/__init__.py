"""Agent-ready tooling for AVS Basilisk."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("basilisk-tools")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"

__all__ = ["__version__"]
