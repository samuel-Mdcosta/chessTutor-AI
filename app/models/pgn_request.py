from pydantic import BaseModel

class PgnRequest(BaseModel):
    pgn: str