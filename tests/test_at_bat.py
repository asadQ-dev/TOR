import unittest

from at_bat import AtBat, Pitch, SCORE_WEIGHTS
from scorer import player_tor, rank_players
from trends import get_trends


class AtBatTests(unittest.TestCase):
    def test_hard_foul_after_bunts_survives_hbp_or_intentional_walk(self):
        for outcome in ("hit_by_pitch", "intentional_walk"):
            with self.subTest(outcome=outcome):
                ab = AtBat("Example", outcome, "2026-06-01")
                ab.add_pitch(Pitch(1, "foul_bunt", 0, 0, 121, 100))
                ab.add_pitch(Pitch(2, "foul_bunt", 0, 1, 121, 100))
                ab.add_pitch(Pitch(3, "foul", 0, 2, 120, 84))
                ab.add_pitch(Pitch(4, outcome, 0, 2, 0, 0))

                self.assertTrue(ab.is_valid_ab())
                self.assertEqual(ab.quality_contact_score(), 80)
                self.assertAlmostEqual(ab.bat_speed_score(), 12 * 0.6)
                self.assertEqual(ab.outcome_score(), 0)
                expected = (
                    50
                    + ab.pitch_count_score() * SCORE_WEIGHTS["pitch_count"]
                    + ab.count_management_score() * SCORE_WEIGHTS["count_management"]
                    + 12 * 0.6 * SCORE_WEIGHTS["bat_speed"]
                    + 80 * SCORE_WEIGHTS["quality_contact"]
                )
                self.assertAlmostEqual(ab.calculate_tor(), expected)
                self.assertAlmostEqual(player_tor([ab]), expected)
                self.assertEqual(rank_players([ab], min_pas=1), [("Example", expected)])

                day = get_trends([ab], "2026-06-01", "2026-06-01")[0]
                self.assertAlmostEqual(day["tor"], expected)
                self.assertEqual(day["plate_appearances"], 1)
                self.assertEqual(day["avg_exit_velo"], 120)
                self.assertEqual(day["bunt_swing_count"], 2)
                self.assertEqual(day["speedq_swing_count"], 1)

    def test_hbp_and_intentional_walk_without_nonbunt_swings_stay_excluded(self):
        for outcome in ("hit_by_pitch", "intentional_walk"):
            for descriptions in (
                (),
                (outcome,),
                ("ball", "called_strike", outcome),
                ("foul_bunt", "missed_bunt", "bunt_foul_tip", outcome),
            ):
                with self.subTest(outcome=outcome, descriptions=descriptions):
                    ab = AtBat("Example", outcome, "2026-06-01")
                    for number, description in enumerate(descriptions, 1):
                        ab.add_pitch(Pitch(number, description, 0, 0, 121, 100))
                    self.assertFalse(ab.is_valid_ab())
                    self.assertEqual(ab.calculate_tor(), 0)
                    self.assertEqual(rank_players([ab], min_pas=1), [])

    def test_unscored_hbp_still_keeps_pitch_measurements_in_trends(self):
        ab = AtBat("Example", "hit_by_pitch", "2026-06-01")
        ab.add_pitch(Pitch(1, "ball", 0, 0, 0, 0))
        ab.add_pitch(Pitch(2, "hit_by_pitch", 1, 0, 0, 0))

        day = get_trends([ab], "2026-06-01", "2026-06-01")[0]

        self.assertIsNone(day["tor"])
        self.assertIsNone(day["tor_z_score"])
        self.assertEqual(day["plate_appearances"], 0)
        self.assertEqual(day["total_plate_appearances"], 1)
        self.assertEqual(day["pitch_count"], 2)

    def test_hbp_without_swings_does_not_dilute_player_tor_or_eligibility(self):
        scored = AtBat("Example", "field_out", "2026-06-01")
        scored.add_pitch(Pitch(1, "hit_into_play", 0, 0, 100, 80))
        hbp = AtBat("Example", "hit_by_pitch", "2026-06-01")
        hbp.add_pitch(Pitch(1, "hit_by_pitch", 0, 0, 0, 0))

        self.assertEqual(player_tor([scored, hbp]), scored.calculate_tor())
        self.assertEqual(rank_players([scored, hbp], min_pas=2), [])

    def test_strikeout_looking_remains_valid_and_scored_correctly(self):
        ab = AtBat("Example", "strikeout", "2026-06-01")
        ab.add_pitch(Pitch(1, "called_strike", 0, 0, 0, 0))
        ab.add_pitch(Pitch(2, "called_strike", 0, 1, 0, 0))
        ab.add_pitch(Pitch(3, "called_strike", 0, 2, 0, 0))

        self.assertTrue(ab.is_valid_ab())
        self.assertEqual(ab.outcome_score(), -1)
        self.assertEqual(ab.quality_contact_score(), 0)
        self.assertEqual(ab.bat_speed_score(), 0)
        expected = (
            50
            + ab.pitch_count_score() * SCORE_WEIGHTS["pitch_count"]
            + ab.count_management_score() * SCORE_WEIGHTS["count_management"]
            + (-1) * SCORE_WEIGHTS["outcome"]
        )
        self.assertAlmostEqual(ab.calculate_tor(), expected)
        self.assertAlmostEqual(player_tor([ab]), expected)
        self.assertEqual(rank_players([ab], min_pas=1), [("Example", expected)])

        day = get_trends([ab], "2026-06-01", "2026-06-01")[0]
        self.assertAlmostEqual(day["tor"], expected)
        self.assertEqual(day["plate_appearances"], 1)
        self.assertEqual(day["total_plate_appearances"], 1)
        self.assertEqual(day["pitch_count"], 3)
        self.assertEqual(day["swing_count"], 0)
        self.assertEqual(day["whiff_count"], 0)
        self.assertEqual(day["swing_rate"], 0)
        self.assertEqual(day["swstr_rate"], 0)
        self.assertIsNone(day["whiff_rate"])
        self.assertIsNone(day["nonbunt_whiff_rate"])
        self.assertIsNone(day["speedq_whiff_rate"])
        self.assertEqual(day["nonbunt_swing_count"], 0)
        self.assertEqual(day["nonbunt_whiff_count"], 0)
        self.assertEqual(day["bunt_swing_count"], 0)
        self.assertEqual(day["speedq_swing_count"], 0)
        self.assertEqual(day["speedq_whiff_count"], 0)