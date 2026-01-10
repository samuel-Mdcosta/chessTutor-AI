import chess.pgn
import io
from fastapi import HTTPException
from app.database.database import get_database
from app.models.gameModel import GameCreate

async def save_pgn_for_user(username: str, game_data: GameCreate):
    db = await get_database()

    user = await db["users"].find_one({"username": username})

    if not user:
        raise HTTPException(status_code=404, detail=f"Usuário '{username}' não encontrado.")

    pgn_io = io.StringIO(game_data.pgn)
    
    try:
        # A biblioteca lê o PGN e separa headers dos lances
        parsed_game = chess.pgn.read_game(pgn_io)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PGN inválido ou corrompido: {str(e)}")

    if parsed_game is None:
        raise HTTPException(status_code=400, detail="Nenhuma partida encontrada no texto fornecido.")

    headers = parsed_game.headers
    
    games_collection = db["games"]
    
    new_game = {
        "user_id": str(user["_id"]),
        "original_pgn": game_data.pgn,
        "white_player": headers.get("White", "?"),
        "black_player": headers.get("Black", "?"),
        "result": headers.get("Result", "*"),
        "date": headers.get("Date", ""),
        "event": headers.get("Event", ""),
        "eco": headers.get("ECO", ""),
        "moves": str(parsed_game.mainline_moves()), 
        "analyzed": False,
    }
    
    result = await games_collection.insert_one(new_game)
    
    return {
        "message": "Partida processada e salva!",
        "game_id": str(result.inserted_id),
        "white": new_game["white_player"],
        "black": new_game["black_player"],
        "result": new_game["result"]
    }