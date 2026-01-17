import chess.engine
import os
import platform
import stat

current_dir = os.path.dirname(os.path.abspath(__file__))

base_dir = os.path.dirname(os.path.dirname(current_dir))

system_platform = platform.system()

if system_platform == "Windows":
    engine_filename = "stockfish-windows-x86-64-avx2.exe"
else:
    engine_filename = "stockfish_linux"

ENGINE_PATH = os.path.join(base_dir, "engineStockfish", engine_filename)

print(f"--- TENTANDO CARREGAR STOCKFISH EM: {ENGINE_PATH} ---")

if system_platform != "Windows":
    if os.path.exists(ENGINE_PATH):
        st = os.stat(ENGINE_PATH)
        os.chmod(ENGINE_PATH, st.st_mode | stat.S_IEXEC)
    else:
        print(f"ERRO CRÍTICO: Arquivo não encontrado em {ENGINE_PATH}")

def get_engine():
    try:
        return chess.engine.SimpleEngine.popen_uci(ENGINE_PATH)
    except Exception as e:
        print(f"Erro ao iniciar Stockfish: {e}")
        raise e

def analyze_position(engine, board: chess.Board, time_limit: float = 0.1):
    info = engine.analyse(board, chess.engine.Limit(time=time_limit))
    score = info["score"].white()
    
    mate = score.mate()
    cp = score.score()

    best_move = info.get("pv")[0] if info.get("pv") else None

    return {
        "fen": board.fen(),
        "best_move": str(best_move),
        "evaluation": {
            "type": "mate" if mate is not None else "cp",
            "value": mate if mate is not None else cp
        }
    }