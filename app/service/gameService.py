from datetime import datetime
from bson import ObjectId
from app.database.database import get_database
from app.models.gameModel import GameCreate

async def save_pgn_for_user(game_data: GameCreate):
    db = await get_database()
    games_collection = db["games"] # Coleção separada
    
    # Verifica se o user_id é válido (se existe mesmo esse usuário)
    users_collection = db["users"]
    try:
        user_obj = await users_collection.find_one({"_id": ObjectId(game_data.user_id)})
        if not user_obj:
            return {"error": "Usuário não encontrado. Não é possível salvar a partida."}
    except:
        return {"error": "ID de usuário inválido."}

    # Prepara o documento
    new_game = {
        "user_id": game_data.user_id, # <--- O VÍNCULO
        "pgn": game_data.pgn,
        "analyzed": False,            # Flag para a IA saber que precisa ler depois
    }
    
    result = await games_collection.insert_one(new_game)
    
    return {
        "message": "Partida salva!",
        "game_id": str(result.inserted_id),
        "user_id_linked": game_data.user_id
    }