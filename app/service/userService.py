from fastapi import HTTPException
from app.database.database import get_database
from app.models.userModel import UserCreate
from app.models.userModel import userLogin


async def creat_user(user: UserCreate):
    db = await get_database()
    user_collection = db["users"]

    if await user_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Ops! Esse email já está cadastrado.")
        
    if await user_collection.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Ops! Esse nome de usuário já existe.")
    
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

async def authenticate_user(user_data: userLogin):
    db = await get_database()
    user_collection = db["users"]

    user = await user_collection.find_one({"email": user_data.email})

    if not user:
        raise HTTPException(status_code=400, detail="Email não encontrado.")

    if user["password"] != user_data.password:
        raise HTTPException(status_code=400, detail="Senha incorreta.")

    return {
        "message": "Login realizado com sucesso",
        "username": user["username"],
        "user_id": str(user["_id"])
    }