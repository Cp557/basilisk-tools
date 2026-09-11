from types import SimpleNamespace

import pytest

from basilisk_tools import doctor
from basilisk_tools.doctor import DependencyStatus


def test_doctor_reports_missing_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(doctor.sys, "version_info", (3, 10))
    monkeypatch.setattr(
        doctor,
        "_distribution_status",
        lambda name: DependencyStatus(name=name, installed=False, version=None),
    )

    report = doctor.collect_doctor_report()

    assert report["ok"] is False
    assert report["python"]["ok"] is False
    assert report["basilisk"]["version"] is None
    assert any("Python 3.11" in error for error in report["errors"])
    assert any("missing required dependencies" in error for error in report["errors"])


def test_doctor_reports_unsupported_basilisk_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def distribution_status(name: str) -> DependencyStatus:
        return DependencyStatus(name=name, installed=True, version="9.9.9")

    monkeypatch.setattr(doctor, "_distribution_status", distribution_status)
    monkeypatch.setattr(
        doctor.importlib,
        "import_module",
        lambda name: SimpleNamespace(__version__="9.9.9"),
    )

    report = doctor.collect_doctor_report()

    assert report["ok"] is False
    assert report["basilisk"]["ok"] is False
    assert any("supported Basilisk version" in error for error in report["errors"])
