from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

fake_leaderboard = [
    {"rank": 1, "player": "Ruth, Babe", "tor": 99.9},
    {"rank": 2, "player": "Bonds, Barry", "tor": 95.3},
    {"rank": 3, "player": "Trout, Mike", "tor": 92.1},
]

@app.get("/")
def dummy_leaderboard(request: Request):
    rows = [
        {"rank": i, "player": player["player"], "tor": player["tor"]}
        for i, player in enumerate(fake_leaderboard, start=1)
    ]
    return templates.TemplateResponse(request=request, name="leaders.html", context={"rows": rows})