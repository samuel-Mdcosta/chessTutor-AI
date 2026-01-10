from app.database.database import get_database
from app.models.userModel import UserCreate

async def creat_user(user: UserCreate):
    db = await get_database()
    user_collection = db["users"]
    
    user_dict = {
        "username": user.username,
        "email": user.email,
        "password": user.password,
    }

    result = await user_collection.insert_one(user_dict)
    
    return {
        "id": str(result.inserted_id),
        "username": user.username,
        "message": "Usuário criado com sucesso!"
    }