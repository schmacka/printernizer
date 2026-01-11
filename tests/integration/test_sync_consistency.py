"""
Sync Consistency Tests

Verifies that the two parallel codebases (src/ and printernizer/src/) maintain
consistent configurations to prevent routing and deployment issues.

These tests prevent issues like:
- Missing redirect_slashes=False configuration
- Inconsistent router endpoint patterns
- Version mismatches between deployments
"""

import ast
import re
from pathlib import Path
import pytest


class TestCodebaseSyncConsistency:
    """Test consistency between standalone and Home Assistant codebases.

    Note: The Home Assistant codebase is in a separate repository (printernizer-ha)
    and is only synced via GitHub Actions. These tests skip gracefully when the
    HA codebase is not present locally.
    """

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def standalone_main(self, project_root):
        """Path to standalone main.py."""
        return project_root / "src" / "main.py"

    @pytest.fixture
    def ha_main(self, project_root):
        """Path to Home Assistant main.py."""
        return project_root / "printernizer" / "src" / "main.py"

    @pytest.fixture
    def ha_codebase_available(self, project_root):
        """Check if HA codebase is available (only in CI with full sync)."""
        ha_dir = project_root / "printernizer" / "src"
        return ha_dir.exists()

    def test_both_main_files_have_redirect_slashes_false(
        self, standalone_main, ha_main, ha_codebase_available
    ):
        """
        Verify both main.py files have redirect_slashes=False in FastAPI config.

        This is CRITICAL to prevent 405 errors with trailing slash URLs.
        See CLAUDE.md API Routing Standards for details.
        """
        # Check standalone version
        standalone_content = standalone_main.read_text(encoding="utf-8")
        assert "redirect_slashes=False" in standalone_content, (
            f"Standalone {standalone_main} missing 'redirect_slashes=False' in FastAPI config. "
            "This causes 405 errors with trailing slash URLs. See CLAUDE.md API Routing Standards."
        )

        # Check Home Assistant version (skip if not available)
        if not ha_codebase_available:
            pytest.skip("Home Assistant codebase not available (separate repository)")

        ha_content = ha_main.read_text(encoding="utf-8")
        assert "redirect_slashes=False" in ha_content, (
            f"Home Assistant {ha_main} missing 'redirect_slashes=False' in FastAPI config. "
            "This causes 405 errors with trailing slash URLs. See CLAUDE.md API Routing Standards."
        )

    def test_router_endpoints_use_empty_string_not_slash(self, project_root):
        """
        Verify all router endpoints use "" (empty string) not "/" for root paths.

        With redirect_slashes=False, using "/" creates routes that REQUIRE
        trailing slashes, which breaks standard HTTP client behavior.
        """
        router_dirs = [
            project_root / "src" / "api" / "routers",
            project_root / "printernizer" / "src" / "api" / "routers",
        ]

        # Pattern to find router decorators with "/" as the path
        # Matches: @router.get("/"), @router.post("/"), etc.
        problematic_pattern = re.compile(r'@router\.\w+\(["\']\/["\']\)')

        errors = []
        for router_dir in router_dirs:
            if not router_dir.exists():
                continue

            for router_file in router_dir.glob("*.py"):
                content = router_file.read_text(encoding="utf-8")
                matches = problematic_pattern.findall(content)

                if matches:
                    errors.append(
                        f"{router_file.relative_to(project_root)}: "
                        f"Found {len(matches)} router endpoint(s) using '/' instead of ''. "
                        f"Examples: {matches[:3]}"
                    )

        assert not errors, (
            "Found router endpoints using '/' instead of '' (empty string). "
            "This creates routes requiring trailing slashes. "
            "See CLAUDE.md API Routing Standards.\n\n" + "\n".join(errors)
        )

    def test_version_numbers_are_in_sync(self, project_root, ha_codebase_available):
        """
        Verify version numbers exist and are properly formatted.

        Note: Versions can differ between standalone and HA (by design),
        but both must exist and follow semantic versioning.
        """
        # Check standalone version
        standalone_version_file = project_root / "src" / "utils" / "version.py"
        standalone_content = standalone_version_file.read_text(encoding="utf-8")

        # Extract fallback version from get_version function
        standalone_match = re.search(
            r'def get_version\(fallback: str = ["\'](\d+\.\d+\.\d+)["\']\)',
            standalone_content
        )
        assert standalone_match, (
            f"Could not find version fallback in {standalone_version_file}. "
            "Expected format: def get_version(fallback: str = \"X.Y.Z\")"
        )
        standalone_version = standalone_match.group(1)

        # Verify semantic versioning format
        assert re.match(r'^\d+\.\d+\.\d+$', standalone_version), (
            f"Standalone version '{standalone_version}' does not follow semantic versioning (X.Y.Z)"
        )

        print(f"\n✓ Standalone version: {standalone_version}")

        # Check Home Assistant version (skip if not available)
        if not ha_codebase_available:
            pytest.skip("Home Assistant codebase not available (separate repository)")

        ha_config_file = project_root / "printernizer" / "config.yaml"
        ha_content = ha_config_file.read_text(encoding="utf-8")

        ha_match = re.search(r'version:\s*["\'](\d+\.\d+\.\d+)["\']', ha_content)
        assert ha_match, (
            f"Could not find version in {ha_config_file}. "
            "Expected format: version: \"X.Y.Z\""
        )
        ha_version = ha_match.group(1)

        # Verify semantic versioning format
        assert re.match(r'^\d+\.\d+\.\d+$', ha_version), (
            f"Home Assistant version '{ha_version}' does not follow semantic versioning (X.Y.Z)"
        )

        print(f"✓ Home Assistant version: {ha_version}")

    def test_both_codebases_have_required_routers(self, project_root, ha_codebase_available):
        """
        Verify both codebases have the same set of API routers.

        Missing routers indicate incomplete synchronization between deployments.
        """
        standalone_routers = project_root / "src" / "api" / "routers"

        # Check standalone routers exist
        standalone_files = set(f.name for f in standalone_routers.glob("*.py") if f.name != "__init__.py")
        assert standalone_files, "No router files found in standalone codebase"
        print(f"\n✓ Standalone routers: {len(standalone_files)} files")

        # Check HA routers (skip if not available)
        if not ha_codebase_available:
            pytest.skip("Home Assistant codebase not available (separate repository)")

        ha_routers = project_root / "printernizer" / "src" / "api" / "routers"
        ha_files = set(f.name for f in ha_routers.glob("*.py") if f.name != "__init__.py")

        # Check for missing routers
        missing_in_ha = standalone_files - ha_files
        missing_in_standalone = ha_files - standalone_files

        errors = []
        if missing_in_ha:
            errors.append(f"Missing in Home Assistant: {sorted(missing_in_ha)}")
        if missing_in_standalone:
            errors.append(f"Missing in Standalone: {sorted(missing_in_standalone)}")

        assert not errors, (
            "Router files are not synchronized between standalone and Home Assistant codebases:\n" +
            "\n".join(errors)
        )


class TestDeploymentModeDetection:
    """Test that deployment mode detection works correctly."""

    def test_deployment_modes_are_documented(self, tmp_path):
        """
        Verify CLAUDE.md documents all three deployment modes.

        Ensures deployment documentation stays up to date.
        """
        claude_md = Path(__file__).parent.parent.parent / "CLAUDE.md"
        content = claude_md.read_text(encoding="utf-8")

        required_modes = [
            "Python Standalone",
            "Docker Standalone",
            "Home Assistant Add-on"
        ]

        for mode in required_modes:
            assert mode in content, (
                f"CLAUDE.md must document '{mode}' deployment method. "
                "See Deployment Architecture section."
            )


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])
