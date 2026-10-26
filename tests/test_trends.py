import json
import math
import unittest
from dataclasses import dataclass, field

from at_bat import AtBat, Pitch
from scorer import player_tor

from trends import filter_by_date_range, get_trends, group_by_date


@dataclass
class ExampleAtBat:
    game_date: str
    score: float
    valid: bool = True
    pitches: list[Pitch] = field(default_factory=list)

    def is_valid_ab(self):
        return self.valid

    def calculate_tor(self):
        return self.score


class TrendTests(unittest.TestCase):
    def test_correlation_pools_contacts_across_selected_days(self):
        appearances = [
            ExampleAtBat(f"2026-06-0{number}", 70, pitches=[
                Pitch(1, "hit_into_play", 0, 0, ev, speed),
            ])
            for number, (speed, ev) in enumerate(
                ((72, 80), (77, 90), (82, 100)), 1
            )
        ]
        result = get_trends(appearances, "2026-06-01", "2026-06-03")
        self.assertEqual(set(result), {"daily_data", "summary"})
        self.assertEqual(len(result["daily_data"]), 3)
        for day in result["daily_data"]:
            self.assertNotIn("bs_ev_correlation_index", day)
        summary = result["summary"]
        self.assertAlmostEqual(summary["bs_ev_correlation_index"], 1)
        self.assertEqual(summary["contact_count"], 3)
        self.assertEqual(summary["populated_tier_count"], 3)
        shorter = get_trends(appearances, "2026-06-02", "2026-06-03")["summary"]
        self.assertEqual(shorter["contact_count"], 2)
        self.assertIsNone(shorter["bs_ev_correlation_index"])

    def test_window_tiers_preserve_weights_and_boundary_membership(self):
        result = get_trends(
            [ExampleAtBat("2026-06-01", 70, pitches=[
                Pitch(1, "foul", 0, 0, 60, 69.5),
                Pitch(2, "hit_into_play", 0, 0, 100, 74),
                Pitch(3, "hit_into_play_no_out", 0, 0, 90, 75),
                Pitch(4, "hit_into_play_score", 0, 0, 100, 80),
                Pitch(5, "foul_tip", 0, 0, 110, 85),
            ])],
            "2026-06-01", "2026-06-01",
        )
        profile = result["summary"]["bs_ev_tier_profile"]
        low = profile["<75"]
        self.assertEqual(low["contact_count"], 2)
        self.assertAlmostEqual(low["weight_sum"], 1.6)
        self.assertAlmostEqual(low["avg_exit_velo"], (60 * 0.6 + 100) / 1.6)
        self.assertAlmostEqual(low["avg_bat_speed"], (69.5 * 0.6 + 74) / 1.6)
        for tier, speed in (("75-80", 75), ("80-85", 80), ("85+", 85)):
            self.assertEqual(profile[tier]["contact_count"], 1)
            self.assertAlmostEqual(profile[tier]["avg_bat_speed"], speed)
        self.assertAlmostEqual(profile["85+"]["weight_sum"], 0.6)

    def test_window_correlation_handles_empty_sparse_and_constant_data(self):
        for measurements in (
            (),
            ((72, 90),),
            ((72, 90), (77, 100)),
            ((72, 90), (77, 90), (82, 90)),
        ):
            with self.subTest(measurements=measurements):
                result = get_trends(
                    [ExampleAtBat("2026-06-01", 70, pitches=[
                        Pitch(i, "foul", 0, 0, ev, speed)
                        for i, (speed, ev) in enumerate(measurements, 1)
                    ])],
                    "2026-06-01", "2026-06-01",
                )
                self.assertIsNone(result["summary"]["bs_ev_correlation_index"])
        empty = get_trends([], "2026-06-01", "2026-06-01")
        self.assertEqual(empty["daily_data"], [])
        self.assertEqual(empty["summary"]["contact_count"], 0)
        for tier in empty["summary"]["bs_ev_tier_profile"].values():
            self.assertIsNone(tier["avg_bat_speed"])
            self.assertIsNone(tier["avg_exit_velo"])

    def test_window_correlation_excludes_invalid_pairs_and_can_be_negative(self):
        result = get_trends(
            [ExampleAtBat("2026-06-01", 70, pitches=[
                Pitch(1, "hit_into_play", 0, 0, 100, 72),
                Pitch(2, "hit_into_play", 0, 0, 90, 77),
                Pitch(3, "hit_into_play", 0, 0, 80, 82),
                Pitch(4, "foul", 0, 0, 120, math.inf),
                Pitch(5, "foul", 0, 0, math.inf, 85),
                Pitch(6, "foul", 0, 0, 120, None),
                Pitch(7, "foul", 0, 0, math.nan, 85),
                Pitch(8, "foul_bunt", 0, 0, 120, 85),
                Pitch(9, "swinging_strike", 0, 0, 120, 85),
                Pitch(10, "foul", 0, 0, 120, 69),
                Pitch(11, "foul", 0, 0, 0, 85),
            ])],
            "2026-06-01", "2026-06-01",
        )
        self.assertEqual(result["summary"]["contact_count"], 3)
        self.assertAlmostEqual(result["summary"]["bs_ev_correlation_index"], -1)
        json.dumps(result, allow_nan=False)

    def test_bat_speed_population_includes_swinging_strikes(self):
        result = get_trends(
            [ExampleAtBat(
                "2026-06-01",
                70,
                pitches=[Pitch(1, "swinging_strike", 0, 0, 0, 80)],
            )],
            "2026-06-01",
            "2026-06-01",
        )
        result = result["daily_data"]
        self.assertEqual(result[0]["avg_bat_speed"], 80)
        self.assertEqual(result[0]["qualifying_bat_speed_count"], 1)
        self.assertEqual(result[0]["excluded_bat_speed_count"], 0)
        self.assertEqual(result[0]["missing_bat_speed_count"], 0)
        self.assertIsNone(result[0]["avg_exit_velo"])
        self.assertEqual(result[0]["qualifying_exit_velo_count"], 0)
        self.assertEqual(result[0]["excluded_exit_velo_count"], 0)
        self.assertEqual(result[0]["missing_exit_velo_count"], 0)
        self.assertEqual(result[0]["swing_count"], 1)
        self.assertEqual(result[0]["whiff_count"], 1)
        self.assertEqual(result[0]["nonbunt_swing_count"], 1)
        self.assertEqual(result[0]["nonbunt_whiff_count"], 1)
        self.assertEqual(result[0]["speedq_swing_count"], 1)
        self.assertEqual(result[0]["speedq_whiff_count"], 1)
        self.assertEqual(result[0]["whiff_rate"], 1)
        self.assertEqual(result[0]["nonbunt_whiff_rate"], 1)
        self.assertEqual(result[0]["speedq_whiff_rate"], 1)

    def test_speed_qualified_whiffs_require_measured_speed_above_cutoff(self):
        for description in ("swinging_strike", "swinging_strike_blocked"):
            for speed, qualifies in (
                (69, False),
                (69.0001, True),
                (30, False),
                (0, False),
                (None, False),
                (math.nan, False),
                (math.inf, False),
            ):
                with self.subTest(description=description, speed=speed):
                    result = get_trends(
                        [ExampleAtBat(
                            "2026-06-01",
                            70,
                            pitches=[Pitch(1, description, 0, 0, 0, speed)],
                        )],
                        "2026-06-01",
                        "2026-06-01",
                    )
                    day = result["daily_data"][0]
                    self.assertEqual(day["swing_count"], 1)
                    self.assertEqual(day["whiff_count"], 1)
                    self.assertEqual(day["nonbunt_swing_count"], 1)
                    self.assertEqual(day["nonbunt_whiff_count"], 1)
                    self.assertEqual(day["nonbunt_whiff_rate"], 1)
                    self.assertEqual(day["speedq_swing_count"], int(qualifies))
                    self.assertEqual(day["speedq_whiff_count"], int(qualifies))
                    if qualifies:
                        self.assertEqual(day["speedq_whiff_rate"], 1)
                    else:
                        self.assertIsNone(day["speedq_whiff_rate"])

    def test_date_filter_includes_both_boundaries(self):
        appearances = [
            ExampleAtBat(game_date="2026-06-01", score=10),
            ExampleAtBat("2026-06-02", 20),
            ExampleAtBat("2026-06-03", 30),
            ExampleAtBat("2026-06-04", 40),
        ]
        self.assertEqual(
            filter_by_date_range(appearances, "2026-06-02", "2026-06-03"),
            appearances[1:3],
        )

    def test_grouping_retains_all_appearances_without_mutation(self):
        valid = ExampleAtBat("2026-06-01", 60)
        invalid = ExampleAtBat("2026-06-02", 1000, valid=False)
        self.assertEqual(
            group_by_date([valid, invalid]),
            {"2026-06-01": [valid], "2026-06-02": [invalid]},
        )
        self.assertEqual(valid.game_date, "2026-06-01")
        self.assertEqual(invalid.game_date, "2026-06-02")

    def test_trends_average_and_count_each_appearance_once(self):
        appearances = [
            ExampleAtBat("2026-06-02", 90),
            ExampleAtBat("2026-06-01", 60),
            ExampleAtBat("2026-06-01", 80),
            ExampleAtBat("2026-06-01", 1000, valid=False),
            ExampleAtBat("2026-06-03", 1000, valid=False),
            ExampleAtBat("2026-07-01", 1000),
        ]
        result = get_trends(appearances, "2026-06-01", "2026-06-03")["daily_data"]
        self.assertEqual(
            [(day["date"], day["tor"], day["plate_appearances"]) for day in result],
            [("2026-06-01", 70.0, 2), ("2026-06-02", 90.0, 1), ("2026-06-03", None, 0)],
        )
        self.assertEqual([day["total_plate_appearances"] for day in result], [3, 1, 1])

    def test_current_z_scores_use_pa_weighted_daily_means(self):
        appearances = [
            ExampleAtBat("2026-06-01", 60),
            ExampleAtBat("2026-06-01", 80),
            ExampleAtBat("2026-06-02", 90),
        ]
        result = get_trends(appearances, "2026-06-01", "2026-06-02")["daily_data"]
        mean = (60 + 80 + 90) / 3
        deviation = math.sqrt((2 * (70 - mean) ** 2 + (90 - mean) ** 2) / 3)
        self.assertEqual(result[0]["tor_z_score"], round((70 - mean) / deviation, 2))
        self.assertEqual(result[1]["tor_z_score"], round((90 - mean) / deviation, 2))

    def test_equal_daily_means_have_zero_window_z_score(self):
        result = get_trends(
            [ExampleAtBat("2026-06-01", 70), ExampleAtBat("2026-06-02", 70)],
            "2026-06-01",
            "2026-06-02",
        )
        self.assertEqual([day["tor_z_score"] for day in result["daily_data"]], [0, 0])

    def test_one_appearance_preserves_current_output(self):
        self.assertEqual(
            get_trends([ExampleAtBat("2026-06-01", 70)], "2026-06-01", "2026-06-01")["daily_data"],
            [{
                "date": "2026-06-01",
                "tor": 70.0,
                "plate_appearances": 1,
                "total_plate_appearances": 1,
                "avg_exit_velo": None,
                "qualifying_exit_velo_count": 0,
                "excluded_exit_velo_count": 0,
                "missing_exit_velo_count": 0,
                "contact_exit_velo_count": 0,
                "hard_exit_velo_count": 0,
                "very_hard_exit_velo_count": 0,
                "elite_exit_velo_count": 0,
                "missing_power_exit_velo_count": 0,
                "hard_contact_rate": None,
                "very_hard_contact_rate": None,
                "elite_contact_rate": None,
                "exit_velo_z_score": None,
                "tor_z_score": None,
                "avg_bat_speed": None,
                "qualifying_bat_speed_count": 0,
                "excluded_bat_speed_count": 0,
                "missing_bat_speed_count": 0,
                "bat_speed_z_score": None,
                "pitch_count": 0,
                "swing_count": 0,
                "whiff_count": 0,
                "bunt_swing_count": 0,
                "nonbunt_swing_count": 0,
                "nonbunt_whiff_count": 0,
                "speedq_swing_count": 0,
                "speedq_whiff_count": 0,
                "swing_rate": None,
                "whiff_rate": None,
                "swstr_rate": None,
                "nonbunt_whiff_rate": None,
                "speedq_whiff_rate": None,
                "contact_exit_velo_count": 0,
                "hard_exit_velo_count": 0,
                "very_hard_exit_velo_count": 0,
                "elite_exit_velo_count": 0
            }],
        )

    def test_empty_and_out_of_range_inputs_have_no_points(self):
        for appearances in (
            [],
            [ExampleAtBat("2026-07-01", 1000)],
        ):
            with self.subTest(appearances=appearances):
                self.assertEqual(
                    get_trends(appearances, "2026-06-01", "2026-06-02")["daily_data"],
                    [],
                )

    def test_hbp_with_nonbunt_swings_contributes_to_measurements_and_tor(self):
        valid = AtBat("Example", "field_out", "2026-06-01")
        valid.add_pitch(Pitch(1, "hit_into_play", 0, 0, 90, 80))
        hbp = AtBat("Example", "hit_by_pitch", "2026-06-01")
        hbp.add_pitch(Pitch(1, "foul", 0, 0, 100, 90))
        hbp.add_pitch(Pitch(2, "swinging_strike", 0, 1, 0, 80))
        hbp.add_pitch(Pitch(3, "hit_by_pitch", 0, 2, 0, 0))
        scores_before = [ab.calculate_tor() for ab in (valid, hbp)]
        expected_tor = player_tor([valid, hbp])

        day = get_trends([valid, hbp], "2026-06-01", "2026-06-01")["daily_data"][0]

        self.assertEqual(day["tor"], expected_tor)
        self.assertEqual(day["plate_appearances"], 2)
        self.assertEqual(day["total_plate_appearances"], 2)
        self.assertEqual(day["pitch_count"], 4)
        self.assertEqual(day["swing_count"], 3)
        self.assertEqual(day["whiff_count"], 1)
        self.assertEqual(day["avg_exit_velo"], 95)
        self.assertEqual(day["qualifying_bat_speed_count"], 3)
        self.assertAlmostEqual(day["avg_bat_speed"], 250 / 3)
        self.assertEqual(day["speedq_whiff_rate"], 1 / 3)
        self.assertEqual([ab.calculate_tor() for ab in (valid, hbp)], scores_before)
        self.assertTrue(hbp.is_valid_ab())

    def test_unscored_day_retains_measurements_without_affecting_tor_z_scores(self):
        result = get_trends(
            [
                ExampleAtBat("2026-06-01", 60),
                ExampleAtBat(
                    "2026-06-02",
                    1000,
                    valid=False,
                    pitches=[Pitch(1, "swinging_strike", 0, 0, 0, 80)],
                ),
                ExampleAtBat("2026-06-03", 80),
            ],
            "2026-06-01",
            "2026-06-03",
        )
        result = result["daily_data"]
        day = result[1]
        self.assertEqual([point["tor_z_score"] for point in result], [-1, None, 1])
        self.assertIsNone(day["tor"])
        self.assertEqual(day["plate_appearances"], 0)
        self.assertEqual(day["total_plate_appearances"], 1)
        self.assertEqual(day["avg_bat_speed"], 80)
        self.assertEqual(day["speedq_whiff_rate"], 1)

    def test_bat_speed_average_and_speed_qualified_counts_share_population(self):
        result = get_trends(
            [ExampleAtBat("2026-06-01", 70, pitches=[
                Pitch(1, "swinging_strike_blocked", 0, 0, 0, 80),
                Pitch(2, "foul_tip", 0, 0, 0, 90),
                Pitch(3, "foul", 0, 0, 0, None),
                Pitch(4, "swinging_strike", 0, 0, 0, 69),
                Pitch(5, "missed_bunt", 0, 0, 0, 100),
                Pitch(6, "ball", 0, 0, 0, 100),
            ])],
            "2026-06-01",
            "2026-06-01",
        )
        day = result["daily_data"][0]
        self.assertEqual(day["avg_bat_speed"], 85)
        self.assertEqual(day["qualifying_bat_speed_count"], 2)
        self.assertEqual(day["speedq_swing_count"], 2)
        self.assertEqual(day["speedq_whiff_count"], 1)
        self.assertEqual(day["speedq_whiff_rate"], 0.5)
        self.assertEqual(day["missing_bat_speed_count"], 1)
        self.assertEqual(day["excluded_bat_speed_count"], 1)
        self.assertEqual(
            day["nonbunt_swing_count"],
            day["qualifying_bat_speed_count"]
            + day["missing_bat_speed_count"]
            + day["excluded_bat_speed_count"],
        )

    def test_swinging_bunts_are_counted_once(self):
        result = get_trends(
            [ExampleAtBat("2026-06-01", 70, pitches=[
                Pitch(1, "foul", 0, 0, 0, 80),
                Pitch(2, "foul_bunt", 0, 0, 0, 80),
                Pitch(3, "missed_bunt", 0, 0, 0, 80),
                Pitch(4, "bunt_foul_tip", 0, 0, 0, 80),
                Pitch(5, "ball", 0, 0, 0, 0),
            ])],
            "2026-06-01",
            "2026-06-01"
        )
        result = result["daily_data"]
        self.assertEqual(result[0]["swing_count"], 4)
        self.assertEqual(result[0]["pitch_count"], 5)
        self.assertEqual(result[0]["swing_rate"], 4 / 5)
        self.assertEqual(result[0]["nonbunt_swing_count"], 1)
        self.assertEqual(result[0]["bunt_swing_count"], 3)
        self.assertEqual(result[0]["speedq_swing_count"], 1)
        self.assertEqual(result[0]["whiff_count"], 1)
        self.assertEqual(result[0]["nonbunt_whiff_count"], 0)
        self.assertEqual(result[0]["speedq_whiff_count"], 0)
        self.assertEqual(result[0]["whiff_rate"], 0.25)
        self.assertEqual(result[0]["swstr_rate"], 1 / 5)
        self.assertEqual(result[0]["nonbunt_whiff_rate"], 0)
        self.assertEqual(result[0]["speedq_whiff_rate"], 0)

    def test_hard_contact_tiers_count_cumulatively(self):
        result = get_trends(
            [ExampleAtBat("2026-06-01", 70, pitches=[
                Pitch(1, "hit_into_play", 0, 0, 117, 80),
                Pitch(2, "foul",          0, 0, 108, 80),
                Pitch(3, "hit_into_play", 0, 0,  97, 80),
                Pitch(4, "hit_into_play", 0, 0,  70, 80),
                Pitch(5, "foul_bunt",     0, 0, 120, 80),
                Pitch(6, "hit_into_play", 0, 0,   0, 80),
            ])],
            "2026-06-01","2026-06-01"
        )["daily_data"][0]
        self.assertEqual(result["contact_exit_velo_count"], 4)
        self.assertEqual(result["hard_exit_velo_count"], 3)
        self.assertEqual(result["very_hard_exit_velo_count"], 2)
        self.assertEqual(result["elite_exit_velo_count"], 1)
        self.assertEqual(result["hard_contact_rate"], 3 / 4)
        self.assertEqual(result["very_hard_contact_rate"], 2 / 4)
        self.assertEqual(result["elite_contact_rate"], 1 / 4)
        self.assertEqual(result["missing_power_exit_velo_count"], 1)
        self.assertEqual(result["qualifying_exit_velo_count"], 3)
        self.assertEqual(result["excluded_exit_velo_count"], 1)
        self.assertAlmostEqual(result["avg_exit_velo"], (117 + 108 + 97) / 3)

    def test_contact_tier_boundaries_match_chart_definition(self):
        for ev, counts in (
            (94.9, (0, 0, 0)),
            (95, (1, 0, 0)),
            (95.1, (1, 0, 0)),
            (104.9, (1, 0, 0)),
            (105, (1, 1, 0)),
            (105.1, (1, 1, 0)),
            (114.9, (1, 1, 0)),
            (115, (1, 1, 1)),
            (115.1, (1, 1, 1)),
        ):
            with self.subTest(exit_velo=ev):
                day = get_trends(
                    [ExampleAtBat("2026-06-01", 70, pitches=[
                        Pitch(1, "foul", 0, 0, ev, 80),
                    ])],
                    "2026-06-01", "2026-06-01",
                )["daily_data"][0]
                self.assertEqual(day["contact_exit_velo_count"], 1)
                for key, expected in zip(
                    ("hard_exit_velo_count", "very_hard_exit_velo_count", "elite_exit_velo_count"),
                    counts,
                ):
                    self.assertEqual(day[key], expected)

    def test_hard_contact_swings_survive_hbp_or_intentional_walk(self):
        for outcome in ["hit_by_pitch", "intentional_walk"]:
            with self.subTest(outcome=outcome):
                ab = AtBat("Example", outcome, "2026-06-01")
                ab.add_pitch(Pitch(1, "foul_bunt", 0, 0, 121, 100))
                ab.add_pitch(Pitch(2, "foul_bunt", 0, 1,  90, 100))
                ab.add_pitch(Pitch(3, "foul",      0, 2,  98,  84))
                ab.add_pitch(Pitch(4, "foul",      0, 2, 119,  90))
                ab.add_pitch(Pitch(5, outcome,     0, 2,   0,   0))
                self.assertTrue(ab.is_valid_ab())
                day = get_trends([ab], "2026-06-01", "2026-06-01")["daily_data"][0]
                self.assertEqual(day["contact_exit_velo_count"], 2)
                self.assertEqual(day["hard_exit_velo_count"], 2)
                self.assertEqual(day["very_hard_exit_velo_count"], 1)
                self.assertEqual(day["elite_exit_velo_count"], 1)
                self.assertEqual(day["hard_contact_rate"], 1)
                self.assertEqual(day["very_hard_contact_rate"], 0.5)
                self.assertEqual(day["elite_contact_rate"], 0.5)
                self.assertEqual(day["avg_exit_velo"], (98 + 119) / 2)

    def test_power_population_requires_contact_speed_and_measured_ev(self):
        for description, bat_speed, ev, eligible in (
            ("foul", 69, 120, False),
            ("foul", 69.01, 120, True),
            ("foul", None, 120, False),
            ("foul", math.inf, 120, False),
            ("foul", math.nan, 120, False),
            ("foul", 30, 120, False),
            ("foul", 80, None, False),
            ("foul", 80, 0, False),
            ("foul", 80, -1, False),
            ("foul", 80, math.nan, False),
            ("foul", 80, math.inf, False),
            ("foul_tip", 80, 120, True),
            ("hit_into_play_no_out", 80, 120, True),
            ("hit_into_play_score", 80, 120, True),
            ("swinging_strike", 80, 120, False),
            ("swinging_strike_blocked", 80, 120, False),
            ("foul_bunt", 80, 120, False),
            ("bunt_foul_tip", 80, 120, False),
            ("missed_bunt", 80, 120, False),
            ("ball", 80, 120, False),
        ):
            with self.subTest(description=description, bat_speed=bat_speed, ev=ev):
                day = get_trends(
                    [ExampleAtBat("2026-06-01", 70, pitches=[
                        Pitch(1, description, 0, 0, ev, bat_speed),
                    ])],
                    "2026-06-01", "2026-06-01",
                )["daily_data"][0]
                self.assertEqual(day["contact_exit_velo_count"], int(eligible))
                self.assertEqual(day["hard_exit_velo_count"], int(eligible))
                if eligible:
                    self.assertEqual(day["hard_contact_rate"], 1)
                else:
                    self.assertIsNone(day["hard_contact_rate"])
                    self.assertIsNone(day["very_hard_contact_rate"])
                    self.assertIsNone(day["elite_contact_rate"])
