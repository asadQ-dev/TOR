from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

fake_leaderboard = [
    {"rank": 1, "player": "Ruth, Babe", "tor": 99.9},
    {"rank": 2, "player": "Bonds, Barry", "tor": 95.3},
    {"rank": 3, "player": "Trout, Mike", "tor": 92.1},
]

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
def leaders(request: Request):
    rows = fake_leaderboard
    return templates.TemplateResponse(request, "leaders.html", {"rows": rows})
    for ab in at_bats:
        ranked = sorted(at_bats)
    return ranked