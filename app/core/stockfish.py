import chess.engine
import chess
import os
import platform

system_platform = platform.system()

if system_platform == "Windows":
    ENGINE_PATH = os.path.join("engineStockfish", "stockfish-windows-x86-64-avx2.exe")
else:
    ENGINE_PATH = os.path.join("engineStockfish", "stockfish_linux")

    if os.path.exists(ENGINE_PATH):
        os.chmod(ENGINE_PATH, 0o755)

def get_engine():
    return chess.engine.SimpleEngine.popen_uci(ENGINE_PATH)

def analyze_game(board, depth=15):
    engine = get_engine()


def analyze_position(engine, board: chess.Board, time_limit: float = 0.1):
    info = engine.analyse(board, chess.engine.Limit(time=time_limit))

    score = info["score"].white()

    mate = score.mate()

    cp = score.score()

    best_move = info.get("pv")[0] if info.get("pv") else None

    return{
        "fen": board.fen(),
        "best_move": str(best_move),
        "evaluation": {
            "type": "mate" if mate is not None else "cp",
            "value": mate if mate is not None else cp
        }
    }