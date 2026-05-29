import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import flagged


class AlertScopeTests(unittest.TestCase):
    def test_set_alert_scope_updates_config_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config = {
                "score_threshold": 7,
                "alert_channels": flagged.default_alert_channels(),
            }

            with patch.object(flagged, "CONFIG_PATH", config_path):
                updated = flagged.set_alert_scope(
                    config,
                    "money_admin",
                    mode="mute",
                    min_score=10,
                    description="Only show admin if explicitly requested.",
                )
                reloaded = flagged.load_config()

        self.assertEqual(updated["mode"], "mute")
        self.assertEqual(updated["min_score"], 10)
        self.assertEqual(
            reloaded["alert_channels"]["money_admin"]["description"],
            "Only show admin if explicitly requested.",
        )


if __name__ == "__main__":
    unittest.main()
