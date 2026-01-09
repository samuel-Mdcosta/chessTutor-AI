from fastapi import FastAPI
from fastapi.params import Body
from app.models.pgn_request import PgnRequest
from app.service.game_analysis import analyze_game
import chess.pgn
from io import StringIO

app = FastAPI(title="Chess Tutor")

@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/analyze")
def analyze_pgn(
    pgn: str = Body(..., media_type="text/plain")
):
    return analyze_game(pgn)