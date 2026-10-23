import math

from at_bat import CONTACT_DESCRIPTIONS, QUALITY_CONTACT_TIERS
from scorer import player_tor


def group_by_date(player_at_bats):
    ab_by_date = {}
    for ab in player_at_bats:
        if not ab.is_valid_ab():
            continue
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
    qualifying_exit_velos = []
    exit_velo_cutoff = min(threshold for threshold, _ in QUALITY_CONTACT_TIERS)

    for game_date, at_bats in sorted(ab_by_date.items()):
        daily_exit_velos = []
        excluded_exit_velo_count = 0
        missing_exit_velo_count = 0
        for ab in at_bats:
            for pitch in ab.pitches:
                if pitch.description not in CONTACT_DESCRIPTIONS:
                    continue
                exit_velo = pitch.exit_velo
                # The loader represents missing exit velocity with zero.
                if exit_velo is None or not math.isfinite(exit_velo) or exit_velo <= 0:
                    missing_exit_velo_count += 1
                elif exit_velo > exit_velo_cutoff:
                    daily_exit_velos.append(exit_velo)
                else:
                    excluded_exit_velo_count += 1
        qualifying_exit_velos.extend(daily_exit_velos)

        daily_avg_exit_velo = sum(daily_exit_velos) / len(daily_exit_velos) if daily_exit_velos else None

        daily_data.append({
            "date": game_date,
            "tor": player_tor(at_bats),
            "plate_appearances": len(at_bats),
            "avg_exit_velo": daily_avg_exit_velo,
            "qualifying_exit_velo_count": len(daily_exit_velos),
            "excluded_exit_velo_count": excluded_exit_velo_count,
            "missing_exit_velo_count": missing_exit_velo_count,
            "exit_velo_z_score": None,
        })

    # Window-relative variation of daily means, not a league or per-PA reference.
    total_pas = sum(day["plate_appearances"] for day in daily_data)
    if total_pas > 1:
        weighted_tor_sum = sum(day["tor"] * day["plate_appearances"] for day in daily_data)
        mean_tor = weighted_tor_sum / total_pas

        weighted_variance_tor = sum(
            day["plate_appearances"] * (day["tor"] - mean_tor) ** 2
            for day in daily_data
        ) / total_pas

        stddev_tor = math.sqrt(weighted_variance_tor)

        for day in daily_data:
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
            if stddev_exit_velo > 0 and day["avg_exit_velo"] is not None:
                day["exit_velo_z_score"] = round((day["avg_exit_velo"] - mean_exit_velo) / stddev_exit_velo, 2)
    return daily_data