from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
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
