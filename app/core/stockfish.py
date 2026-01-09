import chess.engine
import chess
import os

ENGINE_PATH = "engineStockfish/stockfish-windows-x86-64-avx2.exe"

engine = chess.engine.SimpleEngine.popen_uci(ENGINE_PATH)

def analyze_game(board, depth=15):
    return engine.analyse(board, chess.engine.Limit(depth=depth))

def get_engine():
    return engine

def analyze_position(engine, board: chess.Board, time_limit: float = 0.1):
    info = engine.analyse(board, chess.engine.Limit(time=time_limit))

    #score#
    score = info["score"].white() #padrao da perspectiva das brancas#

    #mate#
    mate = score.mate()

    #quando for mate retorna 0#
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