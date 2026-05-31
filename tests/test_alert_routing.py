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
        self.assertEqual(score_data["gist"], "Customer asks a direct question.")
        self.assertEqual(score_data["why_flagged"], "Customer asks a direct question.")
        self.assertIn("noise", score_data["why_not_noise"].lower())

    def test_feedback_context_includes_good_bad_and_digest_examples(self):
        feedback = {
            "positive_examples": [
                {
                    "email": {"from": "Client <client@example.com>", "subject": "Can we talk?", "gist": "A client asks about paid work."},
                    "user_reason": "Real customer opportunity.",
                }
            ],
            "negative_examples": [
                {
                    "email": {"from": "Promo <promo@example.com>", "subject": "Last chance", "gist": "A generic sale."},
                    "user_reason": "Marketing blast.",
                }
            ],
            "digest_examples": [
                {
                    "email": {"from": "Platform <no-reply@example.com>", "subject": "Payout", "gist": "Automated payout notice."},
                    "user_reason": "Useful but not urgent.",
                }
            ],
        }

        context = flagged.build_feedback_context(feedback)

        self.assertIn("Good alerts", context)
        self.assertIn("Real customer opportunity", context)
        self.assertIn("Bad alerts", context)
        self.assertIn("Marketing blast", context)
        self.assertIn("digest-only", context)
        self.assertIn("Useful but not urgent", context)

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

    def test_school_family_email_can_be_opportunity(self):
        score_data = flagged.normalize_score_data(
            {
                "score": 8,
                "category": "opportunity",
                "reason": "Kid's school sent a specific action-required update.",
                "relationship": "knows_me",
                "ask_type": "needs_reply",
                "alert_channel": "opportunities",
            },
            {},
        )

        decision = flagged.alert_decision(score_data, {})

        self.assertEqual(decision["mode"], "immediate")
        self.assertTrue(decision["send_now"])


if __name__ == "__main__":
    unittest.main()
