"""Tests for HomeKit Guard blocking logic."""

import importlib.util
from pathlib import Path
import unittest

GUARD_MODULE = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "homekit_guard"
    / "guard.py"
)
spec = importlib.util.spec_from_file_location("homekit_guard_guard", GUARD_MODULE)
assert spec is not None
guard = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(guard)
should_block_service = guard.should_block_service


class GuardLogicTest(unittest.TestCase):
    """Tests for guard service blocking decisions."""

    def test_allow_list_only_blocks_everything_except_allowed(self) -> None:
        """Allow-only mode blocks all other HomeKit service calls."""
        self.assertFalse(
            should_block_service("cover.close_cover", set(), {"cover.close_cover"})
        )
        self.assertTrue(
            should_block_service("cover.open_cover", set(), {"cover.close_cover"})
        )

    def test_block_list_only_blocks_only_blocked_services(self) -> None:
        """Block-only mode allows services that are not listed."""
        self.assertTrue(
            should_block_service("cover.open_cover", {"cover.open_cover"}, set())
        )
        self.assertFalse(
            should_block_service("cover.close_cover", {"cover.open_cover"}, set())
        )

    def test_allowed_services_take_precedence_over_blocked_services(self) -> None:
        """Allowed services win when both lists contain the same service."""
        self.assertFalse(
            should_block_service(
                "cover.open_cover",
                {"cover.open_cover"},
                {"cover.open_cover"},
            )
        )

    def test_empty_lists_block_nothing(self) -> None:
        """An empty configuration blocks nothing."""
        self.assertFalse(should_block_service("cover.open_cover", set(), set()))


if __name__ == "__main__":
    unittest.main()
