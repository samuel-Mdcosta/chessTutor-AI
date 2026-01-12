from fastapi import FastAPI, Body
from contextlib import asynccontextmanager
from app.models.pgn_request import PgnRequest
from app.service.game_analysis import process_full_game
from app.database.database import connect_to_mongo, close_mongo_connection
from app.service.gameService import save_pgn_for_user
from app.models.gameModel import GameCreate
from app.service.userService import creat_user
from app.models.userModel import UserCreate 
from app.service.tutorService import generate_coach_report
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()

app = FastAPI(title="Chess Tutor", lifespan=lifespan)

origins = [
    "http://localhost:5173",    
    "http://127.0.0.1:5173",    
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],       
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/register")
async def register_user(user: UserCreate): 
    return await creat_user(user)

@app.post("/users/{username}/games")
async def add_game(username: str, pgn_text: str = Body(..., media_type="text/plain")):
    game_data = GameCreate(pgn=pgn_text)
    return await save_pgn_for_user(username, game_data)

@app.post("/users/{username}/report")
async def get_coach_report(username: str):
    return await generate_coach_report(username)

@app.post("/analyze")
async def analyze_pgn(
    pgn: str = Body(..., media_type="text/plain")
):
    try:
        result = await process_full_game(pgn)
        return result
    except Exception as e:
        return {"error": str(e)}