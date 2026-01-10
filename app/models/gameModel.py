from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class GameCreate(BaseModel):
    pgn: str

class GameInDB(GameCreate):
    id: str = Field(alias="_id")
    analyzed: bool = False
    created_at: datetime
    
    class Config:
        populate_by_name = True