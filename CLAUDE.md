# chessTutor — Backend (FastAPI + Python)

## Stack
- Python / FastAPI (async)
- MongoDB via Motor (async) + PyMongo
- Google Gemini API (`app/ia/`)
- Stockfish chess engine (`app/core/stockfish.py`)
- python-chess for PGN parsing and move validation

## Source layout (read these)
```
app/
├── main.py              # FastAPI entry point, CORS, lifespan, routes
├── models.py            # Shared model definitions
├── core/
│   ├── analyze.py       # Core analysis logic
│   ├── pgnGetter.py     # PGN fetching helpers
│   └── stockfish.py     # Stockfish engine pool
├── database/
│   └── mongo.py         # MongoDB connection/client
├── ia/
│   ├── client.py        # Gemini API client
│   └── prompts.py       # LLM prompt templates
├── models/
│   ├── gameModel.py
│   ├── pgn_request.py
│   └── userModel.py
└── service/
    ├── gameService.py
    ├── game_analysis.py  # Full game analysis pipeline
    ├── pgn_parser.py
    ├── single_analysis.py
    ├── tutorService.py   # Coaching/tutor logic with caching
    └── userService.py    # Auth and user management
```

## Ignore (do not read unless explicitly asked)
- `.venv/` — Python virtual environment
- `**/__pycache__/` — Compiled bytecode
- `.env` — Secrets file
- `requirements.txt` — Only relevant when adding/removing dependencies
- `models.py` (root-level) — Prefer `app/models/`

## Key conventions
- All business logic lives in `app/service/`
- AI/LLM interactions are isolated in `app/ia/`
- Database access goes through `app/database/mongo.py`
- Entry point is `app/main.py`; run via `uvicorn app.main:app`
