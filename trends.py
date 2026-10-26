import math

import numpy as np

from at_bat import (
    BAT_SPEED_TIERS,
    BUNT_SWING_DESCRIPTIONS,
    CONTACT_DESCRIPTIONS,
    POWER_CONTACT_DESCRIPTIONS,
    QUALITY_CONTACT_TIERS,
    SWING_DESCRIPTIONS,
    WHIFF_DESCRIPTIONS,
)
from scorer import player_tor

BAT_SPEED_PROFILE_TIERS = ("<75", "75-80", "80-85", "85+")


def bat_speed_profile_tier(bat_speed):
    """Classify a finite, speed-qualified swing into a profile tier."""
    if bat_speed < 75:
        return "<75"
    if bat_speed < 80:
        return "75-80"
    if bat_speed < 85:
        return "80-85"
    return "85+"


def group_by_date(player_at_bats):
    """Group all appearances; each metric applies its own eligibility rules."""
    ab_by_date = {}
    for ab in player_at_bats:
        game_date = ab.game_date
        if game_date not in ab_by_date:
            ab_by_date[game_date] = []
        ab_by_date[game_date].append(ab)
    return ab_by_date


def filter_by_date_range(player_at_bats, start_date, end_date):
    return [
        ab for ab in player_at_bats
        if start_date <= ab.game_date <= end_date
    ]


