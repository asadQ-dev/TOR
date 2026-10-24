import math
import unittest
from dataclasses import dataclass, field

from at_bat import Pitch

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
        self.assertEqual(result[0]["avg_bat_speed"], 80)
        self.assertEqual(result[0]["qualifying_bat_speed_count"], 1)
        self.assertEqual(result[0]["excluded_bat_speed_count"], 0)
        self.assertEqual(result[0]["missing_bat_speed_count"], 0)
        self.assertIsNone(result[0]["avg_exit_velo"])
        self.assertEqual(result[0]["qualifying_exit_velo_count"], 0)
        self.assertEqual(result[0]["excluded_exit_velo_count"], 0)
        self.assertEqual(result[0]["missing_exit_velo_count"], 0)

    def test_date_filter_includes_both_boundaries(self):
        appearances = [
            ExampleAtBat("2026-06-01", 10),
            ExampleAtBat("2026-06-02", 20),
            ExampleAtBat("2026-06-03", 30),
            ExampleAtBat("2026-06-04", 40),
        ]
        self.assertEqual(
            filter_by_date_range(appearances, "2026-06-02", "2026-06-03"),
            appearances[1:3],
        )

    def test_grouping_excludes_invalid_appearances_without_mutation(self):
        valid = ExampleAtBat("2026-06-01", 60)
        invalid = ExampleAtBat("2026-06-02", 1000, valid=False)
        self.assertEqual(
            group_by_date([valid, invalid]),
            {"2026-06-01": [valid]},
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
        result = get_trends(appearances, "2026-06-01", "2026-06-03")
        self.assertEqual(
            [(day["date"], day["tor"], day["plate_appearances"]) for day in result],
            [("2026-06-01", 70.0, 2), ("2026-06-02", 90.0, 1)],
        )

    def test_current_z_scores_use_pa_weighted_daily_means(self):
        appearances = [
            ExampleAtBat("2026-06-01", 60),
            ExampleAtBat("2026-06-01", 80),
            ExampleAtBat("2026-06-02", 90),
        ]
        result = get_trends(appearances, "2026-06-01", "2026-06-02")
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
        self.assertEqual([day["tor_z_score"] for day in result], [0, 0])

    def test_one_appearance_preserves_current_output(self):
        self.assertEqual(
            get_trends([ExampleAtBat("2026-06-01", 70)], "2026-06-01", "2026-06-01"),
            [{
                "date": "2026-06-01",
                "tor": 70.0,
                "plate_appearances": 1,
                "avg_exit_velo": None,
                "qualifying_exit_velo_count": 0,
                "excluded_exit_velo_count": 0,
                "missing_exit_velo_count": 0,
                "exit_velo_z_score": None,
                "tor_z_score": None,
                "avg_bat_speed": None,
                "qualifying_bat_speed_count": 0,
                "excluded_bat_speed_count": 0,
                "missing_bat_speed_count": 0,
                "bat_speed_z_score": None,
            }],
        )

    def test_empty_invalid_and_out_of_range_inputs_have_no_points(self):
        for appearances in (
            [],
            [ExampleAtBat("2026-06-01", 1000, valid=False)],
            [ExampleAtBat("2026-07-01", 1000)],
        ):
            with self.subTest(appearances=appearances):
                self.assertEqual(
                    get_trends(appearances, "2026-06-01", "2026-06-02"),
                    [],
                )
