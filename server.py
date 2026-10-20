from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from scorer import player_tor
from fastapi.templating import Jinja2Templates

from fetcher import build_at_bats, load_statcast_csv
from scorer import rank_players

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Loaded once at server startup, not per-request.
df = load_statcast_csv("statcast_data/2026_to_date.csv")

def get_all_at_bats(df):
    players = df["batter_name"].unique()
    all_at_bats = []
    for player in players:
        all_at_bats.extend(build_at_bats(df, player))
    return all_at_bats

all_at_bats = get_all_at_bats(df)


@app.get("/")
def leaderboard(request: Request):
    ranked = rank_players(all_at_bats, min_pas=100)
    rows = [
        {"rank": i, "player": name, "tor": round(score, 2)}
        for i, (name, score) in enumerate(ranked, start=1)
    ]
    return templates.TemplateResponse(
        request, "leaderboard.html", {"rows": rows}
    )

@app.get("/api/player/{player_name}")
def player_details(player_name: str):
    player_at_bats = build_at_bats(df, player_name)
    if not player_at_bats:
        return {"error": "Player not found"}
    tor_score = round(player_tor(player_at_bats), 2)

    player_df = df[df["batter_name"] == player_name]
    valid_ev = player_df[player_df["launch_speed"] > 0]["launch_speed"]
    valid_bs = player_df[player_df["bat_speed"] > 0]["bat_speed"]

    avg_ev = round(valid_ev.mean(), 1) if not valid_ev.empty else 0
    max_ev = round(valid_ev.max(), 1) if not valid_ev.empty else 0
    avg_bs = round(valid_bs.mean(), 1) if not valid_bs.empty else 0
    max_bs = round(valid_bs.max(), 1) if not valid_bs.empty else 0

    hard_hits = len(valid_ev[valid_ev >= 95])
    hard_hit_rate = round(hard_hits / len(valid_ev), 3) if not valid_ev.empty else 0

    return {
        "player": player_name,
        "tor": tor_score,
        "avg_ev": avg_ev,
        "max_ev": max_ev,
        "avg_bs": avg_bs,
        "max_bs": max_bs,
        "hard_hits": hard_hits,
        "hard_hit_rate": hard_hit_rate
    }