import hashlib
from functools import lru_cache
from fastapi import HTTPException
from app.database.mongo import get_database
from app.ia.prompts import build_tutor_prompt
from app.ia.client import get_gemini_analysis

async def generate_coach_report(username: str):
    db = await get_database()

    user = await db["users"].find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    cursor = db["games"].find({"user_id": str(user["_id"])}).sort("created_at", -1).limit(10)
    games = await cursor.to_list(length=None)

    if not games:
        return {
            "player": username,
            "message": "Nenhuma partida encontrada para análise. Jogue ou importe partidas primeiro."
        }

    pgns_concatenated = ""
    for i, game in enumerate(games, 1):
        content = game.get("original_pgn") or game.get("pgn", "")
        result = game.get("result", "?")
        white = game.get("white_player", "?")
        black = game.get("black_player", "?")
        
        pgns_concatenated += f"--- PARTIDA {i} ({white} vs {black} | Resultado: {result}) ---\n{content}\n\n"

    print(f"🤖 Gerando prompt para {len(games)} partidas...")
    final_prompt = build_tutor_prompt(
        username=username, 
        pgns_text=pgns_concatenated, 
        total_games=len(games)
    )

    ai_response = await get_gemini_analysis(final_prompt)

    return {
        "player": username,
        "games_analyzed": len(games),
        "tutor_report": ai_response
    }

async def get_chache(pgn_hash: str):
    db = await get_database()
    chached = await db["tutor_cache"].find_one({"pgn_hash": pgn_hash})
    if chached:
        return chached['result']
    return None

async def save_cache(pgn_hash: str, result: str):
    db = await get_database()
    await db["tutor_cache"].insert_one(
        {"pgn_hash": pgn_hash, "result": result}
    )