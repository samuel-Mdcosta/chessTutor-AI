from fastapi import FastAPI
from fastapi.params import Body
from app.models.pgn_request import PgnRequest
from app.service.game_analysis import analyze_game, process_full_game
import chess.pgn
from io import StringIO


app = FastAPI(title="Chess Tutor")

@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/analyze")
async def analyze_pgn(
    pgn: str = Body(..., media_type="text/plain")
):
    try:
        # O await aqui é essencial para esperar o Stockfish terminar o trabalho
        result = await process_full_game(pgn)
        return result
    except Exception as e:
        return {"error": str(e)}