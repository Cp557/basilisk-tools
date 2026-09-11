"""Environment diagnostics for Basilisk Tools."""

import importlib
import platform
import sys
from dataclasses import asdict, dataclass
from importlib.metadata import PackageNotFoundError, version
from typing import Any

from basilisk_tools import __version__
from basilisk_tools.results import SCHEMA_VERSION

BASILISK_DISTRIBUTION = "bsk"
BASILISK_MODULE = "Basilisk"
BASILISK_REQUIRED_VERSION = "2.11.1"

REQUIRED_DEPENDENCIES = ("matplotlib", "numpy", "rich", "typer")
OPTIONAL_DEPENDENCIES = ("pytest", "ruff")


@dataclass(frozen=True)
class DependencyStatus:
    """Installation status for one Python distribution."""

    name: str
    installed: bool
    version: str | None


def _distribution_status(name: str) -> DependencyStatus:
    try:
        installed_version = version(name)
    except PackageNotFoundError:
        return DependencyStatus(name=name, installed=False, version=None)
    return DependencyStatus(name=name, installed=True, version=installed_version)


def collect_doctor_report() -> dict[str, Any]:
    """Collect deterministic runtime and dependency diagnostics."""
    errors: list[str] = []
    python_ok = sys.version_info >= (3, 11)
    if not python_ok:
        errors.append("Install Python 3.11 or newer and recreate the environment.")

    basilisk_status = _distribution_status(BASILISK_DISTRIBUTION)
    basilisk_import_error: str | None = None
    if basilisk_status.installed:
        try:
            module = importlib.import_module(BASILISK_MODULE)
            basilisk_version = getattr(module, "__version__", basilisk_status.version)
        except Exception as error:  # pragma: no cover - depends on local installation
            basilisk_version = basilisk_status.version
            basilisk_import_error = f"{type(error).__name__}: {error}"
            errors.append(
                "Basilisk is installed but cannot be imported; reinstall the locked "
                "environment with 'uv sync --locked'."
            )
    else:
        basilisk_version = None
        errors.append("Install project dependencies with 'uv sync --locked'.")

    if basilisk_version and basilisk_version != BASILISK_REQUIRED_VERSION:
        errors.append(
            "Install the supported Basilisk version with "
            f"'uv add bsk=={BASILISK_REQUIRED_VERSION}'."
        )

    required = [_distribution_status(name) for name in REQUIRED_DEPENDENCIES]
    missing = [dependency.name for dependency in required if not dependency.installed]
    if missing:
        errors.append(
            "Install missing required dependencies with 'uv sync --locked': "
            + ", ".join(missing)
            + "."
        )

    optional = [_distribution_status(name) for name in OPTIONAL_DEPENDENCIES]
    return {
        "schema_version": SCHEMA_VERSION,
        "ok": not errors,
        "python": {
            "ok": python_ok,
            "version": platform.python_version(),
            "executable": sys.executable,
            "requirement": ">=3.11",
        },
        "basilisk": {
            "ok": (
                basilisk_status.installed
                and basilisk_import_error is None
                and basilisk_version == BASILISK_REQUIRED_VERSION
            ),
            "version": basilisk_version,
            "requirement": f"=={BASILISK_REQUIRED_VERSION}",
            "import_error": basilisk_import_error,
        },
        "basilisk_tools": {"version": __version__},
        "required_dependencies": [asdict(item) for item in required],
        "optional_dependencies": [asdict(item) for item in optional],
        "errors": errors,
    }