def get_trends(player_at_bats, start_date, end_date):
    filtered_abs = filter_by_date_range(player_at_bats, start_date, end_date)
    ab_by_date = group_by_date(filtered_abs)

    daily_data = []
    qualifying_bat_speeds = []
    qualifying_exit_velos = []

    qualifying_power_pairs = []
    qualifying_power_vs_misses_pairs = []

    bat_speed_cutoff = min(threshold for threshold, _ in BAT_SPEED_TIERS)
    exit_velo_cutoff = min(threshold for threshold, _ in QUALITY_CONTACT_TIERS)

    hard_exit_velo_cutoff = 95
    very_hard_exit_velo_cutoff = 105
    elite_exit_velo_cutoff = 115

    for game_date, at_bats in sorted(ab_by_date.items()):
        scored_at_bats = [ab for ab in at_bats if ab.is_valid_ab()]

        daily_pitches = 0
        daily_swings = 0
        daily_whiffs = 0
        daily_bunt_swings = 0

        daily_nonbunt_swings = 0
        daily_nonbunt_whiffs = 0

        daily_bat_speeds = []
        daily_speedq_swings = 0
        daily_speedq_whiffs = 0
        excluded_bat_speed_count = 0
        missing_bat_speed_count = 0

        daily_exit_velos = []
        excluded_exit_velo_count = 0
        missing_exit_velo_count = 0

        daily_contact_ev = 0
        daily_hard = 0
        daily_vhard = 0
        daily_elite = 0
        missing_power_exit_velo_count = 0

        daily_power_pairs = []
        daily_power_vs_misses_pairs = []

        for ab in at_bats:
            for pitch in ab.pitches:
                exit_velo = pitch.exit_velo
                bat_speed = pitch.bat_speed
                daily_pitches += 1
                if pitch.description in SWING_DESCRIPTIONS:
                    daily_swings += 1
                    is_whiff = pitch.description in WHIFF_DESCRIPTIONS
                    if is_whiff:
                        daily_whiffs += 1

                    if pitch.description in BUNT_SWING_DESCRIPTIONS:
                        daily_bunt_swings += 1
                    else:
                        daily_nonbunt_swings += 1
                        if is_whiff:
                            daily_nonbunt_whiffs += 1

                        # Average speed and speed-qualified whiffs use the same swings.
                        if bat_speed is None or not math.isfinite(bat_speed) or bat_speed <= 0:
                            missing_bat_speed_count += 1
                        elif bat_speed > bat_speed_cutoff:
                            daily_bat_speeds.append(bat_speed)
                            daily_speedq_swings += 1
                            daily_power_vs_misses_pairs.append(
                                (bat_speed, pitch.description)
                            )
                            if is_whiff:
                                daily_speedq_whiffs += 1
                        else:
                            excluded_bat_speed_count += 1

                # The loader represents missing measurements with zero.
                if pitch.description in CONTACT_DESCRIPTIONS:
                    if exit_velo is None or not math.isfinite(exit_velo) or exit_velo <= 0:
                        missing_exit_velo_count += 1
                    elif exit_velo > exit_velo_cutoff:
                        daily_exit_velos.append(exit_velo)
                    else:
                        excluded_exit_velo_count += 1

                # Power rates include weak measured contact, but not misses or bunts.
                if (
                    pitch.description in SWING_DESCRIPTIONS
                    and pitch.description not in WHIFF_DESCRIPTIONS
                    and pitch.description not in BUNT_SWING_DESCRIPTIONS
                    and bat_speed is not None
                    and math.isfinite(bat_speed)
                    and bat_speed > bat_speed_cutoff
                ):
                    if exit_velo is None or not math.isfinite(exit_velo) or exit_velo <= 0:
                        missing_power_exit_velo_count += 1
                    else:
                        daily_contact_ev += 1
                        if exit_velo >= hard_exit_velo_cutoff:
                            daily_hard += 1
                        if exit_velo >= very_hard_exit_velo_cutoff:
                            daily_vhard += 1
                        if exit_velo >= elite_exit_velo_cutoff:
                            daily_elite += 1

                if (
                    pitch.description in POWER_CONTACT_DESCRIPTIONS
                    and bat_speed is not None
                    and math.isfinite(bat_speed)
                    and bat_speed > bat_speed_cutoff
                    and exit_velo is not None
                    and math.isfinite(exit_velo)
                    and exit_velo > 0
                ):
                    if pitch.description in ("foul", "foul_tip"):
                        weight = 0.6
                    else:
                        weight = 1.0
                    daily_power_pairs.append((bat_speed, exit_velo, weight))

        qualifying_exit_velos.extend(daily_exit_velos)
        qualifying_bat_speeds.extend(daily_bat_speeds)
        qualifying_power_pairs.extend(daily_power_pairs)
        qualifying_power_vs_misses_pairs.extend(daily_power_vs_misses_pairs)
        

        daily_avg_exit_velo = sum(daily_exit_velos) / len(daily_exit_velos) if daily_exit_velos else None
        daily_avg_bat_speed = sum(daily_bat_speeds) / len(daily_bat_speeds) if daily_bat_speeds else None

        daily_data.append({
            "date": game_date,
            "tor": player_tor(scored_at_bats) if scored_at_bats else None,
            "tor_z_score": None,
            # Retained as the TOR weight; total appearances also include HBP/IBB.
            "plate_appearances": len(scored_at_bats),
            "total_plate_appearances": len(at_bats),

            "pitch_count": daily_pitches,
            "swing_count": daily_swings,
            "whiff_count": daily_whiffs,
            "bunt_swing_count": daily_bunt_swings,
            "swing_rate": daily_swings / daily_pitches if daily_pitches else None,
            "whiff_rate": daily_whiffs / daily_swings if daily_swings else None,
            "swstr_rate": daily_whiffs / daily_pitches if daily_pitches else None,

            "nonbunt_swing_count": daily_nonbunt_swings,
            "nonbunt_whiff_count": daily_nonbunt_whiffs,
            "nonbunt_whiff_rate": daily_nonbunt_whiffs / daily_nonbunt_swings if daily_nonbunt_swings else None,

            "speedq_swing_count": daily_speedq_swings,
            "speedq_whiff_count": daily_speedq_whiffs,
            "speedq_whiff_rate": daily_speedq_whiffs / daily_speedq_swings if daily_speedq_swings else None,
            "avg_bat_speed": daily_avg_bat_speed,
            "bat_speed_z_score": None,
            "qualifying_bat_speed_count": len(daily_bat_speeds),
            "excluded_bat_speed_count": excluded_bat_speed_count,
            "missing_bat_speed_count": missing_bat_speed_count,

            "avg_exit_velo": daily_avg_exit_velo,
            "exit_velo_z_score": None,
            "qualifying_exit_velo_count": len(daily_exit_velos),
            "excluded_exit_velo_count": excluded_exit_velo_count,
            "missing_exit_velo_count": missing_exit_velo_count,

            "contact_exit_velo_count": daily_contact_ev,
            "missing_power_exit_velo_count": missing_power_exit_velo_count,
            "hard_exit_velo_count": daily_hard,
            "hard_contact_rate": daily_hard / daily_contact_ev if daily_contact_ev else None,
            "very_hard_exit_velo_count": daily_vhard,
            "very_hard_contact_rate": daily_vhard / daily_contact_ev if daily_contact_ev else None,
            "elite_exit_velo_count": daily_elite,
            "elite_contact_rate": daily_elite / daily_contact_ev if daily_contact_ev else None,
        })

    # Window-relative variation of daily means, not a league or per-PA reference.
    scored_days = [day for day in daily_data if day["plate_appearances"] > 0]
    total_pas = sum(day["plate_appearances"] for day in scored_days)
    if total_pas > 1:
        weighted_tor_sum = sum(day["tor"] * day["plate_appearances"] for day in scored_days)
        mean_tor = weighted_tor_sum / total_pas

        weighted_variance_tor = sum(
            day["plate_appearances"] * (day["tor"] - mean_tor) ** 2
            for day in scored_days
        ) / total_pas

        stddev_tor = math.sqrt(weighted_variance_tor)

        for day in scored_days:
            if stddev_tor > 0:
                day["tor_z_score"] = round((day["tor"] - mean_tor) / stddev_tor, 2)
            else:
                day["tor_z_score"] = 0

    # Daily EV means relative to individual qualifying measurements in this window.
    if len(qualifying_exit_velos) > 1:
        mean_exit_velo = sum(qualifying_exit_velos) / len(qualifying_exit_velos)
        variance_exit_velo = sum(
            (exit_velo - mean_exit_velo) ** 2 for exit_velo in qualifying_exit_velos
        ) / len(qualifying_exit_velos)
        
        stddev_exit_velo = math.sqrt(variance_exit_velo)
        
        for day in daily_data:
            if day["avg_exit_velo"] is None:
                day["exit_velo_z_score"] = None
            elif stddev_exit_velo > 0:
                day["exit_velo_z_score"] = round((day["avg_exit_velo"] - mean_exit_velo) / stddev_exit_velo, 2)
            else:
                day["exit_velo_z_score"] = 0
                
    # Daily bat speed means relative to individual qualifying measurements in this window.
    if len(qualifying_bat_speeds) > 1:
        mean_bat_speed = sum(qualifying_bat_speeds) / len(qualifying_bat_speeds)
        variance_bat_speed = sum(
            (bat_speed - mean_bat_speed) ** 2 for bat_speed in qualifying_bat_speeds
        ) / len(qualifying_bat_speeds)
        
        stddev_bat_speed = math.sqrt(variance_bat_speed)
        
        for day in daily_data:
            if day["avg_bat_speed"] is None:
                day["bat_speed_z_score"] = None
            elif stddev_bat_speed > 0:
                day["bat_speed_z_score"] = round((day["avg_bat_speed"] - mean_bat_speed) / stddev_bat_speed, 2)
            else:
                day["bat_speed_z_score"] = 0

    # Pool contacts across the selected window, not daily correlations.
    bs_ev_correlation_index = None

    bs_ev_tier_profile = {
        tier: {
            "bs_sum": 0.0,
            "weighted_ev_sum": 0.0,
            "weight_sum": 0.0,
            "contact_count": 0,
        }
        for tier in BAT_SPEED_PROFILE_TIERS
    }
    for bat_speed, exit_velo, weight in qualifying_power_pairs:
        tier = bat_speed_profile_tier(bat_speed)

        data = bs_ev_tier_profile[tier]
        data["bs_sum"] += bat_speed * weight
        data["weighted_ev_sum"] += exit_velo * weight
        data["weight_sum"] += weight
        data["contact_count"] += 1

    for data in bs_ev_tier_profile.values():
        if data["weight_sum"] > 0:
            data["avg_bat_speed"] = data["bs_sum"] / data["weight_sum"]
            data["avg_exit_velo"] = data["weighted_ev_sum"] / data["weight_sum"]
        else:
            data["avg_bat_speed"] = None
            data["avg_exit_velo"] = None

    populated_tiers = [
        data for data in bs_ev_tier_profile.values() if data["weight_sum"] > 0
    ]
    if len(populated_tiers) >= 3:
        bat_speed_means = [data["avg_bat_speed"] for data in populated_tiers]
        exit_velo_means = [data["avg_exit_velo"] for data in populated_tiers]
        if (
            max(bat_speed_means) > min(bat_speed_means)
            and max(exit_velo_means) > min(exit_velo_means)
        ):
            bs_ev_correlation_index = float(
                np.corrcoef(bat_speed_means, exit_velo_means)[0, 1]
            )

    power_vs_misses_profile = {
        tier: {
            "swing_count": 0,
            "tiered_whiff_count": 0,
            "tiered_whiff_rate": None,
        }
        for tier in BAT_SPEED_PROFILE_TIERS
    }

    for bat_speed, description in qualifying_power_vs_misses_pairs:
        tier = bat_speed_profile_tier(bat_speed)

        data = power_vs_misses_profile[tier]
        data["swing_count"] += 1
        if description in WHIFF_DESCRIPTIONS:
            data["tiered_whiff_count"] += 1

    for data in power_vs_misses_profile.values():
        data["tiered_whiff_rate"] = (
            data["tiered_whiff_count"] / data["swing_count"]
            if data["swing_count"] else None
        )

    return {
        "daily_data": daily_data,
        "summary": {
            "bs_ev_correlation_index": bs_ev_correlation_index,
            "bs_ev_tier_profile": bs_ev_tier_profile,
            "contact_count": len(qualifying_power_pairs),
            "populated_tier_count": len(populated_tiers),
            "tiered_whiff_rate": {tier: data["tiered_whiff_rate"] for tier, data in power_vs_misses_profile.items()},
            "power_vs_misses_profile": power_vs_misses_profile,
        },
    }