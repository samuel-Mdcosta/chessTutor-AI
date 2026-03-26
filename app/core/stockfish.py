import chess.engine
import os
import platform
import stat
import queue
import logging
import asyncio

logger = logging.getLogger("stockfish")

current_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(os.path.dirname(current_dir))
system_platform = platform.system()

if system_platform == "Windows":
    engine_filename = "stockfish-windows-x86-64-avx2.exe"
else:
    engine_filename = "stockfish_linux"

ENGINE_PATH = os.path.join(base_dir, "engineStockfish", engine_filename)

logger.info(f"Stockfish path: {ENGINE_PATH}")

if system_platform != "Windows":
    if os.path.exists(ENGINE_PATH):
        st = os.stat(ENGINE_PATH)
        os.chmod(ENGINE_PATH, st.st_mode | stat.S_IEXEC)
    else:
        logger.error(f"Arquivo não encontrado em {ENGINE_PATH}")

# --- Pool de engines reutilizáveis ---
POOL_SIZE = 2
_engine_pool: queue.Queue = queue.Queue(maxsize=POOL_SIZE)

def _create_engine():
    try:
        engine = chess.engine.SimpleEngine.popen_uci(ENGINE_PATH)
        return engine
    except Exception as e:
        logger.error(f"Erro ao iniciar Stockfish: {e}")
        raise e

def init_engine_pool():
    for _ in range(POOL_SIZE):
        _engine_pool.put(_create_engine())
    logger.info(f"Pool de {POOL_SIZE} engines Stockfish inicializado")

def shutdown_engine_pool():
    while not _engine_pool.empty():
        try:
            engine = _engine_pool.get_nowait()
            engine.quit()
        except Exception:
            pass
    logger.info("Pool de engines Stockfish encerrado")

def acquire_engine():
    try:
        return _engine_pool.get(timeout=30)
    except queue.Empty:
        logger.warning("Pool vazio, criando engine temporária")
        return _create_engine()

def release_engine(engine):
    try:
        engine.ping()
        _engine_pool.put_nowait(engine)
    except Exception:
        logger.warning("Engine inválida, criando substituta")
        try:
            engine.quit()
        except Exception:
            pass
        try:
            _engine_pool.put_nowait(_create_engine())
        except queue.Full:
            pass

def get_engine():
    return _create_engine()

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