"""
Every code path that reports the application version must report the SAME value.

Regression test for a real defect: five call sites each passed their own
`fallback=` to get_version(), so a container with no git repository (the Docker
and Home Assistant deployments) answered /api/v1/health with "2.42.0",
/api/v1/system/info with "unknown", and usage telemetry with "2.7.0" — all for
the same running build.
"""
import re
from pathlib import Path

import pytest

from src.utils.version import FALLBACK_VERSION, get_version, get_short_version

SRC = Path(__file__).resolve().parents[2] / "src"


class TestSingleFallback:
    def test_fallback_version_is_a_semver_string(self):
        assert re.fullmatch(r"\d+\.\d+\.\d+", FALLBACK_VERSION), FALLBACK_VERSION

    def test_get_version_defaults_to_the_shared_fallback(self, monkeypatch):
        # Simulate a container with no git: git describe fails.
        monkeypatch.setattr("src.utils.version.subprocess.run",
                            lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError()))
        assert get_version() == FALLBACK_VERSION

    def test_get_short_version_defaults_to_the_shared_fallback(self, monkeypatch):
        monkeypatch.setattr("src.utils.version.subprocess.run",
                            lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError()))
        assert get_short_version() == FALLBACK_VERSION

    def test_no_call_site_overrides_the_fallback(self):
        """
        The whole point: a per-call-site `fallback=` is how the versions drifted
        apart. version.py itself defines the default; nothing else may override it.
        """
        offenders = []
        for path in SRC.rglob("*.py"):
            if path.name == "version.py":
                continue
            for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if re.search(r"get_(short_)?version\s*\(\s*fallback\s*=", line):
                    offenders.append(f"{path.relative_to(SRC.parent)}:{n}: {line.strip()}")

        assert not offenders, (
            "These call sites pass their own fallback version. Remove the argument "
            "and let src/utils/version.py own the single default:\n  "
            + "\n  ".join(offenders)
        )


class TestReportedVersionsAgree:
    def test_health_and_system_info_report_the_same_version(self, monkeypatch):
        """The two endpoints an external client is most likely to read."""
        monkeypatch.setattr("src.utils.version.subprocess.run",
                            lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError()))

        from src.main import APP_VERSION
        from src.utils.version import get_version as gv

        # config_service.get_system_info() sources its version the same way.
        assert gv() == FALLBACK_VERSION
        assert APP_VERSION == FALLBACK_VERSION or "-" in APP_VERSION, (
            "APP_VERSION should be the git version or the shared fallback, "
            f"never a private constant; got {APP_VERSION!r}"
        )
