class Pitch:
    def __init__(self, pitch_number, description, balls, strikes, exit_velo, bat_speed):
        self.pitch_number = pitch_number
        self.description = description
        self.balls = balls
        self.strikes = strikes
        self.exit_velo = exit_velo
        self.bat_speed = bat_speed


# ---------------------------------------------------------------------------
# TOR scoring configuration
# Every tunable weight, threshold, and point value for the metric lives here.
# Recalibrating the model should only ever require editing this block.
# ---------------------------------------------------------------------------

BASELINE_SCORE = 50

SCORE_WEIGHTS = {
    "pitch_count":      1.1,
    "count_management": 1.1,
    "bat_speed":        1.15,
    "quality_contact":  1.4,
    "outcome":          2,
}

INVALID_OUTCOMES = ["hit_by_pitch", "intentional_walk"]

# Pitch descriptions that count as "contact" for each sub-score.
CONTACT_DESCRIPTIONS = ("foul", "hit_into_play")
BAT_SPEED_DESCRIPTIONS = ("foul", "hit_into_play", "swinging_strike")

# (minimum pitch count, score) tiers, checked in order from most to least pitches.
PITCH_COUNT_TIERS = [
    (6, 4),
    (4, 2),
    (3, 0),
]
PITCH_COUNT_DEFAULT = -3

COUNT_MANAGEMENT = {
    "ahead_bonus":    0.25,  # balls > strikes
    "behind_penalty": -0.08, # strikes > balls
    "milestone_3_0":  0.3,
    "milestone_3_1":  0.22,
}

# (minimum exit velo, points) tiers. Below the lowest threshold contributes 0 -
# weak/bunt/outlier contact is intentionally excluded, not penalized.
QUALITY_CONTACT_TIERS = [
    (120, 175),
    (116, 80),
    (111, 40),
    (106, 24),
    (101, 14),
    (95,  7),
    (80,  2),
]

# (minimum bat speed, base points) tiers. Below the lowest threshold contributes 0.
BAT_SPEED_TIERS = [
    (84, 16),
    (81, 12),
    (78,  8),
    (75,  4),
    (72,  2),
    (69,  1),
]

# How much of the bat-speed base score counts, depending on what happened to the pitch.
BAT_SPEED_CONTACT_MULTIPLIER = {
    "hit_into_play":   1.0,
    "foul":            0.6,
    "swinging_strike": 0.1,
}

OUTCOME_SCORES = {
    "home_run": 80,
    "triple":   58,
    "double":   20,
    "single":    5,
    "walk":      3,
    "field_out": 0,
    "strikeout": -1,
}


def _lookup_tier(value, tiers, default=0):
    """Return the points for the highest tier whose threshold `value` exceeds."""
    for threshold, points in tiers:
        if value > threshold:
            return points
    return default


class AtBat:
    def __init__(self, player_name, final_outcome, game_date):
        self.player_name = player_name
        self.final_outcome = final_outcome
        self.game_date = game_date
        self.pitches = []

    def add_pitch(self, pitch):
        self.pitches.append(pitch)

    def is_valid_ab(self):
        if self.final_outcome in INVALID_OUTCOMES:
            return False
        if len(self.pitches) == 0:
            return False
        return True

    def pitch_count_score(self):
        n = len(self.pitches)
        for min_pitches, points in PITCH_COUNT_TIERS:
            if n >= min_pitches:
                return points
        return PITCH_COUNT_DEFAULT

    def count_management_score(self):
        score = 0
        milestone30 = False
        milestone31 = False
        for pitch in self.pitches:
            if pitch.balls > pitch.strikes:
                score += COUNT_MANAGEMENT["ahead_bonus"]
            elif pitch.strikes > pitch.balls:
                score += COUNT_MANAGEMENT["behind_penalty"]
            if pitch.balls == 3 and pitch.strikes == 0 and not milestone30:
                score += COUNT_MANAGEMENT["milestone_3_0"]
                milestone30 = True
            elif pitch.balls == 3 and pitch.strikes == 1 and not milestone30 and not milestone31:
                score += COUNT_MANAGEMENT["milestone_3_1"]
                milestone31 = True
        return score

    def quality_contact_score(self):
        score = 0
        for pitch in self.pitches:
            if pitch.description in CONTACT_DESCRIPTIONS:
                score += _lookup_tier(pitch.exit_velo, QUALITY_CONTACT_TIERS)
        return score

    def bat_speed_score(self):
        score = 0
        for pitch in self.pitches:
            if pitch.bat_speed and pitch.description in BAT_SPEED_DESCRIPTIONS:
                base = _lookup_tier(pitch.bat_speed, BAT_SPEED_TIERS)
                score += base * BAT_SPEED_CONTACT_MULTIPLIER[pitch.description]
        return score

    def outcome_score(self):
        return OUTCOME_SCORES.get(self.final_outcome, 0)

    def calculate_tor(self):
        if not self.is_valid_ab():
            return 0

        score = BASELINE_SCORE
        score += self.pitch_count_score()      * SCORE_WEIGHTS["pitch_count"]
        score += self.count_management_score() * SCORE_WEIGHTS["count_management"]
        score += self.bat_speed_score()        * SCORE_WEIGHTS["bat_speed"]
        score += self.quality_contact_score()  * SCORE_WEIGHTS["quality_contact"]
        score += self.outcome_score()          * SCORE_WEIGHTS["outcome"]
        return score