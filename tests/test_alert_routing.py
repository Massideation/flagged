import unittest

import flagged


class AlertRoutingTests(unittest.TestCase):
    def test_opportunity_sends_immediate_alert(self):
        score_data = flagged.normalize_score_data(
            {
                "score": 8,
                "category": "customer",
                "reason": "Customer asks a direct question.",
                "alert_channel": "opportunities",
            },
            {},
        )

        decision = flagged.alert_decision(score_data, {})

        self.assertEqual(decision["mode"], "immediate")
        self.assertEqual(decision["channel"], "opportunities")
        self.assertTrue(decision["send_now"])

    def test_money_admin_defaults_to_digest(self):
        score_data = flagged.normalize_score_data(
            {
                "score": 10,
                "category": "affiliate",
                "reason": "Affiliate payout notification.",
            },
            {},
        )

        decision = flagged.alert_decision(score_data, {})

        self.assertEqual(decision["mode"], "digest")
        self.assertEqual(decision["channel"], "money_admin")
        self.assertFalse(decision["send_now"])

    def test_sales_pitch_is_muted(self):
        score_data = flagged.normalize_score_data(
            {
                "score": 10,
                "category": "sales_pitch",
                "reason": "Cold vendor pitch.",
            },
            {},
        )

        decision = flagged.alert_decision(score_data, {})

        self.assertEqual(decision["mode"], "mute")
        self.assertEqual(decision["channel"], "sales_pitches")
        self.assertFalse(decision["send_now"])


if __name__ == "__main__":
    unittest.main()
