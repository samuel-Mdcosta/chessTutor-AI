import chess.engine

ENGINE_PATH = "engineStockfish/stockfish-windows-x86-64-avx2.exe"

engine = chess.engine.SimpleEngine.popen_uci(ENGINE_PATH)

def analyze_game(board, depth=15):
    return engine.analyse(board, chess.engine.Limit(depth=depth))